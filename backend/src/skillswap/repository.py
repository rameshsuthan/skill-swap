import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from .models import CATALOG, ActorContext, MemberProfile
from .settings import ROOT


class Repository:
    def __init__(self, db_path: Path):
        self.path = Path(db_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connection() as db:
            db.executescript("""CREATE TABLE IF NOT EXISTS profiles(id TEXT PRIMARY KEY, data TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS metadata(key TEXT PRIMARY KEY,value INTEGER);
            INSERT OR IGNORE INTO metadata VALUES('revision',0);
            CREATE TABLE IF NOT EXISTS proposals(id TEXT PRIMARY KEY, idempotency_key TEXT UNIQUE, member_id TEXT, cohort_id TEXT, run_id TEXT, fingerprint TEXT, data TEXT);""")

    @contextmanager
    def connection(self):
        db = sqlite3.connect(self.path, timeout=5)
        db.execute("PRAGMA journal_mode=WAL")
        db.execute("PRAGMA busy_timeout=5000")
        try:
            with db:
                yield db
        finally:
            db.close()

    def seed_demo(self, profiles):
        from .scheduling import normalize_window, zone

        validated = [MemberProfile.model_validate(p) for p in profiles]
        for p in validated:
            zone(p.timezone)
            for w in p.availability:
                if w.source.timezone != p.timezone or normalize_window(w.source) != w:
                    raise ValueError("availability_provenance_mismatch")
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            db.execute("DELETE FROM profiles")
            db.executemany(
                "INSERT INTO profiles VALUES(?,?)", [(p.id, p.model_dump_json()) for p in validated]
            )
            db.execute("UPDATE metadata SET value=value+1 WHERE key='revision'")
        return len(validated)

    def ensure_seeded(self):
        with self.connection() as db:
            count = db.execute("SELECT COUNT(*) FROM profiles").fetchone()[0]
        if not count:
            self.seed_demo(json.loads((ROOT / "data/demo_cohort.json").read_text()))

    def get_context(self, ctx: ActorContext, db=None):
        if db is None:
            with self.connection() as conn:
                return self.get_context(ctx, conn)
        profiles = [
            json.loads(row[0]) for row in db.execute("SELECT data FROM profiles ORDER BY id")
        ]
        profiles = [p for p in profiles if p["cohort_id"] == ctx.cohort_id and p["active"]]
        member = next((p for p in profiles if p["id"] == ctx.member_id), None)
        if not member:
            raise ValueError("actor_not_found")
        revision = db.execute("SELECT value FROM metadata WHERE key='revision'").fetchone()[0]
        return dict(catalog=CATALOG, member=member, profiles=profiles, dataset_revision=revision)

    def update_profile(self, member_id, **changes):
        """Explicit demo maintenance; never exposed as a model tool."""
        from .scheduling import normalize_window, zone

        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT data FROM profiles WHERE id=?", (member_id,)).fetchone()
            if not row:
                raise ValueError("profile_not_found")
            old = json.loads(row[0])
            if (
                "timezone" in changes
                and changes["timezone"] != old["timezone"]
                and "availability" not in changes
            ):
                raise ValueError("revalidated_availability_required")
            value = MemberProfile.model_validate({**old, **changes})
            zone(value.timezone)
            for w in value.availability:
                if w.source.timezone != value.timezone or normalize_window(w.source) != w:
                    raise ValueError("availability_provenance_mismatch")
            db.execute(
                "UPDATE profiles SET data=? WHERE id=?", (value.model_dump_json(), member_id)
            )
            db.execute("UPDATE metadata SET value=value+1 WHERE key='revision'")

    def remove_availability(self, member_id, date):
        with self.connection() as db:
            p = json.loads(
                db.execute("SELECT data FROM profiles WHERE id=?", (member_id,)).fetchone()[0]
            )
        self.update_profile(
            member_id,
            availability=[w for w in p["availability"] if not w["start_utc"].startswith(date)],
        )

    def save_proposal(self, ctx, plan, approval_fingerprint, idempotency_key):
        from datetime import datetime, timezone
        from uuid import uuid4

        from .matching import fingerprint_plan, validate_plan

        if plan.cohort_id != ctx.cohort_id or plan.member_id != ctx.member_id:
            raise ValueError("scope_mismatch")
        if (
            plan.fingerprint != approval_fingerprint
            or fingerprint_plan(plan) != approval_fingerprint
        ):
            raise ValueError("approval_mismatch")
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            existing = db.execute(
                "SELECT data FROM proposals WHERE idempotency_key=?", (idempotency_key,)
            ).fetchone()
            if existing:
                saved = json.loads(existing[0])
                if saved["plan"]["fingerprint"] != approval_fingerprint or saved[
                    "actor"
                ] != ctx.model_dump(mode="json"):
                    raise ValueError("idempotency_conflict")
                return saved
            context = self.get_context(ctx, db)
            profiles = {p["id"]: MemberProfile.model_validate(p) for p in context["profiles"]}
            validation = validate_plan(
                plan, profiles, context["dataset_revision"], set(ctx.exclusions)
            )
            if not validation.valid:
                raise ValueError(",".join(validation.issues))
            result = dict(
                id=str(uuid4()),
                actor=ctx.model_dump(mode="json"),
                plan=plan.model_dump(mode="json"),
                idempotency_key=idempotency_key,
                status="awaiting_participant_confirmation",
                created_at=datetime.now(timezone.utc).isoformat(),
            )
            db.execute(
                "INSERT INTO proposals VALUES(?,?,?,?,?,?,?)",
                (
                    result["id"],
                    idempotency_key,
                    ctx.member_id,
                    ctx.cohort_id,
                    ctx.run_id,
                    approval_fingerprint,
                    json.dumps(result),
                ),
            )
            return result

    def get_proposal_status(self, ctx, *, idempotency_key=None, proposal_id=None):
        if bool(idempotency_key) == bool(proposal_id):
            raise ValueError("exactly_one_lookup_key_required")
        column = "idempotency_key" if idempotency_key else "id"
        with self.connection() as db:
            row = db.execute(
                f"SELECT data FROM proposals WHERE {column}=? AND member_id=? AND cohort_id=?",
                (idempotency_key or proposal_id, ctx.member_id, ctx.cohort_id),
            ).fetchone()
            return json.loads(row[0]) if row else None
