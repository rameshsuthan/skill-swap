# SkillSwap validation

Checked October 25, 2026 (America/Chicago). This report distinguishes deterministic tests, controlled LLM responses, real local transport, and live provider calls.

| Layer | Evidence | Result |
| --- | --- | --- |
| Python | Project-local CPython 3.12.15 | Installed |
| Node | Project-local 22.23.4, official archive SHA256 checked | Installed |
| Packages | `backend/requirements.lock`, `frontend/package-lock.json` | Resolved and pinned |
| Timezone data | System IANA `2026c-rearguard`; portable `tzdata` package 2026.5 also installed | Fixture zones resolve |
| Custom MCP | Real stdio subprocess, discovery of six schemas, 15 profiles, validate/save/status/retry | Passed |
| Domain tests | Direct swap; three-cycle without common slot; no participant overlaps; proficiency; exclusions; no feasible exchange | Passed |
| Time rules | Chicago gap/repeated hour; October vs November offset; Kolkata +05:30; Kathmandu +05:45 and 15-minute grid; midnight rollover; missing/invalid zones | Passed |
| Proposal safety | Exact fingerprint/times, stale revision, run-local goal, idempotency conflict, scoped lookup, historical timezone snapshots | Passed |
| LangGraph/API | Three roles using real MCP, clarification, independent rejection, exact approval, quota, bounded malformed-output retry, model-call ceiling, read timeout | Passed with controlled LLM responses |
| Recovery | Reopened SQLite checkpointer; two fresh Python processes; lost save response; lost save response plus failed status lookup and recovery | Passed with controlled LLM responses |
| React | TypeScript check and Vite production build | Passed |
| Browser | Save/export/reload; stale-plan second approval; participant times with Honolulu browser timezone | Passed against real local backend, controlled model |
| Visual QA | Desktop 1280px and mobile 390px full-page screenshots | Inspected; no horizontal clipping |
| Gemini metadata | Authenticated exact `models/gemini-3.8-flash` metadata | Accessible; generateContent supported |
| Gemini generation | LangChain structured output and plain generation | **Blocked: HTTP 503 UNAVAILABLE, high demand** |
| Live Gemini ↔ MCP and three-role workflow | `preflight.py --core`, `smoke_core.py --live-model` | **Not verified while generation is unavailable** |
| Account free tier / quota | Google publishes free-tier availability; generation API does not expose account tier/remaining quota | Account-level verification remains open |
| Mem0 / Pinecone | No integration enabled or live success claimed | Deferred until live core passes |

Normal controlled-model search uses **7 model calls**: interpreter 2, coordinator 3, reviewer 2. This measures orchestration, not Gemini latency. The normal browser tests complete in seconds with controlled responses. No real-provider under-two-minute performance claim is made.

The implementation uses at most 16 model invocations per run (including retries), two automatic revisions, and 90 seconds of active execution excluding human waiting. Quota errors receive one bounded retry; provider errors remain visible without model substitution. Saved status is always `awaiting_participant_confirmation`.

No live integration success is inferred from dependency installation, documentation, mock behavior, or a provider badge. API credentials and raw provider exceptions are absent from tracked files and application activity records.

Latest full local check: **43 backend tests passed**, focused Ruff checks passed, TypeScript/Vite production build passed, and **4 Playwright cases passed in 5.7 seconds**, including a visible quota-error state with no fabricated proposal. The fresh-process test is separate from in-process service reopen coverage. Screenshot artifacts remain in ignored `frontend/test-results/`.
