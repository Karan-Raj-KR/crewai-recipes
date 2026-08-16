"""Unit tests for llm.py environment handling and fallback logic."""

import os
from unittest.mock import patch
import pytest

from llm import get_llm


def test_missing_key_raises_environment_error() -> None:
    # Remove all keys
    env = {}
    with patch.dict(os.environ, env, clear=True):
        with pytest.raises(EnvironmentError) as exc:
            get_llm()
        assert "LLM_API_KEY is not set" in str(exc.value)
        assert "1. Copy .env.example" in str(exc.value)


@patch("llm.LLM")
def test_nvidia_api_key_fallback_and_warning(
    mock_llm,
) -> None:
    env = {"NVIDIA_API_KEY": "nvapi-test"}
    with patch.dict(os.environ, env, clear=True):
        with pytest.warns(UserWarning, match="NVIDIA_API_KEY is deprecated"):
            get_llm()

        mock_llm.assert_called_once()
        kwargs = mock_llm.call_args.kwargs
        assert kwargs["api_key"] == "nvapi-test"


@patch("llm.LLM")
def test_overrides_apply(mock_llm) -> None:
    env = {
        "LLM_API_KEY": "test-key",
        "LLM_MODEL": "custom-model",
        "LLM_BASE_URL": "http://custom-url",
    }
    with patch.dict(os.environ, env, clear=True):
        get_llm()

        mock_llm.assert_called_once()
        kwargs = mock_llm.call_args.kwargs
        assert kwargs["api_key"] == "test-key"
        assert kwargs["model"] == "openai/custom-model"
        assert kwargs["base_url"] == "http://custom-url"


@patch("llm.LLM")
def test_model_prefix_applied(mock_llm) -> None:
    env = {"LLM_API_KEY": "test-key", "LLM_MODEL": "llama-3.1"}
    with patch.dict(os.environ, env, clear=True):
        get_llm()
        assert mock_llm.call_args.kwargs["model"] == "openai/llama-3.1"

    mock_llm.reset_mock()
    env = {"LLM_API_KEY": "test-key", "LLM_MODEL": "openai/already-prefixed"}
    with patch.dict(os.environ, env, clear=True):
        get_llm()
        assert mock_llm.call_args.kwargs["model"] == "openai/already-prefixed"

    mock_llm.reset_mock()
    env = {"LLM_API_KEY": "test-key", "LLM_MODEL": "hosted_vllm/model"}
    with patch.dict(os.environ, env, clear=True):
        get_llm()
        assert mock_llm.call_args.kwargs["model"] == "hosted_vllm/model"
