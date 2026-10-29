"""Unit tests for run.py CLI validation."""

import json
import os
import sys
from unittest.mock import MagicMock, patch
import pytest

import run
from run import main, preflight

SCORECARD = (
    "**Total Score:** 69 / 100\n\n"
    "| Dimension | Score |\n"
    "|-----------|-------|\n"
    "| Industry Fit | 22 / 25 |\n"
)
DESCRIPTION = "A 40-person B2B SaaS company selling workflow automation to ops."


def _run_with_mocked_crew(monkeypatch: pytest.MonkeyPatch, *flags: str) -> None:
    """Run main() end to end with build_crew mocked to return SCORECARD."""
    monkeypatch.setenv("LLM_API_KEY", "test-key")
    monkeypatch.setenv("CREWAI_RECIPES_SKIP_DOTENV", "1")
    monkeypatch.delenv("FORCE_COLOR", raising=False)
    monkeypatch.delenv("TTY_COMPATIBLE", raising=False)
    crew = MagicMock()
    crew.kickoff.return_value = SCORECARD
    monkeypatch.setattr("crew.build_crew", lambda **kwargs: crew)
    monkeypatch.setattr(
        sys,
        "argv",
        ["run.py", "--company", "Acme", "--description", DESCRIPTION, *flags],
    )
    main()


def test_missing_args_exits(capsys: pytest.CaptureFixture[str]) -> None:
    """Test that missing required arguments raises SystemExit."""
    test_args = ["run.py"]
    with patch.object(sys, "argv", test_args):
        with pytest.raises(SystemExit) as exc:
            main()
        assert exc.value.code == 2
        captured = capsys.readouterr()
        assert (
            "the following arguments are required: --company, --description"
            in captured.err
        )


def test_whitespace_args_exits(capsys: pytest.CaptureFixture[str]) -> None:
    """Test that whitespace-only args are rejected by the custom check in main."""
    test_args = ["run.py", "--company", "   ", "--description", "   "]
    with patch.object(sys, "argv", test_args):
        # We need to bypass preflight key check to reach the validation
        env = {"LLM_API_KEY": "test-key"}
        with patch.dict(os.environ, env, clear=True):
            with pytest.raises(SystemExit) as exc:
                main()
            assert exc.value.code == 1
            captured = capsys.readouterr()
            assert "Error: --company and --description cannot be empty." in captured.out


def test_preflight_missing_key_exits(capsys: pytest.CaptureFixture[str]) -> None:
    """Test that preflight exits cleanly with instructions when no key is set."""
    env = {}
    with patch.dict(os.environ, env, clear=True):
        with pytest.raises(SystemExit) as exc:
            preflight()
        assert exc.value.code == 1
        captured = capsys.readouterr()
        assert "LLM_API_KEY is not set." in captured.out
        assert "Copy .env.example" in captured.out


def test_markdown_result_rendered_without_escape_codes(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Markdown is rendered, and captured (non-TTY) output has no ANSI codes."""
    _run_with_mocked_crew(monkeypatch)
    out = capsys.readouterr().out
    assert "QUALIFICATION RESULT" in out
    assert "Total Score:" in out
    assert "Industry Fit" in out
    assert "**" not in out
    assert "|---" not in out
    assert "\x1b" not in out


def test_json_output_stays_plain(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """--json stdout is a single JSON document with no Rich decoration."""
    _run_with_mocked_crew(monkeypatch, "--json")
    out = capsys.readouterr().out
    assert "\x1b" not in out
    assert json.loads(out) == {"company": "Acme", "raw_output": SCORECARD}


def test_falls_back_to_plain_print_without_rich(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Without rich installed, the result is printed as-is between banners."""
    monkeypatch.setattr(run, "Console", None)
    _run_with_mocked_crew(monkeypatch)
    out = capsys.readouterr().out
    assert "QUALIFICATION RESULT" in out
    assert "**Total Score:** 69 / 100" in out
    assert "═" * 60 in out
