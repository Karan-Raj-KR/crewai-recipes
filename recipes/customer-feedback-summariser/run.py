"""
Customer Feedback Summariser Recipe — run.py

CLI entry point. Summarise customer feedback in one command:

    python run.py --feedback "Checkout is easy but the payment page is slow."

For JSON output:
    python run.py --feedback "..." --json

For help:
    python run.py --help
"""

import argparse
import json
import os
import sys

# Reconfigure streams to support UTF-8 (for emojis) on Windows
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

# Input bounds checked at the CLI boundary (before any LLM call).
MIN_FEEDBACK_CHARS = 20
MAX_FEEDBACK_CHARS = 8_000


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="customer-feedback-summariser",
        description=(
            "💬 CrewAI Customer Feedback Summariser Recipe\n"
            "Runs a two-agent crew (Feedback Analyst + Action Summariser) to\n"
            "extract themes, classify sentiment, and generate action items from\n"
            "raw customer feedback.\n\n"
            "Powered by NVIDIA NIM (default: Llama 3.1 8B; set LLM_MODEL for 70B)."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            '  python run.py --feedback "Checkout is easy to use, but the payment page is slow."\n\n'
            "  python run.py \\\n"
            '    --feedback "Login is confusing. I had to reset my password twice." \\\n'
            "    --json\n"
        ),
    )
    parser.add_argument(
        "--feedback",
        required=True,
        help=(
            "Raw customer feedback text to analyse. "
            "Can be a single review, a batch of responses separated by newlines, "
            "or any free-form text."
        ),
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose CrewAI execution trace.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output the result as structured JSON only.",
    )
    return parser.parse_args()


def preflight(json_output: bool = False) -> None:
    """Validate environment before running the crew."""
    if not os.getenv("CREWAI_RECIPES_SKIP_DOTENV"):
        from dotenv import load_dotenv

        load_dotenv()

    if not os.getenv("LLM_API_KEY") and not os.getenv("NVIDIA_API_KEY"):
        if json_output:
            print(json.dumps({"error": "LLM_API_KEY is not set."}))
        else:
            print("❌  LLM_API_KEY is not set.")
            print("   1. Copy .env.example → .env")
            print("   2. Add your key: LLM_API_KEY=nvapi-...")
            print("   3. Get a free key at https://build.nvidia.com/")
        sys.exit(1)


def main() -> None:
    """Run the customer feedback summariser crew."""
    args = parse_args()

    preflight(json_output=args.json)

    from crew import build_crew

    feedback = args.feedback.strip()

    if not feedback:
        if args.json:
            print(json.dumps({"error": "--feedback cannot be empty."}))
        else:
            print("❌  Error: --feedback cannot be empty.")
        sys.exit(1)

    if len(feedback) < MIN_FEEDBACK_CHARS:
        msg = (
            f"--feedback is too short ({len(feedback)} chars; "
            f"need at least {MIN_FEEDBACK_CHARS}). "
            "Please provide enough text for a meaningful analysis."
        )
        if args.json:
            print(json.dumps({"error": msg}))
        else:
            print(f"❌  {msg}")
        sys.exit(1)

    if len(feedback) > MAX_FEEDBACK_CHARS:
        msg = (
            f"--feedback is too long ({len(feedback)} chars; "
            f"max {MAX_FEEDBACK_CHARS}). "
            "Please summarise or split the feedback before passing it in."
        )
        if args.json:
            print(json.dumps({"error": msg}))
        else:
            print(f"❌  {msg}")
        sys.exit(1)

    if not args.json:
        print()
        print("💬  Customer Feedback Summariser — Starting")
        print(f"   Feedback: {feedback[:80]}{'...' if len(feedback) > 80 else ''}")
        print()
        print("─" * 60)
        print()

    try:
        crew = build_crew(
            feedback=feedback,
            verbose=args.verbose,
            json_output=args.json,
        )
        result = crew.kickoff()

        if args.json:
            print(json.dumps({"raw_output": str(result)}))
        else:
            print()
            print("═" * 60)
            print("📋  FEEDBACK SUMMARY")
            print("═" * 60)
            print(str(result))
            print("═" * 60)
            print()
    except Exception as e:
        if args.json:
            print(json.dumps({"error": str(e)}))
            sys.exit(1)
        else:
            raise


if __name__ == "__main__":
    main()
