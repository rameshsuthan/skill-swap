from copy import deepcopy
from types import SimpleNamespace

import pytest
from skillswap.models import LearningGoal
from skillswap.settings import Settings
from skillswap.vendor_search import SemanticSearch, offer_hash


class SearchClient:
    def __init__(self):
        self.calls = []
        self.hits = []
        self.fail = False

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass

    async def list_tools(self):
        if self.fail:
            raise TimeoutError("vendor offline")
        return [
            SimpleNamespace(
                name="search-records",
                input_schema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "object",
                            "properties": {
                                "inputs": {
                                    "type": "object",
                                    "properties": {"text": {"type": "string"}},
                                }
                            },
                        }
                    },
                },
            )
        ]

    async def call_tool(self, name, args):
        self.calls.append((name, deepcopy(args)))
        if self.fail:
            raise TimeoutError("vendor failure with sensitive details")
        return SimpleNamespace(is_error=False, structured_content={"result": {"hits": self.hits}})


def hit(profile, **fields):
    return {
        "_id": profile.id,
        "_score": 0.9,
        "fields": {
            "project": "skillswap-demo",
            "cohort_id": profile.cohort_id,
            "active": profile.active,
            "profile_id": profile.id,
            "offer_hash": offer_hash(profile),
            **fields,
        },
    }


@pytest.fixture
def semantic(tmp_path):
    settings = Settings(
        pinecone_enabled=True,
        pinecone_api_key="test",
        pinecone_index="skillswap-demo",
        pinecone_namespace="global-2026",
        domain_db=tmp_path / "domain.sqlite",
        checkpoint_db=tmp_path / "checkpoint.sqlite",
    )
    client = SearchClient()
    search = SemanticSearch(settings, client_factory=lambda: client)
    return search, client


async def test_semantic_hit_cannot_bypass_proficiency(semantic, profiles, actor):
    search, client = semantic
    zara = next(p for p in profiles if p.id == "zara")
    client.hits = [hit(zara)]
    hits = await search.search(actor, "beautiful slides")
    assert search.hydrate(actor, hits, profiles, LearningGoal(skill_id="presentation_design")) == []


async def test_stale_or_other_cohort_ids_dropped(semantic, profiles, actor):
    search, client = semantic
    nina = next(p for p in profiles if p.id == "nina")
    client.hits = [
        hit(nina, cohort_id="other"),
        hit(nina, offer_hash="old-hash"),
        hit(nina, profile_id="unknown"),
        hit(nina, active=False),
        hit(nina),
    ]
    hits = await search.search(actor, "slides")
    hydrated = search.hydrate(actor, hits, profiles, LearningGoal(skill_id="presentation_design"))
    assert [h.profile_id for h in hydrated] == ["nina"]
    assert "presentation" in hydrated[0].evidence.lower()
    args = client.calls[-1][1]
    assert args["name"] == "skillswap-demo"
    assert args["namespace"] == "global-2026"
    assert args["query"]["filter"] == {
        "project": {"$eq": "skillswap-demo"},
        "cohort_id": {"$eq": "global-2026"},
        "active": {"$eq": True},
    }


async def test_top_k_does_not_hide_valid_cycle(semantic, actor):
    from fake_model import ControlledModel
    from skillswap.mcp_router import MCPRouter
    from skillswap.models import MemberProfile
    from skillswap.repository import Repository
    from skillswap.workflow import RunService

    search, client = semantic
    repo = Repository(search.settings.domain_db)
    repo.ensure_seeded()
    profiles = [MemberProfile.model_validate(p) for p in repo.get_context(actor)["profiles"]]
    # Strong semantic hit, but no overlap with Maya. Full cohort must still find Nina.
    client.hits = [hit(next(p for p in profiles if p.id == "olivia"))]
    async with MCPRouter(search.settings, semantic=search) as router:
        async with RunService(search.settings, router, ControlledModel()) as service:
            rid = await service.start("maya", "Presentation design")
            await service.wait(rid)
            state = await service.snapshot(rid)
            assert state["status"] == "awaiting_approval"
            assert "nina" in state["plan"]["cycle"]["member_ids"]
            assert state["discovery"]["source"] == "semantic"
            assert state["model_calls"] == 8


async def test_outage_uses_labeled_local_search(semantic, actor):
    from fake_model import ControlledModel
    from skillswap.mcp_router import MCPRouter
    from skillswap.workflow import RunService

    search, client = semantic
    async with MCPRouter(search.settings, semantic=search) as router:
        client.fail = True
        async with RunService(search.settings, router, ControlledModel()) as service:
            rid = await service.start("maya", "Presentation design")
            await service.wait(rid)
            state = await service.snapshot(rid)
            assert state["status"] == "awaiting_approval"
            assert state["discovery"]["source"] == "local"
            assert "unavailable" in state["discovery"]["detail"].lower()
            assert search.provider()["mode"] == "degraded"


async def test_runtime_tool_allowlist_excludes_admin(semantic, actor):
    from skillswap.mcp_router import MCPRouter

    search, _ = semantic
    router = MCPRouter(search.settings, semantic=search)
    for name in ["create-index-for-model", "upsert-records", "delete-index"]:
        with pytest.raises(ValueError, match="tool_not_allowed"):
            await router.call("pinecone", name, {}, actor, role="coordinator")
    with pytest.raises(ValueError, match="scope_override"):
        await router.call(
            "pinecone",
            "search-records",
            {"query_text": "slides", "namespace": "foreign"},
            actor,
            role="coordinator",
            goal=LearningGoal(skill_id="presentation_design"),
        )


async def test_setup_accepts_vendor_plain_text_upsert_acknowledgement():
    import runpy

    from skillswap.settings import ROOT

    call = runpy.run_path(str(ROOT / "scripts/seed_pinecone.py"))["call"]

    class Client:
        async def call_tool(self, name, args):
            return SimpleNamespace(
                is_error=False,
                structured_content=None,
                content=[
                    SimpleNamespace(
                        text="Upserted 2 record(s) successfully. Pinecone is eventually consistent."
                    )
                ],
            )

    assert await call(Client(), "upsert-records", {"records": [{}, {}]}) == {"upserted_count": 2}


async def test_concurrent_success_and_failure_keep_their_own_search_status(
    semantic, profiles, actor
):
    import asyncio

    from skillswap.mcp_router import MCPRouter

    search, client = semantic
    client.hits = [hit(next(p for p in profiles if p.id == "nina"))]
    delayed = asyncio.Event()
    release = asyncio.Event()
    async with MCPRouter(search.settings, semantic=search) as router:
        original = router.call

        async def hydrate_barrier(server, tool, arguments, ctx, role="host", **kwargs):
            if (
                server == "skillswap"
                and tool == "get_learning_context"
                and ctx.run_id == "successful"
            ):
                delayed.set()
                await release.wait()
            return await original(server, tool, arguments, ctx, role, **kwargs)

        router.call = hydrate_barrier
        good_actor = actor.model_copy(update={"run_id": "successful"})
        bad_actor = actor.model_copy(update={"run_id": "failed"})
        goal = LearningGoal(skill_id="presentation_design")
        good_task = asyncio.create_task(
            router.call(
                "pinecone",
                "search-records",
                {"query_text": "slides"},
                good_actor,
                role="coordinator",
                goal=goal,
            )
        )
        await asyncio.wait_for(delayed.wait(), 2)
        client.fail = True
        bad = await router.call(
            "pinecone",
            "search-records",
            {"query_text": "slides"},
            bad_actor,
            role="coordinator",
            goal=goal,
        )
        release.set()
        good = await good_task
        assert good["mode"] == "test"
        assert good["candidates"]
        assert bad["mode"] == "degraded"
        assert bad["candidates"] == []
        assert "unavailable" in bad["detail"]
