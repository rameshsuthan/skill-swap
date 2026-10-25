import time

from fake_model import ControlledModel
from fastapi.testclient import TestClient
from skillswap.api import create_app
from skillswap.settings import Settings


def test_api_context_approval_export_and_event_replay(tmp_path):
    settings = Settings(
        domain_db=tmp_path / "domain.sqlite", checkpoint_db=tmp_path / "check.sqlite"
    )
    with TestClient(create_app(settings, ControlledModel())) as c:
        assert len(c.get("/api/context?member_id=maya").json()["profiles"]) == 15
        assert c.get("/api/providers").json()["mem0"]["mode"] == "disabled"
        rid = c.post(
            "/api/runs",
            json={"member_id": "maya", "request": "Presentation design", "excluded_member_ids": []},
        ).json()["run_id"]
        for _ in range(100):
            state = c.get("/api/runs/" + rid).json()
            if state["status"] != "running":
                break
            time.sleep(0.05)
        assert state["status"] == "awaiting_approval"
        assert (
            c.post(
                f"/api/runs/{rid}/resume", json={"decision": "approve", "fingerprint": "wrong"}
            ).status_code
            == 409
        )
        events = c.get(f"/api/runs/{rid}/events").json()
        assert len(events) > 5
        assert c.get(f"/api/runs/{rid}/events?after=" + str(events[-1]["sequence"])).json() == []
        c.post(
            f"/api/runs/{rid}/resume",
            json={"decision": "approve", "fingerprint": state["plan"]["fingerprint"]},
        )
        for _ in range(100):
            state = c.get("/api/runs/" + rid).json()
            if state["status"] != "running":
                break
            time.sleep(0.05)
        assert state["status"] == "saved"
        pid = state["result"]["id"]
        assert (
            c.get(f"/api/proposals/{pid}/export?member_id=maya").json()["status"]
            == "awaiting_participant_confirmation"
        )
        assert c.get(f"/api/proposals/{pid}/export?member_id=leo").status_code == 404
        assert c.get("/api/runs/unknown").status_code == 404
