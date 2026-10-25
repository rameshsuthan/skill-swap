# SkillSwap planning package

Prepared October 24, 2026. Implementation update October 25: the local prototype is verified with real MCP, automated acceptance tests, and a live three-specialist workflow using user-authorized `gemini-3.5-flash-lite`. The original `gemini-3.8-flash` checks returned HTTP 503/504. See the [startup guide](../../README.md) and [validation report](../validation-results.md); the linked design/plan preserve the original planning package.

SkillSwap helps a worldwide remote learning community discover reciprocal teaching opportunities, including three-person exchanges when a direct swap is unavailable.

- [Product and technical design](../superpowers/specs/2026-10-24-skillswap-design.md)
- [Implementation plan](../superpowers/plans/2026-10-24-skillswap.md)
- [Architecture and component diagrams](architecture.md)

The first delivery is a local, single-operator demonstration with 15 fictional profiles, real model calls, a real custom MCP server/client, and reviewable exchange proposals. Mem0 through MCP now has explicit preference controls and separately verified live CRUD; Pinecone remains an optional future milestone. See the startup guide for configuration and the memory-alternatives demo.

Planning defaults: React and TypeScript UI; Python/FastAPI backend; LangGraph orchestration; SQLite for domain records and durable checkpoints; one learning cohort. The user confirmed `gemini-3.8-flash` on the free tier. Credentials, quota, and actual integration success remain setup checks.

Each member supplies an IANA timezone. Optional self-declared city/country provide context; they never infer a timezone or exclude distant members. Dated local availability retains its source zone and ambiguity choice (`fold` where needed), then normalizes to UTC inside the existing custom MCP server. Thirty-minute pairwise sessions use a 15-minute UTC start grid, supporting quarter-hour offsets. Session cards show both participants' local dates/times, IANA zone IDs, date-specific offsets, and previous/next-day badges. A timezone change increments the dataset revision and invalidates staged approval; saved plans preserve participant timezone snapshots.

Geocoding, maps, distance ranking, and in-person matching are outside this remote prototype. This extension adds deterministic `scheduling.py` normalization using `zoneinfo`; the same three agents and MCP topology remain in place.

The 4–6 hour schedule is a target assuming runtime and model prerequisites are resolved. With global scheduling included, allocate about 4½ hours to the core demonstration; include vendor MCP integrations within six hours only when their live checks pass.
