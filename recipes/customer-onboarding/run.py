"""
Customer Onboarding Recipe — run.py

CLI entry point for running the customer onboarding workflow recipe.

Usage:
    python run.py --customer_name "Alice Smith" --company "Acme SaaS" --role "VP of Engineering" \
                  --use_case "Automating CI/CD deployment pipelines" --team_size "30"
    python run.py --json
"""

import argparse
import json
import os
import sys

if not os.getenv("CREWAI_RECIPES_SKIP_DOTENV"):
    from dotenv import load_dotenv

    load_dotenv()

# Reconfigure streams to support UTF-8 on Windows
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

from crew import build_crew


def check_env(json_output: bool = False) -> None:
    """Preflight environment check for required API key."""
    api_key = os.getenv("LLM_API_KEY") or os.getenv("NVIDIA_API_KEY")
    if not api_key:
        if json_output:
            print(json.dumps({"error": "LLM_API_KEY is not set."}))
        else:
            print("❌ Error: Missing API key.", file=sys.stderr)
            print(
                "   Please set LLM_API_KEY or NVIDIA_API_KEY in your .env file or environment.",
                file=sys.stderr,
            )
            print("   Get a free key at https://build.nvidia.com", file=sys.stderr)
        sys.exit(1)


def format_json_output(result: object) -> str:
    """Format the CrewAI execution result as a clean, machine-readable JSON string."""
    from pydantic import BaseModel

    if isinstance(result, BaseModel):
        return result.model_dump_json(indent=2)

    pydantic_val = getattr(result, "pydantic", None)
    if isinstance(pydantic_val, BaseModel):
        return pydantic_val.model_dump_json(indent=2)

    json_dict = getattr(result, "json_dict", None)
    if isinstance(json_dict, dict) and json_dict:
        return json.dumps(json_dict, indent=2)

    raw_json = getattr(result, "json", None)
    if isinstance(raw_json, str) and raw_json.strip():
        try:
            parsed = json.loads(raw_json)
            return json.dumps(parsed, indent=2)
        except (json.JSONDecodeError, TypeError):
            pass

    if isinstance(result, dict):
        return json.dumps(result, indent=2)

    raw_str = getattr(result, "raw", None)
    if not isinstance(raw_str, str):
        raw_str = str(result)

    if isinstance(raw_str, str):
        clean_str = raw_str.strip()
        if clean_str.startswith("```"):
            lines = clean_str.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            clean_str = "\n".join(lines).strip()
        try:
            parsed = json.loads(clean_str)
            return json.dumps(parsed, indent=2)
        except (json.JSONDecodeError, TypeError):
            pass

    fallback_text = raw_str if isinstance(raw_str, str) else str(result)
    return json.dumps({"raw_output": fallback_text}, indent=2)


def main() -> None:
    """Parse CLI arguments and run the customer onboarding crew."""
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
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output the result as JSON only.",
    )

    args = parser.parse_args()
    check_env(json_output=args.json)

    if not args.json:
        print("\n🚀  Customer Onboarding Workflow — Processing Signup\n")
        print(f"   Customer Name : {args.customer_name}")
        print(f"   Company       : {args.company}")
        print(f"   Role          : {args.role}")
        print(f"   Use Case      : {args.use_case}")
        print(f"   Team Size     : {args.team_size}\n")
        print("─" * 60)

    try:
        crew = build_crew(
            customer_name=args.customer_name,
            company=args.company,
            role=args.role,
            use_case=args.use_case,
            team_size=args.team_size,
            json_output=args.json,
        )
        result = crew.kickoff()

        if args.json:
            print(format_json_output(result))
        else:
            print("\n" + "═" * 60)
            print("📧  ONBOARDING EMAIL OUTPUT")
            print("═" * 60)
            print(result)
            print("═" * 60 + "\n")
    except Exception as e:
        if args.json:
            print(json.dumps({"error": str(e)}))
            sys.exit(1)
        else:
            raise


if __name__ == "__main__":
    main()
