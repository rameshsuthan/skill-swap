"""Advisory Pinecone MCP retrieval; canonical SkillSwap profiles remain authoritative."""

import asyncio
import hashlib
import json
import math
import os
import shutil
import time
from pathlib import Path

from fastmcp import Client
from fastmcp.client.transports import StdioTransport
from pydantic import BaseModel

from .events import EventStore
from .models import CATALOG, MemberProfile
from .settings import ROOT


def offer_hash(profile):
    p = profile if isinstance(profile, MemberProfile) else MemberProfile.model_validate(profile)
    public = {
        "id": p.id,
        "cohort_id": p.cohort_id,
        "source_record_id": p.source_record_id,
        "offer": p.offer.model_dump(),
    }
    return hashlib.sha256(json.dumps(public, sort_keys=True).encode()).hexdigest()


def pinecone_client(settings):
    local_node = ROOT / ".tools/node/bin/node"
    node = str(local_node) if local_node.is_file() else shutil.which("node")
    entry = ROOT / "integrations/pinecone/node_modules/@pinecone-database/mcp/dist/index.js"
    if not node or not entry.is_file():
        raise ValueError("pinecone_runtime_missing")
    return Client(
        StdioTransport(
            command=node,
            args=[str(entry)],
            cwd=str(ROOT),
            env={"PINECONE_API_KEY": settings.pinecone_api_key.get_secret_value()},
            log_file=Path(os.devnull),
        ),
        timeout=10,
    )


class CandidateHit(BaseModel):
    profile_id: str
    advisory_score: float
    evidence: str = ""
    offer_hash: str


class SearchResult(BaseModel):
    hits: list[CandidateHit]
    mode: str
    detail: str


class SemanticSearch:
    TOOLS = {"search-records"}

    def __init__(self, settings, client_factory=None):
        self.settings = settings
        self.enabled = bool(
            settings.pinecone_enabled
            and settings.pinecone_api_key.get_secret_value()
            and settings.pinecone_index
            and settings.pinecone_namespace
        )
        self.test_client = client_factory is not None
        self.client_factory = client_factory or (lambda: pinecone_client(settings))
        self.schemas = {}
        self.events = EventStore(settings.checkpoint_db)
        self.mode = "connecting" if self.enabled else "disabled"
        self.detail = (
            "Awaiting semantic search verification."
            if self.enabled
            else "Semantic discovery is disabled; using complete local cohort search."
        )

    def provider(self):
        return {"mode": self.mode, "detail": self.detail}

    def degraded(self):
        self.mode = "degraded"
        self.detail = "Pinecone unavailable; using complete local cohort search."

    async def open(self):
        if not self.enabled:
            return self
        try:
            async with self.client_factory() as client:
                tools = {t.name: t for t in await client.list_tools()}
                self.schemas = {name: tools[name] for name in self.TOOLS}
        except Exception:
            self.schemas = {}
            self.degraded()
        return self

    async def search(self, ctx, goal_text):
        return (await self.search_result(ctx, goal_text)).hits

    async def search_result(self, ctx, goal_text):
        if not self.enabled:
            return SearchResult(hits=[], **self.provider())
        start = time.monotonic()
        status = "ok"
        try:
            if ctx.cohort_id != self.settings.cohort_id:
                raise ValueError("semantic_scope_mismatch")
            arguments = {
                "name": self.settings.pinecone_index,
                "namespace": self.settings.pinecone_namespace,
                "query": {
                    "topK": 5,
                    "inputs": {"text": goal_text[:2000]},
                    "filter": {
                        "project": {"$eq": "skillswap-demo"},
                        "cohort_id": {"$eq": ctx.cohort_id},
                        "active": {"$eq": True},
                    },
                },
            }
            async with self.client_factory() as client:
                result = await client.call_tool("search-records", arguments)
            data = result.structured_content
            if data is None:
                data = json.loads(result.content[0].text)
            if result.is_error or not isinstance(data, dict) or data.get("error"):
                raise ValueError("semantic_provider_error")
            rows = data.get("result", {}).get("hits")
            if not isinstance(rows, list):
                raise ValueError("semantic_response_invalid")
            hits = []
            for row in rows:
                if not isinstance(row, dict):
                    continue
                fields = row.get("fields")
                score = row.get("_score")
                if (
                    not isinstance(fields, dict)
                    or fields.get("project") != "skillswap-demo"
                    or fields.get("cohort_id") != ctx.cohort_id
                    or fields.get("active") is not True
                    or fields.get("profile_id") != row.get("_id")
                    or not isinstance(row.get("_id"), str)
                    or not isinstance(fields.get("offer_hash"), str)
                    or isinstance(score, bool)
                    or not isinstance(score, (int, float))
                    or not math.isfinite(score)
                ):
                    continue
                hits.append(
                    CandidateHit(
                        profile_id=row["_id"], advisory_score=score, offer_hash=fields["offer_hash"]
                    )
                )
            self.mode = "test" if self.test_client else "live"
            self.detail = "Semantic suggestions plus complete local cohort validation."
            # Capture this call's outcome before telemetry/hydration yields control.
            return SearchResult(hits=hits, **self.provider())
        except Exception:
            status = "error"
            self.degraded()
            return SearchResult(hits=[], **self.provider())
        finally:
            await asyncio.to_thread(
                self.events.append,
                ctx.run_id,
                agent="coordinator",
                server="pinecone",
                tool="search-records",
                status=status,
                duration_ms=(time.monotonic() - start) * 1000,
            )

    @staticmethod
    def hydrate(ctx, hits, profiles, goal):
        canonical = {p.id: p for p in profiles}
        hydrated, seen = [], set()
        for hit in hits:
            p = canonical.get(hit.profile_id)
            if (
                p is None
                or not p.active
                or p.cohort_id != ctx.cohort_id
                or p.id in seen
                or p.id == ctx.member_id
                or p.id in ctx.exclusions
                or p.offer.skill_id != goal.skill_id
                or p.offer.proficiency < goal.minimum_teacher_proficiency
                or hit.offer_hash != offer_hash(p)
            ):
                continue
            seen.add(p.id)
            # Never expose vendor-supplied prose as current profile evidence.
            hydrated.append(
                hit.model_copy(
                    update={
                        "evidence": f"{p.display_name} declares {CATALOG[p.offer.skill_id]} at proficiency {p.offer.proficiency}/3; styles: {', '.join(p.offer.styles)}."
                    }
                )
            )
        return hydrated
