"""Scoped hosted Mem0 MCP access. Only explicit host actions can mutate memory."""

import asyncio
import hashlib
import json
import sqlite3
import time
from contextlib import contextmanager
from typing import Literal
from uuid import uuid4

from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport
from pydantic import BaseModel

from .events import EventStore


class MemoryFact(BaseModel):
    id: str
    text: str


class MemoryWriteResult(BaseModel):
    operation_id: str
    status: Literal["pending", "saved", "failed"]
    memory_id: str | None = None
    event_id: str | None = None
    detail: str = ""
    acknowledged: bool = False


class MemoryService:
    # Read-by-ID/list are host-only ownership/UI operations. No entity/admin tools.
    TOOLS = {
        "search_memories",
        "get_memories",
        "get_memory",
        "add_memory",
        "update_memory",
        "delete_memory",
        "get_event_status",
    }

    def __init__(self, settings, client_factory=None):
        self.settings = settings
        self.enabled = settings.mem0_enabled and bool(settings.mem0_api_key.get_secret_value())
        self.mode = "connecting" if self.enabled else "disabled"
        self.detail = (
            "Awaiting scoped read"
            if self.enabled
            else "Enable Mem0 and configure its key to retain preferences."
        )
        self.test_client = client_factory is not None
        self.schemas = {}
        self.client_factory = client_factory or self._client
        self.events = EventStore(settings.checkpoint_db)
        with self.db() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS memory_operations(
                id TEXT PRIMARY KEY, scope TEXT NOT NULL, kind TEXT NOT NULL,
                expected_hash TEXT, status TEXT NOT NULL, memory_id TEXT, event_id TEXT,
                detail TEXT NOT NULL)""")

            if "acknowledged" not in {
                r[1] for r in db.execute("PRAGMA table_info(memory_operations)")
            }:
                db.execute(
                    "ALTER TABLE memory_operations ADD COLUMN acknowledged INTEGER NOT NULL DEFAULT 0"
                )

    def _client(self):
        return Client(
            StreamableHttpTransport(
                "https://mcp.mem0.ai/mcp",
                headers={
                    "Authorization": "Bearer " + self.settings.mem0_api_key.get_secret_value()
                },
            ),
            timeout=10,
        )

    @contextmanager
    def db(self):
        db = sqlite3.connect(self.settings.checkpoint_db, timeout=5)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    async def open(self):
        if not self.enabled:
            return self
        try:
            async with self.client_factory() as client:
                self.schemas = {t.name: t for t in await client.list_tools()}
                tools = set(self.schemas)
            if not self.TOOLS <= tools:
                raise ValueError("missing_memory_tools")
        except Exception:
            self.schemas = {}
            self._degraded()
        return self

    def _degraded(self):
        self.mode = "degraded"
        self.detail = "Mem0 unavailable. Matching continues without remembered preferences."

    def provider(self):
        return {"mode": self.mode, "detail": self.detail}

    @staticmethod
    def scope(ctx):
        return f"skillswap-demo:{ctx.cohort_id}:{ctx.member_id}"

    @staticmethod
    def metadata(ctx):
        return {"project": "skillswap-demo", "cohort_id": ctx.cohort_id, "member_id": ctx.member_id}

    def owned(self, ctx, record):
        return (
            isinstance(record, dict)
            and record.get("user_id") == self.scope(ctx)
            and isinstance(record.get("metadata"), dict)
            and all(record["metadata"].get(k) == v for k, v in self.metadata(ctx).items())
        )

    async def _call(self, ctx, name, arguments, role="host"):
        if not self.enabled or name not in self.TOOLS:
            raise ValueError("memory_unavailable")
        start = time.monotonic()
        status = "ok"
        try:
            async with self.client_factory() as client:
                result = await client.call_tool(name, arguments)
            data = result.structured_content
            if data is None:
                data = json.loads(result.content[0].text)
            if result.is_error or (isinstance(data, dict) and data.get("error")):
                raise ValueError("memory_provider_error")
            self.mode, self.detail = (
                ("test", "Controlled Mem0 test boundary.")
                if self.test_client
                else ("live", "Scoped Mem0 MCP calls verified.")
            )
            return data
        except Exception:
            status = "error"
            self._degraded()
            raise ValueError("memory_unavailable") from None
        finally:
            await asyncio.to_thread(
                self.events.append,
                ctx.run_id,
                agent=role,
                server="mem0",
                tool=name,
                status=status,
                duration_ms=(time.monotonic() - start) * 1000,
            )

    @staticmethod
    def rows(data):
        rows = data if isinstance(data, list) else data.get("results", [])
        if not isinstance(rows, list):
            raise ValueError("memory_unavailable")
        return rows

    def facts(self, ctx, rows):
        return [
            MemoryFact(id=r["id"], text=r["memory"])
            for r in rows
            if self.owned(ctx, r)
            and isinstance(r.get("id"), str)
            and isinstance(r.get("memory"), str)
        ]

    async def search(self, ctx, query):
        if not self.enabled:
            return []
        try:
            data = await self._call(
                ctx,
                "search_memories",
                {
                    "query": query[:2000],
                    "filters": {"user_id": self.scope(ctx)},
                    "top_k": 10,
                    "threshold": 0.0,
                },
                role="interpreter",
            )
            return self.facts(ctx, self.rows(data))
        except ValueError:
            self._degraded()
            return []

    async def list(self, ctx):
        if not self.enabled:
            return []
        return self.facts(ctx, await self._list_records(ctx))

    async def _list_records(self, ctx):
        rows = []
        # No local content cache: edit/forget is visible on the next retrieval.
        for page in range(1, 11):
            data = await self._call(
                ctx,
                "get_memories",
                {"filters": {"user_id": self.scope(ctx)}, "page": page, "page_size": 100},
            )
            batch = self.rows(data)
            rows.extend(batch)
            if len(batch) < 100:
                return rows
        # Never use an incomplete listing to confirm a deletion.
        raise ValueError("memory_list_limit")

    async def _owned_record(self, ctx, memory_id):
        data = await self._call(ctx, "get_memory", {"memory_id": memory_id})
        if not self.owned(ctx, data) or data.get("id") != memory_id:
            raise ValueError("memory_not_found")
        return data

    def _record(self, ctx, operation_id):
        with self.db() as db:
            row = db.execute(
                "SELECT * FROM memory_operations WHERE id=? AND scope=?",
                (operation_id, self.scope(ctx)),
            ).fetchone()
        if row is None:
            raise ValueError("memory_operation_not_found")
        return dict(row)

    def operations(self, ctx):
        with self.db() as db:
            rows = db.execute(
                "SELECT * FROM memory_operations WHERE scope=? ORDER BY rowid DESC LIMIT 20",
                (self.scope(ctx),),
            ).fetchall()
        return [self._result(dict(r)) for r in rows]

    @staticmethod
    def _result(row):
        return MemoryWriteResult(
            operation_id=row["id"],
            **{k: row[k] for k in ("status", "memory_id", "event_id", "detail", "acknowledged")},
        )

    def _update(self, ctx, op, **values):
        with self.db() as db:
            db.execute(
                "UPDATE memory_operations SET "
                + ",".join(f"{k}=?" for k in values)
                + " WHERE id=? AND scope=?",
                (*values.values(), op, self.scope(ctx)),
            )
        return self._result(self._record(ctx, op))

    @staticmethod
    def digest(text):
        return hashlib.sha256(text.encode()).hexdigest()

    async def remember(self, ctx, text):
        return await self._write(ctx, "add", text=text)

    async def update(self, ctx, memory_id, text):
        await self._owned_record(ctx, memory_id)
        return await self._write(ctx, "update", text=text, memory_id=memory_id)

    async def forget(self, ctx, memory_id):
        await self._owned_record(ctx, memory_id)
        return await self._write(ctx, "delete", memory_id=memory_id)

    async def _write(self, ctx, kind, text="", memory_id=None):
        if kind != "delete" and not (0 < len(text.strip()) <= 1000):
            raise ValueError("invalid_memory_text")
        op = str(uuid4())
        with self.db() as db:
            db.execute(
                "INSERT INTO memory_operations(id,scope,kind,expected_hash,status,memory_id,event_id,detail) VALUES(?,?,?,?,?,?,?,?)",
                (
                    op,
                    self.scope(ctx),
                    kind,
                    self.digest(text),
                    "pending",
                    memory_id,
                    None,
                    "Waiting for Mem0 confirmation.",
                ),
            )
        args = {"memory_id": memory_id} if memory_id else {}
        if kind != "delete":
            args.update(text=text, metadata={**self.metadata(ctx), "operation_id": op})
        if kind == "add":
            args.update(user_id=self.scope(ctx), infer=False)
        try:
            if not self.enabled:
                return self._update(ctx, op, status="failed", detail="Mem0 is disabled.")
            data = await self._call(ctx, f"{kind}_memory", args)
            return await self._finish(ctx, op, data)
        except ValueError:
            # A timeout may follow a completed vendor write. Never repeat it automatically.
            return self._update(
                ctx,
                op,
                detail="Outcome unconfirmed. Refresh to check; this write will not be repeated automatically.",
            )

    async def _finish(self, ctx, op, data):
        row = self._record(ctx, op)
        event_id = data.get("event_id")
        if event_id:
            self._update(ctx, op, event_id=event_id)
        status = str(data.get("status", "")).upper()
        if status in {"FAILED", "CANCELLED", "ERROR"}:
            return self._update(ctx, op, status="failed", detail="Mem0 did not save this change.")
        if status in {"PENDING", "PROCESSING", "QUEUED", "RUNNING"}:
            return self._result(self._record(ctx, op))
        if row["kind"] == "delete":
            if status == "SUCCEEDED" or data.get("message") == "Memory deleted successfully!":
                return self._update(ctx, op, status="saved", detail="Preference forgotten.")
        else:
            # Event responses also have an `id`: that identifies the event, not a memory.
            mid = row["memory_id"] or (data.get("id") if self.owned(ctx, data) else None)
            if not mid:
                mid = next(
                    (r.get("id") for r in data.get("results", []) if r.get("event") == "ADD"), None
                )
            if mid and (status == "SUCCEEDED" or self.owned(ctx, data)):
                record = await self._owned_record(ctx, mid)
                if self.digest(record.get("memory", "")) == row["expected_hash"]:
                    return self._update(
                        ctx,
                        op,
                        status="saved",
                        memory_id=mid,
                        detail="Preference saved for future searches.",
                    )
        return self._result(self._record(ctx, op))

    async def poll_write(self, ctx, operation_id):
        row = self._record(ctx, operation_id)
        if row["status"] != "pending":
            return self._result(row)
        try:
            if not row["event_id"]:
                records = await self._list_records(ctx)
                owned = [r for r in records if self.owned(ctx, r)]
                if row["kind"] == "delete":
                    if not any(r.get("id") == row["memory_id"] for r in owned):
                        return self._update(
                            ctx, operation_id, status="saved", detail="Preference forgotten."
                        )
                else:
                    for record in owned:
                        if record["metadata"].get("operation_id") == operation_id:
                            return await self._finish(ctx, operation_id, record)
                return self._result(row)
            data = await self._call(ctx, "get_event_status", {"event_id": row["event_id"]})
            payload = data.get("payload") or {}
            if payload.get("user_id") and payload["user_id"] != self.scope(ctx):
                raise ValueError("memory_scope_mismatch")
            return await self._finish(ctx, operation_id, data)
        except ValueError:
            return self._result(self._record(ctx, operation_id))

    def acknowledge_unknown(self, ctx, operation_id):
        row = self._record(ctx, operation_id)
        if row["status"] != "pending":
            return self._result(row)
        return self._update(
            ctx,
            operation_id,
            acknowledged=True,
            detail="Outcome still unconfirmed; you chose to continue. The change may appear later. Refresh before repeating it.",
        )
