import asyncio
import sqlite3
import time
from contextlib import contextmanager
from typing import TypedDict
from uuid import uuid4

from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt

from .agents import build_agents
from .model_factory import error_code
from .models import ActorContext


class RunState(TypedDict, total=False):
    actor: dict
    request: str
    goal: dict | None
    plan: dict | None
    result: dict | None
    status: str
    question: str | None
    revisions: int
    message: str
    decision: dict
    preferences: list[dict]


class RunService:
    def __init__(self, settings, router, model):
        self.settings = settings
        self.router = router
        self.events = router.events
        self.agents = build_agents(model, router, self.invoke)
        self.tasks = {}
        self.locks = {}
        self.model_lock = asyncio.Lock()
        self.started = {}
        with self.db() as db:
            db.execute(
                "CREATE TABLE IF NOT EXISTS runs(id TEXT PRIMARY KEY,member_id TEXT,parent_id TEXT,status TEXT,error TEXT,model_calls INTEGER DEFAULT 0,active_seconds REAL DEFAULT 0)"
            )

    @contextmanager
    def db(self):
        db = sqlite3.connect(self.settings.checkpoint_db, timeout=5)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA journal_mode=WAL")
        try:
            with db:
                yield db
        finally:
            db.close()

    def record(self, rid):
        with self.db() as db:
            row = db.execute("SELECT * FROM runs WHERE id=?", (rid,)).fetchone()
        if row is None:
            raise ValueError("run_not_found")
        return dict(row)

    def update(self, rid, **values):
        with self.db() as db:
            db.execute(
                "UPDATE runs SET " + ",".join(f"{key}=?" for key in values) + " WHERE id=?",
                (*values.values(), rid),
            )

    async def __aenter__(self):
        self.saver_context = AsyncSqliteSaver.from_conn_string(str(self.settings.checkpoint_db))
        saver = await self.saver_context.__aenter__()
        self.graph = self.build(saver)
        with self.db() as db:
            pending = [r[0] for r in db.execute("SELECT id FROM runs WHERE status='running'")]
        for rid in pending:
            self.tasks[rid] = asyncio.create_task(self.drive(rid, None))
        return self

    async def __aexit__(self, *args):
        for task in self.tasks.values():
            if not task.done():
                task.cancel()
        await asyncio.gather(*self.tasks.values(), return_exceptions=True)
        await self.saver_context.__aexit__(*args)

    def config(self, rid):
        return {"configurable": {"thread_id": rid}, "recursion_limit": 40}

    async def invoke(self, rid, model, messages, role):
        async with self.model_lock:
            for attempt in range(2):
                rec = self.record(rid)
                elapsed = time.monotonic() - self.started.get(rid, time.monotonic())
                if rec["active_seconds"] + elapsed >= 90:
                    raise TimeoutError("investigation_budget_exhausted")
                if rec["model_calls"] >= 16:
                    raise ValueError("model_call_budget_exhausted")
                await asyncio.to_thread(self.update, rid, model_calls=rec["model_calls"] + 1)
                start = time.monotonic()
                status = "ok"
                try:
                    return await model.ainvoke(messages)
                except Exception as exc:
                    status = error_code(exc)
                    if status == "quota_limited" and attempt == 0:
                        await asyncio.sleep(1)
                        continue
                    raise
                finally:
                    await asyncio.to_thread(
                        self.events.append,
                        rid,
                        agent=role,
                        server="gemini",
                        tool="model",
                        status=status,
                        duration_ms=(time.monotonic() - start) * 1000,
                        summary={"model_calls": rec["model_calls"] + 1},
                    )

    def build(self, saver):
        async def interpret(state):
            ctx = ActorContext.model_validate(state["actor"])
            out, results = await self.agents.run("interpreter", ctx, {"request": state["request"]})
            if out.goal is None:
                return {
                    "status": "awaiting_clarification",
                    "question": out.clarification
                    or "Which supported skill would you like to learn?",
                }
            return {
                "goal": out.goal.model_dump(),
                "status": "running",
                "question": None,
                "preferences": results.get("search_memories", {}).get("memories", []),
            }

        def clarify(state):
            answer = interrupt({"kind": "clarification", "question": state["question"]})
            if answer.get("decision") == "cancel":
                return {"status": "cancelled"}
            return {
                "request": state["request"] + "\nclarification: " + answer["answer"],
                "status": "running",
            }

        async def coordinate(state):
            if state.get("revisions", 0) > 2:
                return {
                    "status": "stopped",
                    "message": "Automatic revision budget exhausted. Start a new search.",
                }
            ctx = ActorContext.model_validate(state["actor"])
            preferences = state.get("preferences", [])
            if state.get("revisions", 0) and self.router.memory.enabled:
                facts = await self.router.memory.search(ctx, "learning and teaching preferences")
                preferences = [f.model_dump() for f in facts]
            out, results = await self.agents.run(
                "coordinator",
                ctx,
                {
                    "request": state["request"],
                    "goal": state["goal"],
                    "feedback": state.get("message", ""),
                    "remembered_preferences": preferences,
                },
            )
            plans = results["find_exchange_cycles"]["plans"]
            if not plans:
                return {
                    "status": "no_match",
                    "plan": None,
                    "message": "; ".join(results["find_exchange_cycles"]["issues"]),
                }
            plan = next((p for p in plans if p["fingerprint"] == out.fingerprint), None)
            if plan is None:
                raise ValueError("unsupported_plan_selection")
            return {"status": "running", "plan": plan, "message": out.summary}

        async def review(state):
            ctx = ActorContext.model_validate(state["actor"])
            out, results = await self.agents.run("reviewer", ctx, {"plan": state["plan"]})
            validation = results["validate_and_schedule"]
            if (
                not out.accepted
                or not validation["valid"]
                or validation["plan"]["fingerprint"] != state["plan"]["fingerprint"]
            ):
                return {
                    "status": "replan",
                    "revisions": state.get("revisions", 0) + 1,
                    "message": out.summary,
                    "plan": None,
                }
            plan = validation["plan"]
            plan["reviewer_summary"] = out.summary
            return {"status": "awaiting_approval", "plan": plan}

        def approval(state):
            decision = interrupt({"kind": "approval", "fingerprint": state["plan"]["fingerprint"]})
            return {
                "decision": decision,
                "status": "cancelled" if decision["decision"] == "cancel" else "committing",
            }

        async def commit(state):
            ctx = ActorContext.model_validate(state["actor"])
            plan = state["plan"]
            key = ctx.run_id + ":" + plan["fingerprint"]

            async def call(tool, args):
                return await self.router.call("skillswap", tool, args, ctx)

            # Check first: a previous process may have committed before it lost its response.
            known = await call("get_proposal_status", {"idempotency_key": key})
            if known["proposal"]:
                return {"status": "saved", "result": known["proposal"]}
            validated = await call(
                "validate_and_schedule",
                {
                    "cycle": plan["cycle"],
                    "goal": plan["goal"],
                    "proposed_sessions": plan["sessions"],
                },
            )
            if not validated["valid"] or validated["plan"]["fingerprint"] != plan["fingerprint"]:
                return {
                    "status": "replan",
                    "plan": None,
                    "revisions": state.get("revisions", 0) + 1,
                    "message": "Availability or profile data changed. Review the new proposal before saving.",
                }
            args = {
                "plan": plan,
                "approval_fingerprint": state["decision"]["fingerprint"],
                "idempotency_key": key,
            }
            try:
                saved = await call("save_proposal", args)
            except Exception:
                known = await call("get_proposal_status", {"idempotency_key": key})
                saved = known if known["proposal"] else await call("save_proposal", args)
            if not saved.get("proposal"):
                if "stale_revision" in saved.get("issues", []):
                    return {
                        "status": "replan",
                        "plan": None,
                        "revisions": state.get("revisions", 0) + 1,
                        "message": "Dataset changed during save; fresh approval required.",
                    }
                raise ValueError("proposal_save_rejected")
            return {"status": "saved", "result": saved["proposal"]}

        builder = StateGraph(RunState)
        for name, fn in [
            ("interpret", interpret),
            ("clarify", clarify),
            ("coordinate", coordinate),
            ("review", review),
            ("approval", approval),
            ("commit", commit),
        ]:
            builder.add_node(name, fn)
        builder.add_edge(START, "interpret")
        builder.add_conditional_edges(
            "interpret",
            lambda s: "clarify" if s["status"] == "awaiting_clarification" else "coordinate",
        )
        builder.add_conditional_edges(
            "clarify", lambda s: END if s["status"] == "cancelled" else "interpret"
        )
        builder.add_conditional_edges(
            "coordinate", lambda s: "review" if s["status"] == "running" else END
        )
        builder.add_conditional_edges(
            "review", lambda s: "coordinate" if s["status"] == "replan" else "approval"
        )
        builder.add_conditional_edges(
            "approval", lambda s: END if s["status"] == "cancelled" else "commit"
        )
        builder.add_conditional_edges(
            "commit", lambda s: "coordinate" if s["status"] == "replan" else END
        )
        return builder.compile(checkpointer=saver)

    async def start(self, member_id, request, exclusions=None, parent_run_id=None):
        if not request.strip() or len(request) > 2000:
            raise ValueError("invalid_request")
        if parent_run_id:
            parent = await self.snapshot(parent_run_id)
            if parent["member_id"] != member_id:
                raise ValueError("parent_scope_mismatch")
            if parent["status"] in {"awaiting_approval", "awaiting_clarification"}:
                await self.resume(parent_run_id, {"decision": "cancel"})
                await self.wait(parent_run_id)
            elif parent["status"] == "running":
                raise ValueError("parent_still_running")
        rid = str(uuid4())
        ctx = ActorContext(member_id=member_id, run_id=rid, exclusions=tuple(exclusions or []))
        context = await self.router.call("skillswap", "get_learning_context", {}, ctx)
        if (
            any(i not in {p["id"] for p in context["profiles"]} for i in ctx.exclusions)
            or member_id in ctx.exclusions
        ):
            raise ValueError("invalid_exclusions")

        def register():
            with self.db() as db:
                db.execute(
                    "INSERT INTO runs(id,member_id,parent_id,status) VALUES(?,?,?,?)",
                    (rid, member_id, parent_run_id, "running"),
                )

        await asyncio.to_thread(register)
        self.tasks[rid] = asyncio.create_task(
            self.drive(
                rid,
                {
                    "actor": ctx.model_dump(mode="json"),
                    "request": request,
                    "goal": None,
                    "plan": None,
                    "result": None,
                    "revisions": 0,
                    "status": "running",
                },
            )
        )
        return rid

    async def drive(self, rid, value):
        start = time.monotonic()
        self.started[rid] = start
        previous = self.record(rid)["active_seconds"]
        try:
            checkpoint = await self.graph.aget_state(self.config(rid))
            recovering_commit = (
                value is None
                and checkpoint.values.get("status") == "committing"
                and "commit" in checkpoint.next
            )
            # Recovery reads/saves only the already-approved exact key. It cannot
            # spend more model time when the investigation budget is exhausted.
            remaining = 30 if recovering_commit else 90 - previous
            if remaining <= 0:
                raise TimeoutError()
            async with asyncio.timeout(remaining):
                result = await self.graph.ainvoke(value, self.config(rid))
            await asyncio.to_thread(self.update, rid, status=result["status"], error=None)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            code = "stopped" if "budget_exhausted" in str(exc) else error_code(exc)
            checkpoint = await self.graph.aget_state(self.config(rid))
            if checkpoint.values.get("status") == "committing":
                code = "save_error"
            await asyncio.to_thread(self.update, rid, status=code, error=code)
        finally:
            await asyncio.to_thread(
                self.update, rid, active_seconds=previous + time.monotonic() - start
            )

    async def wait(self, rid):
        if rid in self.tasks:
            await self.tasks[rid]

    async def snapshot(self, rid):
        rec = self.record(rid)
        state = await self.graph.aget_state(self.config(rid))
        values = state.values or {}
        return {
            "run_id": rid,
            "member_id": rec["member_id"],
            "parent_run_id": rec["parent_id"],
            "status": rec["status"],
            "request": values.get("request", ""),
            "goal": values.get("goal"),
            "plan": values.get("plan"),
            "question": values.get("question"),
            "result": values.get("result"),
            "message": values.get("message", ""),
            "error": rec["error"],
            "model_calls": rec["model_calls"],
            "revisions": values.get("revisions", 0),
            "active_seconds": round(rec["active_seconds"], 2),
        }

    async def resume(self, rid, payload):
        async with self.locks.setdefault(rid, asyncio.Lock()):
            state = await self.snapshot(rid)
            status = state["status"]
            command = Command(resume=payload)
            if status == "save_error" and payload.get("decision") == "retry":
                checkpoint = await self.graph.aget_state(self.config(rid))
                approved = checkpoint.values.get("decision", {})
                if (
                    "commit" not in checkpoint.next
                    or approved.get("fingerprint") != state["plan"]["fingerprint"]
                ):
                    raise ValueError("approval_fingerprint_mismatch")
                command = None
            elif status == "awaiting_approval":
                if payload.get("decision") not in {"approve", "cancel"}:
                    raise ValueError("approval_decision_required")
                if (
                    payload["decision"] == "approve"
                    and payload.get("fingerprint") != state["plan"]["fingerprint"]
                ):
                    raise ValueError("approval_fingerprint_mismatch")
            elif status == "awaiting_clarification":
                if payload.get("decision") != "cancel" and (
                    not isinstance(payload.get("answer"), str)
                    or not 1 <= len(payload["answer"].strip()) <= 2000
                ):
                    raise ValueError("clarification_answer_required")
            else:
                raise ValueError("run_not_waiting")
            await asyncio.to_thread(self.update, rid, status="running")
            self.tasks[rid] = asyncio.create_task(self.drive(rid, command))
            return await self.snapshot(rid)
