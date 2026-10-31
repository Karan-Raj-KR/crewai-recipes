"""Smoke test: main() runs without errors and build_crew signature is correct."""

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

os.environ.setdefault("LLM_API_KEY", "nvapi-test")
sys.path.insert(0, str(Path(__file__).parent))

import main as recipe_main  # noqa: E402
import run as recipe_run  # noqa: E402
from knowledge_base import FAQ_KNOWLEDGE_BASE, get_knowledge_base_text  # noqa: E402
from crew import build_crew  # noqa: E402
from crewai import Process  # noqa: E402

REPLY = "Hi Priya,\n\nThe **Team** plan is $29/month per user.\n\n- Unlimited projects"


def _run_cli_with_mocked_crew(monkeypatch: pytest.MonkeyPatch) -> None:
    """Run run.main() end to end with build_crew mocked to return REPLY."""
    monkeypatch.setenv("CREWAI_RECIPES_SKIP_DOTENV", "1")
    monkeypatch.delenv("FORCE_COLOR", raising=False)
    monkeypatch.delenv("TTY_COMPATIBLE", raising=False)
    crew = MagicMock()
    crew.kickoff.return_value = REPLY
    monkeypatch.setattr("crew.build_crew", lambda **kwargs: crew)
    monkeypatch.setattr(sys, "argv", ["run.py", "--question", "How much is it?"])
    recipe_run.main()


def test_main_runs() -> None:
    mock_output = MagicMock()
    mock_output.__str__ = lambda self: (
        "Hi Rahul, yes — we offer a free 21-day trial, no credit card required!\n\n"
        "Is there anything else I can help with?"
    )
    with patch("crewai.Crew.kickoff", return_value=mock_output):
        recipe_main.main()


def test_run_renders_markdown_without_escape_codes(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Markdown is rendered, and captured (non-TTY) output has no ANSI codes."""
    _run_cli_with_mocked_crew(monkeypatch)
    out = capsys.readouterr().out
    assert "SUPPORT REPLY" in out
    assert "Team" in out
    assert "**" not in out
    assert "\x1b" not in out


def test_run_falls_back_to_plain_print_without_rich(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Without rich installed, the reply is printed as-is between banners."""
    monkeypatch.setattr(recipe_run, "Console", None)
    _run_cli_with_mocked_crew(monkeypatch)
    out = capsys.readouterr().out
    assert "SUPPORT REPLY" in out
    assert "The **Team** plan" in out
    assert "═" * 60 in out


def test_kb_shape() -> None:
    for entry in FAQ_KNOWLEDGE_BASE:
        assert "topic" in entry, "missing 'topic'"
        assert "question" in entry, "missing 'question'"
        assert "answer" in entry, "missing 'answer'"
        assert entry["topic"], "empty 'topic'"
        assert entry["question"], "empty 'question'"
        assert entry["answer"], "empty 'answer'"


def test_kb_text_contains_entries() -> None:
    text = get_knowledge_base_text()

    # Check headers and footers
    assert "=== ORBITLY FAQ KNOWLEDGE BASE ===" in text
    assert "=== END OF KNOWLEDGE BASE ===" in text

    for i, entry in enumerate(FAQ_KNOWLEDGE_BASE, 1):
        assert f"[{i}] Topic:" in text
        assert entry["topic"].upper() in text
        assert entry["question"] in text
        assert entry["answer"] in text


def test_kb_addition_flows_through() -> None:
    new_entry = {
        "topic": "test_topic",
        "question": "test_question?",
        "answer": "test_answer!",
    }
    FAQ_KNOWLEDGE_BASE.append(new_entry)
    try:
        text = get_knowledge_base_text()
        assert "TEST_TOPIC" in text
        assert "test_question?" in text
        assert "test_answer!" in text
    finally:
        FAQ_KNOWLEDGE_BASE.pop()


def test_crew_structure() -> None:
    crew = build_crew(question="how do I refund?")
    assert len(crew.agents) == 1
    assert len(crew.tasks) == 1
    assert crew.process == Process.sequential

    assert "how do I refund?" in crew.tasks[0].description
    assert "there" in crew.tasks[0].description

    crew_with_name = build_crew(question="how do I refund?", customer_name="Alice")
    assert "Alice" in crew_with_name.tasks[0].description
