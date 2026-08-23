"""tasks.py — Task definitions for the pr-review-assistant recipe.

Defines the task pipeline:
  1. Diff Analysis Task
  2. Correctness & Bug Detection Task
  3. Style & Convention Audit Task
  4. Final PR Review Comment Consolidation Task
"""

from crewai import Task


def create_diff_analysis_task(
    analyst_agent,
    repo: str,
    pr_number: str,
    pr_title: str,
    raw_diff: str,
) -> Task:
    """Create diff analysis task."""
    return Task(
        description=(
            f"Target PR: #{pr_number} in {repo}\n"
            f"PR Title: '{pr_title}'\n\n"
            f"Unified Git Diff:\n```diff\n{raw_diff}\n```\n\n"
            "Analyze the unified diff above. Map out all modified files, added/deleted functions, "
            "and provide a high-level summary of what this PR changes."
        ),
        expected_output=(
            "A structured summary of PR changes broken down by file, highlighting modified functions, "
            "additions, deletions, and architectural scope."
        ),
        agent=analyst_agent,
    )


def create_correctness_review_task(
    reviewer_agent,
    repo: str,
    pr_number: str,
    analysis_task: Task,
) -> Task:
    """Create code correctness review task."""
    return Task(
        description=(
            f"Target PR: #{pr_number} in {repo}\n\n"
            "Review the diff analysis from the previous step. Evaluate code correctness, looking for:\n"
            "- Potential runtime bugs or unhandled exception cases.\n"
            "- Logic flaws or edge cases (e.g. boundary conditions, empty collections).\n"
            "- Missing input validation or missing unit tests.\n\n"
            "For each finding, specify the target file path, line/hunk reference, severity (critical/warning/info), "
            "and a clear technical explanation."
        ),
        expected_output=(
            "A list of correctness findings categorized by severity and file path, with specific explanations "
            "and suggested fixes."
        ),
        agent=reviewer_agent,
        context=[analysis_task],
    )


def create_style_review_task(
    style_agent,
    repo: str,
    pr_number: str,
    analysis_task: Task,
) -> Task:
    """Create style & convention review task."""
    return Task(
        description=(
            f"Target PR: #{pr_number} in {repo}\n\n"
            "Review the diff analysis. Evaluate code style and conventions:\n"
            "- Naming consistency and readability.\n"
            "- Type annotations and docstring completeness.\n"
            "- Dead code, unnecessary complexity, or refactoring opportunities.\n\n"
            "Format findings by file path with actionable suggestions."
        ),
        expected_output=(
            "A list of code style and convention findings with clear suggestions for improvement."
        ),
        agent=style_agent,
        context=[analysis_task],
    )


def create_summary_task(
    summarizer_agent,
    repo: str,
    pr_number: str,
    pr_title: str,
    correctness_task: Task,
    style_task: Task,
) -> Task:
    """Create summary consolidation task to produce the final Markdown review comment."""
    return Task(
        description=(
            f"Target PR: #{pr_number} in {repo}\n"
            f"PR Title: '{pr_title}'\n\n"
            "Consolidate the correctness findings and style findings into a professional, "
            "GitHub-flavored Markdown PR review comment.\n\n"
            "Structure the Markdown output as follows:\n"
            "## 🔍 Pull Request Review: #{pr_number}\n"
            "**Title:** {pr_title}\n\n"
            "### 📋 Overview\n"
            "[Concise 2-3 sentence summary]\n\n"
            "### ⚠️ Correctness & Bugs\n"
            "[Bullet points with file references, severity badges, and code suggestions]\n\n"
            "### 🎨 Style & Conventions\n"
            "[Bullet points for readability and formatting]\n\n"
            "### 💡 Overall Recommendation\n"
            "[Final verdict: Approve, Request Changes, or Comment]"
        ),
        expected_output=(
            "A complete, formatted Markdown PR review comment ready to copy-paste onto GitHub."
        ),
        agent=summarizer_agent,
        context=[correctness_task, style_task],
    )
