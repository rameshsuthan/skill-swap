import asyncio
import json
import sys
import time

from fastmcp import Client
from fastmcp.client.transports import StdioTransport

from .events import EventStore
from .models import ActorContext
from .settings import ROOT
from .vendor_memory import MemoryService

ROLE_TOOLS = {
    "interpreter": {"get_learning_context"},
    "coordinator": {"search_teachers", "find_exchange_cycles"},
    "reviewer": {"get_learning_context", "validate_and_schedule"},
    "host": {
        "get_learning_context",
        "validate_and_schedule",
        "save_proposal",
        "get_proposal_status",
    },
}


class MCPRouter:
    def __init__(self, settings, memory=None):
        self.settings = settings
        self.events = EventStore(settings.checkpoint_db)
        self.schemas = {}
        self.memory = memory or MemoryService(settings)
        self.process_transport = StdioTransport(
            command=sys.executable,
            args=["-m", "skillswap.mcp_server"],
            cwd=str(ROOT),
            env={
                "SKILLSWAP_DOMAIN_DB": str(settings.domain_db.resolve()),
                "FASTMCP_LOG_LEVEL": "ERROR",
            },
        )
        self.client = Client(self.process_transport, timeout=15)

    async def open(self):
        await self.client.__aenter__()
        self.schemas = {t.name: t for t in await self.client.list_tools()}
        await self.memory.open()
        return self

    async def close(self):
        await self.client.__aexit__(None, None, None)

    async def __aenter__(self):
        return await self.open()

    async def __aexit__(self, *args):
        await self.close()

    async def call(self, server, tool, arguments, ctx: ActorContext, role="host"):
        if server == "mem0":
            if role != "interpreter" or tool != "search_memories":
                raise ValueError("tool_not_allowed")
            if set(arguments) != {"query"} or not isinstance(arguments["query"], str):
                raise ValueError("scope_override")
            facts = await self.memory.search(ctx, arguments["query"])
            return {"memories": [f.model_dump() for f in facts], **self.memory.provider()}
        if server != "skillswap" or tool not in ROLE_TOOLS.get(role, set()):
            raise ValueError("tool_not_allowed")
        if set(arguments) & {"ctx", "member_id", "cohort_id", "run_id", "exclusions"}:
            raise ValueError("scope_override")
        if role == "coordinator" and set(arguments.get("excluded_member_ids", [])) - set(
            ctx.exclusions
        ):
            raise ValueError("scope_override")
        start = time.monotonic()
        status = "ok"
        try:
            result = await self.client.call_tool(
                tool, {**arguments, "ctx": ctx.model_dump(mode="json")}
            )
            if result.is_error:
                raise ValueError("mcp_tool_error")
            if result.structured_content is not None:
                return result.structured_content
            return json.loads(result.content[0].text)
        except Exception:
            status = "error"
            raise
        finally:
            await asyncio.to_thread(
                self.events.append,
                ctx.run_id,
                agent=role,
                server=server,
                tool=tool,
                status=status,
                duration_ms=(time.monotonic() - start) * 1000,
            )
