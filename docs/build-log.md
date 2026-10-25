# Build log

October 25, 2026. Started from the approved October 24 planning package and two untouched handouts.

1. **Configuration:** no existing Git repository, Node unavailable on PATH, Python 3.14 present. Initialized `build/skillswap`, created secret/runtime exclusions before the first commit, preserved the planning baseline. Installed Python 3.12.15 and checksum-verified Node 22.23.4 locally. Accepted existing `GEMINI_API_KEY` naming as an alias without rewriting secrets.
2. **First real boundary:** wrote MCP tests before implementation. Built a real FastMCP stdio server and application client, discovered all six schemas and read 15 fictional profiles. Verified scope override rejection and sanitized event replay.
3. **Provider blocker:** authenticated model metadata works. Both plain and structured generation return HTTP 503 with Google's high-demand message. No alternate model or billing change. Continued independent local implementation and deferred bonuses.
4. **Domain:** wrote timezone, matching, persistence tests first. Implemented round-trip local-time validation, pairwise cycle scheduling with no participant conflicts, source provenance, canonical fingerprints, revision checks, and transactional idempotency. Verified actual MCP writes and reads.
5. **Orchestration:** three role-specific prompts/tools in LangGraph, SQLite interruptions, exact approval, revisions/exclusions, host-only writes, replayable activity, FastAPI. Fixed synchronous SQLite writes that blocked async checkpoint commits by moving runtime writes to worker threads. Controlled-model integration tests cover real MCP and graph behavior.
6. **Workspace:** React/TypeScript, coherent green/cream design, stable circle/direct diagrams, both participant-local times, export and status labels. Browser tests were first observed failing on the absent UI, then passed after implementation. Inspected desktop and mobile screenshots; increased secondary-text contrast and sizing.
7. **Hardening:** bounded invalid structured-output retry; explicit recovery when both save response and status lookup fail; real fresh-process approval recovery; guaranteed SQLite connection close; source formatting and focused lint rules. Added local startup/test scripts and documentation.

## Decisions carried from the execution ledger

- Work in the newly initialized project on `build/skillswap`: there was no prior code branch to isolate. This preserves the requested project directory; unrelated future edits would share the checkout.
- Treat the existing design plus explicit build instruction as authorization to execute; do not repeat design approval.
- Support `GEMINI_API_KEY` alongside canonical `GOOGLE_API_KEY`; no credential migration needed.
- A no-match scenario means no **feasible schedule**, not necessarily no skill-only cycle. The full candidate graph is still searched.
- Keep optional providers disabled until a real live core run passes. The consequence is a smaller honest demo while Gemini generation is unavailable.
- Local implementation tests may use the explicit `backend/tests` model fixture. Production startup has no test/fallback model switch. Live verification remains a separate unmet gate.

Git commits are local and focused by milestone. The first runtime commit also captured the next milestone's repository/MCP method edits while verification ran; the immediately following domain commit supplies their pure modules and tests. The current tree is tested as a whole. No history was rewritten to hide that sequencing defect.
8. **Independent review:** a fresh reviewer inspected the whole implementation and reproduced three Important issues. Fixed recovery that had incorrectly reused an exhausted active budget; exposed both endpoint offsets across a DST clock change; and removed readiness claims for an unreviewed candidate after model failure. All three have RED→GREEN regression coverage. No minor findings were deferred.

Final rulings: a separately bounded 30-second host-only recovery action is necessary to retrieve a write that may already exist after the 90-second investigation limit. It never authorizes a different plan or additional model time; its cost is up to 30 additional seconds when the operator explicitly retries or an approved commit is resumed after restart. Live model quality/latency and account-level free-tier entitlement remain unverified because generation failed and the generation API exposes neither account billing settings nor remaining quota. These are explicit acceptance gaps, not claimed successes.

9. **User-authorized model change:** switched active/default configuration to `gemini-3.5-flash-lite` after the user's explicit request. Structured output and the actual Gemini/MCP round trip passed. The full live three-specialist workflow reached approval in 6.8 seconds using seven calls, saved proposal `a6bd50fd-e899-4171-bc1d-9eac07864408`, and recovered it after restart. This resolves the earlier live-core provider blocker for the newly selected model. Billing-tier entitlement remains outside generation API evidence. No automatic fallback or vendor bonus was introduced.

## Mem0 milestone — October 25

Connected to hosted Mem0 via the application MCP client, discovered the vendor tools, and verified scoped add/read/edit/delete with fictional data. The live API rejected a nested metadata filter, so reads inject a unique project/cohort/member user ID and strictly verify returned metadata. Host-only get/list operations support ownership validation and UI; no admin/bulk tools reach the application or agents.

Added explicit preference controls, durable pending operations, scoped reconciliation after lost responses, and honest acknowledgement of unresolved outcomes. The interpreter fixes the hard goal before reading memory; the coordinator gets preferences only for feasible-option ranking. Added an opt-in alternatives scenario so the original three-cycle demo remains unchanged.

Independent review found three Important issues: memory could reach goal interpretation, missing event IDs could strand the UI, and failed discovery could permanently suppress retrieval. Each was reproduced and fixed with regression coverage. No Critical or deferred Minor findings. Production auth remains outside this local single-operator prototype; live service claims are verified separately from controlled tests.

## Search selection correction

Investigated the user's generic search failure through sanitized activity and durable checkpoint task errors. Provider calls were successful; the model selected null despite a feasible result. Constrained the coordinator's structured selection to the tool's returned fingerprints and reused the single bounded correction attempt. Added a specific error for persistent invalid selections. Verified the same live request through the restarted app, stopping at human approval, and added three regression cases. No model change, fallback selection, or automatic save.
