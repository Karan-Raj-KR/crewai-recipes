"""
Template Recipe — run.py

CLI entry point for running your recipe.

Usage:
    python run.py --your-param "value"

TODO: Replace the argparse arguments with your recipe's inputs.
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
    """Parse CLI arguments and run your crew."""
    parser = argparse.ArgumentParser(
        description="TODO: Update this description. Run your recipe with NVIDIA NIM"
    )

    # TODO: Replace these arguments with your recipe's inputs.
    # Make sure the argument names (dest) match the keys in inputs.json.
    parser.add_argument(
        "--your-param",
        type=str,
        default="default_value",
        help="TODO: Update this help text to describe your parameter",
    )

    args = parser.parse_args()
    check_env()

    print("\n🚀  Your Recipe — Processing Input\n")
    print(f"   Your Param: {args.your_param}\n")
    print("─" * 60)

    crew = build_crew(
        your_param=args.your_param,
    )
    result = crew.kickoff()

    print("\n" + "═" * 60)
    print("📋 RESULT")
    print("═" * 60)
    print(result)
    print("═" * 60 + "\n")


if __name__ == "__main__":
    main()
