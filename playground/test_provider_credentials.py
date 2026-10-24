"""Offline regression coverage for playground provider preflight (#237)."""

import importlib.util
import os
import sys
import threading
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

playground_dir = Path(__file__).parent.resolve()
if str(playground_dir) not in sys.path:
    sys.path.insert(0, str(playground_dir))

import main as playground  # noqa: E402

PRIMARY = "dummy-primary-237"
LEGACY = "dummy-legacy-237"
FALLBACK = "dummy-fallback-237"
INPUTS = {"question": "Hi", "customer_name": "Test"}

CASES = [
    pytest.param({"LLM_API_KEY": PRIMARY}, PRIMARY, id="primary-default"),
    pytest.param(
        {"LLM_PROVIDER": "primary", "LLM_API_KEY": PRIMARY},
        PRIMARY,
        id="primary-explicit",
    ),
    pytest.param({"NVIDIA_API_KEY": LEGACY}, LEGACY, id="legacy-primary"),
    pytest.param({"LLM_FALLBACK_API_KEY": FALLBACK}, FALLBACK, id="implicit-fallback"),
    pytest.param(
        {"LLM_PROVIDER": "primary", "LLM_FALLBACK_API_KEY": FALLBACK},
        FALLBACK,
        id="primary-with-automatic-fallback",
    ),
    pytest.param(
        {"LLM_PROVIDER": "fallback", "LLM_FALLBACK_API_KEY": FALLBACK},
        FALLBACK,
        id="explicit-fallback",
    ),
    pytest.param(
        {"LLM_PROVIDER": "secondary", "LLM_FALLBACK_API_KEY": FALLBACK},
        FALLBACK,
        id="secondary-alias",
    ),
    pytest.param({}, None, id="missing-all-keys"),
    pytest.param(
        {"LLM_PROVIDER": "fallback", "LLM_API_KEY": PRIMARY},
        None,
        id="fallback-requires-own-key",
    ),
    pytest.param(
        {"LLM_PROVIDER": "secondary", "NVIDIA_API_KEY": LEGACY},
        None,
        id="secondary-requires-own-key",
    ),
    pytest.param({"LLM_PROVIDER": "secondary"}, None, id="secondary-missing-all-keys"),
    pytest.param(
        {
            "LLM_PROVIDER": "primary",
            "LLM_API_KEY": PRIMARY,
            "LLM_FALLBACK_API_KEY": FALLBACK,
        },
        PRIMARY,
        id="primary-precedence",
    ),
    pytest.param(
        {
            "LLM_PROVIDER": "fallback",
            "LLM_API_KEY": PRIMARY,
            "LLM_FALLBACK_API_KEY": FALLBACK,
        },
        FALLBACK,
        id="fallback-precedence",
    ),
    pytest.param(
        {"LLM_PROVIDER": "other", "LLM_API_KEY": PRIMARY},
        PRIMARY,
        id="unknown-provider-primary",
    ),
    pytest.param(
        {"LLM_PROVIDER": "other", "LLM_FALLBACK_API_KEY": FALLBACK},
        FALLBACK,
        id="unknown-provider-automatic-fallback",
    ),
    pytest.param(
        {"LLM_PROVIDER": "FALLBACK", "LLM_FALLBACK_API_KEY": FALLBACK},
        FALLBACK,
        id="case-insensitive-provider",
    ),
    pytest.param(
        {"LLM_API_KEY": "", "NVIDIA_API_KEY": "", "LLM_FALLBACK_API_KEY": FALLBACK},
        FALLBACK,
        id="empty-primary-keys",
    ),
    pytest.param(
        {"NVIDIA_API_KEY": LEGACY, "LLM_FALLBACK_API_KEY": FALLBACK},
        LEGACY,
        id="legacy-before-automatic-fallback",
    ),
    pytest.param(
        {
            "LLM_PROVIDER": "fallback",
            "LLM_API_KEY": PRIMARY,
            "LLM_FALLBACK_API_KEY": "",
        },
        None,
        id="empty-explicit-fallback-key",
    ),
]


@pytest.fixture
def execution():
    """Stub the external LLM constructor while running the real provider factory."""
    llm_constructor = MagicMock()
    provider_path = playground_dir.parent / "recipes" / "_template" / "llm.py"
    spec = importlib.util.spec_from_file_location("provider_contract", provider_path)
    provider = importlib.util.module_from_spec(spec)
    with patch.dict(sys.modules, {"crewai": SimpleNamespace(LLM=llm_constructor)}):
        spec.loader.exec_module(provider)

    crew = MagicMock()
    crew.kickoff.return_value = "Offline answer"

    def build_crew(**inputs):
        provider.get_llm()
        return crew

    module = SimpleNamespace(build_crew=MagicMock(side_effect=build_crew))
    loader = MagicMock()
    cache = playground.ResponseCache()
    with (
        patch.object(playground, "response_cache", cache),
        patch.object(
            playground, "rate_limiter", playground.SlidingWindowRateLimiter("0")
        ),
        patch.object(
            playground.importlib.util,
            "spec_from_file_location",
            return_value=SimpleNamespace(loader=loader),
        ),
        patch.object(
            playground.importlib.util, "module_from_spec", return_value=module
        ),
    ):
        yield SimpleNamespace(
            crew=crew,
            build_crew=module.build_crew,
            llm=llm_constructor,
            loader=loader,
            cache=cache,
        )


def invoke(path: str):
    """Exercise the HTTP endpoint or the worker shared by SSE and WebSocket."""
    if path == "http":
        with TestClient(playground.app) as client:
            return client.post(
                "/run",
                json={"recipe": "faq-bot", "inputs": INPUTS, "no_cache": True},
            )
    events = []
    playground.execute_recipe_stream(
        "faq-bot", INPUTS, events.append, threading.Event()
    )
    return events


@pytest.mark.parametrize("path", ["http", "stream"])
@pytest.mark.parametrize("environment, selected_key", CASES)
def test_provider_preflight(environment, selected_key, path, execution, caplog, capsys):
    """Preflight agrees with get_llm and never starts execution on invalid keys."""
    with patch.dict(os.environ, environment, clear=True):
        result = invoke(path)

    if selected_key is None:
        if path == "http":
            assert result.status_code == 401
            assert result.json() == {
                "detail": "LLM_API_KEY is not set in the environment."
            }
        else:
            assert result == [
                {
                    "type": "error",
                    "error": "API Key is missing. Please check your .env file.",
                }
            ]
        execution.loader.exec_module.assert_not_called()
        execution.build_crew.assert_not_called()
        execution.llm.assert_not_called()
        execution.crew.kickoff.assert_not_called()
        assert execution.cache.get("faq-bot", INPUTS) is None
    else:
        if path == "http":
            assert result.status_code == 200
            assert result.json() == {"output": "Offline answer", "cached": False}
        else:
            assert result == [
                {"type": "complete", "output": "Offline answer", "cached": False}
            ]
        execution.build_crew.assert_called_once_with(**INPUTS)
        execution.crew.kickoff.assert_called_once_with()
        execution.llm.assert_called_once()
        assert execution.llm.call_args.kwargs["api_key"] == selected_key
        assert execution.cache.get("faq-bot", INPUTS) == "Offline answer"

    captured = capsys.readouterr()
    for key in (PRIMARY, LEGACY, FALLBACK):
        assert key not in caplog.text + captured.out + captured.err


@pytest.mark.parametrize("path", ["http", "stream"])
@pytest.mark.parametrize(
    "error", [TimeoutError("Request timed out"), ValueError("bad input")]
)
def test_fallback_execution_errors(path, error, execution):
    """Accepted fallback configurations retain timeout and execution-error mapping."""
    execution.crew.kickoff.side_effect = error
    with patch.dict(os.environ, {"LLM_FALLBACK_API_KEY": FALLBACK}, clear=True):
        result = invoke(path)

    message = (
        "LLM call timed out after 120s, try again, or raise LLM_TIMEOUT"
        if isinstance(error, TimeoutError)
        else "Execution error: bad input"
    )
    if path == "http":
        assert result.status_code == (504 if isinstance(error, TimeoutError) else 500)
        assert result.json() == {"detail": message}
    else:
        assert result == [{"type": "error", "error": message}]
    execution.build_crew.assert_called_once_with(**INPUTS)
    execution.crew.kickoff.assert_called_once_with()
    assert execution.cache.get("faq-bot", INPUTS) is None
