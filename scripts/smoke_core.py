"""Explicitly approves a fictional proposal using live Gemini and real MCP."""

import argparse
import asyncio
import json

from skillswap.mcp_router import MCPRouter
from skillswap.model_factory import make_model
from skillswap.settings import Settings
from skillswap.workflow import RunService


async def main():
    p = argparse.ArgumentParser()
    p.add_argument("--live-model", required=True, action="store_true")
    p.parse_args()
    settings = Settings()
    async with MCPRouter(settings) as router:
        async with RunService(settings, router, make_model(settings)) as service:
            rid = await service.start(
                "maya", "I want to learn presentation design from a working-level teacher."
            )
            await service.wait(rid)
            state = await service.snapshot(rid)
            print(
                json.dumps(
                    {
                        k: state[k]
                        for k in ("run_id", "status", "model_calls", "active_seconds", "error")
                    }
                )
            )
            if state["status"] != "awaiting_approval":
                raise SystemExit(1)
            await service.resume(
                rid, {"decision": "approve", "fingerprint": state["plan"]["fingerprint"]}
            )
            await service.wait(rid)
            state = await service.snapshot(rid)
            if state["status"] != "saved":
                raise SystemExit(1)
            print(
                json.dumps(
                    {"proposal_id": state["result"]["id"], "status": state["result"]["status"]}
                )
            )
        async with RunService(settings, router, make_model(settings)) as restarted:
            recovered = await restarted.snapshot(rid)
            assert recovered["result"] == state["result"]
            print(json.dumps({"restart_recovery": "passed"}))


asyncio.run(main())
