"""
WhatsApp Action Sim Recipe — run.py

CLI entry point for running the WhatsApp action simulation recipe.

Usage:
    python run.py --user_message "Where is my order 12345?" --sender_name "Ravi"
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
    """Parse CLI arguments and run the WhatsApp action simulation crew."""
    check_env()

    parser = argparse.ArgumentParser(
        description="Run WhatsApp Action Simulation Recipe with NVIDIA NIM"
    )
    parser.add_argument(
        "--user_message",
        "--user-message",
        "--message",
        dest="user_message",
        type=str,
        default="Hey! Where's my order? It's been 3 days now 😤",
        help="Incoming WhatsApp message text to process",
    )
    parser.add_argument(
        "--sender_name",
        "--sender-name",
        dest="sender_name",
        type=str,
        default="Ravi",
        help="Sender display name",
    )

    args = parser.parse_args()

    print("\n📱  WhatsApp Action Sim — Processing Message\n")
    print(f"   From    : {args.sender_name}")
    print(f"   Message : {args.user_message}\n")
    print("─" * 60)

    crew = build_crew(user_message=args.user_message, sender_name=args.sender_name)
    result = crew.kickoff()

    print("\n" + "═" * 60)
    print("📤  WHATSAPP REPLY")
    print("═" * 60)
    print(result)
    print("═" * 60 + "\n")


if __name__ == "__main__":
    main()
