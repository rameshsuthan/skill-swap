"""Two fresh Python processes prove persisted approval is not process memory."""

import json
import os
import subprocess
import sys

from skillswap.settings import ROOT

WORKER = """
import asyncio,json,sys
from skillswap.settings import Settings
from skillswap.mcp_router import MCPRouter
from skillswap.workflow import RunService
from fake_model import ControlledModel
async def main():
 s=Settings()
 async with MCPRouter(s) as r:
  async with RunService(s,r,ControlledModel()) as service:
   if len(sys.argv)==1:
    rid=await service.start('maya','Presentation design')
   else:
    rid=sys.argv[1]
    state=await service.snapshot(rid)
    assert state['status']=='awaiting_approval'
    await service.resume(rid,{'decision':'approve','fingerprint':state['plan']['fingerprint']})
   await service.wait(rid)
   state=await service.snapshot(rid)
   print(json.dumps({'run_id':rid,'status':state['status'],'plan':state['plan'],'result':state['result']}))
asyncio.run(main())
"""


def test_fresh_process_restores_and_saves_exact_approved_plan(tmp_path):
    env = {
        **os.environ,
        "SKILLSWAP_DOMAIN_DB": str(tmp_path / "domain.sqlite"),
        "SKILLSWAP_CHECKPOINT_DB": str(tmp_path / "check.sqlite"),
        "PYTHONPATH": str(ROOT / "backend/tests"),
    }

    def run(*args):
        result = subprocess.run(
            [sys.executable, "-c", WORKER, *args],
            env=env,
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=20,
            check=True,
        )
        return json.loads(result.stdout)

    before = run()
    assert before["status"] == "awaiting_approval"
    after = run(before["run_id"])
    assert after["status"] == "saved"
    assert after["result"]["plan"] == before["plan"]
