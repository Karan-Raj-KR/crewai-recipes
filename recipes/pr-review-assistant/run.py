"""run.py — CLI entry point for the pr-review-assistant recipe.

Usage:
    python run.py --repo Karan-Raj-KR/crewai-recipes --pr 187 --pretty
    python run.py --repo owner/repo --pr 123 --json-out review.json
"""

import argparse
import json
import os
import sys
from pathlib import Path

from crew import build_crew
from github_client import validate_repo
from llm import get_llm
from models import PRReviewOutput


def parse_args():
    parser = argparse.ArgumentParser(
        description="PR Review Assistant — Fetch GitHub PR diffs and generate structured Markdown review comments."
    )
    parser.add_argument(
        "--repo",
        type=str,
        required=True,
        help="GitHub repository in 'owner/name' format (e.g. 'Karan-Raj-KR/crewai-recipes').",
    )
    parser.add_argument(
        "--pr",
        type=str,
        required=True,
        help="Pull request ID or number (e.g. '187').",
    )
    parser.add_argument(
        "--token",
        type=str,
        default=None,
        help="Optional GitHub token for higher rate limits (defaults to GITHUB_TOKEN env var).",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Format output nicely for human reading.",
    )
    parser.add_argument(
        "--json-out",
        type=str,
        help="Optional path to write output JSON.",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    try:
        owner, repo_name = validate_repo(args.repo)
        clean_repo = f"{owner}/{repo_name}"
    except ValueError as e:
        print(f"Validation Error: {e}", file=sys.stderr)
        sys.exit(1)

    clean_pr_id = str(args.pr).strip().lstrip("#")
    github_token = args.token or os.getenv("GITHUB_TOKEN")

    try:
        llm = get_llm()
    except OSError as e:
        print(f"Environment Error: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"🔍 Fetching diff and reviewing PR #{clean_pr_id} in {clean_repo}...")

    try:
        crew = build_crew(
            repo=clean_repo,
            pr_number=clean_pr_id,
            github_token=github_token,
            llm=llm,
        )
        result = crew.kickoff()
        markdown_comment = str(result.raw).strip()
    except (RuntimeError, ValueError, OSError) as e:
        print(f"Error during PR review execution: {e}", file=sys.stderr)
        sys.exit(1)

    output_obj = PRReviewOutput(
        repo=clean_repo,
        pr_number=clean_pr_id,
        pr_title=f"Pull Request #{clean_pr_id}",
        summary=f"Automated PR review for {clean_repo}#{clean_pr_id}.",
        findings=[],
        markdown_comment=markdown_comment,
    )

    if args.pretty:
        print("\n" + "=" * 60)
        print("GENERATED PR REVIEW COMMENT (Output Only — Copy-Paste to GitHub)")
        print("=" * 60)
        print(markdown_comment)
    else:
        print(json.dumps(output_obj.model_dump(), indent=2))

    if args.json_out:
        out_path = Path(args.json_out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(
            json.dumps(output_obj.model_dump(), indent=2), encoding="utf-8"
        )
        print(f"\nSaved output JSON to: {out_path}")


if __name__ == "__main__":
    main()
