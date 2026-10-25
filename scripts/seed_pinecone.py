"""Explicit setup only: create a SkillSwap index and upsert public fictional offers via MCP."""

import argparse
import asyncio
import json

from skillswap.mcp_router import MCPRouter
from skillswap.models import CATALOG, ActorContext, MemberProfile
from skillswap.settings import Settings
from skillswap.vendor_search import offer_hash, pinecone_client

SKILL_CONTEXT = {
    "presentation_design": "Clear slide decks, visual storytelling and layouts for presentations.",
    "python": "Python programming, scripts, debugging and practical coding projects.",
    "sql": "SQL database queries, joins and analysis of structured data.",
    "spanish": "Spanish conversation, vocabulary and language practice.",
    "excel_automation": "Excel spreadsheets, formulas and automation of repetitive workbook tasks.",
}


def public_record(profile):
    return {
        "_id": profile.id,
        "profile_id": profile.id,
        "cohort_id": profile.cohort_id,
        "project": "skillswap-demo",
        "active": profile.active,
        "skill_id": profile.offer.skill_id,
        "offer_hash": offer_hash(profile),
        "text": f"{profile.display_name} teaches {CATALOG[profile.offer.skill_id]}. "
        f"{SKILL_CONTEXT[profile.offer.skill_id]} {profile.offer.description} "
        f"Declared proficiency {profile.offer.proficiency}/3. "
        f"Teaching styles: {', '.join(profile.offer.styles)}.",
    }


async def call(client, name, args):
    result = await client.call_tool(name, args)
    if result.is_error:
        raise ValueError("pinecone_setup_failed")
    data = result.structured_content
    if data is None:
        text = result.content[0].text
        if name == "upsert-records" and text.startswith(
            f"Upserted {len(args['records'])} record(s) successfully."
        ):
            return {"upserted_count": len(args["records"])}
        if name == "create-index-for-model" and text.startswith(
            "Index not created. An index named "
        ):
            return {"already_exists": True}
        data = json.loads(text)
    if isinstance(data, dict) and data.get("error"):
        raise ValueError("pinecone_setup_failed")
    return data


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--create-index",
        action="store_true",
        help="Explicitly create the configured SkillSwap index if absent; uses the existing account plan.",
    )
    args = parser.parse_args()
    settings = Settings()
    if not settings.pinecone_index.startswith("skillswap-"):
        raise ValueError("setup_requires_skillswap_index")
    if not settings.pinecone_api_key.get_secret_value():
        raise ValueError("pinecone_key_required")
    async with MCPRouter(
        settings.model_copy(update={"mem0_enabled": False, "pinecone_enabled": False})
    ) as router:
        data = await router.call(
            "skillswap",
            "get_learning_context",
            {},
            ActorContext(member_id="maya", cohort_id=settings.cohort_id, run_id="pinecone-seed"),
        )
    profiles = [MemberProfile.model_validate(p) for p in data["profiles"]]
    async with pinecone_client(settings) as client:
        indexes = await call(client, "list-indexes", {})
        if not any(i["name"] == settings.pinecone_index for i in indexes["indexes"]):
            if not args.create_index:
                raise ValueError("index_missing_run_with_explicit_create_flag")
            await call(
                client,
                "create-index-for-model",
                {
                    "name": settings.pinecone_index,
                    "cloud": "aws",
                    "region": "us-east-1",
                    "embed": {"model": "llama-text-embed-v2", "fieldMap": {"text": "text"}},
                },
            )
        for _ in range(20):
            index = await call(client, "describe-index", {"name": settings.pinecone_index})
            if index.get("status", {}).get("ready"):
                break
            await asyncio.sleep(2)
        else:
            raise ValueError("index_not_ready")
        embed = index.get("embed", {})
        if embed.get("model") != "llama-text-embed-v2" or embed.get("fieldMap") != {"text": "text"}:
            raise ValueError("index_embedding_config_mismatch")
        result = await call(
            client,
            "upsert-records",
            {
                "name": settings.pinecone_index,
                "namespace": settings.pinecone_namespace,
                "records": [public_record(p) for p in profiles],
            },
        )
        print(
            json.dumps(
                {
                    "index": settings.pinecone_index,
                    "namespace": settings.pinecone_namespace,
                    "fictional_records_submitted": len(profiles),
                    "upsert_acknowledged": result is not None,
                }
            )
        )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as exc:
        # SDK exceptions can contain request details; never emit their raw representation.
        print(json.dumps({"setup": "failed", "error_type": type(exc).__name__}))
        raise SystemExit(1) from None
