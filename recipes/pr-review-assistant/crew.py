"""crew.py — Crew assembly for the pr-review-assistant recipe."""

import os

from agents import (
    create_code_reviewer_agent,
    create_diff_analyst_agent,
    create_style_reviewer_agent,
    create_summarizer_agent,
)
from crewai import Crew, Process
from github_client import fetch_pr_diff, validate_repo
from llm import get_llm
from tasks import (
    create_correctness_review_task,
    create_diff_analysis_task,
    create_style_review_task,
    create_summary_task,
)


def build_crew(
    repo: str,
    pr_number: int | str,
    github_token: str | None = None,
    raw_diff: str | None = None,
    pr_title: str | None = None,
    llm: object | None = None,
) -> Crew:
    """Build and configure the pr-review-assistant Crew.

    Args:
        repo: GitHub repository in 'owner/name' format (e.g. 'Karan-Raj-KR/crewai-recipes').
        pr_number: Pull request number or ID.
        github_token: Optional GitHub personal access token (defaults to GITHUB_TOKEN env var).
        raw_diff: Optional pre-fetched diff string (used for offline testing/stubbing).
        pr_title: Optional PR title.
        llm: Optional pre-configured LLM instance.

    Returns:
        Configured Crew instance ready for kickoff().
    """
    if llm is None:
        llm = get_llm()

    owner, repo_name = validate_repo(repo)
    clean_repo = f"{owner}/{repo_name}"
    clean_pr_id = str(pr_number).strip().lstrip("#")

    if github_token is None:
        github_token = os.getenv("GITHUB_TOKEN")

    if raw_diff is None:
        meta, raw_diff = fetch_pr_diff(
            clean_repo, clean_pr_id, github_token=github_token
        )
        pr_title = meta.get("title", f"Pull Request #{clean_pr_id}")
    elif pr_title is None:
        pr_title = f"Pull Request #{clean_pr_id}"

    diff_analyst = create_diff_analyst_agent(llm=llm)
    code_reviewer = create_code_reviewer_agent(llm=llm)
    style_reviewer = create_style_reviewer_agent(llm=llm)
    summarizer = create_summarizer_agent(llm=llm)

    analysis_task = create_diff_analysis_task(
        analyst_agent=diff_analyst,
        repo=clean_repo,
        pr_number=clean_pr_id,
        pr_title=pr_title,
        raw_diff=raw_diff,
    )

    correctness_task = create_correctness_review_task(
        reviewer_agent=code_reviewer,
        repo=clean_repo,
        pr_number=clean_pr_id,
        analysis_task=analysis_task,
    )

    style_task = create_style_review_task(
        style_agent=style_reviewer,
        repo=clean_repo,
        pr_number=clean_pr_id,
        analysis_task=analysis_task,
    )

    summary_task = create_summary_task(
        summarizer_agent=summarizer,
        repo=clean_repo,
        pr_number=clean_pr_id,
        pr_title=pr_title,
        correctness_task=correctness_task,
        style_task=style_task,
    )

    return Crew(
        agents=[diff_analyst, code_reviewer, style_reviewer, summarizer],
        tasks=[analysis_task, correctness_task, style_task, summary_task],
        process=Process.sequential,
        verbose=True,
    )
