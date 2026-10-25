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
- Account billing tier and remaining quota are not exposed by the generation API and remain unverified. At that milestone Mem0/Pinecone were not enabled; the subsequent Mem0 checks are recorded below.

## Mem0 preference milestone

Hosted Mem0 MCP authentication/discovery and actual application CRUD passed. The client uses bearer credentials only in transport headers; no credentials enter activity or validation output. Live add returned memory `93331386-f78d-4fc0-b2e5-4b6fd704d998`, event `1409f744-8b5a-454e-bb2e-e7b41a4fc7fe`; a new service retrieved it, another learner could not, update was reflected, and delete/absence confirmation passed. Only isolated fictional test memories were changed and cleaned up. Safe result IDs are retained in ignored local validation logs.

- **60 backend tests passed** after the integration and independent-review fixes. Coverage includes host scope, foreign records/IDs, pending/failed writes, no stale content cache, lost-response reconciliation without replay, explicit acknowledgement of unknown outcomes, discovery recovery, and untrusted-memory isolation from goal/proficiency.
- Controlled-model tests traverse real custom MCP and fresh LangGraph sessions: a preference changes a feasible Olivia swap to the Nina three-cycle; exclusions or absent availability still select the feasible alternative. Mem0 outage continues without memory.
- **9 Playwright cases passed**, including explicit remember/edit/forget, reload, member isolation, pending/degraded behavior, and acknowledged unknown writes. Browser model and vendor responses are controlled and labeled test; local graph/MCP/API/storage are real.
- Ruff and TypeScript/Vite production build passed. Desktop/mobile preference panels were visually inspected; no horizontal clipping.
- The initial live two-session attempt reached approval in 8 calls/12.44s, then encountered Gemini quota limiting on the second run. Its test memory was cleaned up. The live script now spaces sessions by 65 seconds; quota failures remain visible and never trigger model substitution.

Independent review found three Important issues, all addressed with regressions: goal interpretation formerly saw memory, unknown write responses could lock controls, and a discovery outage could silently suppress future memory retrieval. No Critical or deferred Minor findings.

Final live two-session verification passed with `gemini-3.5-flash-lite` and actual hosted Mem0 MCP. Baseline run `7b9583ab-a1aa-4532-a5da-1f259d00ab77` reached approval in **8 calls / 16.06s**, selecting Olivia. After an explicitly remembered guided-project preference and a 65-second between-session pause, fresh run `78606081-1592-489f-9324-b6548060c4d1` reached approval in **8 calls / 15.85s**, selecting Nina. Proposal `285f0647-418f-4e93-a2bb-d563a5ff1ddc` saved and recovered unchanged in a fresh service. Test memory `1f2a1364-ac49-4733-9712-0e91661ae22e` (event `940a0680-18ec-4589-b983-2a703cd52546`) was cleaned up. A diagnostic wrapper inspected fictional reviewer arguments without altering responses; cycle, goal, and sessions matched exactly. An earlier attempt stopped at review without saving; the successful retry used the same guarded workflow.

Final backend suite: **60 passed / 18.48s**. Browser suite: **9 passed / 10.3s**. Async-event coverage also reproduces the live response shape in which top-level `id` identifies the event; completion resolves the separate memory result ID and verifies ownership. Credential scan found **zero configured key values** in 76 tracked/intended source files. Mem0 is enabled in this machine's private configuration. Pinecone remains disabled.

## Invalid proposal selection fix

The reported generic search error was traced to saved checkpoint `e3c48546-c669-4b01-afb9-b9b2d497a972`: the coordinator raised `unsupported_plan_selection` after all provider/tool calls succeeded. Live replay of the same inputs returned a null selection despite one feasible proposal. The coordinator output schema now restricts its choice to the actual returned fingerprints (null only when there are no plans). Invalid output receives one correction within existing model/time budgets; repeated failure becomes a specific `planning_error`, without approval or saving.

Three regression cases failed before the fix and passed afterward: null choice, invented choice, and repeated invalid choice with bounded failure. Full backend suite: **63 passed / 20.43s**; Ruff and frontend production build passed. An isolated browser check verified the specific error message and absent approval. After restarting the local backend, the same user search reached **awaiting_approval** in live run `2899cd04-7464-4cbf-beac-f04b198a97ea`: **8 calls / 10.67s**, independent reviewer passed, nothing saved. Existing failed runs remain as history; start a new search to use the fix.
