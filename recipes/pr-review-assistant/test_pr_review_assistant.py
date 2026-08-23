import sys
import urllib.error
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

recipe_dir = Path(__file__).parent.resolve()
if str(recipe_dir) not in sys.path:
    sys.path.insert(0, str(recipe_dir))

try:
    import crewai  # noqa: F401
except ImportError:
    sys.modules["crewai"] = MagicMock()

from crew import build_crew
from github_client import fetch_pr_diff, validate_repo
from models import PRReviewOutput, ReviewFinding


@pytest.fixture
def sample_diff() -> str:
    diff_path = Path(__file__).parent / "tests" / "fixtures" / "sample_diff.diff"
    return diff_path.read_text(encoding="utf-8")


def test_validate_repo_valid():
    owner, repo = validate_repo("Karan-Raj-KR/crewai-recipes")
    assert owner == "Karan-Raj-KR"
    assert repo == "crewai-recipes"

    owner2, repo2 = validate_repo("octocat/Hello-World")
    assert owner2 == "octocat"
    assert repo2 == "Hello-World"


def test_validate_repo_invalid():
    invalid_inputs = [
        "../etc/passwd",
        "/absolute/path/repo",
        "C:\\path\\repo",
        "invalid_no_slash",
        "owner/repo/extra",
        "owner/repo; rm -rf /",
    ]
    for inp in invalid_inputs:
        with pytest.raises(ValueError, match="Invalid repository format"):
            validate_repo(inp)


def test_github_client_rate_limit_handling():
    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.side_effect = urllib.error.HTTPError(
            url="https://api.github.com",
            code=403,
            msg="Forbidden",
            hdrs={},
            fp=None,
        )
        with pytest.raises(RuntimeError, match="rate limit exceeded"):
            fetch_pr_diff("owner/repo", 1)


def test_github_client_not_found_handling():
    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.side_effect = urllib.error.HTTPError(
            url="https://api.github.com",
            code=404,
            msg="Not Found",
            hdrs={},
            fp=None,
        )
        with pytest.raises(RuntimeError, match="not found"):
            fetch_pr_diff("owner/repo", 99999)


def test_build_crew_offline_stubbed(sample_diff: str):
    llm_mock = MagicMock()
    crew = build_crew(
        repo="Karan-Raj-KR/crewai-recipes",
        pr_number="185",
        raw_diff=sample_diff,
        pr_title="Add PR Review Assistant Recipe",
        llm=llm_mock,
    )
    assert crew is not None


def test_models_instantiation():
    finding = ReviewFinding(
        file_path="src/utils.py",
        line_range="L10-L15",
        category="bug",
        severity="warning",
        comment="Potential zero division or incorrect return value on discount > 100",
    )
    assert finding.category == "bug"

    out = PRReviewOutput(
        repo="owner/repo",
        pr_number="123",
        summary="PR review summary",
        findings=[finding],
        markdown_comment="## Review\nGreat PR!",
    )
    assert out.pr_number == "123"
    assert len(out.findings) == 1
