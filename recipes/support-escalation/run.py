"""
Support Escalation Recipe — run.py

CLI entry point for running the support ticket escalation workflow recipe.

Usage:
    python run.py --ticket_text "How do I download my monthly billing invoice PDF?" --customer_tier "pro"
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
    """Parse CLI arguments and run the support ticket escalation crew."""
    parser = argparse.ArgumentParser(
        description="Run Support Ticket Escalation Recipe with NVIDIA NIM"
    )
    parser.add_argument(
        "--ticket_text",
        "--ticket-text",
        "--ticket",
        dest="ticket_text",
        type=str,
        default="Our custom SAML SSO integration is failing with HTTP 500 errors after key rotation.",
        help="Support ticket issue description",
    )
    parser.add_argument(
        "--customer_tier",
        "--customer-tier",
        dest="customer_tier",
        type=str,
        choices=["free", "pro", "enterprise"],
        default="enterprise",
        help="Customer account tier (free / pro / enterprise)",
    )
    parser.add_argument(
        "--previous_contacts",
        "--previous-contacts",
        dest="previous_contacts",
        type=str,
        default="2",
        help="Number of previous contact attempts",
    )

    args = parser.parse_args()
    check_env()

    print("\n🎧  Support Ticket Workflow — Processing Ticket\n")
    print(f"   Ticket Text       : {args.ticket_text}")
    print(f"   Customer Tier     : {args.customer_tier}")
    print(f"   Previous Contacts : {args.previous_contacts}\n")
    print("─" * 60)

    crew = build_crew(
        ticket_text=args.ticket_text,
        customer_tier=args.customer_tier,
        previous_contacts=args.previous_contacts,
    )
    result = crew.kickoff()

    print("\n" + "═" * 60)
    print("📋  SUPPORT TICKET WORKFLOW OUTCOME")
    print("═" * 60)
    print(result)
    print("═" * 60 + "\n")


if __name__ == "__main__":
    main()
