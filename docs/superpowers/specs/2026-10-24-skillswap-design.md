# SkillSwap: product and technical design

Date: October 24, 2026. Status: proposed design for review. This document and the accompanying plan are planning artifacts, not a claim that the application or integrations are working.

## 1. Intent and success

SkillSwap helps members of a learning community find people who can teach what they want to learn, while offering something useful in return. It investigates direct swaps and three-person exchanges, explains why they fit, and produces a proposal for people to review.

**Project one-liner:** SkillSwap replaces a global cohort member's manual search for teaching partners and compatible times with a web agent that uses six MCP tools to investigate reciprocal exchanges, asks for clarification and approval, and targets valid proposals within two minutes with the core workflow and timezone checks passing.

The two-minute target excludes human response time and is a proposed acceptance target, not a measured result. The eight cases in section 10 cover supported proposal creation as well as truthful clarification, no-match, failure, and restart handling; passing does not mean every request must produce a match. The underlying problem is that a useful exchange may involve three people even when nobody can offer a direct reciprocal swap.

### Confirmed requirements

- A distinctive community-learning use case, separate from the handout's six supplied projects.
- Approximately four to six hours of focused implementation.
- A custom MCP server and a client inside the application backend.
- Meaningful multi-agent behavior and a polished UI.
- Explore Mem0 and Pinecone through MCP as bonus integrations.
- A plan plus architecture and component diagrams before implementation.
- Gemini Developer API using `gemini-3.8-flash` on the free tier, confirmed by the user after model-name clarification.
- Account for members' geographical locations and timezones across a global cohort.

### Proposed defaults, open to correction

- One learning cohort, 15 fictional profiles, one operator selecting a demo learner.
- Remote sessions worldwide; optional self-declared city/country and a required IANA timezone per member. Geography provides context; actual availability determines scheduling.
- React/TypeScript browser UI, FastAPI/Python backend, explicit LangGraph workflow.
- Gemini Developer API through `langchain-google-genai`, with `GEMINI_MODEL=gemini-3.8-flash` and validated tool/structured-output smoke tests; no credentials are assumed available.
- SQLite domain storage and a separate SQLite checkpoint database.
- A local presentation first. Public hosting and production authentication are future work.

The project directory beside the two supplied Markdown handouts is not a Git repository. Read-only inspection found Python 3.14.3; Node was not found in the checked shell paths. Implementation starts by establishing a compatible Python 3.12 environment and Node 22+ runtime, rather than assuming the current interpreter works with every dependency.

The user clarified the original “Gemini 3.8 Flash Lite” wording and selected `gemini-3.8-flash`. Use `GOOGLE_API_KEY`, explicitly select the Gemini Developer API rather than the enterprise backend, and confirm account-level free-tier access and quota in preflight. Never substitute a different or paid model automatically. Mem0/Pinecone service usage is separate from Gemini pricing.

## 2. Approaches and recommendation

| Approach | Benefit | Tradeoff | Decision |
| --- | --- | --- | --- |
| Explicit LangGraph workflow with three specialist roles | Predictable approval, state, bounded revision, and visible tool use | More explicit state definitions | Proposed default; builds on the user's sample architecture |
| Deep Agents supervisor with delegated specialists | Built-in planning and context-management features | More open-ended behavior than this small matching task needs | Defer unless the product expands into longer learning workflows |
| One general agent with all tools | Fastest baseline | Weaker demonstration of distinct responsibilities | Useful comparison, not the selected proposal |

The user selected SkillSwap and requested this plan. The detailed architecture below is the assistant's proposal and remains reviewable before product implementation.

## 3. Product scope and completion semantics

### Core

1. Select a fictional member and enter a learning goal.
2. Resolve unclear skill or proficiency requirements through a focused question.
3. Investigate direct two-member swaps and three-member cycles.
4. Show teaching directions, the evidence for each match, and feasible session times.
5. Let the proposer approve, revise, or cancel.
6. Save exactly one proposal for an approved plan; reload it after an application restart.

**Approval saves a proposal. It does not book time, contact participants, or mean that other people have agreed.** Saved proposal status is `awaiting_participant_confirmation`; the UI states that clearly. The app exports a JSON proposal containing participants, teaching sessions, evidence, and status.

Each teaching edge is its own 30-minute session. A two-person swap has two sessions; a three-person exchange has three. A participant cannot be in overlapping sessions within one proposal. All participants do not need a common group meeting time. Separate unconfirmed proposals do not reserve or consume availability.

Global scheduling is part of the core, not a vendor bonus. The proposed first version supports remote exchanges between any countries when skills and declared availability fit. It shows both participants' local dates and times before approval. City/country do not impose a distance cutoff or a same-country preference.

### Bonus milestones

- Mem0 MCP: retrieve and explicitly save the selected learner's teaching/learning preferences across fresh sessions; edit and forget supported memories.
- Pinecone MCP: use semantic profile discovery to inform candidate ordering and explanations.
- Display actual server/tool activity and provider status for these integrations.

### Deferred

Real member onboarding, production authentication, messaging, email, live calendars, payments, global marketplaces, automatic confirmation, attendance tracking, ratings, arbitrary-length cycles, and a recommendation algorithm that claims to verify teaching ability.

Also defer in-person matching, maps, geocoding, distance calculations, weekly recurrence, travel itineraries, and a full availability editor. Seed dated local availability and normalize it with the same reusable validation contract that a future profile form can use.

### Anti-goals

Fake agent activity; fabricated participant skills; treating similarity as eligibility; pretending local fallback is a successful cloud call; silently replacing people or times after approval; spending the build window on integrations while the core path remains incomplete.

## 4. Architecture and ownership

See [architecture and component diagrams](../../skillswap/architecture.md).

The browser calls FastAPI over HTTP. FastAPI runs LangGraph and owns scoped MCP client connections. The custom SkillSwap MCP server runs as a separate local stdio subprocess and owns domain operations. The agents must actually discover and invoke its MCP tools; they do not bypass it by importing domain functions.

Use `fastmcp.Client` for transport and connection lifecycle, with small scoped LangChain tool wrappers around discovered calls. Keep library-specific result parsing in the router. This isolates integration details from matching and graph logic.

The custom server delegates arithmetic, graph search, scheduling, and persistence to ordinary Python modules. Model reasoning interprets requests, chooses investigative steps, and explains supported results.

Within that server, `scheduling.py` resolves dated local availability and constructs local session views using timezone rules; `matching.py` compares UTC instants and finds cycles. Time conversion is deterministic. The existing reviewer checks the results through MCP; no extra agent or server is needed.

| Store/service | Owns | Must not be treated as |
| --- | --- | --- |
| `storage/skillswap.sqlite` | Profiles, city/country, member timezones, canonical skill IDs, local-source and UTC availability, dataset revision, saved proposals, idempotency records | A vector index or graph checkpoint store |
| `storage/checkpoints.sqlite` | Run state, staged plans, interruptions, approvals, run-scoped exclusions, active model-call count | Long-term personal memory |
| Mem0, optional | Explicitly retained personal preferences and feedback | The authority for availability, exclusions, or proposal acceptance |
| Pinecone, optional | Searchable copies of public fictional teaching profiles | The authority for eligibility, reciprocity, or current scheduling |

The domain server is the only runtime writer to the domain database. Checkpoints are owned by the graph host. Seed/scenario utilities are explicit demo-maintenance operations, not model tools.

## 5. Data contracts

All shared backend types are defined in `backend/src/skillswap/models.py`. The frontend mirrors these through `frontend/src/types.ts`.

| Type | Required fields and semantics |
| --- | --- |
| `ActorContext` | `cohort_id`, `member_id`, `run_id`, immutable run exclusions; injected by the host, not chosen by an LLM |
| `SkillId` | One of `python`, `sql`, `presentation_design`, `spanish`, `excel_automation` |
| `TeachingOffer` | `skill_id`, `proficiency` in 1–3, `description`, `styles` from `guided_project`, `discussion`, `exercises` |
| `LearningGoal` | `skill_id`, `minimum_teacher_proficiency` in 1–3; default 2 unless explicitly chosen otherwise |
| `LocalAvailabilityInput` | `start_local`, `end_local` as dated wall times, `timezone` as an IANA ID, optional `start_fold`/`end_fold` for repeated times; dates are explicit, end exclusive |
| `AvailabilityWindow` | `start_utc`, `end_utc` as aware UTC ISO timestamps, plus the validated local input as provenance; end exclusive |
| `MemberProfile` | `id`, `cohort_id`, `display_name`, optional self-declared `city`/`country_code`, required IANA `timezone`, one `offer`, one `learning_goal`, availability windows, active flag, source record ID |
| `ExchangeCycle` | Ordered distinct member IDs, two or three directed teaching edges, matching offer/need evidence IDs |
| `LocalSessionView` | `member_id`, IANA `timezone`, `start_local`/`end_local` as dated ISO timestamps with their actual UTC offsets; derived from the UTC session |
| `Session` | `teacher_id`, `learner_id`, `skill_id`, `start_utc`, `end_utc`, two derived `local_views` for its teacher and learner |
| `ExchangePlan` | `cohort_id`, `member_id`, run-local `goal`, `cycle`, `sessions`, `participant_timezones` snapshot, `dataset_revision`, `fingerprint`, `evidence`, reviewer summary; scope must match the injected actor |
| `ValidationResult` | `valid`, optional `plan`, explicit `issues` with stable reason codes |
| `Proposal` | `id`, actor, plan, `idempotency_key`, `status=awaiting_participant_confirmation`, created timestamp |
| `RunSnapshot` | `run_id`, `status`, interpreted goal, staged plan, clarification/approval payload, result/error, provider modes |
| `ActivityEvent` | Monotonic per-run `sequence`, timestamp, agent, server, tool, status, duration, sanitized result summary |

Proficiency is self-declared teacher capability: 1 basic, 2 working, 3 advanced. It is not the learner's level and is not a verified credential. Learner prerequisites are outside the first version.

The selected member's current goal may differ from their stored learning goal. Use it as a run-local override for the incoming teaching edge; do not silently edit their profile. Other members' goals remain those in the authoritative cohort data.

### Global location and time rules

Use an explicit IANA timezone such as `America/Chicago`, `Europe/London`, or `Asia/Kolkata` for each member. A country can contain multiple timezones; neither city/country text nor a fixed offset is the authority. Browser timezone detection may suggest a value for a future onboarding form, but must not overwrite a member's setting. Missing or invalid zones produce `profile_timezone_required` and identify the profile that needs correction; seed validation fails before matching starts.

For the prototype, define dated local windows for October 26–30, 2026, with endpoints on local 15-minute boundaries. Local wall times are accepted only together with their explicit timezone; fixture validation requires that zone to match the member's current setting. Use Python `zoneinfo` with an available IANA database and declare `tzdata` as a portable dependency. Convert to UTC once when validating the fixture, retain local provenance, and perform comparisons and 30-minute duration arithmetic in UTC. Generate starts on a 15-minute UTC grid so quarter-hour offsets are supported.

Resolve both endpoints by round-tripping candidate timezone-aware values through UTC. A local time with no valid instant is rejected as `nonexistent_local_time`; one with two distinct valid instants requires an explicit fold/offset choice and otherwise returns `ambiguous_local_time`. Never silently move a nonexistent time or choose one occurrence of a repeated hour. Require end UTC after start UTC, even across midnight or a daylight-saving transition. Use date-specific rules for each window, not today's offset. These choices build on [Python's IANA timezone support](https://docs.python.org/3/library/zoneinfo.html) and the [IANA timezone database](https://www.iana.org/time-zones).

Only member-declared availability permits a meeting, including any explicitly available late-night slots. Do not infer availability from country, working-day stereotypes, geographical distance, or a small timezone difference. If compatible people have no overlapping windows, report `no_shared_availability` with their local windows; do not schedule outside them. Recurring schedules are deferred.

The main viewer timezone defaults to the selected member's setting. Every session card also shows teacher-local and learner-local date, start/end time, IANA zone, and the offset for that session; dates and next/previous-day indicators make midnight crossings explicit. The graph keeps compact viewer-local times and exposes full details in cards. Export UTC instants and the approved participant-local views. Save timezone IDs/local ISO values in the plan so a later profile change does not relabel a historical proposal. A timezone change requires explicit revalidation of future local availability, increments the dataset revision, and invalidates staged approval; a display-only viewer preference does not change the plan.

## 6. Agent responsibilities and workflow

| Role | Responsibility | Accessible tools |
| --- | --- | --- |
| Goal interpreter | Map natural language to the supported skill catalog; ask when ambiguous; retrieve relevant learner preferences | `get_learning_context`; scoped Mem0 search when enabled |
| Matching coordinator | Investigate teaching candidates, find reciprocal cycles, choose supported options, revise after feedback | `search_teachers`, `find_exchange_cycles`; scoped Pinecone `search-records` when enabled |
| Feasibility reviewer | Inspect profile evidence and proposal claims; validate UTC overlaps and participant-local session views; explain schedule problems | `get_learning_context`, `validate_and_schedule` |
| Host-controlled nodes | Pause for clarification/approval, enforce budgets, persist the approved proposal, emit activity | `save_proposal`, `get_proposal_status`; write tools are not exposed to LLM roles |

The same model may implement all three roles; they receive distinct prompts, tool subsets, and structured outputs. Three provider accounts or three different models are unnecessary.

Use one Gemini model call at a time to reduce free-tier quota pressure. Multi-agent specialization does not require simultaneous model requests. On HTTP 429, respect a bounded retry delay within the active run budget, then preserve state and show `quota_limited`; do not switch providers or enable billing. Verify the account's current limits during preflight rather than assuming a fixed requests-per-minute allowance.

Workflow: context → goal interpretation → clarification if needed → candidate investigation → cycle discovery → independent review/validation → approval interrupt → revalidation → save → result.

The reviewer can reject a coordinator proposal. A stale profile or availability revision invalidates the staged plan and triggers investigation again. Bound automatic revisions to two per run and total model calls to sixteen, counting tool-loop continuations and retries. Aim for six to eight calls on the normal path; the ceiling leaves room for a reviewed revision. Limit active execution to 90 seconds, excluding time waiting for the human. On exhaustion, return a visible stopped state with the current blocker.

User-requested revisions start a new run with `parent_run_id`, the revised request, and explicitly selected exclusions. The earlier run remains cancelled or superseded, providing traceable history. Do not infer a permanent dislike of a person from rejection of one proposal.

## 7. Custom MCP tool contracts

Tool names below are exact application contracts. Each receives an injected `ActorContext`. The router validates cohort/member scope and hides injected context fields from model-visible schemas. Host-provided run exclusions are always enforced in search, validation, and save; model-supplied exclusions may add members but cannot remove an explicit exclusion.

| Tool | Arguments beyond context | Result |
| --- | --- | --- |
| `get_learning_context` | none | Catalog, selected member, public cohort profiles including location/timezone and availability, dataset revision |
| `search_teachers` | `goal: LearningGoal`, `excluded_member_ids: list[str]` | Eligible profiles and declared-skill evidence; deterministic baseline order |
| `find_exchange_cycles` | `goal`, `excluded_member_ids`, `preferred_member_ids`, `limit=5` | Up to five feasible cycles, provisional schedules, and diagnostic counts |
| `validate_and_schedule` | `cycle: ExchangeCycle`, `goal: LearningGoal`, optional `proposed_sessions: list[Session]` | A current `ValidationResult` and fingerprinted plan with participant-local views; validate supplied UTC times and derived views exactly, otherwise find a schedule |
| `save_proposal` | `plan`, `approval_fingerprint`, `idempotency_key` | Saved `Proposal`, or typed stale/invalid/approval-mismatch result |
| `get_proposal_status` | Exactly one of `idempotency_key` or `proposal_id` | Existing scoped `Proposal` or explicit `not_found` |

Pure functions in `matching.py` implement directed skill compatibility, two/three-cycle enumeration, and pairwise scheduling. Search the full active authorized cohort before selecting the five results. Pinecone top-k results may influence ordering, but never limit the eligible graph or hide a valid cycle.

An edge teacher → learner exists only if a declared canonical skill matches the learner's need and the teacher meets the minimum proficiency. Enumerate distinct-member cycles containing the selected learner. Deduplicate cycle rotations while preserving teaching direction. Search 30-minute sessions with starts on a 15-minute UTC grid inside the finite normalized fixture windows; use deterministic backtracking to avoid a participant's incoming and outgoing sessions overlapping. Sort feasible results by preferred-member order, then shorter cycle, then stable member IDs. A model may explain or select feasible options but may not relax these constraints. Geographic proximity and timezone difference alone are not eligibility or ranking rules for remote sessions.

`fingerprint = SHA256(canonical JSON of cohort, selected learner, goal, directed edges, session UTC times, participant timezone IDs and derived local ISO values, dataset revision)`. Exclude prose explanations and presentation-only formatting. `dataset_revision` increases monotonically whenever profiles, timezones, or availability change, including scenario resets; it does not increase merely because a proposal is saved.

Save checks the approval fingerprint, validates the approved session times exactly, verifies the revision, and writes the proposal plus unique idempotency record in one SQLite transaction. It never silently substitutes a new schedule. Use `run_id:fingerprint` as the stable idempotency key. A repeated identical key returns the existing proposal; reuse for a different plan is rejected. Returning an already saved identical proposal is allowed even after a later dataset change, since it remains an unconfirmed historical proposal.

The trusted approval handler checks that the resumed run is waiting for approval of exactly that fingerprint. The LLM cannot invoke `save_proposal`, mint approvals, or call arbitrary router tools. This is a local single-operator trust boundary, not production multi-user authorization.

## 8. Vendor MCP bonuses

### Mem0

Use the hosted `https://mcp.mem0.ai/mcp` server with backend credentials. Permit scoped `search_memories`, `add_memory`, `update_memory`, `delete_memory`, and, when needed for async writes, `get_event_status`. Exclude bulk deletion and entity administration.

Host-injected identity is `skillswap-demo:<cohort_id>:<member_id>` plus project metadata. Queries and returned memory IDs must stay in that scope. Writes require an explicit Remember/Save/Edit/Forget action. A pending async memory write is displayed as pending until its event completes; it is not immediately claimed as saved. Edit/forget invalidates relevant local caches. Current structured availability and explicit exclusions always override memory.

The two-session test writes a preference, waits for confirmation, starts a fresh graph thread without the earlier chat transcript, retrieves the memory, and changes a recommendation only when profile evidence supports the preference.

### Pinecone

Use the official `@pinecone-database/mcp` local stdio server for the bonus. Its documented `search-records` tool requires an index with integrated embeddings. Seed public fictional offers into a project-specific index/namespace with profile ID, cohort ID, active flag, skill ID, and description.

Only `search-records` is available to the matching agent. Index creation/upsert are explicit setup operations, not runtime agent tools. The router injects the configured index, namespace, cohort filter, and active filter; hydrate returned IDs from SQLite and discard unknown/inactive/out-of-cohort IDs. Semantic similarity never certifies skill, proficiency, reciprocal value, or time compatibility.

Mem0 hosted memory and Pinecone community-profile search are separate integrations. Configuring Pinecone only as an internal Mem0 store would not demonstrate Pinecone MCP calls from SkillSwap.

### Modes and failure behavior

Provider modes are `disabled`, `connecting`, `live`, `degraded`, `error`. Missing credentials disable the bonus visibly. Failed Pinecone search falls back to the full deterministic cohort search with a visible local-search label. Failed Mem0 reads continue without memory and say so. Failed memory writes remain unsaved/pending; do not silently report success. Core custom MCP failure stops matching; there is no hidden direct-Python bypass.

Documentation establishes available interfaces, not authenticated compatibility. Verify discovery and a real scoped read/write before marking an integration live. Pin tested versions after smoke checks; the current LangChain MCP adapter API is documented as beta.

## 9. API and polished UI

Planned endpoints:

- `GET /api/context?member_id=...`: public demo context through custom MCP.
- `POST /api/runs`: `{member_id, request, excluded_member_ids, parent_run_id?}` → `{run_id}`.
- `GET /api/runs/{run_id}`: persisted `RunSnapshot`.
- `GET /api/runs/{run_id}/events?after=N`: replayable activity JSON, polled once per second while active; polling keeps the first UI simpler than bidirectional streaming.
- `POST /api/runs/{run_id}/resume`: clarification answer or `{decision: approve|cancel, fingerprint}`; serialized per run.
- `GET /api/proposals/{id}/export`: JSON download, verified through stored proposal lookup.
- `GET /api/providers`: actual connection/mode statuses.
- Bonus `GET/POST/PATCH/DELETE /api/memories`: scoped actions, user triggered; no arbitrary user IDs or server URLs accepted.

One desktop-first responsive workspace, with keyboard-operable alternatives to graph clicking:

- Header: fictional global cohort label, selected learner and viewing timezone, provider status indicators.
- Left: learning request, profile facts including city/country and timezone, and optional remembered preferences.
- Center: direct-swap or triangle graph; arrows explicitly mean “teaches”; each edge includes skill and compact viewer-local session time; nodes show city/timezone labels.
- Right: profile evidence, both participants' local dates/times/offsets per session, validation results, and proposal review with Save proposal / Revise / Cancel.
- Collapsible activity drawer: actual agent/tool events, failures, durations, and concise decision summaries; never fabricated animations or private reasoning traces.
- Saved view: `Awaiting participant confirmation`, downloadable proposal, and restart continuity.

Use SVG for the bounded two/three-person graph; no general graph editor. Preserve graph node positions during a time-only replan. Responsive fallback is an ordered session-card list. Clearly show loading, clarification, no feasible exchange, stale proposal, degraded provider, save failure, and saved states.

Render server-derived local views consistently; use locale formatting only for presentation. JavaScript's [Intl.DateTimeFormat](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Intl/DateTimeFormat) supports explicit timezone formatting for optional viewer-local labels. Never depend on the browser's implicit local timezone for participant times. Geography and timezone facts travel through the six existing tools and current API responses; no new MCP tool or map service is required.

## 10. Reliability and evaluation

Retry idempotent reads at most twice after the first attempt, with 0.5- and 1-second delays, respecting the run budget. Per-call tool timeout is 10 seconds. On uncertain save response, query `get_proposal_status` before retrying the exact idempotent write. Do not blindly repeat a memory write; inspect its event/status first.

Record activity in a small `app_run_events` table alongside graph state, with append-only sequence numbers. Persist the staged plan before interrupting. Serialize approval/resume per run so repeated clicks cannot start competing graph executions. Run one backend worker; enable SQLite WAL mode and a bounded busy timeout. Multi-worker execution is outside this prototype.

| Case | Required result |
| --- | --- |
| Direct reciprocal pair | Two valid, non-overlapping pairwise sessions |
| Three-way exchange with no common group slot | Three individually feasible sessions; no group-slot requirement |
| Unsupported or ambiguous goal | Focused clarification, no invented skill |
| No reciprocal path | Explain the actual blocker, no fabricated match |
| Profile/availability changes after preview | Reject stale approval; show revised plan and request approval again |
| Double approval or lost save response | One saved proposal, same ID on retry |
| Restart while awaiting approval | Resume same staged plan from SQLite checkpoints |
| Restart after save | Existing proposal and status remain accessible |
| Pinecone returns wrong-cohort/stale profile | Filter/hydrate and exclude it; complete local graph search remains available |
| Memory from another member | Never included in this member's prompt or UI |
| Mem0/Pinecone unavailable | Honest degraded behavior; no fabricated live-provider badge |

The core demo must complete the first eight applicable cases. Vendor assertions require separate live tests; mocks do not prove a live integration. Report measured elapsed time, calls, and results; do not invent an accuracy percentage.

Global-cohort checks are also required: verified Chicago/London/Bengaluru local views for the demo; a cross-date session; half-hour and quarter-hour offsets; date-specific DST offsets; rejection of nonexistent local times; explicit disambiguation of repeated times; missing timezone; no shared availability; timezone-change approval invalidation; and unchanged historical local views after profile edits. These are deterministic checks, without additional paid/model calls.

## 11. Demo fixture and story

Maya in Chicago (`America/Chicago`) offers Python and wants presentation design. Leo in London (`Europe/London`) offers Spanish and wants Python. Nina in Bengaluru (`Asia/Kolkata`) offers presentation design and wants Spanish. All offers meet the required proficiency. Seed local windows that cover precisely these sessions and the alternate below, while providing no common three-person slot.

| Session | UTC interval | Teacher's local time | Learner's local time |
| --- | --- | --- | --- |
| Maya → Leo: Python | Oct 26, 2026, 18:00–18:30 | Chicago, Oct 26, 13:00–13:30, UTC−05:00 | London, Oct 26, 18:00–18:30, UTC+00:00 |
| Leo → Nina: Spanish | Oct 26, 2026, 13:00–13:30 | London, Oct 26, 13:00–13:30, UTC+00:00 | Bengaluru, Oct 26, 18:30–19:00, UTC+05:30 |
| Nina → Maya: presentation design | Oct 27, 2026, 14:00–14:30 | Bengaluru, Oct 27, 19:30–20:00, UTC+05:30 | Chicago, Oct 27, 09:00–09:30, UTC−05:00 |

Seed a replacement Nina → Maya window on October 28 at 14:00 UTC (19:30 Bengaluru / 09:00 Chicago). A scenario control removes only the original October 27 window and increments dataset revision. Attempting to save the old plan must trigger a replan and fresh approval. The graph remains a three-cycle while one session changes. These offsets were checked against the available timezone database during planning; implementation must verify its installed database as part of fixture validation.

Other seed profiles provide a direct swap, a higher-ranked but incompatible semantic candidate, a no-cycle goal, and two feasible alternatives with different teaching styles for the memory demo. Seed expectations live in tests and are disclosed as fictional examples.

Distribute the other twelve profiles across additional locations including Sydney, São Paulo, and Kathmandu. Include a quarter-hour-offset fixture: Oct 26 at 12:15 UTC is 18:00 in `Asia/Kathmandu`. Separate deterministic boundary fixtures use a Chicago/India date rollover and Chicago's March/November clock transitions; these are validation cases, not suggested overnight meetings for the hero exchange.

Five-minute recording: problem and user (30 seconds); agents/MCP structure (30); find and inspect exchange (90); introduce conflict and recover (60); approve, reload and export (45); optional cross-session memory and semantic lookup (45). Adjust timings after rehearsal so the final recording stays under five minutes.

## 12. Delivery boundaries and references

The [implementation plan](../plans/2026-10-24-skillswap.md) specifies tasks, interfaces, verification, and stop rules. Runtime/provider setup is the first feasibility check. If setup consumes the reserve, keep the core complete and explicitly defer bonuses. No claims of real participant agreement or production readiness.

Primary references checked October 24, 2026:

- [Week 3 handout](../../../Week%203%20Project%20Handout%20%28Oct%202026%29.md) and [sample architecture](../../../Oct%20Multi-Agent%20Deal%20Review%20%28LangChain%20and%20LangGraph%29%20.md).
- [LangChain MCP adapter](https://docs.langchain.com/oss/python/langchain/mcp): discover/adapt MCP tools; current API status and transport options.
- [FastMCP client](https://gofastmcp.com/clients/client) and [tool calls](https://gofastmcp.com/clients/tools): actual MCP discovery, scoped wrappers, and transport lifecycle.
- [LangGraph interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts) and [persistence](https://docs.langchain.com/oss/python/langgraph/persistence): approval pause/resume and durable checkpoints; in-memory saving does not survive a process restart.
- [Mem0 MCP](https://docs.mem0.ai/platform/mem0-mcp): hosted connection, authentication, scoped memory operations, async event status.
- [Pinecone MCP](https://docs.pinecone.io/guides/operations/mcp-server): official tools and integrated-embedding requirement.
- [Gemini model catalog](https://ai.google.dev/gemini-api/docs/models) and [pricing](https://ai.google.dev/gemini-api/docs/pricing): verify the exact text-model ID and free-tier availability during setup.

These references inform the design. Exact installed versions, credentials, connection success, latency, and output quality remain implementation checks.
