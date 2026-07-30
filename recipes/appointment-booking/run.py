"""
Appointment Booking Recipe — run.py

CLI entry point. Process an appointment booking request:

    python run.py --name "Priya Sharma" --email "priya.sharma@example.com" \
        --meeting-type "Product Demo" \
        --preferred-times "Any morning slot this week"

For help:
    python run.py --help
"""

import argparse
import os
import sys

# Reconfigure streams to support UTF-8 (for emojis) on Windows
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        pass


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="appointment-booking",
        description=(
            "📅 CrewAI Appointment Booking Recipe\n"
            "Runs a three-agent crew (Intake → Availability → Confirmation) to process\n"
            "a booking request, match against available slots, and draft confirmation.\n\n"
            "Powered by NVIDIA NIM (default: Llama 3.1 8B; set LLM_MODEL for 70B)."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            '  python run.py --name "Priya Sharma" \\\n'
            '    --email "priya@example.com" \\\n'
            '    --meeting-type "Product Demo" \\\n'
            '    --preferred-times "Monday morning or Tuesday afternoon"\n'
        ),
    )
    parser.add_argument(
        "--name",
        required=True,
        help="Full name of the requester",
    )
    parser.add_argument(
        "--email",
        required=True,
        help="Email address of the requester",
    )
    parser.add_argument(
        "--meeting-type",
        dest="meeting_type",
        required=True,
        help="Type or topic of the meeting (e.g. 'Product Demo', '1-on-1 Consultation')",
    )
    parser.add_argument(
        "--preferred-times",
        dest="preferred_times",
        required=True,
        help="Stated preferences for meeting day/time",
    )
    parser.add_argument(
        "--notes",
        default="None",
        help="Optional additional context or special notes",
    )
    return parser.parse_args()


def preflight() -> None:
    """Validate environment before running the crew."""
    if not os.getenv("CREWAI_RECIPES_SKIP_DOTENV"):
        from dotenv import load_dotenv

        load_dotenv()

    if not os.getenv("LLM_API_KEY") and not os.getenv("NVIDIA_API_KEY"):
        print("❌  LLM_API_KEY is not set.")
        print("   1. Copy .env.example → .env")
        print("   2. Add your key: LLM_API_KEY=your-key-here")
        print("   3. Get a free key at https://build.nvidia.com/")
        sys.exit(1)


def main() -> None:
    """Run the appointment booking crew."""
    args = parse_args()

    preflight()

    from crew import build_crew

    name = args.name.strip()
    email = args.email.strip()
    meeting_type = args.meeting_type.strip()
    preferred_times = args.preferred_times.strip()
    notes = args.notes.strip() if args.notes else "None"

    if not name or not email or not meeting_type or not preferred_times:
        print(
            "❌  Error: --name, --email, --meeting-type, and --preferred-times cannot be empty."
        )
        sys.exit(1)

    print()
    print("📅  Appointment Booking Crew — Starting")
    print(f"   Requester : {name} ({email})")
    print(f"   Meeting   : {meeting_type}")
    print(f"   Preferred : {preferred_times}")
    print(f"   Notes     : {notes}")
    print()
    print("─" * 60)
    print()

    crew = build_crew(
        name=name,
        email=email,
        meeting_type=meeting_type,
        preferred_times=preferred_times,
        notes=notes,
    )
    result = crew.kickoff()

    print()
    print("═" * 60)
    print("📨  CONFIRMATION EMAIL DRAFT")
    print("═" * 60)
    print(str(result))
    print("═" * 60)
    print()


if __name__ == "__main__":
    main()
