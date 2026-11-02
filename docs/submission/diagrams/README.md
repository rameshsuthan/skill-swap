# Submission diagrams

These diagrams describe the implemented November 2, 2026 prototype, including
the explicitly authorized `gemini-3.5-flash-lite` model and both optional MCP
integrations. They complement the historical planning diagrams.

- [System architecture](system-architecture.svg) — services, MCP transports, storage, and authority.
- [Agent workflow](agent-workflow.svg) — specialist roles, clarification, approval, and replanning.
- [Approval sequence](approval-sequence.svg) — exact-plan consent, revalidation, idempotent save, and recovery.

Each diagram has an editable vector SVG and a high-resolution PNG embedded in
the submission Word document and Markdown report. The sequence summarizes
logical messages; ordinary database results return through MCP and the host.

Regenerate from the repository root:

```bash
.venv/bin/python scripts/build_submission_diagrams.py
PLAYWRIGHT_BROWSERS_PATH="$PWD/.tools/browsers" \
  .tools/node/bin/node scripts/render_submission_diagrams.cjs
```

Then rebuild the Word report with `scripts/build_submission_doc.py` using the
Codex document runtime Python. Apply the document skill's Google Docs title
sanitizer and render/inspect the report before delivering a revised artifact.
