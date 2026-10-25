"""Live two-session personalization, approval and recovery on isolated fictional data."""

import argparse
import asyncio
import json
from uuid import uuid4

from skillswap.mcp_router import MCPRouter
from skillswap.model_factory import make_model
from skillswap.models import ActorContext
from skillswap.repository import Repository
from skillswap.scenarios import memory_alternatives
from skillswap.settings import ROOT, Settings
from skillswap.workflow import RunService
from smoke_mem0 import confirm


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--live-model", required=True, action="store_true")
    parser.parse_args()
    tag = uuid4().hex[:8]
    member = "maya-smoke-" + tag
    settings = Settings(
        mem0_enabled=True,
        domain_db=ROOT / f"storage/memory-live-{tag}.sqlite",
        checkpoint_db=ROOT / f"storage/memory-live-{tag}-checkpoints.sqlite",
    )
    data = json.loads((ROOT / "data/demo_cohort.json").read_text())
    next(p for p in data if p["id"] == "maya")["id"] = member
    repo = Repository(settings.domain_db)
    repo.seed_demo(data)
    memory_alternatives(repo)
    actor = ActorContext(member_id=member, run_id="memory-workflow-smoke")
    async with MCPRouter(settings) as router:

        async def recommend():
            async with RunService(settings, router, make_model(settings)) as service:
                rid = await service.start(
                    member, "I want to learn presentation design from a working-level teacher."
                )
                await service.wait(rid)
                state = await service.snapshot(rid)
                print(
                    json.dumps(
                        {
                            k: state[k]
                            for k in ("run_id", "status", "model_calls", "active_seconds", "error")
                        }
                    ),
                    flush=True,
                )
                assert state["status"] == "awaiting_approval"
                return state

        before = await recommend()
        assert "olivia" in before["plan"]["cycle"]["member_ids"]
        print(
            json.dumps(
                {"cooldown_seconds": 65, "reason": "Space live runs for the free-tier target."}
            ),
            flush=True,
        )
        await asyncio.sleep(65)
        saved = await confirm(
            router.memory,
            actor,
            await router.memory.remember(
                actor, "I prefer guided-project teaching over discussion for my learning."
            ),
        )
        print(json.dumps({"memory_id": saved.memory_id, "event_id": saved.event_id}), flush=True)
        try:
            after = await recommend()  # New LangGraph thread and model, no old transcript.
            assert "nina" in after["plan"]["cycle"]["member_ids"]
            assert "olivia" not in after["plan"]["cycle"]["member_ids"]
            assert after["run_id"] != before["run_id"]
            async with RunService(settings, router, make_model(settings)) as service:
                await service.resume(
                    after["run_id"],
                    {"decision": "approve", "fingerprint": after["plan"]["fingerprint"]},
                )
                await service.wait(after["run_id"])
                state = await service.snapshot(after["run_id"])
                assert state["status"] == "saved"
            async with RunService(settings, router, make_model(settings)) as restarted:
                recovered = await restarted.snapshot(after["run_id"])
                assert recovered["result"] == state["result"]
            print(
                json.dumps(
                    {
                        "fresh_session_preference_ranking": "passed",
                        "before_teacher": "olivia",
                        "after_teacher": "nina",
                        "proposal_id": state["result"]["id"],
                        "restart_recovery": "passed",
                    }
                ),
                flush=True,
            )
        finally:
            await confirm(router.memory, actor, await router.memory.forget(actor, saved.memory_id))
            print(json.dumps({"test_memory_cleanup": "passed"}), flush=True)


if __name__ == "__main__":
    asyncio.run(main())
