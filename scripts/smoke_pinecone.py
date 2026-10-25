"""Read-only live semantic search through official Pinecone MCP + authoritative hydration."""

import asyncio
import json

from skillswap.mcp_router import MCPRouter
from skillswap.models import ActorContext, LearningGoal
from skillswap.settings import Settings


async def main():
    settings = Settings(pinecone_enabled=True, mem0_enabled=False)
    actor = ActorContext(member_id="maya", cohort_id=settings.cohort_id, run_id="pinecone-smoke")
    async with MCPRouter(settings) as router:
        result = await router.call(
            "pinecone",
            "search-records",
            {"query_text": "Help me create clear slide decks and visual stories for a talk"},
            actor,
            role="coordinator",
            goal=LearningGoal(skill_id="presentation_design"),
        )
        assert result["mode"] == "live", result["detail"]
        ids = [c["profile_id"] for c in result["candidates"]]
        assert "nina" in ids or "olivia" in ids, "no relevant eligible offer retrieved"
        assert "zara" not in ids, "insufficient proficiency must not pass hydration"
        print(
            json.dumps(
                {
                    "provider": "live",
                    "index": settings.pinecone_index,
                    "namespace": settings.pinecone_namespace,
                    "eligible_candidate_ids": ids,
                    "mcp_search_events": len(
                        [
                            e
                            for e in router.events.list_after(actor.run_id, 0)
                            if e["server"] == "pinecone" and e["status"] == "ok"
                        ]
                    ),
                }
            )
        )


if __name__ == "__main__":
    asyncio.run(main())
