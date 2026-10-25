"""Tiny live check. Never emit provider exception strings or credentials."""

import asyncio
import json
import logging

from langchain_core.messages import HumanMessage, ToolMessage
from pydantic import BaseModel
from skillswap.model_factory import make_model
from skillswap.settings import Settings

logging.disable(logging.CRITICAL)


class Probe(BaseModel):
    ok: bool


async def main():
    settings = Settings()
    print(
        json.dumps(
            {
                "key_configured": bool(settings.google_api_key.get_secret_value()),
                "model": settings.gemini_model,
            }
        ),
        flush=True,
    )
    model = make_model(settings)
    try:
        answer = await model.with_structured_output(Probe).ainvoke("Return ok true.")
        print(json.dumps({"structured_response": answer.ok}), flush=True)
        schema = {
            "name": "probe_context",
            "description": "Get the fictional cohort size.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        }
        messages = [HumanMessage(content="Call probe_context to learn the cohort size.")]
        result = await model.bind_tools([schema], tool_choice="any").ainvoke(messages)
        assert result.tool_calls and result.tool_calls[0]["name"] == "probe_context"
        messages += [
            result,
            ToolMessage(content='{"profile_count":15}', tool_call_id=result.tool_calls[0]["id"]),
        ]
        final = await model.ainvoke(messages)
        print(
            json.dumps(
                {
                    "model_tool_roundtrip": bool(final.content),
                    "quota": "request accepted; account tier and remaining quota are not exposed by generation API",
                }
            )
        )
    except Exception as e:
        code = getattr(e, "code", None) or getattr(e, "status_code", None)
        print(
            json.dumps(
                {
                    "gemini": "blocked",
                    "error_type": type(e).__name__,
                    "status_code": str(code) if code else None,
                }
            )
        )
        raise SystemExit(1)


asyncio.run(main())
