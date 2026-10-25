"""Run from the project root with .venv/bin/python scripts/preflight.py --core."""

import argparse
import asyncio
import json
import platform
from importlib.metadata import version
from zoneinfo import TZPATH, ZoneInfo

from langchain_core.messages import HumanMessage, ToolMessage
from pydantic import BaseModel
from skillswap.mcp_router import MCPRouter
from skillswap.model_factory import error_code, make_model
from skillswap.models import ActorContext
from skillswap.settings import Settings


class Probe(BaseModel):
    ok: bool


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--core", action="store_true")
    parser.add_argument("--local-only", action="store_true")
    args = parser.parse_args()
    settings = Settings()
    print(
        json.dumps(
            {
                "python": platform.python_version(),
                "tzdata": version("tzdata"),
                "zoneinfo_sources": list(TZPATH),
                "model": settings.gemini_model,
                "key_configured": bool(settings.google_api_key.get_secret_value()),
            }
        )
    )
    for p in ("fastmcp", "langgraph", "langchain-google-genai", "fastapi"):
        print(json.dumps({"package": p, "version": version(p)}))
    async with MCPRouter(settings) as router:
        ctx = ActorContext(member_id="maya", run_id="preflight")
        context = await router.call("skillswap", "get_learning_context", {}, ctx)
        for p in context["profiles"]:
            ZoneInfo(p["timezone"])
        print(
            json.dumps(
                {
                    "mcp": "live",
                    "tools": list(router.schemas),
                    "profiles": len(context["profiles"]),
                    "timezone_validation": "passed",
                }
            )
        )
        if args.local_only:
            return
        model = make_model(settings)
        try:
            result = await model.with_structured_output(Probe).ainvoke("Return ok true.")
            assert result.ok
            schema = {
                "name": "get_learning_context",
                "description": "Retrieve the selected fictional learner and public cohort.",
                "parameters": {"type": "object", "properties": {}},
            }
            messages = [
                HumanMessage(content="Call get_learning_context and report the number of profiles.")
            ]
            response = await model.bind_tools([schema], tool_choice="any").ainvoke(messages)
            assert response.tool_calls[0]["name"] == "get_learning_context"
            actual = await router.call(
                "skillswap",
                "get_learning_context",
                response.tool_calls[0]["args"],
                ctx,
                role="interpreter",
            )
            messages.extend(
                [
                    response,
                    ToolMessage(
                        content=json.dumps(actual), tool_call_id=response.tool_calls[0]["id"]
                    ),
                ]
            )
            final = await model.ainvoke(messages)
            assert final.content
            print(
                json.dumps(
                    {
                        "structured_response": "passed",
                        "gemini_mcp_roundtrip": "passed",
                        "tier": "free-tier target; remaining account quota not exposed",
                    }
                )
            )
        except Exception as exc:
            print(
                json.dumps(
                    {
                        "gemini": "blocked",
                        "code": error_code(exc),
                        "exception_type": type(exc).__name__,
                    }
                )
            )
            raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())
