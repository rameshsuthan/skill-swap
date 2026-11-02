"""Generate editable SVG architecture diagrams for the submission report."""

from html import escape
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "docs/submission/diagrams"


def canvas(title, height=850):
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="{height}" viewBox="0 0 1000 {height}" role="img"><title>{escape(title)}</title><defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8" fill="#45636b"/></marker></defs><rect width="100%" height="100%" fill="white"/>'
    ]


def text(s, x, y, words, size=20, bold=False, anchor="middle"):
    for i, line in enumerate(words.split("\n")):
        s.append(
            f'<text x="{x}" y="{y + i * 27}" text-anchor="{anchor}" font-family="Arial, sans-serif" font-size="{size}" font-weight="{700 if bold else 400}" fill="#18333a">{escape(line)}</text>'
        )


def box(s, x, y, w, h, title, body="", fill="#edf5f2"):
    s.append(
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="{fill}" stroke="#7b9696" stroke-width="1.5"/>'
    )
    text(s, x + w / 2, y + 31, title, 21, True)
    if body:
        text(s, x + w / 2, y + 60, body, 18)


def arrow(s, points, label="", lx=0, ly=0, dashed=False):
    dash = ' stroke-dasharray="7 5"' if dashed else ""
    s.append(
        f'<polyline points="{points}" fill="none" stroke="#45636b" stroke-width="2"{dash} marker-end="url(#arrow)"/>'
    )
    if label:
        text(s, lx, ly, label, 17)


def save(name, s):
    (OUT / (name + ".svg")).write_text("\n".join(s + ["</svg>"]))


def architecture():
    s = canvas("Implemented SkillSwap system architecture", 940)
    box(s, 260, 10, 480, 82, "React workspace", "Goals · both local times · explicit approval")
    arrow(s, "500,92 500,145", "HTTP and activity polling", 650, 121)
    box(s, 235, 145, 530, 88, "FastAPI and LangGraph host", "Interpreter → Coordinator → Reviewer")
    box(s, 15, 145, 190, 88, "Gemini API", "3.5 Flash Lite", "#eef2fa")
    arrow(s, "235,189 205,189")
    box(
        s,
        235,
        270,
        530,
        82,
        "Trusted host and MCP router",
        "Role allowlists · injected scope · approval checks",
    )
    arrow(s, "500,233 500,270")
    box(
        s,
        790,
        270,
        195,
        110,
        "Checkpoint SQLite",
        "Runs · interrupts\nActivity · recovery",
        "#f3f3f3",
    )
    arrow(s, "765,310 790,310")
    box(
        s,
        15,
        425,
        305,
        115,
        "Custom SkillSwap MCP",
        "Separate Python stdio server\nSix typed domain tools",
    )
    box(
        s,
        347,
        425,
        305,
        115,
        "Mem0 MCP",
        "Hosted HTTPS transport\nScoped learner preferences",
        "#fff5e7",
    )
    box(
        s,
        680,
        425,
        305,
        115,
        "Pinecone MCP",
        "Official Node stdio server\nRuntime search-records only",
        "#fff5e7",
    )
    arrow(s, "370,352 370,390 167,390 167,425", "stdio", 235, 380)
    arrow(s, "500,352 500,425", "HTTPS", 545, 395, dashed=True)
    arrow(s, "630,352 630,390 832,390 832,425", "stdio", 758, 380, dashed=True)
    box(
        s,
        15,
        590,
        305,
        110,
        "Deterministic domain",
        "Eligibility · UTC scheduling\nRevision · fingerprint · save",
    )
    arrow(s, "167,540 167,590")
    box(
        s,
        15,
        750,
        305,
        110,
        "Domain SQLite",
        "Profiles · availability\nProposals · idempotency",
        "#f3f3f3",
    )
    arrow(s, "167,700 167,750")
    box(
        s,
        680,
        590,
        305,
        110,
        "Dedicated Pinecone index",
        "15 fictional public offers\nNo availability or memories",
        "#f3f3f3",
    )
    arrow(s, "832,540 832,590", dashed=True)
    text(s, 360, 755, "Authority rules", 22, True, anchor="start")
    text(
        s,
        360,
        790,
        "Models read and validate; only the host saves.\nMemory changes need an explicit UI action.\nSemantic hits are checked against current profiles.\nFull local matching still runs.",
        18,
        anchor="start",
    )
    text(
        s, 500, 910, "Dashed paths are optional integrations, both verified in this prototype.", 18
    )
    save("system-architecture", s)


def workflow():
    s = canvas("Agent workflow and human approval", 1000)
    boxes = [
        (20, "Learner request", "Skill goal + explicit exclusions"),
        (145, "Goal interpreter", "Resolve intent, then retrieve optional memory"),
        (270, "Matching coordinator", "Search teachers → optional Pinecone → full cycle search"),
        (395, "Feasibility reviewer", "Validate exact cycle and session times"),
        (550, "Human review interruption", "Checkpoint the proposal and its fingerprint"),
        (705, "Trusted host revalidation", "Check current revision and approved exact sessions"),
        (850, "Save unconfirmed proposal", "Idempotent MCP save · recoverable persisted result"),
    ]
    for y, title, body in boxes:
        box(s, 195, y, 610, 85, title, body, "#fff5e7" if y == 550 else "#edf5f2")
    for a, b in [(105, 145), (230, 270), (355, 395), (480, 550), (635, 705), (790, 850)]:
        arrow(s, f"500,{a} 500,{b}")
    text(s, 595, 674, "Explicit approval", 17)
    arrow(s, "195,185 55,185 55,110 300,110 300,145")
    text(s, 112, 151, "Clarify", 16)
    arrow(s, "805,748 945,748 945,310 805,310")
    text(s, 878, 500, "Changed facts", 16)
    text(s, 878, 526, "Replan and", 16)
    text(s, 878, 552, "approve again", 16)
    text(s, 590, 515, "Valid plan", 17)
    text(s, 500, 980, "Bounded investigation: 16 model calls · 2 revisions · 90 active seconds", 18)
    save("agent-workflow", s)


def sequence():
    s = canvas("Exact approval and durable proposal saving", 910)
    xs = [110, 370, 635, 895]
    for x, title, body in zip(
        xs,
        ["Human and UI", "Trusted host", "Custom MCP", "Domain SQLite"],
        ["Review decision", "Approval boundary", "Scope and validation", "Atomic persistence"],
    ):
        box(s, x - 100, 15, 200, 85, title, body, "#edf5f2")
        s.append(
            f'<path d="M{x},100 V850" stroke="#a3b4b6" stroke-width="1.5" stroke-dasharray="5 5"/>'
        )
    for y, a, b, label in [
        (155, 0, 1, "Approve staged fingerprint"),
        (240, 1, 2, "Revalidate exact sessions"),
        (325, 2, 3, "Read current facts and revision"),
        (410, 2, 1, "Return validated plan and fingerprint"),
        (560, 1, 2, "Save with stable idempotency key"),
        (645, 2, 3, "Validate and save atomically"),
        (730, 1, 0, "Display saved unconfirmed proposal"),
    ]:
        arrow(s, f"{xs[a]},{y} {xs[b]},{y}", label, (xs[a] + xs[b]) / 2, y - 14)
    s.append('<rect x="185" y="442" width="630" height="65" fill="#fff5e7" stroke="#b89d76"/>')
    text(s, 500, 468, "If facts changed: return to planning and require fresh approval.", 18)
    text(s, 500, 492, "No write is authorized by the old approval.", 18)
    text(s, 500, 810, "If a save response is uncertain: look up status before any retry.", 18)
    text(
        s,
        500,
        878,
        "Graph checkpoints retain the interruption; saved proposals retain timezone snapshots.",
        18,
    )
    save("approval-sequence", s)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    architecture()
    workflow()
    sequence()
