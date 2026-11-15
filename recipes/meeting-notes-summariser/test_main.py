"""
Meeting Notes Summariser Recipe — test_main.py

Offline structural tests. They never call an LLM and need no real API key:
the crew is only *built*, never kicked off.

    pytest test_main.py -v
"""

import json

import pytest
from crewai import Process
from pydantic import ValidationError

from agents import build_agents
from crew import build_crew
from models import (
    ActionItem,
    FollowUpEmail,
    MeetingNotesResult,
    MeetingSummary,
)
from run import format_markdown, read_transcript

SAMPLE_TRANSCRIPT = (
    "Weekly sync. We decided to ship v1 without the invite step. "
    "Alice will send the status report by Friday. Open question: who writes "
    "the announcement post?"
)


@pytest.fixture(autouse=True)
def _offline_env(monkeypatch):
    """Provide a dummy key so get_llm() succeeds without touching the network."""
    monkeypatch.setenv("LLM_API_KEY", "test-key-not-real")
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    monkeypatch.delenv("LLM_FALLBACK_API_KEY", raising=False)


@pytest.fixture
def crew():
    return build_crew(transcript=SAMPLE_TRANSCRIPT)


# ─── Crew shape ──────────────────────────────────────────────────────────────


class TestCrewShape:
    def test_has_two_agents_and_two_tasks(self, crew):
        assert len(crew.agents) == 2
        assert len(crew.tasks) == 2

    def test_process_is_sequential(self, crew):
        assert crew.process == Process.sequential

    def test_each_task_has_its_own_agent(self, crew):
        extract_task, draft_task = crew.tasks
        assert extract_task.agent is crew.agents[0]
        assert draft_task.agent is crew.agents[1]
        assert extract_task.agent is not draft_task.agent

    def test_build_agents_returns_two_distinct_agents(self):
        extractor, drafter = build_agents()
        assert extractor is not drafter
        assert extractor.role != drafter.role

    def test_agents_do_not_use_memory(self, crew):
        # agents.py passes memory=False; guard against it being dropped.
        for agent in crew.agents:
            assert not agent.memory


# ─── Context chaining ────────────────────────────────────────────────────────


class TestContextChaining:
    def test_drafter_receives_extractor_output(self, crew):
        extract_task, draft_task = crew.tasks
        assert draft_task.context == [extract_task]

    def test_extractor_outputs_meeting_summary(self, crew):
        assert crew.tasks[0].output_pydantic is MeetingSummary

    def test_drafter_outputs_follow_up_email(self, crew):
        assert crew.tasks[1].output_pydantic is FollowUpEmail

    def test_transcript_is_embedded_in_extractor_task(self, crew):
        assert SAMPLE_TRANSCRIPT in crew.tasks[0].description

    def test_transcript_is_not_duplicated_in_drafter_task(self, crew):
        # The drafter should work from the extraction, not the raw transcript.
        assert SAMPLE_TRANSCRIPT not in crew.tasks[1].description

    def test_transcript_is_stripped(self):
        crew = build_crew(transcript=f"\n\n  {SAMPLE_TRANSCRIPT}  \n")
        assert crew.tasks[0].description.endswith(SAMPLE_TRANSCRIPT)

    def test_transcript_with_braces_is_preserved(self):
        text = 'Config discussed: {"retries": 3}. Bob owns it.'
        crew = build_crew(transcript=text)
        assert text in crew.tasks[0].description


# ─── Input validation ────────────────────────────────────────────────────────


class TestInputValidation:
    @pytest.mark.parametrize("bad", ["", "   ", "\n\t\n"])
    def test_blank_transcript_raises(self, bad):
        with pytest.raises(ValueError, match="transcript"):
            build_crew(transcript=bad)

    def test_none_transcript_raises(self):
        with pytest.raises(ValueError):
            build_crew(transcript=None)  # type: ignore[arg-type]


# ─── LLM configuration ───────────────────────────────────────────────────────


class TestLLMConfig:
    def test_token_budget_has_headroom_for_reasoning_models(self):
        # The shared llm.py caps at 2048, which reasoning models burn on thinking
        # before emitting any structured output. agents.py must raise it.
        for agent in build_agents():
            assert agent.llm.max_tokens >= 8192


# ─── Pydantic models ─────────────────────────────────────────────────────────


class TestModels:
    @pytest.mark.parametrize(
        "placeholder", ["N/A", "n/a", "TBD", "Not specified", "none", "", "  ", "-"]
    )
    def test_missing_placeholders_become_none(self, placeholder):
        item = ActionItem(task="Ship it", owner=placeholder, due_date=placeholder)
        assert item.owner is None
        assert item.due_date is None

    def test_real_values_are_kept_and_stripped(self):
        item = ActionItem(
            task="  Send report ", owner=" Alice ", due_date="next Friday"
        )
        assert item.task == "Send report"
        assert item.owner == "Alice"
        assert item.due_date == "next Friday"

    def test_owner_and_due_date_are_optional(self):
        item = ActionItem(task="Clean up old posts")
        assert item.owner is None and item.due_date is None

    def test_blank_task_is_rejected(self):
        with pytest.raises(ValidationError):
            ActionItem(task="   ")

    def test_summary_defaults_to_empty_lists(self):
        s = MeetingSummary()
        assert s.decisions == [] and s.action_items == []
        assert s.risks_blockers == [] and s.open_questions == []

    def test_summary_lists_are_deduplicated_and_cleaned(self):
        s = MeetingSummary(
            decisions=["Ship v1", " ship v1 ", "", "Freeze features"],
            open_questions=["Who writes the post?", "  "],
        )
        assert s.decisions == ["Ship v1", "Freeze features"]
        assert s.open_questions == ["Who writes the post?"]

    def test_email_requires_subject_and_body(self):
        with pytest.raises(ValidationError):
            FollowUpEmail(subject="", body="Hello")
        with pytest.raises(ValidationError):
            FollowUpEmail(subject="Recap", body="   ")

    def test_result_round_trips_through_json(self):
        original = MeetingNotesResult(
            summary=MeetingSummary(
                decisions=["Ship v1"],
                action_items=[ActionItem(task="Send report", owner="Alice")],
            ),
            email=FollowUpEmail(subject="Recap", body="Thanks all."),
        )
        restored = MeetingNotesResult.model_validate(
            json.loads(original.model_dump_json())
        )
        assert restored == original


# ─── run.py helpers ──────────────────────────────────────────────────────────


class TestRunHelpers:
    def test_read_transcript_accepts_md_and_txt(self, tmp_path):
        for name in ("notes.md", "notes.txt"):
            f = tmp_path / name
            f.write_text("Alice owns the report.", encoding="utf-8")
            assert read_transcript(str(f)) == "Alice owns the report."

    def test_read_transcript_missing_file_exits(self, tmp_path, capsys):
        with pytest.raises(SystemExit) as exc:
            read_transcript(str(tmp_path / "nope.md"))
        assert exc.value.code == 1
        assert "not found" in capsys.readouterr().err

    def test_read_transcript_empty_file_exits(self, tmp_path, capsys):
        f = tmp_path / "empty.md"
        f.write_text("  \n", encoding="utf-8")
        with pytest.raises(SystemExit) as exc:
            read_transcript(str(f))
        assert exc.value.code == 1
        assert "empty" in capsys.readouterr().err

    def test_read_transcript_binary_file_exits(self, tmp_path, capsys):
        f = tmp_path / "notes.docx"
        f.write_bytes(b"\xff\xfe\x00\x00\x80\x81")
        with pytest.raises(SystemExit) as exc:
            read_transcript(str(f))
        assert exc.value.code == 1
        assert "could not read" in capsys.readouterr().err

    def test_format_markdown_renders_all_sections(self):
        result = MeetingNotesResult(
            summary=MeetingSummary(
                decisions=["Ship v1"],
                action_items=[
                    ActionItem(task="Send report", owner="Alice", due_date="Friday"),
                    ActionItem(task="Clean up blog"),
                ],
                risks_blockers=["Sandbox credentials delayed"],
                open_questions=["Who writes the post?"],
            ),
            email=FollowUpEmail(subject="Recap", body="Thanks all."),
        )
        md = format_markdown(result)
        assert "Ship v1" in md
        assert "**Owner:** Alice | **Due:** Friday" in md
        assert "Clean up blog — **Owner:** TBD | **Due:** TBD" in md
        assert "Sandbox credentials delayed" in md
        assert "Who writes the post?" in md
        assert "**Subject:** Recap" in md

    def test_format_markdown_handles_empty_summary(self):
        result = MeetingNotesResult(
            summary=MeetingSummary(),
            email=FollowUpEmail(subject="Recap", body="Nothing decided."),
        )
        md = format_markdown(result)
        assert md.count("_None_") == 4


# ─── --json stdout purity ────────────────────────────────────────────────────

_JSON_DRIVER = """
import os, sys
import crew
from models import ActionItem, FollowUpEmail, MeetingSummary


class _Out:
    def __init__(self, pydantic):
        self.pydantic = pydantic
        self.raw = "raw"


class _Task:
    def __init__(self, pydantic):
        self.output = _Out(pydantic)


class _NoisyCrew:
    tasks = [
        _Task(MeetingSummary(
            decisions=["Ship v1"],
            action_items=[ActionItem(task="Send report", owner="Alice")],
        )),
        _Task(FollowUpEmail(subject="Recap", body="Thanks all.")),
    ]

    def kickoff(self):
        print("python-level noise")
        os.write(1, b"fd-level noise (e.g. a Tracing Status panel)\\n")


crew.build_crew = lambda transcript: _NoisyCrew()
import run
sys.argv = ["run.py", "--transcript", sys.argv[1], "--json"]
run.main()
"""


def test_json_mode_stdout_contains_only_json(tmp_path):
    import os
    import subprocess
    import sys
    from pathlib import Path

    notes = tmp_path / "notes.md"
    notes.write_text(SAMPLE_TRANSCRIPT, encoding="utf-8")
    env = {**os.environ, "LLM_API_KEY": "test-key-not-real"}

    proc = subprocess.run(
        [sys.executable, "-c", _JSON_DRIVER, str(notes)],
        cwd=Path(__file__).parent,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )

    assert proc.returncode == 0, proc.stderr
    result = MeetingNotesResult.model_validate(json.loads(proc.stdout))
    assert result.summary.decisions == ["Ship v1"]
    assert "python-level noise" in proc.stderr
    assert "fd-level noise" in proc.stderr