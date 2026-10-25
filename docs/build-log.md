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
