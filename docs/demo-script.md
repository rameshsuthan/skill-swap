# Five-minute demo script

Use this as a recording outline after live Gemini generation recovers. A controlled-model rehearsal is clearly labeled test mode and is not proof of live Gemini.

**0:00–0:30 — Problem.** “In a global learning community, the person who can teach me may want a different skill. SkillSwap finds a reciprocal exchange, including a circle of three.” Show Maya's Python offer and presentation-design request. State that profiles and dates are fictional.

**0:30–1:00 — Architecture.** React → FastAPI/LangGraph → real MCP subprocess → deterministic scheduling and SQLite. Three specialists interpret, coordinate, and review. One configured Gemini model, distinct prompts and tools. Only the trusted host can save.

**1:00–2:30 — Find and inspect.** Search as Maya. Expand actual activity. Show Maya → Leo, Leo → Nina, Nina → Maya. Read Chicago 13:00/London 18:00 for the first session and Bengaluru 19:30/Chicago 09:00 for the final one. Explain pairwise sessions do not need a shared three-person time.

**2:30–3:30 — Changed availability.** While awaiting approval, run:

```bash
.venv/bin/python scripts/demo_scenario.py remove-nina-window
```

Approve the old view. The app must revise to October 28 and require a new approval. Do not describe the old approval as authorizing new times.

**3:30–4:30 — Human control and recovery.** Approve the new proposal. Point to “Awaiting participant confirmation.” Reload, export JSON, and show the saved local timezone snapshots. Stop/restart the backend at an approval interruption in a separate rehearsal to demonstrate durability.

**4:30–5:00 — Boundaries.** Nothing is booked or sent. No real participant agreement. Mem0/Pinecone are disabled until separately verified. If Gemini returns 503 or quota errors, show the actual stopped state and explain the provider blocker; never splice a test fixture into a purported live run.

Before the next recording, reset the fictional profiles with `scripts/seed_demo.py`. Reset increments dataset revision and preserves saved proposal history. Keep API keys and terminal environment output out of the recording.

## Optional Mem0 segment

Enable the bonus in `.env` and restart. Run `scripts/demo_scenario.py memory-alternatives` before this segment. Request presentation design as Maya: the default direct exchange uses Olivia. In Learning preferences, explicitly Remember “I prefer guided-project teaching over discussion for my learning.” Start a fresh search and show Nina's declared guided-project offer supporting the three-member alternative. Show the actual `mem0 / search_memories` activity, then Edit or Forget the preference. Reset seed data afterward. Pause between live searches if Gemini reports a quota limit; never substitute a model automatically.
