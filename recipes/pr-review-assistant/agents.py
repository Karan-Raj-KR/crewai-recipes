"""agents.py — Agent definitions for the pr-review-assistant recipe.

Defines four specialized agents:
  1. Diff Analyst Agent: Reads raw unified diff and summarizes structural changes.
  2. Code Reviewer Agent: Evaluates logic correctness, bugs, edge cases, and test coverage.
  3. Style Reviewer Agent: Evaluates naming conventions, code style, formatting, and docstrings.
  4. PR Summarizer Agent: Merges all findings into a clean GitHub-ready Markdown comment.
"""

from crewai import Agent
from llm import get_llm


def create_diff_analyst_agent(llm=None) -> Agent:
    """Create the Diff Analyst Agent."""
    if llm is None:
        llm = get_llm()

    return Agent(
        role="Pull Request Diff Analyst",
        goal="Parse unified git diffs and summarize changed files, added/deleted code blocks, and intent.",
        backstory=(
            "You are a senior software architect specializing in code comprehension. You read git "
            "diffs quickly, mapping out modified files, functions, lines changed, and structural impact "
            "so downstream reviewer agents have a structured summary."
        ),
        llm=llm,
        verbose=True,
    )


def create_code_reviewer_agent(llm=None) -> Agent:
    """Create the Code Correctness Reviewer Agent."""
    if llm is None:
        llm = get_llm()

    return Agent(
        role="Code Correctness Specialist",
        goal="Identify potential logic bugs, unhandled edge cases, missing error handling, and test gaps.",
        backstory=(
            "You are a rigorous code reviewer with a deep eye for detail. You spot off-by-one errors, "
            "null pointer/attribute exceptions, unhandled promises/exceptions, race conditions, and "
            "missing assertions in unit tests. You format findings with specific file paths and line ranges."
        ),
        llm=llm,
        verbose=True,
    )


def create_style_reviewer_agent(llm=None) -> Agent:
    """Create the Code Style & Convention Reviewer Agent."""
    if llm is None:
        llm = get_llm()

    return Agent(
        role="Code Style & Conventions Auditor",
        goal="Enforce code quality standards, naming conventions, docstring completeness, and formatting.",
        backstory=(
            "You are an expert linter and style guide maintainer. You inspect code for variable naming "
            "clarity, type annotation completeness, dead code, verbose/confusing logic, and documentation "
            "quality without nitpicking trivial whitespace."
        ),
        llm=llm,
        verbose=True,
    )


def create_summarizer_agent(llm=None) -> Agent:
    """Create the PR Review Summarizer Agent."""
    if llm is None:
        llm = get_llm()

    return Agent(
        role="PR Review Comment Summarizer",
        goal="Consolidate all correctness and style review findings into a clean, professional Markdown PR comment.",
        backstory=(
            "You are a team tech lead who writes constructive, highly readable GitHub PR review comments. "
            "You organize feedback into clear sections (Summary, Correctness & Bugs, Style & Improvement, "
            "Verdict) with actionable suggestions and code snippets. Your output is ready to copy-paste directly onto GitHub."
        ),
        llm=llm,
        verbose=True,
    )
