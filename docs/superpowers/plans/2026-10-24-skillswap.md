# SkillSwap Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a polished global community-learning demo that uses specialist agents and actual MCP tools to find, validate, and save reciprocal learning proposals across members' timezones, with Mem0 and Pinecone MCP as separately verified bonuses.

**Architecture:** React calls FastAPI, which hosts three scoped Gemini agent roles in LangGraph and real MCP client connections. A custom stdio server owns timezone normalization, deterministic matching/scheduling, and SQLite proposal operations. Durable graph checkpoints preserve clarification and approval; optional vendor MCP connections add personal memory and semantic discovery. Participant-local times are derived deterministically from UTC and explicit IANA zones.

**Tech Stack:** Python 3.12; FastAPI; Pydantic; LangGraph; `langchain-google-genai` with `gemini-3.8-flash` through the Gemini Developer API; FastMCP server/client; SQLite; Node 22+; React, TypeScript, Vite, and CSS; pytest and Playwright for meaningful integration checks. Resolve and pin compatible package versions in Task 1.

**Spec:** [SkillSwap design](../specs/2026-10-24-skillswap-design.md). Read it with this plan. See also [architecture and component diagrams](../../skillswap/architecture.md).

**Status:** Proposed plan for review. No implementation steps have been executed. User authorization in this turn covers planning and diagrams.

## Global Constraints

- One learning cohort, 15 fictional profiles, one operator selecting a demo learner.
- Each teaching edge is its own 30-minute session. A two-person swap has two sessions; a three-person exchange has three.
- Remote sessions worldwide; optional self-declared city/country and a required IANA timezone per member. Geography provides context; actual availability determines scheduling.
- Dated local windows normalize to UTC; session starts use a 15-minute UTC grid. Every approval shows both participants' local dates, times, zones, and offsets.
- Reject nonexistent local times and require explicit disambiguation of repeated local times. Timezone/profile changes invalidate staged approval; stored local views preserve historical proposals.
- Approval saves a proposal. It does not book time, contact participants, or mean that other people have agreed.
- Saved proposal status is `awaiting_participant_confirmation`.
- Bound automatic revisions to two per run and total model calls to sixteen, including tool-loop continuations and retries; target six to eight calls on the normal path.
- Limit active execution to 90 seconds, excluding time waiting for the human.
- Use one Gemini model call at a time to reduce free-tier quota pressure.
- Never substitute a different or paid model automatically.
- The agents must actually discover and invoke the custom server's MCP tools; they do not bypass it by importing domain functions.
- Run one backend worker; enable SQLite WAL mode and a bounded busy timeout.
- Mem0 hosted memory and Pinecone community-profile search are separate integrations.

## Review Focus

1. A timed-out write may already have succeeded: status lookup and stable idempotency must preserve exactly one proposal. Covered in Tasks 2 and 3.
2. A new availability revision between preview and save must invalidate the old approval, without silently changing session times. Covered in Tasks 2, 3, and 4.
3. UTC overlap and local clock interpretation can diverge at midnight or DST transitions: require correctly normalized dated windows, explicit ambiguous-time handling, and no participant overlap. Covered in Tasks 2 and 4.
4. A tool result may contain stale or other-member information: scoped hydration and memory filtering must prevent it influencing the wrong run. Covered in Tasks 6 and 7.
5. A model may return an unsupported skill, malformed output, or quota error: preserve truthful UI state and ask/stop instead of inventing a result or silently changing providers. Covered in Tasks 1 and 3.

## Delivery order and time budget

| Task | Target | Cumulative | Deliverable |
| --- | --- | --- | --- |
| 1. Runtime and real MCP vertical slice | 55 min | 55 min | Discovered custom tools and real context read |
| 2. Global scheduling, exchanges, and safe persistence | 60 min | 115 min | Local/UTC validation, valid exchanges, and idempotent save |
| 3. Three agents, API, and durable approval | 50 min | 165 min | Complete backend workflow with Gemini |
| 4. Polished global workspace | 75 min | 240 min | Participant-local session cards and proposal export |
| 5. Core acceptance and submission package | 30 min | 270 min | Verified 4½-hour baseline |
| 6. Mem0 MCP bonus | 35 min | 305 min | Verified cross-session memory |
| 7. Pinecone MCP bonus | 35 min | 340 min | Verified semantic profile search |
| 8. Integrated demo and final polish | 20 min | 360 min | Six-hour showcase, if bonuses pass |

These are target allocations, not guarantees. Missing runtimes, API access, incompatible packages, or quota restrictions can consume the reserve. If core tasks overrun, omit bonus tasks before reducing core verification. Timebox each optional server's authentication/discovery to 15 minutes; if it cannot pass, mark it disabled/deferred and preserve the remaining demo time.

Global scheduling adds approximately 30 minutes to the previous core allocation. Keep it in the core; use remaining time for the vendor bonuses. No map, geocoding service, new agent, recurring-calendar system, or production availability editor is included.

## Files and interfaces

Paths below are relative to the project root beside the supplied handouts. Existing handouts and planning documents are preserved. Do not initialize unrelated repositories or change machine-wide MCP configuration.

```text
backend/
  pyproject.toml
  requirements.lock
  src/skillswap/
    __init__.py
    settings.py             # validated environment and paths
    models.py               # shared contracts from design section 5
    repository.py           # domain SQLite transactions and revision
    matching.py             # pure eligibility, cycle and scheduling functions
    scheduling.py           # IANA local-time normalization and local session views
    mcp_server.py           # six domain tools; stdio entry point
    mcp_router.py           # actual clients, scopes, allowlists, timeouts
    model_factory.py        # Gemini Developer API, model ID, call budget
    agents.py               # prompts, tool subsets, structured outputs
    workflow.py             # graph state, interrupts, bounded revision, commit
    events.py               # persistent, sanitized activity records
    api.py                  # HTTP endpoints and application lifecycle
    vendor_memory.py        # optional scoped Mem0 operations
    vendor_search.py        # optional Pinecone result hydration
  tests/
    conftest.py
    test_mcp_roundtrip.py
    test_matching.py
    test_timezones.py
    test_proposals.py
    test_workflow.py
    test_api.py
    test_memory_scope.py
    test_semantic_search.py
frontend/
  package.json
  package-lock.json
  src/
    main.tsx
    App.tsx
    api.ts
    types.ts
    time.ts                 # explicit-zone display helpers; no eligibility logic
    styles.css
    components/
      LearnerPanel.tsx
      ExchangeGraph.tsx
      ProposalPanel.tsx
      ActivityDrawer.tsx
      MemoryPanel.tsx
  tests/skillswap.spec.ts
data/demo_cohort.json
scripts/preflight.py
scripts/seed_demo.py
scripts/demo_scenario.py
scripts/smoke_core.py
scripts/smoke_mem0.py
scripts/seed_pinecone.py
scripts/smoke_pinecone.py
docs/demo-script.md
docs/project-summary.md
docs/build-log.md
docs/validation-results.md
.env.example
.gitignore
README.md
```

`storage/` is generated runtime state and excluded from version control. No secrets, actual memory contents, or user data go into lockfiles or logs. If a repository is created when implementation begins, commit coherent completed tasks; do not initialize Git as part of this planning-only deliverable.

## Task 1: Runtime, Gemini preflight, and actual MCP context read

**Files:** Create backend package/config, `settings.py`, `models.py`, `repository.py`, `mcp_server.py`, `mcp_router.py`, `model_factory.py`, `events.py`, `tests/conftest.py`, `tests/test_mcp_roundtrip.py`, `data/demo_cohort.json`, `scripts/preflight.py`, `scripts/seed_demo.py`, `.env.example`, `.gitignore`.

**Interfaces:**

- `Settings`: `google_api_key`, `gemini_model="gemini-3.8-flash"`, domain/checkpoint DB paths, optional Mem0/Pinecone settings, allowed cohort ID, `demo_mode=True`.
- `make_model(settings: Settings) -> BaseChatModel`: explicitly use Gemini Developer API, with no alternate-model fallback.
- `Repository(db_path: Path)`; `seed_demo(profiles: list[MemberProfile]) -> int`; `get_context(ctx: ActorContext) -> dict`.
- `MCPRouter(settings: Settings)`; async `open()`, `close()`, `call(server: str, tool: str, arguments: dict, ctx: ActorContext) -> dict`; model-visible wrappers do not expose scope fields.
- `create_mcp_server(repository: Repository) -> FastMCP`; module entry point runs stdio with logs on stderr.
- `EventStore(checkpoint_db_path: Path)`; `append(run_id: str, event: ActivityEvent) -> int`; `list_after(run_id: str, sequence: int) -> list[ActivityEvent]`.

- [ ] **Check prerequisites.** Confirm Python 3.12 and Node 22+ are executable, create the project-local Python environment, and resolve dependencies including portable `tzdata`. Record exact resolved versions and the timezone data source/version. Verify `zoneinfo` resolves all fixture timezone IDs. Create `.env.example` with variable names and empty secret values. Do not print credentials.
- [ ] **Check Gemini access.** With `GOOGLE_API_KEY` configured, run a tiny structured-response call and a real tool-call round trip using the confirmed model. Use `langchain-google-genai`; verify the account's free-tier quota. Fail visibly on unavailable model/access or quota; do not switch automatically.
- [ ] **Write failing MCP tests.** `test_stdio_context_roundtrip` must discover the six named tool schemas and receive exactly 15 fictional profiles through an actual subprocess connection. `test_scope_override_rejected` must prove model arguments cannot override host cohort/member scope. `test_no_secret_in_events` checks sanitized results.
- [ ] **Run the tests before implementation.** `cd backend && python -m pytest tests/test_mcp_roundtrip.py -q` must initially fail because the implementation is absent.
- [ ] **Implement the transport and context slice.** Keep FastMCP clients open through application lifespan using async context management. Discover tools with `list_tools`, call via `call_tool`, and normalize structured results in one router. Non-context tools may be implemented in Task 2; never return fake successful results.
- [ ] **Create fixtures.** Define Maya/Chicago, Leo/London, Nina/Bengaluru and twelve others across the global locations in design section 11. Store optional city/country and required IANA timezone, canonical skills, proficiency, styles, dated local windows, and matching UTC expectations. Task 2 implements normalization; do not guess offsets or silently substitute the operator's zone. Include a direct swap, no-cycle case, invalid semantic candidate, and memory-sensitive alternatives.
- [ ] **Verify.** Rerun MCP tests and `python scripts/preflight.py --core`; expected: real discovery/context plus structured/model-tool smoke pass, provider modes accurately reported. Pin the compatible package set. If prerequisites fail, record the blocker before UI work.
- [ ] **Commit the completed slice when working in Git.** Suggested message: `feat: establish SkillSwap MCP and Gemini runtime`.

## Task 2: Global scheduling, correct exchange search, and proposal persistence

**Files:** Create `matching.py`, `scheduling.py`, `tests/test_matching.py`, `tests/test_timezones.py`, `tests/test_proposals.py`, `scripts/demo_scenario.py`; extend `models.py`, fixture seeding, `repository.py`, and all six `mcp_server.py` tools.

**Interfaces:**

- `enumerate_cycles(profiles: list[MemberProfile], actor_id: str, goal: LearningGoal, excluded: set[str]) -> list[ExchangeCycle]`.
- `schedule_cycle(cycle: ExchangeCycle, profiles: dict[str, MemberProfile]) -> list[Session] | None`.
- `normalize_window(value: LocalAvailabilityInput) -> AvailabilityWindow`: validate IANA zone, resolve each local endpoint or raise a typed `LocalTimeResolutionError`, preserve provenance, and return aware UTC timestamps.
- `local_session_views(session: Session, participant_timezones: dict[str, str]) -> list[LocalSessionView]`: derive exactly teacher/learner local ISO timestamps with offsets; never accept model-invented local times.
- `validate_plan(plan: ExchangePlan, profiles: dict[str, MemberProfile], revision: int) -> ValidationResult` validates the supplied times exactly.
- `fingerprint_plan(plan: ExchangePlan) -> str` uses the design's canonical fields.
- `Repository.save_proposal(ctx, plan, approval_fingerprint: str, idempotency_key: str) -> Proposal` and `get_proposal_status(ctx, *, idempotency_key: str | None, proposal_id: str | None) -> Proposal | None`.

- [ ] **Write failing tests for the matching contract.** `test_direct_swap_has_two_sessions`: two edges, 30 minutes each. `test_three_cycle_needs_no_group_slot`: Maya/Leo/Nina yields the three specified sessions. `test_member_sessions_do_not_overlap`: pairwise-valid but mutually conflicting slots are rejected or reassigned. `test_proficiency_and_reciprocity_required`: similar descriptions cannot bypass canonical skills or level checks. `test_no_exchange_is_explicit`: no fabricated cycle.
- [ ] **Write deterministic timezone tests.** Cover the three local/UTC examples in design section 11, date rollover, UTC+05:30 and UTC+05:45 offsets, and invalid/missing zones. Assert Chicago `2026-03-08 02:30` is nonexistent; `2026-11-01 01:30` requires an explicit fold and maps to 06:30Z or 07:30Z. Assert 14:00Z becomes 09:00 in Chicago on October 26 and 08:00 on November 2. Test a Kathmandu 18:00 start maps to 12:15Z and is considered by the 15-minute UTC grid. Dates across midnight must carry both explicit local dates. A geographically nearby candidate with no actual overlap cannot match; a distant one with overlap can.
- [ ] **Write failing persistence tests.** `test_stale_revision_requires_fresh_approval`; `test_same_key_returns_same_proposal`; `test_same_key_different_plan_rejected`; `test_approved_times_never_silently_change`; `test_run_local_goal_survives_save_validation`; `test_host_exclusions_cannot_be_removed_by_model`; `test_timezone_change_invalidates_staged_plan`; `test_saved_local_views_survive_profile_timezone_change`. Assert proposal count stays one on retries and status is exactly `awaiting_participant_confirmation`.
- [ ] **Run red tests.** `cd backend && python -m pytest tests/test_matching.py tests/test_timezones.py tests/test_proposals.py -q`.
- [ ] **Implement timezone normalization.** Use `zoneinfo`; UTC round-trip both fold candidates, deduplicate instants, reject gaps, and require an explicit choice for repeated times. Validate 15-minute local input boundaries and positive UTC duration. Normalize fixture windows and preserve their source local values. Never use a fixed offset, city lookup, or LLM conversion as the scheduling authority.
- [ ] **Implement deterministic search and scheduling.** Enumerate two/three cycles anchored at the learner; search all authorized profiles. Backtrack 30-minute sessions on a 15-minute UTC start grid with no participant overlap. Derive both local views and snapshot participant zones. Return up to five feasible results after ordering, plus diagnostic reasons such as `no_shared_availability`. Use preference/Pinecone ordering only after eligibility; never add a geographic distance cutoff.
- [ ] **Implement transactions and demo revision.** Save proposal plus unique idempotency row atomically, enforce fingerprint/revision including the exact participant timezone/local ISO views, and return existing identical writes. The scenario command removes Nina's October 27 14:00Z window while retaining October 28 14:00Z and increments revision. A timezone-change scenario requires revalidated future availability and increments revision, leaving saved proposal snapshots intact. Seed reset also increments revision and touches only the local fictional dataset.
- [ ] **Verify green tests and actual MCP writes.** Run the unit suite plus a subprocess MCP test that validates, saves, reads status, and retries with the same key. Assert identical proposal IDs and unchanged approved times.
- [ ] **Commit.** Suggested message: `feat: validate reciprocal exchanges and persist proposals safely`.

## Task 3: Specialist agents, durable approval, and API

**Files:** Create `agents.py`, `workflow.py`, `api.py`, `tests/test_workflow.py`, `tests/test_api.py`; extend router/events/model factory; create `scripts/smoke_core.py`.

**Interfaces:**

- `build_agents(model: BaseChatModel, router: MCPRouter) -> AgentRoles`: interpreter, coordinator, reviewer with the design's distinct tool responsibilities.
- `build_workflow(agents: AgentRoles, router: MCPRouter, checkpointer, events: EventStore) -> CompiledStateGraph`.
- `RunState`: actor, request, interpreted goal, evidence, staged plan, fingerprint, exclusions, model-call/revision counters, status, result/error.
- `RunService.start(member_id: str, request: str, exclusions: list[str], parent_run_id: str | None) -> str`; `snapshot(run_id: str) -> RunSnapshot`; async `resume(run_id: str, payload: dict) -> RunSnapshot`.
- `create_app(settings: Settings) -> FastAPI`; expose the exact routes in design section 9.

- [ ] **Write failing workflow tests using controlled model responses.** `test_ambiguous_goal_interrupts`; `test_reviewer_can_request_investigation`; `test_approve_requires_waiting_state_and_fingerprint`; `test_restart_restores_approval`; `test_double_resume_and_unknown_write_outcome_create_one_proposal`; `test_model_budget_and_quota_stop_truthfully`. Assert the LLM tool catalog never includes commit/status-write capabilities. API tests cover context retrieval, replay after an event sequence, invalid resume rejection, and scoped proposal export.
- [ ] **Run red tests.** `cd backend && python -m pytest tests/test_workflow.py tests/test_api.py -q`.
- [ ] **Implement role prompts and validated outputs.** Interpreter returns a supported goal or clarification; coordinator uses evidence-backed MCP candidates; reviewer invokes deterministic validation and may reject the proposal. Share only role-relevant context. A malformed output consumes a bounded retry and then becomes a visible error.
- [ ] **Implement approval and commit nodes.** Checkpoint the immutable staged plan before `interrupt`. Resume with an exact fingerprint; use a host-only node for final validation and MCP save. On stale data, stage a revised plan and interrupt again. On lost save response, query status before retry. Serialize resumes per run.
- [ ] **Implement lifecycle/API/activity.** Open clients and the SQLite checkpointer at startup; close on shutdown. Persist event sequence numbers. Pollable snapshots/events must survive restart; initial `/api/context` goes through MCP. Export uses scoped `get_proposal_status(proposal_id=...)`. Keep all APIs local/single-operator for this prototype.
- [ ] **Verify.** Run workflow/API tests. Run `python scripts/smoke_core.py --live-model`; the script exercises all three real Gemini roles and the real custom MCP server, pauses before approval, then explicitly approves the fictional proposal. Record IDs/calls/durations and inspect the saved status. Restart and retrieve it. Automated model fixtures do not replace this live check.
- [ ] **Commit.** Suggested message: `feat: orchestrate SkillSwap agents with durable human approval`.

## Task 4: Polished, honest browser workspace

**Files:** Create frontend package, Vite config, `main.tsx`, `App.tsx`, `api.ts`, `types.ts`, `time.ts`, `styles.css`, `LearnerPanel.tsx`, `ExchangeGraph.tsx`, `ProposalPanel.tsx`, `ActivityDrawer.tsx`, and `tests/skillswap.spec.ts`.

**Interfaces:** `api.ts` exports typed `getContext`, `startRun`, `getRun`, `getEvents`, `resumeRun`, `getProviders`, and `downloadProposal` for Task 3 routes. Components consume `RunSnapshot`, `ExchangePlan`, `ActivityEvent`, and provider modes without recomputing eligibility.

- [ ] **Write behavior-focused browser tests.** `propose_review_save_reload` asserts teaching arrows/session labels, exact approval, saved unconfirmed status, download, and reload persistence. `stale_plan_requires_second_approval` changes availability through the demo scenario command, attempts old approval, and requires a changed time plus a new approval action. `participant_times_ignore_browser_zone` uses a browser timezone different from the selected member, asserts both participant-local dates/offsets, and includes a next-day boundary example. Use the real local backend with a controlled model only for repeatable automation.
- [ ] **Implement the workspace.** One page with clear learner/request entry, centered graph, and proposal/evidence panel. Use a cohesive light theme, restrained accent color, readable spacing, and accessible contrast. A small SVG triangle/direct-pair layout is sufficient; use stable node positions and labeled arrows.
- [ ] **Implement the global schedule display.** Profile/graph labels include self-declared city/country when present and the required zone. Viewer-local times default to the selected member. Session cards present both participants' local date, interval, IANA zone, actual offset, and date-boundary indicators using the server-derived values. Keep graph labels compact. Format any additional viewer-local labels with an explicit timezone, never browser defaults. Download includes UTC and approved local views. No map or location API is needed.
- [ ] **Implement product states.** Clarification, loading, no feasible exchange, quota limited, provider degraded, stale approval, save error, and saved proposal must all be visible. Provide keyboard-accessible session cards as a graph alternative. Keep approval disabled for stale/invalid plans.
- [ ] **Implement genuine activity.** Poll once per second while active; append by event sequence and avoid duplicate rows. Provider badges reflect backend health. Show concise evidence and tool status rather than generated thinking or simulated work.
- [ ] **Verify.** `cd frontend && npm run build`; then `npx playwright test tests/skillswap.spec.ts`. Inspect desktop and narrow-width screenshots for clipping, text legibility, focus order, and disabled states. Run one manual browser path with live Gemini and MCP.
- [ ] **Commit.** Suggested message: `feat: add SkillSwap exchange workspace and review flow`.

## Task 5: Core acceptance and submission baseline

**Files:** Create/update root `README.md`, `docs/demo-script.md`, `docs/project-summary.md`, `docs/build-log.md`, and `docs/validation-results.md`.

**Interfaces:** Uses completed backend/frontend and the design's evaluation matrix; no new product feature.

- [ ] **Run required checks.** `cd backend && python -m pytest -q`; `cd frontend && npm run build`; run the three browser cases. Record actual outputs and distinguish mocks, local integration, and live-provider checks. Confirm timezone fixtures against the installed timezone database.
- [ ] **Exercise failure and restart.** Run the availability-change scenario, a read timeout, a post-save response timeout, and a process restart while waiting for approval. Confirm no duplicate proposal and no unapproved schedule substitution.
- [ ] **Write the submission story.** Prepare `docs/project-summary.md` as the source for the handout's required Google Doc: problem, fictional dataset, prompts used during development, iterations, lessons, architecture, and limitations. Give exact startup commands, environment variable names, and demo steps. Preserve the user's sample handouts. Final submission needs the Google Doc, a video of five minutes or less, and a GitHub code link; actual publishing is a later action.
- [ ] **Rehearse the core recording.** Demonstrate a Chicago–London–Bengaluru exchange with each participant's local times, stale-plan recovery, approval, reload, and export in under five minutes. Measure runtime and model/tool call counts.
- [ ] **Create the 4½-hour checkpoint.** If all core acceptance and global-cohort checks pass, the project is a complete local demonstration. Mark vendor bonuses as disabled if they have not been verified. Commit a coherent baseline before optional integration work.

## Task 6: Mem0 MCP memory bonus

**Files:** Create `vendor_memory.py`, `tests/test_memory_scope.py`, `scripts/smoke_mem0.py`, `frontend/src/components/MemoryPanel.tsx`; extend router/API/workflow/settings and frontend API types.

**Interfaces:** `MemoryService.search(ctx: ActorContext, query: str) -> list[MemoryFact]`; `remember(ctx, text: str) -> MemoryWriteResult`; `update(ctx, memory_id: str, text: str)`; `forget(ctx, memory_id: str)`; `poll_write(ctx, event_id: str)`. Define `MemoryFact` and `MemoryWriteResult(status: pending|saved|failed, memory_id?, event_id?)` in shared models/types.

- [ ] **Timebox a live connection check.** With `MEM0_API_KEY` configured, discover the documented hosted server tools and verify scoped search. If account/authentication cannot work in 15 minutes, defer this task and leave the provider visibly disabled.
- [ ] **Write failing tests.** `test_memory_scope_is_host_injected`; `test_other_member_memory_is_excluded`; `test_async_add_is_pending_until_confirmed`; `test_failed_write_is_not_reported_saved`; `test_edit_forget_invalidates_cache`. Only explicit UI actions may invoke writes.
- [ ] **Implement scoped integration and UI.** Add only the permitted memory tools. Enforce the selected fictional learner and project namespace outside model arguments. Add a small memory panel with Remember/Edit/Forget, pending state, and an accurate provider badge. Memory influences soft preference ranking, never hard eligibility.
- [ ] **Verify unit and live behavior.** `cd backend && python -m pytest tests/test_memory_scope.py -q`; run `python scripts/smoke_mem0.py` to save a fictional preference, confirm completion, retrieve it in a new run without the old transcript, then update/forget only that test memory. Verify another member cannot see it. Record actual provider result IDs in the local validation log without secrets.
- [ ] **Commit.** Suggested message: `feat: personalize SkillSwap through scoped Mem0 MCP memory`.

## Task 7: Pinecone MCP semantic-discovery bonus

**Files:** Create `vendor_search.py`, `tests/test_semantic_search.py`, `scripts/seed_pinecone.py`, `scripts/smoke_pinecone.py`; extend router/settings/coordinator/provider status.

**Interfaces:** `SemanticSearch.search(ctx: ActorContext, goal_text: str) -> list[CandidateHit]`; `CandidateHit(profile_id: str, advisory_score: float, evidence: str)`. Resolve authoritative profile facts through the custom MCP server after vendor retrieval.

- [ ] **Timebox live discovery.** Start the official `@pinecone-database/mcp` stdio server with `PINECONE_API_KEY`. Confirm `search-records` and an integrated-embedding index/namespace configured for this project. Seed only fictional public offers. Check account/service costs before enabling billable setup; no automatic billing changes.
- [ ] **Write failing tests.** `test_semantic_hit_cannot_bypass_proficiency`; `test_stale_or_other_cohort_ids_dropped`; `test_top_k_does_not_hide_valid_cycle`; `test_outage_uses_labeled_local_search`; `test_runtime_tool_allowlist_excludes_admin`.
- [ ] **Implement retrieval and hydration.** Host injects index, namespace, cohort/active filters. Use semantic ordering as advisory input; the custom server still searches the complete cohort for feasible cycles. Register no index administration/upsert tools with agents. The seed script is an explicit setup utility.
- [ ] **Verify.** Run semantic-search tests and `python scripts/smoke_pinecone.py`. Use a paraphrased request to retrieve a relevant real indexed offer. Confirm actual MCP search events, authoritative hydration, filtering, and explicit degradation when the vendor is unavailable. No SDK-only call may be presented as a Pinecone MCP demonstration.
- [ ] **Commit.** Suggested message: `feat: discover SkillSwap candidates through Pinecone MCP`.

## Task 8: Complete the integrated showcase

**Files:** Update demo/validation/submission docs; product changes only for issues discovered by verification.

- [ ] **Repeat checks affected by the bonuses.** Run the full backend suite, frontend build, and browser flows including memory/provider states. Run live core, Mem0, and Pinecone smoke scripts only for configured providers.
- [ ] **Review the final trace.** Confirm visible evidence of three distinct agent roles, custom MCP discovery/calls, human approval, durable reload, and each enabled vendor MCP. Record disabled bonuses honestly.
- [ ] **Finish visual QA.** Inspect proposal and activity views at desktop and narrow widths, including a degraded-provider state. Fix layout defects; avoid adding features.
- [ ] **Finalize the five-minute recording and project summary.** Show the problem and outcome first, then a brief architecture explanation. Include Gemini model ID, fixture disclosure, measured validation results, and the fact that saved proposals await other participants.
- [ ] **Prepare repository/submission assets.** Commit locally if Git is in use. Public repository creation, pushing, publishing, or form submission are separate external actions requiring the user's request or established authorization.

## Implementation handoff

Recommended execution: one primary implementer owns domain contracts, MCP, and graph integration; a parallel worker can build the UI after Task 3 API/types are stable. Use an independent review of matching and approval behavior before recording. Do not parallelize edits to shared models or tool contracts.

The current turn stops at the requested planning package. Before product implementation, review the proposed defaults and plan. The implementation must preserve the user's confirmed `gemini-3.8-flash` choice, real MCP requirement, and explicit bonus status of Mem0/Pinecone.
