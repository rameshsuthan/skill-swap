# SkillSwap

Turn what you know into what you want to learn. A local React workspace uses three Gemini specialists in LangGraph and a real custom MCP server to propose reciprocal learning exchanges across a global cohort.

**Current status:** the local prototype and a complete live `gemini-3.5-flash-lite` workflow are verified. The user authorized this model after `gemini-3.8-flash` returned HTTP 503/504. Structured output, a real Gemini-requested MCP round trip, all three specialists, approval/save, and restart recovery passed. Mem0 preference memory now has verified live MCP CRUD, explicit UI controls, and a live fresh-session recommendation change with approval/save/recovery. Pinecone remains optional and disabled.

Approval saves an **unconfirmed proposal**. It does not book sessions, reserve availability, or contact anyone. All 15 profiles are fictional. Dates are October 26–30, 2026.

## Start on this machine

```bash
bash scripts/dev.sh
```

Open <http://127.0.0.1:5173>. The backend listens only on `127.0.0.1:8000`, with one worker. The script uses project-local Node when available. Credentials stay in the root `.env`; `GEMINI_API_KEY` is accepted as an alias for `GOOGLE_API_KEY`.

## Reproducible setup

Requirements: Python 3.12, Node 22.12+ (tested 22.23.4), and `uv`.

```bash
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -r backend/requirements.lock
uv pip install --python .venv/bin/python --no-deps -e backend
npm --prefix frontend ci
# Only if .env does not already exist:
cp .env.example .env
```

Set the API key privately. The active setting is `GEMINI_MODEL=gemini-3.5-flash-lite`. Both explicitly authorized model IDs remain allowed; the app never switches automatically. This uses the Gemini Developer API with `vertexai=False`. No billing changes occur. The generation API cannot prove the account's billing tier or remaining quota; inspect the project's tier and limits in Google AI Studio. [Google's model pricing](https://ai.google.dev/gemini-api/docs/pricing) lists free-tier access for the configured model.

```bash
.venv/bin/python scripts/preflight.py --core
.venv/bin/python scripts/preflight.py --local-only
.venv/bin/python scripts/smoke_core.py --live-model
```

The live smoke explicitly approves one fictional proposal, then reloads it through a fresh service. A provider failure exits nonzero with a sanitized reason. It never switches models. `scripts/check_gemini.py` is the small isolated generation diagnostic; `preflight.py` tests Gemini's requested tool call through actual MCP.

## Core workflow

1. Select Maya and request presentation design. The interpreter resolves the goal, coordinator investigates teachers and cycles, and reviewer validates the exact schedule.
2. Review Maya → Leo (Python), Leo → Nina (Spanish), and Nina → Maya (presentation design). Each edge is a separate 30-minute session, displayed in both participants' zones.
3. Approve the exact fingerprint to save. Reload and download its JSON. A SQLite checkpoint preserves an approval or clarification across process restart.
4. Use **Revise my exchange** and optional explicit exclusions for a new child run. The old pending run is cancelled. **New search** clears the browser's current selection, not saved records.

Only read/validation tools reach LLM roles, including scoped Mem0 search when enabled. Host-only save/status calls enforce current revision, exact sessions, immutable exclusions, fingerprint, scope, and idempotency. A lost save response triggers status lookup before retry; **Recover save** handles an unresolved outcome without creating a second proposal. Recovery has a separate 30-second host-only window even if the 90-second investigation budget is exhausted; it cannot add model time or change the approved plan.

## Demo scenarios

```bash
# Removes Nina's original Oct 27 slot; Oct 28 replacement remains.
.venv/bin/python scripts/demo_scenario.py remove-nina-window
# Revalidates a timezone edit by clearing future availability.
.venv/bin/python scripts/demo_scenario.py timezone-change
# Reset fictional profiles, increment revision, preserve historical proposals.
.venv/bin/python scripts/seed_demo.py
```

After a scenario, attempting old approval must produce a fresh proposal requiring another approval. Never edit a runtime database directly. Historical proposals retain approved timezone snapshots.

## Verification

```bash
.venv/bin/python -m pytest backend/tests -q
.venv/bin/ruff check backend scripts
npm --prefix frontend run build
```

Browser tests use an explicitly separate test entry point and databases. Controlled model/memory boundaries exist only in `backend/tests`; they are never selectable in the production application and carry test badges. MCP, SQLite, LangGraph, HTTP, and browser interactions are real.

```bash
export PATH="$PWD/.tools/node/bin:$PATH" # or use your installed Node
export PLAYWRIGHT_BROWSERS_PATH="$PWD/.tools/browsers"
frontend/node_modules/.bin/playwright install chromium
# Stop the ordinary dev servers first; the test runner needs 8000 and 5173.
bash scripts/test_browser.sh
```

## Layout and boundaries

- `backend/src/skillswap`: domain contracts, deterministic scheduling, MCP server/client, three agent roles, LangGraph and API.
- `frontend/src`: React workspace, explicit-zone display helpers and typed API.
- `data/demo_cohort.json`: validated local-source windows and their UTC expectations.
- `storage/skillswap.sqlite`: domain facts and saved proposals; domain MCP process is the runtime writer.
- `storage/checkpoints.sqlite`: graph checkpoints, run metadata and sanitized activity.
- [Architecture](docs/skillswap/architecture.md), [validation](docs/validation-results.md), [demo script](docs/demo-script.md), [build log](docs/build-log.md).

This is a local single-operator prototype, not a public multi-user service. It has no production authentication, messaging or live calendar integration. Keep one backend worker. Matching uses full authorized-cohort skill eligibility and UTC overlap, with no geographic distance filter. LangGraph persists run-local state; optional Mem0 retains explicitly saved preferences. Pinecone is not yet integrated.

Secrets, runtimes, dependencies and runtime databases are ignored by Git. The original handouts remain unchanged and untracked. Commits are local on `build/skillswap`; no remote repository or public deployment has been created.

## Remembered preferences (Mem0 bonus)

Set `SKILLSWAP_MEM0_ENABLED=true` and `MEM0_API_KEY` in the private root `.env`, then restart the backend. The application connects to the [hosted Mem0 MCP server](https://docs.mem0.ai/platform/mem0-mcp); no machine-wide MCP configuration is needed.

Below the exchange workspace, **Learning preferences** supports Remember, Edit, and Forget for the selected fictional learner. Nothing is written automatically. Start a fresh search after changing a preference. Mem0 scopes each record to the project/cohort/member; other learners cannot see or mutate it through the app. These are preferences about teaching style, not changes to availability.

The interpreter resolves the requested skill and proficiency before retrieving memory. The coordinator can then rank feasible exchanges using remembered styles and current profile evidence. Memory cannot override explicit exclusions, scheduling, or eligibility. An unavailable memory provider leaves the core workflow usable and displays a degraded badge.

Pending changes remain unconfirmed across restart. **Check pending change** queries the known event or reconciles the unique operation marker through scoped reads; it never repeats a write. If a response is permanently lost and no result can be found, **Continue without confirmation** unlocks the controls while keeping the outcome visibly uncertain. Refresh before repeating that change because it may still appear later.

```bash
# Real vendor CRUD, fresh-session retrieval, ownership checks, and cleanup.
.venv/bin/python scripts/smoke_mem0.py
# Live Gemini + Mem0 on isolated fictional data; pauses between runs for quota.
.venv/bin/python scripts/smoke_memory_workflow.py --live-model
# Optional visible demo: adds a feasible discussion-based alternative for Maya.
.venv/bin/python scripts/demo_scenario.py memory-alternatives
```

With the alternatives scenario, the default direct swap is Maya/Olivia. Remember “I prefer guided-project teaching over discussion for my learning,” then start a fresh search: Nina's declared guided-project style supports the Maya/Leo/Nina alternative. Reset with `scripts/seed_demo.py` to restore the original hero scenario. The live smoke uses its own learner ID and databases and deletes only its own test memory. Mem0 usage is separate from Gemini's free-tier target.
