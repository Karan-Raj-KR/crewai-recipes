"""Tests for root Makefile targets and syntax."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_makefile_exists_and_defines_standard_targets():
    makefile = ROOT / "Makefile"
    assert makefile.exists(), "Root Makefile must exist"

    content = makefile.read_text(encoding="utf-8")
    assert ".DEFAULT_GOAL := help" in content
    assert "lint:" in content
    assert "format:" in content
    assert "test:" in content
    assert "sync-llm:" in content
    assert "playground:" in content
    assert "check:" in content


def test_makefile_lint_target_matches_ci():
    makefile = ROOT / "Makefile"
    content = makefile.read_text(encoding="utf-8")
    # Must mirror .github/workflows/ci.yml
    assert "ruff check recipes/ playground/ tools/ tests/" in content
    assert "ruff format --check recipes/ playground/ tools/ tests/" in content
