# Five-minute demo outline

The core and both MCP bonuses have passed live verification. Use `gemini-3.5-flash-lite`; show actual provider/activity states. This is an outline for recording, not a claim that a video has been recorded or published. Leave at least 65 seconds between fresh live searches during rehearsal to reduce quota bursts.

Before recording, reset fictional profiles with `scripts/seed_demo.py` if needed. It increments revision and preserves proposal history. Keep credentials and environment output off screen. Existing preferences can influence ordering; inspect them and explicitly edit/forget only the demo preferences you intend to change.

**0:00–0:25 — Problem and people.** “In a global learning community, the person who can teach me may want a different skill. SkillSwap finds reciprocal exchanges, including a circle of three.” Show Maya's Python offer and presentation-design goal. Disclose 15 fictional profiles and October 26–30, 2026 dates.

**0:25–0:55 — Architecture.** React → FastAPI/LangGraph → three specialist roles. Custom MCP owns profile/schedule validation and saving; Mem0 holds explicit preferences; Pinecone suggests relevant public offers. Only the host can save after approval.

**0:55–1:55 — Find and inspect.** Search as Maya. Show the three-cycle and each pair's two local times. Explain that the three people do not need one shared slot. Expand activity to show interpreter, coordinator, reviewer, and actual MCP calls. Semantic similarity helps ordering; it never proves feasibility.

**1:55–2:55 — Changed availability.** While awaiting approval, run:

```bash
.venv/bin/python scripts/demo_scenario.py remove-nina-window
```

Attempt the old approval. Show the revised October 28 session and the new approval requirement. The old approval cannot authorize different times.

**2:55–3:40 — Human control and recovery.** Approve the new proposal, point to “Awaiting participant confirmation,” reload, and export JSON. Nothing is booked or sent. For a separate durability take, restart the backend at an approval interruption and show recovery.

**3:40–4:40 — Personalization and discovery.** Explicitly Remember a teaching-style preference, choose New search, and run a fresh search. Show `mem0 / search_memories`, `pinecone / search-records`, and the search-method label. Explain Edit/Forget and the visible full-cohort fallback if Pinecone fails. Allow the agents to finish; provider errors must remain visible rather than replaced with test footage.

**4:40–5:00 — Outcome and boundaries.** A reviewable, timezone-aware proposal backed by exact schedule checks, scoped memory/search, and durable recovery. All profiles are fictional; participants still need to agree. End on the polished workspace.

For a separate comparison take, enable `scripts/demo_scenario.py memory-alternatives`: the default direct swap can use Olivia, while “I prefer guided-project teaching over discussion for my learning” supports Nina's declared style and the three-cycle. Space the two fresh searches by at least 65 seconds. This take can replace the availability segment to stay under five minutes. Reset the dataset afterward.
