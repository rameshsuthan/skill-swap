# SkillSwap

Turn what you know into what you want to learn. A local React workspace uses three Gemini specialists in LangGraph and a real custom MCP server to propose reciprocal learning exchanges across a global cohort.

**Current status:** local domain, MCP, workflow, API and browser acceptance checks pass. Live `gemini-3.8-flash` metadata is accessible, but generation returned HTTP 503 (high demand) and HTTP 504 (deadline exceeded) during setup. A complete live model workflow is **not yet verified**. No model was substituted. Mem0 and Pinecone remain disabled pending that check.

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

Set the API key privately. Keep `GEMINI_MODEL=gemini-3.8-flash`. This uses the Gemini Developer API with `vertexai=False`. No alternate-model fallback or billing changes occur. The generation API cannot prove the account's billing tier or remaining quota; inspect the project's tier and limits in Google AI Studio. [Google's model pricing](https://ai.google.dev/gemini-api/docs/pricing) lists free-tier access for the configured model.

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

Only the four read/validation tools reach LLM roles. Host-only save/status calls enforce current revision, exact sessions, immutable exclusions, fingerprint, scope, and idempotency. A lost save response triggers status lookup before retry; **Recover save** handles an unresolved outcome without creating a second proposal. Recovery has a separate 30-second host-only window even if the 90-second investigation budget is exhausted; it cannot add model time or change the approved plan.

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

Browser tests use an explicitly separate test entry point and databases. The test model exists only in `backend/tests`; it is never selectable in the production application. MCP, SQLite, LangGraph, HTTP, and browser interactions are real.

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

This is a local single-operator prototype, not a public multi-user service. It has no production authentication, messaging or live calendar integration. Keep one backend worker. Matching uses full authorized-cohort skill eligibility and UTC overlap, with no geographic distance filter. LangGraph persists run-local state; no Mem0/Pinecone integration is claimed.

Secrets, runtimes, dependencies and runtime databases are ignored by Git. The original handouts remain unchanged and untracked. Commits are local on `build/skillswap`; no remote repository or public deployment has been created.
