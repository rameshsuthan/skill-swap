from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .mcp_router import MCPRouter
from .model_factory import make_model
from .models import ActorContext
from .settings import ROOT, Settings
from .workflow import RunService


class StartRun(BaseModel):
    member_id: str
    request: str = Field(min_length=1, max_length=2000)
    excluded_member_ids: list[str] = []
    parent_run_id: str | None = None


class UnconfiguredModel:
    def bind_tools(self, *args, **kwargs):
        return self

    async def ainvoke(self, *args, **kwargs):
        raise ValueError("google_api_key_required")


def create_app(settings=None, model=None):
    settings = settings or Settings()

    @asynccontextmanager
    async def lifespan(app):
        async with MCPRouter(settings) as router:
            chosen = model
            if chosen is None:
                chosen = (
                    make_model(settings)
                    if settings.google_api_key.get_secret_value()
                    else UnconfiguredModel()
                )
            async with RunService(settings, router, chosen) as service:
                app.state.router = router
                app.state.service = service
                yield

    app = FastAPI(title="SkillSwap", lifespan=lifespan)

    @app.middleware("http")
    async def local_writes(request: Request, call_next):
        # Local single-operator demo: reject cross-origin browser writes.
        origin = request.headers.get("origin")
        if (
            request.method not in {"GET", "HEAD", "OPTIONS"}
            and origin
            and origin
            not in {
                "http://127.0.0.1:5173",
                "http://localhost:5173",
                "http://127.0.0.1:8000",
                "http://localhost:8000",
            }
        ):
            return JSONResponse({"detail": "origin_not_allowed"}, status_code=403)
        return await call_next(request)

    @app.exception_handler(ValueError)
    async def value_error(request, exc):
        code = str(exc)
        allowed = {
            "run_not_found",
            "actor_not_found",
            "approval_fingerprint_mismatch",
            "approval_decision_required",
            "clarification_answer_required",
            "run_not_waiting",
            "invalid_request",
            "invalid_exclusions",
            "parent_scope_mismatch",
            "parent_still_running",
        }
        return JSONResponse(
            {"detail": code if code in allowed else "invalid_operation"},
            status_code=404 if code in {"run_not_found", "actor_not_found"} else 409,
        )

    @app.get("/api/context")
    async def context(member_id: str = "maya"):
        return await app.state.router.call(
            "skillswap",
            "get_learning_context",
            {},
            ActorContext(member_id=member_id, run_id="context"),
        )

    @app.post("/api/runs")
    async def start(body: StartRun):
        rid = await app.state.service.start(
            body.member_id, body.request, body.excluded_member_ids, body.parent_run_id
        )
        return {"run_id": rid}

    @app.get("/api/runs/{run_id}")
    async def snapshot(run_id: str):
        return await app.state.service.snapshot(run_id)

    @app.get("/api/runs/{run_id}/events")
    async def events(run_id: str, after: int = 0):
        app.state.service.record(run_id)
        return app.state.router.events.list_after(run_id, max(0, after))

    @app.post("/api/runs/{run_id}/resume")
    async def resume(run_id: str, body: dict):
        return await app.state.service.resume(run_id, body)

    @app.get("/api/proposals/{proposal_id}/export")
    async def export(proposal_id: str, member_id: str):
        result = await app.state.router.call(
            "skillswap",
            "get_proposal_status",
            {"proposal_id": proposal_id},
            ActorContext(member_id=member_id, run_id="export"),
        )
        if not result["proposal"]:
            raise HTTPException(404, "proposal_not_found")
        return JSONResponse(
            result["proposal"],
            headers={"Content-Disposition": f'attachment; filename="skillswap-{proposal_id}.json"'},
        )

    @app.get("/api/providers")
    async def providers():
        with app.state.service.db() as db:
            row = db.execute("SELECT status FROM runs ORDER BY rowid DESC LIMIT 1").fetchone()
            successes = db.execute(
                'SELECT COUNT(*) FROM events WHERE payload LIKE \'%"server": "gemini"%\' AND payload LIKE \'%"status": "ok"%\''
            ).fetchone()[0]
        latest = row[0] if row else None
        mode = (
            "disabled"
            if not settings.google_api_key.get_secret_value() and model is None
            else "connecting"
        )
        if latest in {
            "provider_unavailable",
            "provider_access_denied",
            "quota_limited",
            "execution_error",
        }:
            mode = "degraded"
        elif successes:
            mode = "live" if model is None else "test"
        return {
            "gemini": {
                "mode": mode,
                "model": settings.gemini_model,
                "detail": latest or "Awaiting generation check",
                "tier": "free-tier target; account quota not verified by API",
            },
            "skillswap": {"mode": "live", "tools": list(app.state.router.schemas)},
            "mem0": {"mode": "disabled", "detail": "Bonus deferred until live core passes"},
            "pinecone": {"mode": "disabled", "detail": "Bonus deferred until live core passes"},
        }

    if (ROOT / "frontend/dist").is_dir():
        app.mount("/", StaticFiles(directory=ROOT / "frontend/dist", html=True), name="frontend")
    return app


app = create_app()
