"""Prepare local synthetic narration, then mux the recorded demo into MP4.

Optional recording dependency: imageio-ffmpeg==0.8.0 (not an app dependency).
Run prepare, record_demo.cjs, then render. All media stays in ignored storage/.
"""

import argparse
import json
import re
import subprocess
from pathlib import Path

import imageio_ffmpeg

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "storage/demo-video"
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
SCENES = [
    (
        "intro",
        "Welcome to SkillSwap. In a global learning community, the person who can teach you may want a completely different skill. SkillSwap finds a reciprocal exchange that works for everyone.",
    ),
    (
        "fiction",
        "This walkthrough uses fifteen fictional learners and a fixed demonstration week in October twenty twenty-six. You are watching the working application with live provider calls and synthetic narration.",
    ),
    (
        "maya",
        "Meet Maya in Chicago. She can teach Python and wants to learn presentation design. Her profile, learning goal, exclusions, and local availability define what a valid exchange must satisfy.",
    ),
    (
        "search",
        "Let's find her exchange. Three specialist agents work through LangGraph: a goal interpreter, a matching coordinator, and a feasibility reviewer. Gemini powers their reasoning, while tools check the actual records.",
    ),
    (
        "circle",
        "The result is a circle of three. Maya teaches Python to Leo. Leo teaches Spanish to Nina. Nina teaches presentation design to Maya. Everyone gives a skill and receives one they want.",
    ),
    (
        "times",
        "Each session shows the time for both participants, including their time zones and date-specific offsets. These are separate pairwise meetings. All three learners do not need to be available at the same moment.",
    ),
    (
        "agents",
        "Behind the exchange, the activity panel shows the actual agent and tool calls. The custom MCP server provides cohort records, finds exchange cycles, and performs exact scheduling checks.",
    ),
    (
        "pinecone",
        "Pinecone is connected through its real MCP server. Semantic search suggests relevant public teaching offers. The application checks those results against canonical profiles and still searches the full cohort for feasible exchanges.",
    ),
    (
        "validation",
        "The reviewer validates the selected cycle and schedule. Similarity is useful for discovery, but it does not prove availability or eligibility. The proposal remains staged until a human explicitly approves it.",
    ),
    (
        "change",
        "Now let's change Nina's availability using the demo maintenance command. This happens against a separate recording database. Watch what happens when we try to approve the proposal that was already on screen.",
    ),
    (
        "stale",
        "The application detects the change and asks for review again. Nina's session moves to October twenty-eighth. The previous approval cannot authorize a different schedule, so the revised proposal requires a fresh decision.",
    ),
    (
        "consent",
        "We can inspect the updated participant times before continuing. Once the revised exchange is acceptable, we explicitly choose approve and save. Only the trusted host can perform that write.",
    ),
    (
        "saved",
        "The proposal is now saved and awaiting participant confirmation. This is a proposal, not a booking. No messages or calendar invitations have been sent to these fictional participants.",
    ),
    (
        "recovery",
        "Reloading the browser brings the saved proposal back. Run checkpoints and proposals are persisted locally. This reload demonstrates the browser recovery path; backend restart recovery is also covered by the project's verified checks.",
    ),
    (
        "export",
        "The proposal can also be downloaded as JSON, preserving the exchange details for inspection or a future integration. Saving is idempotent, so retrying the same approval does not create duplicate proposals.",
    ),
    (
        "memory",
        "Mem0 provides optional learning preferences through MCP. This panel lets a learner explicitly remember, edit, or forget a preference. Viewing the panel does not save anything, and this recording leaves existing preferences unchanged.",
    ),
    (
        "memorycontrol",
        "A remembered teaching style can guide future searches, but cannot override availability, exclusions, or skill requirements. Pending and failed memory operations remain visible instead of being presented as confirmed saves.",
    ),
    (
        "services",
        "The service strip reports provider status, and activity records show which tools actually ran. If semantic discovery becomes unavailable, the application can use the complete local cohort while making that fallback visible.",
    ),
    (
        "ending",
        "SkillSwap turns a learning goal into a reviewable global exchange: three specialist agents, real MCP integrations, exact time-zone-aware scheduling, explicit human approval, and durable saved proposals. The next step belongs to the participants: agreeing to learn together.",
    ),
]


def prepare():
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    for key, text in SCENES:
        source = OUT / f"{key}.txt"
        source.write_text(text)
        audio = OUT / f"{key}.aiff"
        subprocess.run(
            ["say", "-v", "Samantha", "-r", "155", "-f", str(source), "-o", str(audio)], check=True
        )
        info = subprocess.run([FFMPEG, "-i", str(audio)], capture_output=True, text=True)
        h, m, s = re.search(r"Duration: (\d+):(\d+):([\d.]+)", info.stderr).groups()
        rows.append(dict(id=key, text=text, duration=int(h) * 3600 + int(m) * 60 + float(s)))
    (OUT / "scenes.json").write_text(json.dumps(rows, indent=2))
    print(
        f"Prepared {len(rows)} narration segments; {sum(r['duration'] for r in rows):.1f}s spoken."
    )


def timestamp(seconds):
    ms = round(seconds * 1000)
    return f"{ms // 3600000:02}:{ms // 60000 % 60:02}:{ms // 1000 % 60:02},{ms % 1000:03}"


def render():
    rows = json.loads((OUT / "timeline.json").read_text())
    video = (OUT / "video-path.txt").read_text().strip()
    command = [FFMPEG, "-y", "-i", video]
    for row in rows:
        command += ["-i", str(OUT / f"{row['id']}.aiff")]
    filters = [
        f"[{i + 1}:a]adelay={round(row['start'] * 1000)}:all=1[a{i}]" for i, row in enumerate(rows)
    ]
    filters += [
        "".join(f"[a{i}]" for i in range(len(rows)))
        + f"amix=inputs={len(rows)}:normalize=0,apad[a]"
    ]
    command += [
        "-filter_complex",
        ";".join(filters),
        "-map",
        "0:v",
        "-map",
        "[a]",
        "-c:v",
        "libx264",
        "-crf",
        "20",
        "-preset",
        "fast",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-b:a",
        "160k",
        "-shortest",
        "-movflags",
        "+faststart",
        str(OUT / "SkillSwap-demo.mp4"),
    ]
    with (OUT / "encoding.log").open("w") as log:
        subprocess.run(command, stdout=log, stderr=log, check=True)
    (OUT / "SkillSwap-demo.srt").write_text(
        "\n\n".join(
            f"{i + 1}\n{timestamp(row['start'])} --> {timestamp(row['start'] + row['duration'])}\n{row['text']}"
            for i, row in enumerate(rows)
        )
        + "\n"
    )
    print(OUT / "SkillSwap-demo.mp4")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["prepare", "render"])
    args = parser.parse_args()
    prepare() if args.action == "prepare" else render()
