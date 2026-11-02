# Five-minute demo outline

The core and both MCP bonuses have passed live verification. Use `gemini-3.5-flash-lite`; show actual provider/activity states. A narrated walkthrough was recorded locally on November 2, 2026; see the recording details below. It has not been published. Leave at least 65 seconds between fresh live searches during rehearsal to reduce quota bursts.

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

## Recording the narrated walkthrough

The reusable recorder captures the real app at 1440×1080, adds visible captions,
uses macOS Samantha synthetic narration, and exports H.264/AAC MP4 plus SRT.
Media, exported proposals, and run evidence stay under ignored
`storage/demo-video/`; no credentials or terminal footage are recorded.

Use a **separate recording database** and stop any existing server on port 8000
before this sequence. The recorder approves a fictional proposal and removes
Nina's October 27 window in `storage/video-domain.sqlite`. Do not point the
recorder at a production preview. Existing Mem0 preferences are read only.

```bash
# Optional media-only dependency; not required by SkillSwap itself.
uv pip install --python .venv/bin/python imageio-ffmpeg==0.8.0
.venv/bin/python scripts/render_demo.py prepare

# In a dedicated terminal, start the isolated server using the current UI build.
export SKILLSWAP_DOMAIN_DB="$PWD/storage/video-domain.sqlite"
export SKILLSWAP_CHECKPOINT_DB="$PWD/storage/video-checkpoints.sqlite"
.venv/bin/python scripts/seed_demo.py
.venv/bin/python -m uvicorn skillswap.api:app --host 127.0.0.1 --port 8000

# In another terminal, record and encode.
PLAYWRIGHT_BROWSERS_PATH="$PWD/.tools/browsers" \
  .tools/node/bin/node scripts/record_demo.cjs
.venv/bin/python scripts/render_demo.py render
```

The recorder requires working live providers and verifies the saved proposal and
semantic discovery before producing its timeline/evidence. Provider failures stop
the take; they are not replaced with simulated success. The video demonstrates
browser reload recovery and explicitly distinguishes it from the separately
verified backend restart check. It shows the memory controls without creating,
editing, or forgetting hosted preferences. Nothing is published automatically.

### Verified recording — November 2, 2026

- Output: `storage/demo-video/SkillSwap-demo.mp4` (4:43.64, 1440×1080,
  H.264/AAC, 10.4 MiB), with visible captions and a companion `.srt` file.
- Live run: `260e3153-271d-45df-8ee0-0311f067b547`; saved after the stale
  availability check and fresh approval, 15 model calls including replanning.
- Activity includes Gemini, SkillSwap MCP, Mem0 MCP, and Pinecone MCP;
  discovery returned two eligible semantic candidates.
- Full video/audio decode passed. Representative frames were visually checked;
  narration peaks at −1.7 dB, with no clipping detected by the level check.
- The take uses separate local databases, reads existing hosted preferences
  without changing them, and exports only fictional proposal data.
