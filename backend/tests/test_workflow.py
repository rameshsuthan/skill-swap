import asyncio

import pytest
from fake_model import ControlledModel
from skillswap.mcp_router import MCPRouter
from skillswap.repository import Repository
from skillswap.settings import Settings
from skillswap.workflow import RunService


async def wait(service, run_id):
    await service.wait(run_id)
    return await service.snapshot(run_id)


@pytest.fixture
async def service(tmp_path):
    settings = Settings(
        domain_db=tmp_path / "domain.sqlite", checkpoint_db=tmp_path / "check.sqlite"
    )
    async with MCPRouter(settings) as router:
        async with RunService(settings, router, ControlledModel()) as service:
            yield service


async def test_ambiguous_goal_interrupts(service):
    service.agents.model.ambiguous = True
    rid = await service.start("maya", "Help me learn")
    s = await wait(service, rid)
    assert s["status"] == "awaiting_clarification"
    await service.resume(rid, {"answer": "Presentation design"})
    assert (await wait(service, rid))["status"] == "awaiting_approval"


async def test_approve_requires_waiting_state_and_fingerprint(service):
    rid = await service.start("maya", "Presentation design")
    s = await wait(service, rid)
    assert s["status"] == "awaiting_approval"
    with pytest.raises(ValueError, match="fingerprint"):
        await service.resume(rid, {"decision": "approve", "fingerprint": "wrong"})
    with pytest.raises(ValueError):
        await service.resume(rid, {"answer": "SQL"})
    await service.resume(rid, {"decision": "approve", "fingerprint": s["plan"]["fingerprint"]})
    done = await wait(service, rid)
    assert done["status"] == "saved"
    assert done["result"]["status"] == "awaiting_participant_confirmation"
    assert done["model_calls"] == 7


async def test_reviewer_can_request_investigation(service):
    service.agents.model.reject_once = True
    rid = await service.start("maya", "Presentation design")
    s = await wait(service, rid)
    assert s["status"] == "awaiting_approval"
    assert s["revisions"] == 1


async def test_stale_plan_requires_fresh_approval(service):
    rid = await service.start("maya", "Presentation design")
    s = await wait(service, rid)
    old = s["plan"]["fingerprint"]
    Repository(service.settings.domain_db).remove_availability("nina", "2026-10-27")
    await service.resume(rid, {"decision": "approve", "fingerprint": old})
    fresh = await wait(service, rid)
    assert fresh["status"] == "awaiting_approval"
    assert fresh["plan"]["fingerprint"] != old
    assert fresh["plan"]["sessions"][2]["start_utc"] == "2026-10-28T14:00:00+00:00"
    assert fresh["result"] is None


async def test_restart_restores_approval(tmp_path):
    settings = Settings(
        domain_db=tmp_path / "domain.sqlite", checkpoint_db=tmp_path / "check.sqlite"
    )
    async with MCPRouter(settings) as router:
        async with RunService(settings, router, ControlledModel()) as first:
            rid = await first.start("maya", "Presentation design")
            before = await wait(first, rid)
        async with RunService(settings, router, ControlledModel()) as second:
            after = await second.snapshot(rid)
            assert after["plan"] == before["plan"]
            assert after["status"] == "awaiting_approval"
            await second.resume(
                rid, {"decision": "approve", "fingerprint": after["plan"]["fingerprint"]}
            )
            assert (await wait(second, rid))["status"] == "saved"


async def test_double_resume_and_unknown_write_outcome_create_one_proposal(service):
    rid = await service.start("maya", "Presentation design")
    s = await wait(service, rid)
    original = service.router.call
    lost = False

    async def unreliable(server, tool, arguments, ctx, role="host"):
        nonlocal lost
        result = await original(server, tool, arguments, ctx, role)
        if tool == "save_proposal" and not lost:
            lost = True
            raise TimeoutError("response lost")
        return result

    service.router.call = unreliable
    payload = {"decision": "approve", "fingerprint": s["plan"]["fingerprint"]}
    await asyncio.gather(
        service.resume(rid, payload), service.resume(rid, payload), return_exceptions=True
    )
    assert (await wait(service, rid))["status"] == "saved"
    with Repository(service.settings.domain_db).connection() as db:
        assert db.execute("SELECT COUNT(*) FROM proposals").fetchone()[0] == 1


async def test_model_budget_and_quota_stop_truthfully(service):
    service.agents.model.quota = True
    rid = await service.start("maya", "Presentation design")
    s = await wait(service, rid)
    assert s["status"] == "quota_limited"
    assert s["plan"] is None
    assert s["model_calls"] <= 2


async def test_cancel_and_revision_exclusions(service):
    rid = await service.start("maya", "Presentation design")
    await wait(service, rid)
    await service.resume(rid, {"decision": "cancel"})
    assert (await wait(service, rid))["status"] == "cancelled"
    child = await service.start("maya", "Presentation design", ["nina", "olivia", "zara"], rid)
    assert (await wait(service, child))["status"] == "no_match"


async def test_malformed_output_gets_one_bounded_retry(service):
    original = service.agents.model.ainvoke
    failures = 0

    async def malformed(messages):
        nonlocal failures
        if service.agents.model.schema and failures < 1:
            failures += 1
            from skillswap.agents import Interpretation

            return Interpretation.model_validate({"goal": {"skill_id": "invented"}})
        return await original(messages)

    service.agents.model.ainvoke = malformed
    rid = await service.start("maya", "Presentation design")
    state = await wait(service, rid)
    assert state["status"] == "awaiting_approval"
    assert state["model_calls"] == 8


async def test_model_call_ceiling_is_enforced(service):
    original = service.agents.model.ainvoke

    async def always_reject(messages):
        service.agents.model.reject_once = True
        return await original(messages)

    service.agents.model.ainvoke = always_reject
    rid = await service.start("maya", "Presentation design")
    state = await wait(service, rid)
    assert state["status"] == "stopped"
    assert state["model_calls"] <= 16
    assert state["result"] is None


async def test_read_timeout_stops_without_fabricated_plan(service):
    original = service.router.call

    async def fail(server, tool, arguments, ctx, role="host"):
        if role == "interpreter":
            raise TimeoutError()
        return await original(server, tool, arguments, ctx, role)

    service.router.call = fail
    rid = await service.start("maya", "Presentation design")
    state = await wait(service, rid)
    assert state["status"] == "execution_timeout"
    assert state["plan"] is None


async def test_uncertain_save_can_be_recovered_without_new_proposal(service):
    rid = await service.start("maya", "Presentation design")
    state = await wait(service, rid)
    original = service.router.call
    save_happened = False

    async def uncertain(server, tool, arguments, ctx, role="host"):
        nonlocal save_happened
        if tool == "get_proposal_status" and save_happened:
            raise TimeoutError()
        result = await original(server, tool, arguments, ctx, role)
        if tool == "save_proposal":
            save_happened = True
            raise TimeoutError()
        return result

    service.router.call = uncertain
    await service.resume(rid, {"decision": "approve", "fingerprint": state["plan"]["fingerprint"]})
    assert (await wait(service, rid))["status"] == "save_error"
    service.router.call = original
    await service.resume(rid, {"decision": "retry"})
    assert (await wait(service, rid))["status"] == "saved"
    with Repository(service.settings.domain_db).connection() as db:
        assert db.execute("SELECT COUNT(*) FROM proposals").fetchone()[0] == 1


async def test_provider_deadline_failure_is_visible(service):
    async def deadline(messages):
        raise RuntimeError("504 DEADLINE_EXCEEDED")

    service.agents.model.ainvoke = deadline
    rid = await service.start("maya", "Presentation design")
    result = await wait(service, rid)
    assert result["status"] == "provider_unavailable"
    assert result["plan"] is None


async def test_saved_proposal_recovery_survives_exhausted_active_budget(service):
    rid = await service.start("maya", "Presentation design")
    before = await wait(service, rid)
    original = service.router.call
    saved = asyncio.Event()

    async def slow_response(server, tool, arguments, ctx, role="host"):
        result = await original(server, tool, arguments, ctx, role)
        if tool == "save_proposal":
            saved.set()
            await asyncio.sleep(1)
        return result

    service.router.call = slow_response
    service.update(rid, active_seconds=89.5)
    await service.resume(rid, {"decision": "approve", "fingerprint": before["plan"]["fingerprint"]})
    await asyncio.wait_for(saved.wait(), 2)
    state = await wait(service, rid)
    assert state["status"] == "save_error"
    assert state["active_seconds"] >= 90
    service.router.call = original
    await service.resume(rid, {"decision": "retry"})
    recovered = await wait(service, rid)
    assert recovered["status"] == "saved"
    assert recovered["result"]["plan"]["fingerprint"] == before["plan"]["fingerprint"]
    with Repository(service.settings.domain_db).connection() as db:
        assert db.execute("SELECT COUNT(*) FROM proposals").fetchone()[0] == 1
