"""Tests for customer-onboarding recipe execution, CLI, and Pydantic models (#169).

Validates:
- Default execution and backward compatibility.
- CLI argument parsing including --json flag.
- Pydantic models validation, serialization, and round-trip.
- Wiring of output_pydantic to terminal task when json_output=True.
- Format of JSON output without extraneous formatting or banners.
- Offline execution with zero external network or NVIDIA API calls.
"""

import importlib.util
import json
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError

# Windows cp1252 guard
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

# Ensure API key is set for offline testing
os.environ.setdefault("LLM_API_KEY", "nvapi-test")

# Ensure crewai mock fallback if not installed in current environment
if importlib.util.find_spec("crewai") is None:

    class MockAgent:
        def __init__(self, **kwargs):
            self.verbose = kwargs.get("verbose", True)
            for k, v in kwargs.items():
                setattr(self, k, v)

    class MockTask:
        def __init__(self, **kwargs):
            self.output_pydantic = kwargs.get("output_pydantic", None)
            for k, v in kwargs.items():
                setattr(self, k, v)

    class MockCrew:
        def __init__(self, agents=None, tasks=None, **kwargs):
            self.agents = agents or []
            self.tasks = tasks or []
            self.verbose = kwargs.get("verbose", True)
            for k, v in kwargs.items():
                setattr(self, k, v)

        def kickoff(self):
            if self.verbose:
                print("[VERBOSE] Agent reasoning trace")
            return "Mocked Onboarding Email"

    mock_crewai = MagicMock()
    mock_crewai.Agent = MockAgent
    mock_crewai.Task = MockTask
    mock_crewai.Crew = MockCrew
    mock_crewai.Process.sequential = "sequential"
    sys.modules["crewai"] = mock_crewai

# Add recipe directory to sys.path
sys.path.insert(0, str(Path(__file__).parent))

import main as recipe_main
import run as recipe_run
from crew import build_crew
from tasks import (
    CustomerOnboardingResult,
    CustomerProfile,
    OnboardingEmail,
)


def sample_onboarding_result() -> CustomerOnboardingResult:
    """Helper creating a valid sample CustomerOnboardingResult."""
    return CustomerOnboardingResult(
        profile=CustomerProfile(
            customer_name="Alice Smith",
            company="TechCorp Solutions",
            role="Head of DevOps",
            use_case="Automating infrastructure provisioning and CI/CD pipelines",
            team_size="25",
            status="READY",
            completeness_score="High",
            missing_fields=[],
        ),
        email=OnboardingEmail(
            subject="Welcome to TechCorp Solutions — Next Steps for Your DevOps Journey",
            body="Hi Alice,\n\nWelcome to TechCorp Solutions! Let's get your CI/CD pipelines automated...",
        ),
    )


def test_crew_build_and_kickoff() -> None:
    """Verify build_crew instantiates Crew and kickoff runs smoothly (default mode)."""
    crew = build_crew(
        customer_name="Test User",
        company="Acme Corp",
        role="DevOps Lead",
        use_case="CI/CD Automation",
        team_size="10",
    )
    assert len(crew.agents) == 3
    assert len(crew.tasks) == 3
    assert crew.verbose is True
    assert all(agent.verbose is True for agent in crew.agents)
    assert crew.tasks[-1].output_pydantic is None

    with patch("crewai.Crew.kickoff", return_value="Mocked Onboarding Email"):
        recipe_main.main()


def test_pydantic_schema_validation_and_roundtrip() -> None:
    """Pydantic models validate required fields and round-trip via JSON cleanly."""
    result = sample_onboarding_result()

    # Model dump to JSON
    json_str = result.model_dump_json(indent=2)
    assert "TechCorp Solutions" in json_str
    assert "Welcome to TechCorp" in json_str

    # Validate JSON string is valid parseable JSON
    parsed = json.loads(json_str)
    assert parsed["profile"]["customer_name"] == "Alice Smith"
    assert parsed["profile"]["status"] == "READY"
    assert parsed["profile"]["completeness_score"] == "High"
    assert (
        parsed["email"]["subject"]
        == "Welcome to TechCorp Solutions — Next Steps for Your DevOps Journey"
    )

    # Model validate from JSON round-trip
    restored = CustomerOnboardingResult.model_validate_json(json_str)
    assert restored.profile.company == "TechCorp Solutions"
    assert (
        restored.email.subject
        == "Welcome to TechCorp Solutions — Next Steps for Your DevOps Journey"
    )
    assert restored == result


def test_pydantic_validation_error() -> None:
    """Pydantic raises ValidationError when required fields are missing."""
    with pytest.raises(ValidationError):
        # Missing required fields
        CustomerProfile(customer_name="Only Name")  # type: ignore[call-arg]


def test_crew_build_json_output_wiring() -> None:
    """build_crew with json_output=True wires output_pydantic to terminal composer_task and silences verbosity."""
    crew = build_crew(
        customer_name="Alice Smith",
        company="TechCorp Solutions",
        role="Head of DevOps",
        use_case="CI/CD Automation",
        team_size="25",
        json_output=True,
    )
    assert len(crew.tasks) == 3
    assert crew.verbose is False
    assert all(agent.verbose is False for agent in crew.agents)
    assert crew.tasks[0].output_pydantic is None
    assert crew.tasks[1].output_pydantic is None
    assert crew.tasks[2].output_pydantic is CustomerOnboardingResult
    assert "JSON" in crew.tasks[2].expected_output


def test_crew_build_explicit_verbosity() -> None:
    """build_crew respects explicit verbose parameter override."""
    crew_silent = build_crew(
        customer_name="Alice Smith",
        company="TechCorp Solutions",
        role="Head of DevOps",
        use_case="CI/CD Automation",
        team_size="25",
        verbose=False,
        json_output=False,
    )
    assert crew_silent.verbose is False
    assert all(agent.verbose is False for agent in crew_silent.agents)

    crew_verbose = build_crew(
        customer_name="Alice Smith",
        company="TechCorp Solutions",
        role="Head of DevOps",
        use_case="CI/CD Automation",
        team_size="25",
        verbose=True,
        json_output=True,
    )
    assert crew_verbose.verbose is True
    assert all(agent.verbose is True for agent in crew_verbose.agents)


def test_format_json_output_with_pydantic_output() -> None:
    """format_json_output extracts and serializes Pydantic model correctly."""
    result = sample_onboarding_result()

    mock_crew_output = MagicMock()
    mock_crew_output.pydantic = result
    formatted = recipe_run.format_json_output(mock_crew_output)

    parsed = json.loads(formatted)
    assert parsed["profile"]["company"] == "TechCorp Solutions"
    assert (
        parsed["email"]["subject"]
        == "Welcome to TechCorp Solutions — Next Steps for Your DevOps Journey"
    )


def test_format_json_output_with_json_dict() -> None:
    """format_json_output serializes json_dict attribute."""
    mock_crew_output = MagicMock()
    mock_crew_output.pydantic = None
    mock_crew_output.json_dict = {"status": "success", "company": "Acme"}

    formatted = recipe_run.format_json_output(mock_crew_output)
    parsed = json.loads(formatted)
    assert parsed == {"status": "success", "company": "Acme"}


def test_format_json_output_with_markdown_fences() -> None:
    """format_json_output strips markdown fences if output contains them."""
    fenced = '```json\n{"status": "ok", "steps": 5}\n```'
    mock_crew_output = MagicMock()
    mock_crew_output.pydantic = None
    mock_crew_output.json_dict = None
    mock_crew_output.json = None
    mock_crew_output.raw = fenced

    formatted = recipe_run.format_json_output(mock_crew_output)
    parsed = json.loads(formatted)
    assert parsed == {"status": "ok", "steps": 5}


def test_run_main_with_json_flag(capsys: pytest.CaptureFixture[str]) -> None:
    """run.py with --json outputs strictly machine-readable JSON without banners."""
    result = sample_onboarding_result()

    mock_output = MagicMock()
    mock_output.pydantic = result

    test_args = [
        "run.py",
        "--customer_name",
        "Alice Smith",
        "--company",
        "TechCorp Solutions",
        "--json",
    ]
    with (
        patch("sys.argv", test_args),
        patch.object(recipe_run, "build_crew") as mock_build_crew,
    ):
        mock_crew = MagicMock()
        mock_crew.kickoff.return_value = mock_output
        mock_build_crew.return_value = mock_crew

        recipe_run.main()

        mock_build_crew.assert_called_once_with(
            customer_name="Alice Smith",
            company="TechCorp Solutions",
            role="Head of DevOps",
            use_case="Automating infrastructure provisioning and CI/CD pipelines",
            team_size="25",
            json_output=True,
        )

    captured = capsys.readouterr()
    # Output must be pure JSON, parseable by json.loads
    parsed = json.loads(captured.out)
    assert parsed["profile"]["customer_name"] == "Alice Smith"
    # No decorative banners in stdout
    assert "🚀" not in captured.out
    assert "ONBOARDING EMAIL OUTPUT" not in captured.out


def test_run_main_with_json_flag_real_crew_silence(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Verify that run.py --json using actual build_crew keeps verbose=False and emits only JSON."""
    result = sample_onboarding_result()
    test_args = ["run.py", "--json"]

    def fake_kickoff(self):
        if self.verbose:
            print("[VERBOSE] Agent reasoning trace")
        return result

    with (
        patch("sys.argv", test_args),
        patch("crewai.Crew.kickoff", new=fake_kickoff),
    ):
        recipe_run.main()

    captured = capsys.readouterr()
    assert "[VERBOSE]" not in captured.out
    parsed = json.loads(captured.out)
    assert parsed["profile"]["customer_name"] == "Alice Smith"


def test_run_main_default_human_readable(capsys: pytest.CaptureFixture[str]) -> None:
    """run.py without --json outputs human-readable banners and email."""
    test_args = [
        "run.py",
        "--customer_name",
        "Alice Smith",
    ]
    with (
        patch("sys.argv", test_args),
        patch.object(recipe_run, "build_crew") as mock_build_crew,
    ):
        mock_crew = MagicMock()
        mock_crew.kickoff.return_value = "Subject: Welcome Alice\nBody: Hello"
        mock_build_crew.return_value = mock_crew

        recipe_run.main()

        mock_build_crew.assert_called_once_with(
            customer_name="Alice Smith",
            company="TechCorp Solutions",
            role="Head of DevOps",
            use_case="Automating infrastructure provisioning and CI/CD pipelines",
            team_size="25",
            json_output=False,
        )

    captured = capsys.readouterr()
    assert "🚀  Customer Onboarding Workflow" in captured.out
    assert "📧  ONBOARDING EMAIL OUTPUT" in captured.out
    assert "Subject: Welcome Alice" in captured.out


def test_incomplete_profile_validation_and_roundtrip() -> None:
    """CustomerProfile supports INCOMPLETE status with missing_fields."""
    result = CustomerOnboardingResult(
        profile=CustomerProfile(
            customer_name="John Doe",
            company="Unknown LLC",
            role="N/A",
            use_case="stuff",
            team_size="1",
            status="INCOMPLETE",
            completeness_score="Low",
            missing_fields=["use_case", "role"],
        ),
        email=OnboardingEmail(
            subject="Thanks for signing up, John! One quick detail to complete onboarding",
            body="Hi John, please share your primary use case...",
        ),
    )
    json_str = result.model_dump_json(indent=2)
    parsed = json.loads(json_str)
    assert parsed["profile"]["status"] == "INCOMPLETE"
    assert parsed["profile"]["missing_fields"] == ["use_case", "role"]

    restored = CustomerOnboardingResult.model_validate_json(json_str)
    assert restored == result


def test_format_json_output_direct_pydantic_model() -> None:
    """format_json_output directly serializes a Pydantic model instance."""
    result = sample_onboarding_result()
    formatted = recipe_run.format_json_output(result)
    parsed = json.loads(formatted)
    assert parsed["profile"]["customer_name"] == "Alice Smith"
    assert parsed["profile"]["company"] == "TechCorp Solutions"


def test_format_json_output_raw_fallback() -> None:
    """format_json_output wraps plain non-JSON text in a raw_output key."""
    mock_crew_output = MagicMock()
    mock_crew_output.pydantic = None
    mock_crew_output.json_dict = None
    mock_crew_output.json = None
    mock_crew_output.raw = "Unstructured plain text response"

    formatted = recipe_run.format_json_output(mock_crew_output)
    parsed = json.loads(formatted)
    assert parsed == {"raw_output": "Unstructured plain text response"}


def test_check_env_missing_key_json(capsys: pytest.CaptureFixture[str]) -> None:
    """check_env with json_output=True prints JSON error and exits with code 1."""
    with (
        patch.dict(os.environ, {}, clear=True),
        pytest.raises(SystemExit) as exc_info,
    ):
        recipe_run.check_env(json_output=True)

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    parsed = json.loads(captured.out)
    assert parsed == {"error": "LLM_API_KEY is not set."}


def test_check_env_missing_key_human(capsys: pytest.CaptureFixture[str]) -> None:
    """check_env with json_output=False prints human-readable error to stderr."""
    with (
        patch.dict(os.environ, {}, clear=True),
        pytest.raises(SystemExit) as exc_info,
    ):
        recipe_run.check_env(json_output=False)

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Missing API key" in captured.err


def test_run_main_exception_handling_json(capsys: pytest.CaptureFixture[str]) -> None:
    """run.py with --json emits JSON error when crew kickoff raises an exception."""
    test_args = ["run.py", "--json"]
    with (
        patch("sys.argv", test_args),
        patch.object(recipe_run, "build_crew") as mock_build_crew,
        pytest.raises(SystemExit) as exc_info,
    ):
        mock_crew = MagicMock()
        mock_crew.kickoff.side_effect = RuntimeError("Rate limit exceeded")
        mock_build_crew.return_value = mock_crew

        recipe_run.main()

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    parsed = json.loads(captured.out)
    assert parsed == {"error": "Rate limit exceeded"}


def test_cli_json_stdin_pipeline_compatibility(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Verify stdout from --json can be parsed directly by json.load(sys.stdin)."""
    import io

    result = sample_onboarding_result()
    test_args = ["run.py", "--json"]
    with (
        patch("sys.argv", test_args),
        patch.object(recipe_run, "build_crew") as mock_build_crew,
    ):
        mock_crew = MagicMock()
        mock_crew.kickoff.return_value = result
        mock_build_crew.return_value = mock_crew

        recipe_run.main()

    captured = capsys.readouterr()
    # Emulate downstream python -c 'import sys, json; data = json.load(sys.stdin)'
    stream = io.StringIO(captured.out)
    loaded_data = json.load(stream)
    assert loaded_data["profile"]["customer_name"] == "Alice Smith"
    assert (
        loaded_data["email"]["subject"]
        == "Welcome to TechCorp Solutions — Next Steps for Your DevOps Journey"
    )


if __name__ == "__main__":
    pytest.main(["-v", __file__])
