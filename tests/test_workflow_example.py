"""Tests for CI workflow examples and integration docs."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_pr_review_workflow_example_structure():
    workflow_path = ROOT / "examples" / "github-actions" / "pr-review-workflow.yml"
    assert workflow_path.exists(), (
        "examples/github-actions/pr-review-workflow.yml must exist"
    )

    content = workflow_path.read_text(encoding="utf-8")
    assert "name: Automated PR Review" in content
    assert "pull_request:" in content
    assert "pull-requests: write" in content
    assert "LLM_API_KEY" in content
    assert "recipes/pr-review-assistant" in content


def test_github_actions_integration_doc():
    doc_path = ROOT / "docs" / "github-actions-integration.md"
    assert doc_path.exists(), "docs/github-actions-integration.md must exist"

    text = doc_path.read_text(encoding="utf-8")
    assert text.startswith("# GitHub Actions Integration Guide")
    assert "LLM_API_KEY" in text
    assert "pull-requests: write" in text
    assert "pr-review-assistant" in text
