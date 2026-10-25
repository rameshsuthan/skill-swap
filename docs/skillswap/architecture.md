# SkillSwap architecture and diagrams

Architecture prepared October 24, 2026. The October 25 local implementation follows this topology; [validation](../validation-results.md) records local checks and the successful live `gemini-3.5-flash-lite` workflow authorized October 25. Model labels below preserve the original design; the configured default is now `gemini-3.5-flash-lite`. The [design spec](../superpowers/specs/2026-10-24-skillswap-design.md) is authoritative. These diagrams describe the proposed build; they do not establish working integrations. The core is a single-operator demo with fictional profiles. Optional vendor connections require separate authenticated smoke tests.

## System architecture

The backend hosts LangGraph and actual `fastmcp.Client` connections with scoped tool wrappers. Agents discover and invoke domain tools across stdio; they never import domain functions to bypass MCP. Gemini 3.8 Flash is configured through `GEMINI_MODEL=gemini-3.8-flash`; account access and quota remain preflight checks. The domain server exclusively writes domain SQLite, while the graph host owns a separate checkpoint database. Dashed vendor paths are bonuses; both can be enabled independently.

The cohort matches remotely worldwide. Each member supplies a required IANA timezone. Optional self-declared city/country are context only: they never infer timezone, filter by distance, or introduce maps/geocoding/in-person scheduling. The workspace shows each session in both participants' local dates/times, zone IDs, date-specific UTC offsets, and previous/next-day badges.

[Standalone SVG](diagrams/architecture.svg) · [Mermaid source](diagrams/architecture.mmd)

```mermaid
flowchart LR
  UI["Worldwide remote workspace<br/>both local dates/times • zones/offsets • day badges"] -->|HTTP and event polling| API["FastAPI / LangGraph host"]
  API --> ROLES["Three LLM roles<br/>interpret • coordinate • review"]
  ROLES --> ROUTER["fastmcp.Client / scoped tool wrappers<br/>role allowlists + injected actor"]
  API --> MODEL["Gemini 3.8 Flash<br/>GEMINI_MODEL=gemini-3.8-flash"]
  API --> HOST["Trusted host nodes<br/>interrupt • approve • commit"]
  HOST --> ROUTER
  API --> CHECK[("Separate checkpoints.sqlite<br/>runs • interruptions • activity")]
  ROUTER -->|stdio: real MCP calls| CUSTOM["Custom SkillSwap MCP server<br/>zoneinfo normalization • UTC matching"]
  CUSTOM --> SQL[("skillswap.sqlite<br/>IANA zones • source-local + UTC windows • proposals")]
  ROUTER -.->|Optional HTTPS MCP| MEM["Mem0 hosted MCP<br/>scoped preferences + explicit writes"]
  ROUTER -.->|Optional stdio: official Node server| PINE["Pinecone MCP<br/>search-records only at runtime"]
  PINE -.-> INDEX[("Project-specific integrated-embedding index<br/>public fictional offers only")]
  SQL --> RESULT["Saved proposal + participant timezone snapshots<br/>awaiting_participant_confirmation"]
  classDef bonus fill:#fff7ed,stroke:#c77721,stroke-dasharray:5 4;
  class MEM,PINE,INDEX bonus;
```

## Components and authority

LLM roles investigate and explain. Deterministic modules enforce skill compatibility, finite cycle search, pairwise scheduling, fingerprints, scope, and idempotency. Only trusted host nodes can call save/status tools. Vendor results cannot override current domain facts. Mem0 writes additionally require explicit user actions.

Within the existing custom MCP process, `scheduling.py` uses `zoneinfo` and validation to normalize dated local availability. It retains source-local dates/times, IANA zone, and `fold` choices for ambiguous endpoints alongside normalized UTC windows. Invalid zones and nonexistent local times are rejected; ambiguous local times require an explicit fold choice. `matching.py` evaluates overlaps in UTC. No additional server or agent is introduced.

[Standalone SVG](diagrams/components.svg) · [Mermaid source](diagrams/components.mmd)

```mermaid
flowchart TB
  subgraph APP["Application backend"]
    API["API + replayable activity + provider modes"] --> GRAPH["LangGraph / checkpoint owner"]
    GRAPH --> I["Goal interpreter<br/>get_learning_context"]
    GRAPH --> C["Matching coordinator<br/>search_teachers / find_exchange_cycles"]
    GRAPH --> R["Feasibility reviewer<br/>get_learning_context / validate_and_schedule"]
    GRAPH --> H["Trusted approval + commit<br/>save_proposal / get_proposal_status"]
    I --> POLICY["fastmcp.Client + scoped wrappers<br/>allowlists • actor scope • timeouts"]
    GRAPH --> MODEL["Gemini 3.8 Flash<br/>GEMINI_MODEL=gemini-3.8-flash"]
    C --> POLICY
    R --> POLICY
    H --> POLICY
    GRAPH --> CP[("checkpoints.sqlite<br/>staged plan • approvals • events")]
  end
  subgraph DOMAIN["Separate custom MCP stdio process"]
    TOOLS["Six typed MCP tools"] --> SCOPE["Scope / revision / approval checks"]
    SCOPE --> TIME["scheduling.py / zoneinfo<br/>dated local input + IANA zone + fold → UTC"]
    TIME --> MATCH["matching.py<br/>compatibility • 2/3 cycles • UTC overlaps"]
    MATCH --> SLOTS["30-minute pairwise sessions<br/>15-minute UTC start grid; no member overlap"]
    SCOPE --> STORE["SQLite repository<br/>atomic save • idempotency"]
    STORE --> DB[("skillswap.sqlite<br/>source local + UTC • zones • plan zone snapshots")]
  end
  POLICY -->|stdio| TOOLS
  POLICY -.->|HTTPS MCP| M["Optional Mem0<br/>interpreter reads; user-triggered writes"]
  POLICY -.->|stdio / Node| P["Optional official Pinecone MCP<br/>coordinator search-records"]
  P -.-> FILTER["Hydrate/filter IDs via domain facts<br/>retain full local cycle search"]
```

## Matching and approval flow

Every edge is a separate 30-minute teaching session, starting on a 15-minute UTC grid to support quarter-hour offsets. A three-cycle does not need one common three-person slot. Validation prevents a participant's incoming and outgoing sessions from overlapping. Human waiting does not consume the active execution budget. Timezone changes increment the dataset revision, invalidate staged approval, and require revalidation and fresh approval. Saved proposals retain participant timezone snapshots for historical interpretation.

[Mermaid source](diagrams/matching-flow.mmd)

```mermaid
flowchart TD
  START["Select fictional learner + enter request"] --> CTX["Load profiles + required IANA zones + availability<br/>optional city/country are context only; memory optional"]
  CTX --> INTERPRET["Interpreter maps request to supported goal"]
  INTERPRET --> CLEAR{"Goal unambiguous?"}
  CLEAR -->|No| QUESTION["Checkpoint + interrupt for clarification"]
  QUESTION --> INTERPRET
  CLEAR -->|Yes| FIND["Coordinator searches full active cohort<br/>optional Pinecone adjusts ordering only"]
  FIND --> ENUM["Enumerate directed 2/3-member cycles<br/>distinct members; declared skill + minimum proficiency"]
  ENUM --> NORMALIZE["scheduling.py / zoneinfo<br/>validate source-local dates + zone/fold; normalize UTC"]
  NORMALIZE --> SCHEDULE["30-minute pairwise sessions; 15-minute UTC start grid<br/>matching.py checks UTC overlaps; no member overlap"]
  SCHEDULE --> EXISTS{"Feasible plan?"}
  EXISTS -->|No| BLOCK["Explain actual blocker; stop without invented match"]
  EXISTS -->|Yes| REVIEW["Reviewer inspects evidence and calls validation"]
  REVIEW --> VALID{"Current and valid?"}
  VALID -->|No| LIMIT{"Within 2 revisions / 16 model calls / 90 active seconds?"}
  LIMIT -->|Yes| FIND
  LIMIT -->|No| STOP["Visible stopped state + blocker"]
  VALID -->|Yes| APPROVE["Checkpoint plan + fingerprint; interrupt for proposer approval"]
  APPROVE --> LOCAL["Review both local dates/times + zone IDs + dated offsets<br/>previous/next-day badges; worldwide remote exchange"]
  LOCAL --> DECISION{"Human decision"}
  DECISION -->|Cancel| CANCEL["Cancelled run"]
  DECISION -->|Revise| NEW["New child run + explicit exclusions"]
  NEW --> START
  DECISION -->|Approve exact fingerprint| FRESH["Host revalidates exact sessions + current zone revision"]
  FRESH --> CURRENT{"Unchanged?"}
  CURRENT -->|No| LIMIT
  CURRENT -->|Yes| SAVE["Host-only idempotent save via MCP"]
  SAVE --> DONE["awaiting_participant_confirmation<br/>saved participant zone snapshots; no booking"]
```

## Proposal sequence and uncertain saves

The host binds approval to the staged fingerprint. Save independently verifies revision and exact times in a transaction. When a save response is uncertain, lookup precedes any retry. An identical saved proposal remains a historical unconfirmed proposal even if the dataset later changes.

[Mermaid source](diagrams/proposal-sequence.mmd)

```mermaid
sequenceDiagram
  actor User as Demo proposer
  participant UI as Workspace
  participant Host as FastAPI / trusted graph host
  participant GraphDB as Checkpoint SQLite
  participant Reviewer as Reviewer LLM
  participant MCP as Scoped backend MCP client
  participant Domain as Custom stdio MCP server
  participant DB as Domain SQLite
  Reviewer->>MCP: validate_and_schedule(cycle, goal)
  MCP->>Domain: Real MCP tool invocation + injected actor
  Domain->>DB: Read profiles, IANA zones, source-local/UTC windows, revision
  Note over Domain,DB: zoneinfo validates local input + fold; matching uses UTC
  Domain-->>MCP: Fingerprinted valid plan
  MCP-->>Reviewer: Adapted tool result
  Host->>GraphDB: Persist staged plan; approval interrupt
  Host-->>UI: Review plan + fingerprint + both local dates/times/zones/offsets
  User->>UI: Approve exact plan
  UI->>Host: Resume(run_id, approve, fingerprint)
  Host->>Host: Serialize resume; verify waiting fingerprint
  Host->>MCP: validate_and_schedule(exact approved sessions)
  MCP->>Domain: Revalidate current facts
  Domain-->>MCP: Current ValidationResult and fingerprinted plan
  MCP-->>Host: Current validation result
  Host->>Host: Compare staged revision and fingerprint with current result
  alt Changed profile/zone revision or invalid sessions
    Host-->>UI: Replan, display changes, require fresh approval
  else Approved plan still current
    Host->>MCP: save_proposal(plan, approval_fingerprint, run_id:fingerprint)
    MCP->>Domain: Host-only write tool
    Domain->>DB: Transaction: reject stale/invalid approval or save proposal + zone snapshots + unique key
    alt Save response received
      Domain-->>MCP: Proposal ID + awaiting_participant_confirmation
      MCP-->>Host: Saved proposal
    else Response lost or timed out
      Host->>MCP: get_proposal_status(idempotency_key)
      MCP->>Domain: Lookup scoped result
      Domain-->>MCP: Existing proposal or explicit not_found
      MCP-->>Host: Scoped lookup result
      Note over Host,Domain: Retry exact idempotent save only after lookup, if needed
    end
    Host->>GraphDB: Persist saved result and activity
    Host-->>UI: Saved proposal + JSON download
    Note over User,UI: Other participants have not confirmed; availability is not reserved
  end
```

## Logical data model

This is a logical relationship view, not a promised SQL migration. Domain entities and graph state belong in different databases. Offer/need evidence, current timezone revision, and UTC times determine eligibility and fingerprints; memory, city/country, and semantic similarity do not. The selected learner's interpreted goal is run-local. Availability preserves the original local input and zone/fold alongside UTC; saved plans preserve participant timezone snapshots rather than relying only on mutable profile zones.

[Mermaid source](diagrams/data-model.mmd)

```mermaid
erDiagram
  COHORT ||--o{ MEMBER_PROFILE : contains
  COHORT ||--|| DATASET_REVISION : versions
  MEMBER_PROFILE ||--|| TEACHING_OFFER : declares
  MEMBER_PROFILE ||--|| LEARNING_GOAL : stores
  MEMBER_PROFILE ||--o{ AVAILABILITY_WINDOW : supplies
  PROPOSAL ||--|| EXCHANGE_PLAN : preserves
  EXCHANGE_PLAN ||--|| EXCHANGE_CYCLE : contains
  EXCHANGE_PLAN ||--|{ SESSION : schedules
  MEMBER_PROFILE ||--o{ SESSION : teaches
  MEMBER_PROFILE ||--o{ SESSION : learns
  PROPOSAL ||--|| IDEMPOTENCY_RECORD : deduplicates
  RUN_SNAPSHOT ||--o{ ACTIVITY_EVENT : records
  RUN_SNAPSHOT ||--o| EXCHANGE_PLAN : stages_logically
  RUN_SNAPSHOT o|--o{ RUN_SNAPSHOT : parent_of
  MEMBER_PROFILE {
    string id PK
    string cohort_id FK
    string display_name
    string iana_timezone_required
    string optional_city
    string optional_country
    boolean active
    string source_record_id
  }
  TEACHING_OFFER {
    string skill_id
    int proficiency_1_to_3
    string description
    string styles
  }
  LEARNING_GOAL {
    string skill_id
    int minimum_teacher_proficiency
  }
  AVAILABILITY_WINDOW {
    string source_local_start
    string source_local_end
    string source_iana_timezone
    int optional_start_fold
    int optional_end_fold
    datetime start_utc
    datetime end_utc_exclusive
  }
  DATASET_REVISION {
    int monotonic_revision
  }
  EXCHANGE_CYCLE {
    string ordered_distinct_member_ids
    string directed_edges_and_evidence_ids
  }
  EXCHANGE_PLAN {
    string cohort_id
    string member_id
    string goal_override
    string participant_timezone_snapshots
    int dataset_revision
    string fingerprint
    string evidence
    string reviewer_summary
  }
  SESSION {
    string teacher_id FK
    string learner_id FK
    string skill_id
    datetime start_utc
    datetime end_utc
    string approved_participant_local_iso_views
  }
  PROPOSAL {
    string id PK
    string actor_context
    string idempotency_key UK
    string status_awaiting_participant_confirmation
    datetime created_at
  }
  IDEMPOTENCY_RECORD {
    string key PK
    string proposal_id FK
  }
  RUN_SNAPSHOT {
    string run_id PK
    string parent_run_id
    string status
    string interpreted_goal_override
    string staged_plan_and_approval
    string result_error_provider_modes
  }
  ACTIVITY_EVENT {
    int sequence_per_run
    datetime timestamp
    string agent_server_tool
    string status_duration_summary
  }
```

## Verification boundary

The SVGs use embedded vector elements and system fonts, with accessible titles/descriptions and no external assets. XML parsing and file/link checks can establish structural integrity; they do not establish browser rendering or Mermaid compilation. Runtime transport, credentials, persistence, and model behavior require implementation-time verification described in the spec.

## Implemented Mem0 boundary (October 25 update)

The hosted MCP client injects `skillswap-demo:<cohort_id>:<member_id>` into vendor identity and verifies all project/cohort/member metadata on returned rows. The interpreter first resolves skill/proficiency without any memory content, then requests scoped memory search. Only the coordinator sees retrieved preferences, for soft ranking against canonical profile styles. Domain MCP still validates every cycle and session.

The UI invokes explicit host-only mutations. Additional host-only `get_memory` and `get_memories` calls validate record ownership and populate the panel; these are not agent tools. No bulk/entity administration is registered. Pending operations persist IDs, scope and content hashes in the checkpoint database. Known events are polled; lost responses are reconciled through operation markers and scoped reads. An explicitly acknowledged unknown outcome remains visibly unconfirmed. There is no automatic retry of memory writes. Failed discovery can be retried on a later fresh run; failed reads leave deterministic matching available.
