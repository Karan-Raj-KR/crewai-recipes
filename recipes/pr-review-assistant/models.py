"""Pydantic data models for the pr-review-assistant recipe."""

from pydantic import BaseModel, Field


class ReviewFinding(BaseModel):
    """Represents a specific finding or suggestion in the code review."""

    file_path: str = Field(description="Target file path in the pull request.")
    line_range: str | None = Field(
        default="N/A", description="Affected line range or section."
    )
    category: str = Field(
        description="Finding category: 'bug', 'edge_case', 'style', 'testing', 'security', or 'architecture'."
    )
    severity: str = Field(
        description="Severity level: 'critical', 'warning', or 'info'."
    )
    comment: str = Field(
        description="Detailed explanation and recommended improvement."
    )


class PRReviewOutput(BaseModel):
    """Complete structured PR review output model."""

    repo: str = Field(description="GitHub repository in owner/name format.")
    pr_number: str = Field(description="Pull Request ID or number.")
    pr_title: str | None = Field(
        default="Pull Request Review", description="Title of the pull request."
    )
    summary: str = Field(description="High-level summary of PR changes.")
    findings: list[ReviewFinding] = Field(
        default_factory=list, description="List of specific code review findings."
    )
    markdown_comment: str = Field(
        description="Formatted Markdown review comment ready for human copy-paste onto GitHub."
    )
