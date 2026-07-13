"""
FAQ Bot Recipe — run.py

CLI entry point. Ask the Orbitly support bot a question:

    python run.py --question "How much does Orbitly cost?"
    python run.py --question "Can I import from Jira?" --name "Priya"

For help:
    python run.py --help
"""

import argparse
import os
import sys

# Reconfigure streams to support UTF-8 (for emojis) on Windows
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass




def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="faq-bot",
        description=(
            "🤖 CrewAI FAQ Bot Recipe — Orbitly Support Agent\n"
            "Answers customer questions from an in-memory knowledge base.\n\n"
            "Powered by NVIDIA NIM (default: Llama 3.1 8B; set LLM_MODEL for 70B)."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            '  python run.py --question "How much does Orbitly cost?"\n'
            '  python run.py --question "Do you offer refunds?" --name "Alex"\n'
            '  python run.py --question "What is your mobile app?"  '
            "# tests fallback\n"
        ),
    )
    parser.add_argument(
        "--question",
        required=True,
        help="The customer question to answer (wrap in quotes).",
    )
    parser.add_argument(
        "--name",
        default="there",
        help="Customer name for a personalised reply (default: 'there').",
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
    """Run the FAQ bot crew."""
    args = parse_args()

    preflight()

    from crew import build_crew

    question = args.question.strip()
    name = args.name.strip() or "there"

    if not question:
        print("❌  Error: --question cannot be empty.")
        sys.exit(1)

    print()
    print("🤖  Orbitly FAQ Bot — Starting")
    print(f"   Customer : {name}")
    print(f"   Question : {question}")
    print()
    print("─" * 60)
    print()

    crew = build_crew(question=question, customer_name=name)
    result = crew.kickoff()

    print()
    print("═" * 60)
    print("💬  SUPPORT REPLY")
    print("═" * 60)
    print(str(result))
    print("═" * 60)
    print()


if __name__ == "__main__":
    main()
