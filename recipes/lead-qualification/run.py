"""
Lead Qualification Recipe — run.py

CLI entry point. Qualify a company lead in one command:

    python run.py --company "Acme Corp" --description "A 40-person B2B SaaS startup..."

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
        prog="lead-qualification",
        description=(
            "🎯 CrewAI Lead Qualification Recipe\n"
            "Runs a two-agent crew (Researcher + Scorer) to qualify a company\n"
            "against B2B SaaS ICP criteria and return a 0-100 score.\n\n"
            "Powered by NVIDIA NIM (default: Llama 3.1 8B; set LLM_MODEL for 70B)."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            '  python run.py --company "Notion" \\\n'
            '    --description "A Series C note-taking and wiki tool used by\n'
            '     50,000+ teams. Heavily adopted in SMB and mid-market.\\n"\n'
        ),
    )
    parser.add_argument(
        "--company",
        required=True,
        help="Company name to qualify (e.g. 'Acme SaaS')",
    )
    parser.add_argument(
        "--description",
        required=True,
        help=(
            "Short description of the company — industry, size, product, "
            "and any context you have. More detail = better score."
        ),
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
    """Run the lead qualification crew."""
    args = parse_args()

    preflight()

    from crew import build_crew

    company = args.company.strip()
    description = args.description.strip()

    if not company or not description:
        print("❌  Error: --company and --description cannot be empty.")
        sys.exit(1)

    print()
    print("🎯  Lead Qualification Crew — Starting")
    print(f"   Company    : {company}")
    print(f"   Description: {description[:80]}{'...' if len(description) > 80 else ''}")
    print()
    print("─" * 60)
    print()

    crew = build_crew(company=company, description=description)
    result = crew.kickoff()

    print()
    print("═" * 60)
    print("📊  QUALIFICATION RESULT")
    print("═" * 60)
    # CrewAI returns a CrewOutput object — convert to string for display
    print(str(result))
    print("═" * 60)
    print()


if __name__ == "__main__":
    main()
