"""
Customer Onboarding Recipe — run.py

CLI entry point for running the customer onboarding workflow recipe.

Usage:
    python run.py --customer_name "Alice Smith" --company "Acme SaaS" --role "VP of Engineering" \
                  --use_case "Automating CI/CD deployment pipelines" --team_size "30"
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
    """Parse CLI arguments and run the customer onboarding crew."""
    check_env()

    parser = argparse.ArgumentParser(
        description="Run Customer Onboarding Workflow Recipe with NVIDIA NIM"
    )
    parser.add_argument(
        "--customer_name",
        "--customer-name",
        "--name",
        dest="customer_name",
        type=str,
        default="Alice Smith",
        help="Customer's full name",
    )
    parser.add_argument(
        "--company",
        dest="company",
        type=str,
        default="TechCorp Solutions",
        help="Company name",
    )
    parser.add_argument(
        "--role",
        dest="role",
        type=str,
        default="Head of DevOps",
        help="Job role or title",
    )
    parser.add_argument(
        "--use_case",
        "--use-case",
        dest="use_case",
        type=str,
        default="Automating infrastructure provisioning and CI/CD pipelines",
        help="Primary use case or goal",
    )
    parser.add_argument(
        "--team_size",
        "--team-size",
        dest="team_size",
        type=str,
        default="25",
        help="Team size",
    )

    args = parser.parse_args()

    print("\n🚀  Customer Onboarding Workflow — Processing Signup\n")
    print(f"   Customer Name : {args.customer_name}")
    print(f"   Company       : {args.company}")
    print(f"   Role          : {args.role}")
    print(f"   Use Case      : {args.use_case}")
    print(f"   Team Size     : {args.team_size}\n")
    print("─" * 60)

    crew = build_crew(
        customer_name=args.customer_name,
        company=args.company,
        role=args.role,
        use_case=args.use_case,
        team_size=args.team_size,
    )
    result = crew.kickoff()

    print("\n" + "═" * 60)
    print("📧  ONBOARDING EMAIL OUTPUT")
    print("═" * 60)
    print(result)
    print("═" * 60 + "\n")


if __name__ == "__main__":
    main()
