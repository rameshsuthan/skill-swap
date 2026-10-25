# SkillSwap validation

Checked October 25, 2026 (America/Chicago). **Update: user-authorized `gemini-3.5-flash-lite` now passes live core verification.** The 3.8 model failures below are historical. This report distinguishes deterministic tests, controlled LLM responses, real local transport, and live provider calls.

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
| Gemini generation | LangChain structured output and plain generation | **Blocked: HTTP 503 UNAVAILABLE (high demand); full workflow smoke returned HTTP 504 DEADLINE_EXCEEDED** |
| Live Gemini ↔ MCP and three-role workflow | `preflight.py --core`, `smoke_core.py --live-model` | **Passed with user-authorized `gemini-3.5-flash-lite`; see update below** |
| Account free tier / quota | Google publishes free-tier availability; generation API does not expose account tier/remaining quota | Account-level verification remains open |
| Mem0 / Pinecone | No integration enabled or live success claimed | Deferred until live core passes |

Normal controlled-model search uses **7 model calls**: interpreter 2, coordinator 3, reviewer 2. This measures orchestration, not Gemini latency. The normal browser tests complete in seconds with controlled responses. A later real-provider run with `gemini-3.5-flash-lite` measured 6.8 active seconds to approval; that is one observed run, not a latency guarantee.

The implementation uses at most 16 model invocations per run (including retries), two automatic revisions, and 90 seconds of active execution excluding human waiting. Quota errors receive one bounded retry; provider errors remain visible without model substitution. Saved status is always `awaiting_participant_confirmation`.

No live integration success is inferred from dependency installation, documentation, mock behavior, or a provider badge. API credentials and raw provider exceptions are absent from tracked files and application activity records.

Latest full local check: **45 backend tests passed**, focused Ruff checks passed, TypeScript/Vite production build passed, and **6 Playwright cases passed in 7.0 seconds**, including a visible quota-error state with no fabricated proposal. The fresh-process test is separate from in-process service reopen coverage. Screenshot artifacts remain in ignored `frontend/test-results/`.

Final independent review found three local issues, each reproduced before its fix: recovery after budget expiration, ending offsets across a repeated DST hour, and a ready banner after reviewer failure. Regression tests now cover all three. Approved-save recovery has a separate **30-second host-only window**; it cannot extend the 90-second model-investigation budget. A Chicago `01:45−05:00 → 01:15−06:00` session shows both endpoint offsets and a clock-change label. Failed review leaves a visibly unreviewed candidate with approval disabled.

Earlier live full-workflow attempt with `gemini-3.8-flash`: `smoke_core.py --live-model`, run `17dca705-5838-4397-8c59-76fe17a8cf31`, one model call, 24.07 active seconds, Google HTTP 504 `DEADLINE_EXCEEDED`. No plan or proposal was produced. This joins earlier HTTP 503 generation failures. Error classification now identifies both as provider unavailability.

## Authorized model change and successful live verification

User requested `gemini-3.5-flash-lite` on October 25. Updated the active local setting, default/example configuration, model allowlist, diagnostic script, and UI provider label. The UI now reads the actual model ID from the backend. There is no automatic fallback. Flash Lite uses fixed sampling defaults, so no temperature override is sent.

- Preflight: structured response passed; Gemini requested `get_learning_context`, the application invoked actual MCP, and Gemini consumed the returned cohort context.
- Live workflow run: `a980c29b-c418-4424-98d0-51af0b5c63b5`. All three roles completed; **7 model calls, 6.8 active seconds** to `awaiting_approval`.
- Explicit smoke-script approval saved proposal `a6bd50fd-e899-4171-bc1d-9eac07864408` with status `awaiting_participant_confirmation`. No booking or messages.
- A fresh service restored the identical saved result from SQLite: restart recovery passed.
- Regression checks: **47 backend tests passed**, Ruff passed, TypeScript/Vite build passed. The earlier six browser cases remain the baseline; this change only replaces their model badge source.
- Account billing tier and remaining quota are not exposed by the generation API and remain unverified. Mem0/Pinecone have not been enabled or claimed verified.
