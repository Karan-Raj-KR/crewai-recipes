"""
Content Pipeline Recipe — run.py

CLI entry point for running the content production pipeline recipe.

Usage:
    python run.py --topic "Autonomous AI Agents in Enterprise Software" \
                  --target_audience "Software Architects & CTOs" \
                  --keywords "AI Agents, Automation, CrewAI"
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
    """Parse CLI arguments and run the content production pipeline crew."""
    check_env()

    parser = argparse.ArgumentParser(
        description="Run Automated Content Production Pipeline Recipe with NVIDIA NIM"
    )
    parser.add_argument(
        "--topic",
        type=str,
        default="Autonomous AI Agents in Enterprise Software",
        help="Blog topic or theme",
    )
    parser.add_argument(
        "--target_audience",
        "--target-audience",
        "--audience",
        dest="target_audience",
        type=str,
        default="Software Architects & Tech Leaders",
        help="Target readership profile",
    )
    parser.add_argument(
        "--keywords",
        type=str,
        default="AI Agents, CrewAI, Workflow Automation",
        help="Comma-separated target keywords",
    )

    args = parser.parse_args()

    print("\n📝  Content Production Pipeline — Generating Article\n")
    print(f"   Topic           : {args.topic}")
    print(f"   Target Audience : {args.target_audience}")
    print(f"   Keywords        : {args.keywords}\n")
    print("─" * 60)

    crew = build_crew(
        topic=args.topic,
        target_audience=args.target_audience,
        keywords=args.keywords,
    )
    result = crew.kickoff()

    print("\n" + "═" * 60)
    print("✨  SEO REVIEW & FINAL POLISHED ARTICLE")
    print("═" * 60)
    print(result)
    print("═" * 60 + "\n")


if __name__ == "__main__":
    main()
