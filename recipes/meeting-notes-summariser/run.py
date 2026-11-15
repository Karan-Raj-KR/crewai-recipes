"""
Meeting Notes Summariser Recipe — run.py

CLI entry point for running the recipe.

Usage:
    python run.py --transcript path/to/notes.md
    python run.py --transcript path/to/notes.md --json
"""

import argparse
import os
import sys
from pathlib import Path
from crew import build_crew  # noqa: E402
from models import MeetingNotesResult  # noqa: E402

from dotenv import load_dotenv

load_dotenv()


def check_env() -> None:
    """Preflight environment check for required API key."""
    api_key = os.getenv("LLM_API_KEY") or os.getenv("NVIDIA_API_KEY")
    if not api_key:
        print("❌ Error: Missing API key.", file=sys.stderr)
        print(
            "   Please set LLM_API_KEY or NVIDIA_API_KEY in your .env file or environment.",
            file=sys.stderr,
        )
        print("   Get a free key at https://build.nvidia.com", file=sys.stderr)
        sys.exit(1)


def read_transcript(path_str: str) -> str:
    """Read the transcript file, exiting with a clear message on failure."""
    path = Path(path_str)
    if not path.is_file():
        print(f"❌ Error: transcript file not found: {path}", file=sys.stderr)
        sys.exit(1)
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        print(f"❌ Error: could not read {path}: {exc}", file=sys.stderr)
        sys.exit(1)
    if not text.strip():
        print(f"❌ Error: transcript file is empty: {path}", file=sys.stderr)
        sys.exit(1)
    return text


def format_markdown(result: MeetingNotesResult) -> str:
    """Render the combined result as human-readable markdown."""
    s, e = result.summary, result.email
    lines: list[str] = ["# Meeting Summary", ""]

    def section(title: str, items: list[str]) -> None:
        lines.append(f"## {title}")
        lines.extend(f"- {i}" for i in items) if items else lines.append("_None_")
        lines.append("")

    section("Decisions", s.decisions)

    lines.append("## Action Items")
    if s.action_items:
        for a in s.action_items:
            owner = a.owner or "TBD"
            due = a.due_date or "TBD"
            lines.append(f"- {a.task} — **Owner:** {owner} | **Due:** {due}")
    else:
        lines.append("_None_")
    lines.append("")

    section("Risks & Blockers", s.risks_blockers)
    section("Open Questions", s.open_questions)

    lines += [
        "---",
        "",
        "# Follow-up Email Draft",
        "",
        f"**Subject:** {e.subject}",
        "",
        e.body,
    ]
    return "\n".join(lines)


def main() -> None:
    """Parse CLI arguments and run the crew."""
    parser = argparse.ArgumentParser(
        description=(
            "Turn meeting notes into decisions, action items, and a "
            "follow-up email draft."
        )
    )
    parser.add_argument(
        "--transcript",
        type=str,
        required=True,
        help="Path to the meeting transcript / notes file (e.g. notes.md)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print a validated JSON object instead of markdown",
    )

    args = parser.parse_args()
    check_env()
    transcript = read_transcript(args.transcript)

    # In --json mode stdout must contain only the JSON. Keep a private handle on
    # the real stdout, then point file descriptor 1 at stderr so everything else
    # (our banner, CrewAI's verbose logs, its "Tracing Status" panel) lands on
    # stderr. Redirecting the fd, not just sys.stdout, also catches output that
    # bypasses Python's sys.stdout.
    json_out = None
    if args.json:
        sys.stdout.flush()
        json_out = os.fdopen(os.dup(1), "w", encoding="utf-8")
        os.dup2(2, 1)

    print("\n🚀  Meeting Notes Summariser — Processing Input\n")
    print(f"   Transcript: {args.transcript} ({len(transcript.split())} words)\n")
    print("─" * 60)

    crew = build_crew(transcript=transcript)
    crew.kickoff()

    # kickoff() returns only the last task's output, so read each task directly.
    extract_task, draft_task = crew.tasks
    summary = extract_task.output.pydantic if extract_task.output else None
    email = draft_task.output.pydantic if draft_task.output else None

    if summary is None or email is None:
        print(
            "❌ Error: the model's output could not be parsed into the expected "
            "structure. Raw output follows:",
            file=sys.stderr,
        )
        for name, task in (("extractor", extract_task), ("drafter", draft_task)):
            raw = task.output.raw if task.output else "(no output)"
            print(f"\n--- {name} ---\n{raw}", file=sys.stderr)
        sys.exit(1)

    result = MeetingNotesResult(summary=summary, email=email)

    if json_out is not None:
        print(result.model_dump_json(indent=2), file=json_out, flush=True)
        json_out.close()
    else:
        print("\n" + "═" * 60)
        print("📋 RESULT")
        print("═" * 60)
        print(format_markdown(result))
        print("═" * 60 + "\n")


if __name__ == "__main__":
    main()