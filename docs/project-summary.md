# SkillSwap project summary

SkillSwap helps a remote learning cohort exchange teaching time. A two-person swap is ideal; a three-person circle creates value when no direct swap exists. The prototype focuses on auditable proposals across timezones, with human approval before persistence.

The dataset contains 15 fictional members across Chicago, London, Bengaluru, Sydney, São Paulo, Kathmandu, Dubai, Tokyo, Toronto, Accra, Paris, Rome, Mexico City, Cape Town, and Auckland. Each profile declares an IANA timezone, dated availability, one teaching offer, and one learning goal. Proficiency is self-declared, not independently verified.

Three Gemini specialist roles run in LangGraph. The goal interpreter maps natural language to the supported catalog or asks a question. The matching coordinator calls actual custom MCP tools to investigate teachers and reciprocal cycles. The independent reviewer validates the proposed sessions. Trusted host nodes enforce exact approval and save through MCP; model roles cannot invoke write tools.

Deterministic Python code resolves DST gaps/folds, converts dated local windows to UTC, schedules each 30-minute edge on a 15-minute grid, and prevents a participant's sessions from overlapping. SQLite stores domain records separately from graph checkpoints. Revision checks and stable idempotency prevent stale approval and duplicate saves. The React workspace shows both participants' local dates, IANA zones, offsets, date-boundary badges, evidence, and real activity.

Development prompts/iterations included: execute the existing design without changing the Gemini model; establish actual stdio discovery before UI; derive tests from the hero timezone examples; verify exact-time approval under stale data and lost responses; implement a coherent accessible workspace; inspect desktop/mobile layouts; perform a fresh code review. No credential-bearing prompts or raw provider responses belong in the submission.

Important lessons: provider availability is a separate verification gate; runtime metadata access does not prove generation works. Synchronous SQLite writes can block async checkpoint commits, so runtime writes must not block the event loop. A saved proposal can exist even if its response is lost, which makes status lookup and stable keys essential. Timezone offsets belong to the session date, not to today's date or a city lookup.

Local automated tests cover the complete approval/save/restart/export workflow using controlled LLM responses and real MCP, graph, databases, and HTTP. Live `gemini-3.8-flash` generation is currently blocked by HTTP 503 high demand / HTTP 504 deadline exceeded. Account-level free-tier quota has not been independently verified. No model substitution occurred. Mem0 and Pinecone remain optional and disabled until the live core passes.

This is a local single-operator prototype. Production authentication, participant messaging, live calendars, recurring availability, arbitrary-length cycles, and public hosting are outside scope. The submission can link this summary, the source repository, architecture, validation report, and a video of five minutes or less. Creating a public repository, uploading a video, or publishing a Google Doc remains a separate user action; none is claimed here.
