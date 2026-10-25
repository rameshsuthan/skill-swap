"""Live MCP CRUD against a unique fictional learner; never touches other memories."""

import asyncio
import json
from uuid import uuid4

from skillswap.models import ActorContext
from skillswap.settings import Settings
from skillswap.vendor_memory import MemoryService


async def confirm(service, ctx, result):
    for _ in range(15):
        if result.status != "pending":
            break
        await asyncio.sleep(1)
        result = await service.poll_write(ctx, result.operation_id)
    assert result.status == "saved", result.model_dump()
    return result


async def main():
    settings = Settings(mem0_enabled=True)
    ctx = ActorContext(member_id="mem0-smoke-" + uuid4().hex[:8], run_id="mem0-smoke")
    service = await MemoryService(settings).open()
    result = await confirm(
        service,
        ctx,
        await service.remember(
            ctx, "Fictional SkillSwap preference: I prefer discussion-based teaching."
        ),
    )
    print(json.dumps({"add": result.model_dump()}), flush=True)
    try:
        fresh = await MemoryService(settings).open()
        facts = await fresh.search(ctx, "teaching preferences")
        assert result.memory_id in [f.id for f in facts], fresh.provider()
        assert result.memory_id in [f.id for f in await fresh.list(ctx)]
        other = ActorContext(member_id="mem0-other-" + uuid4().hex[:8], run_id="mem0-smoke")
        assert await fresh.search(other, "teaching preferences") == []
        edited = await confirm(
            fresh,
            ctx,
            await fresh.update(
                ctx, result.memory_id, "Fictional SkillSwap preference: I prefer hands-on examples."
            ),
        )
        assert any(f.id == result.memory_id and "hands-on" in f.text for f in await fresh.list(ctx))
        print(
            json.dumps(
                {
                    "fresh_session_retrieval": "passed",
                    "other_member_excluded": "passed",
                    "update": edited.model_dump(),
                }
            ),
            flush=True,
        )
    finally:
        deleted = await confirm(service, ctx, await service.forget(ctx, result.memory_id))
        assert result.memory_id not in [f.id for f in await service.list(ctx)]
        print(json.dumps({"forget": deleted.model_dump(), "cleanup": "passed"}), flush=True)


if __name__ == "__main__":
    asyncio.run(main())
