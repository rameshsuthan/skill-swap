import json

import pytest
from skillswap.events import EventStore
from skillswap.mcp_router import MCPRouter
from skillswap.models import ActorContext
from skillswap.settings import Settings


@pytest.mark.asyncio
async def test_stdio_context_roundtrip(tmp_path):
    router = MCPRouter(
        Settings(domain_db=tmp_path / "domain.sqlite", checkpoint_db=tmp_path / "check.sqlite")
    )
    async with router:
        assert set(router.schemas) == {
            "get_learning_context",
            "search_teachers",
            "find_exchange_cycles",
            "validate_and_schedule",
            "save_proposal",
            "get_proposal_status",
        }
        result = await router.call(
            "skillswap", "get_learning_context", {}, ActorContext(member_id="maya", run_id="test")
        )
        assert len(result["profiles"]) == 15
        assert result["member"]["timezone"] == "America/Chicago"
        assert result["member"]["display_name"] == "Maya"
        assert router.process_transport is not None


@pytest.mark.asyncio
async def test_scope_override_rejected(tmp_path):
    router = MCPRouter(
        Settings(domain_db=tmp_path / "domain.sqlite", checkpoint_db=tmp_path / "check.sqlite")
    )
    async with router:
        for field in ("ctx", "member_id", "cohort_id", "run_id", "exclusions"):
            with pytest.raises(ValueError, match="scope_override"):
                await router.call(
                    "skillswap",
                    "get_learning_context",
                    {field: "other"},
                    ActorContext(member_id="maya", run_id="test"),
                )


def test_no_secret_in_events(tmp_path):
    events = EventStore(tmp_path / "events.sqlite")
    events.append(
        "run",
        agent="interpreter",
        server="skillswap",
        tool="context",
        status="ok",
        duration_ms=1,
        summary={"api_key": "secret", "profiles": [{"private": "hidden"}], "count": 15},
    )
    data = json.dumps(events.list_after("run", 0))
    assert "secret" not in data and "hidden" not in data
    assert events.list_after("run", 0)[0]["sequence"] == 1
    assert events.list_after("run", 1) == []


@pytest.mark.asyncio
async def test_real_mcp_validate_save_retry(tmp_path):
    router = MCPRouter(
        Settings(domain_db=tmp_path / "domain.sqlite", checkpoint_db=tmp_path / "check.sqlite")
    )
    ctx = ActorContext(member_id="maya", run_id="write-test")
    async with router:
        found = await router.call(
            "skillswap",
            "find_exchange_cycles",
            {"goal": {"skill_id": "presentation_design"}},
            ctx,
            role="coordinator",
        )
        plan = found["plans"][0]
        verified = await router.call(
            "skillswap",
            "validate_and_schedule",
            {"cycle": plan["cycle"], "goal": plan["goal"], "proposed_sessions": plan["sessions"]},
            ctx,
            role="reviewer",
        )
        assert verified["valid"]
        args = {
            "plan": plan,
            "approval_fingerprint": plan["fingerprint"],
            "idempotency_key": ctx.run_id + ":" + plan["fingerprint"],
        }
        first = await router.call("skillswap", "save_proposal", args, ctx)
        again = await router.call("skillswap", "save_proposal", args, ctx)
        assert first["proposal"]["id"] == again["proposal"]["id"]
        assert first["proposal"]["plan"]["sessions"] == plan["sessions"]
        status = await router.call(
            "skillswap", "get_proposal_status", {"proposal_id": first["proposal"]["id"]}, ctx
        )
        assert status["proposal"]["status"] == "awaiting_participant_confirmation"
        with pytest.raises(ValueError, match="tool_not_allowed"):
            await router.call("skillswap", "save_proposal", args, ctx, role="coordinator")
