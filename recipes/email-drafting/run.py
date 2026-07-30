"""
Email Drafting Recipe — run.py

CLI entry point for running the email drafting recipe.

Usage:
    python run.py --recipient "Engineering Team" --purpose "Sprint Update" \
                  --key_points "Completed 95% of tasks, deployment on Thursday 2 PM" \
                  --tone "professional"
"""

import argparse
import os
import sys

from dotenv import load_dotenv

load_dotenv()

from crew import build_crew  # noqa: E402


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


def main() -> None:
    """Parse CLI arguments and run the email drafting crew."""
    check_env()

    parser = argparse.ArgumentParser(
        description="Run Email Drafting Recipe with NVIDIA NIM"
    )
    parser.add_argument(
        "--recipient",
        type=str,
        default="Engineering Team",
        help="Recipient name or role",
    )
    parser.add_argument(
        "--purpose",
        type=str,
        default="Weekly Sprint & Deployment Update",
        help="Email main purpose",
    )
    parser.add_argument(
        "--key_points",
        "--key-points",
        dest="key_points",
        type=str,
        default="Sprint completion reached 95%, production release scheduled for Thursday at 2:00 PM EST, no blocking security issues remaining",
        help="Key points to cover",
    )
    parser.add_argument(
        "--tone",
        type=str,
        choices=["professional", "friendly", "formal", "direct"],
        default="professional",
        help="Desired email tone (professional / friendly / formal / direct)",
    )

    args = parser.parse_args()

    print("\n📧  Email Drafting Workflow — Processing Brief\n")
    print(f"   Recipient  : {args.recipient}")
    print(f"   Purpose    : {args.purpose}")
    print(f"   Key Points : {args.key_points}")
    print(f"   Tone       : {args.tone}\n")
    print("─" * 60)

    crew = build_crew(
        recipient=args.recipient,
        purpose=args.purpose,
        key_points=args.key_points,
        tone=args.tone,
    )
    result = crew.kickoff()

    print("\n" + "═" * 60)
    print("✉️   POLISHED EMAIL & EDITORIAL NOTES")
    print("═" * 60)
    print(result)
    print("═" * 60 + "\n")


if __name__ == "__main__":
    main()
