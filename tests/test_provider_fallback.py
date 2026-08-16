"""
Unit test for Issue #75: Secondary / Fallback LLM Provider configuration.
"""

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Mock crewai module if not installed in global environment
if "crewai" not in sys.modules:
    mock_crewai = MagicMock()

    # Mock LLM constructor to return an object with assigned attributes
    def mock_llm_init(
        model, base_url, api_key, temperature=0.2, max_tokens=2048, max_retries=3
    ):
        mock_obj = MagicMock()
        mock_obj.model = model
        mock_obj.base_url = base_url
        mock_obj.api_key = api_key
        return mock_obj

    mock_crewai.LLM = mock_llm_init
    sys.modules["crewai"] = mock_crewai

# Ensure recipe dir is on sys.path
recipe_dir = Path(__file__).resolve().parent.parent / "recipes" / "lead-qualification"
sys.path.insert(0, str(recipe_dir))

from llm import get_llm  # noqa: E402


def test_primary_provider_default() -> None:
    """Test 1: Default behavior uses primary provider env vars."""
    env_mock = {
        "LLM_API_KEY": "primary-key-123",
        "LLM_MODEL": "meta/llama-3.1-8b-instruct",
        "LLM_BASE_URL": "https://primary.example.com/v1",
    }
    with patch.dict(os.environ, env_mock, clear=True):
        llm = get_llm()
        assert llm.api_key == "primary-key-123"
        assert "primary.example.com" in llm.base_url
        assert "llama-3.1-8b-instruct" in llm.model


def test_explicit_fallback_provider() -> None:
    """Test 2: Explicit fallback selection via parameter or LLM_PROVIDER=fallback."""
    env_mock = {
        "LLM_API_KEY": "primary-key-123",
        "LLM_FALLBACK_API_KEY": "fallback-key-456",
        "LLM_FALLBACK_MODEL": "openrouter/llama-3.1-8b",
        "LLM_FALLBACK_BASE_URL": "https://openrouter.ai/api/v1",
        "LLM_PROVIDER": "fallback",
    }
    with patch.dict(os.environ, env_mock, clear=True):
        llm = get_llm()
        assert llm.api_key == "fallback-key-456"
        assert "openrouter.ai" in llm.base_url
        assert "openrouter/llama-3.1-8b" in llm.model

    # Also test explicit parameter kwarg override
    with patch.dict(
        os.environ,
        {"LLM_API_KEY": "primary-key", "LLM_FALLBACK_API_KEY": "fallback-key"},
        clear=True,
    ):
        llm_explicit = get_llm(provider="fallback")
        assert llm_explicit.api_key == "fallback-key"


def test_automatic_fallback_on_missing_primary_key() -> None:
    """Test 3: Auto-fallback to secondary provider if primary key is missing."""
    env_mock = {
        "LLM_FALLBACK_API_KEY": "fallback-key-789",
        "LLM_FALLBACK_MODEL": "secondary-model",
        "LLM_FALLBACK_BASE_URL": "https://fallback.example.com/v1",
    }
    with patch.dict(os.environ, env_mock, clear=True):
        llm = get_llm()
        assert llm.api_key == "fallback-key-789"
        assert "fallback.example.com" in llm.base_url
        assert "secondary-model" in llm.model


def test_missing_keys_raises_environment_error() -> None:
    """Test 4: EnvironmentError is raised when neither primary nor fallback keys are provided."""
    with patch.dict(os.environ, {}, clear=True):
        failed = False
        try:
            get_llm()
        except EnvironmentError as e:
            failed = True
            # Assert API keys are NOT printed in exception messages
            assert "primary-key" not in str(e)
            assert "fallback-key" not in str(e)
        assert failed, "Expected EnvironmentError when no keys are configured"


if __name__ == "__main__":
    test_primary_provider_default()
    test_explicit_fallback_provider()
    test_automatic_fallback_on_missing_primary_key()
    test_missing_keys_raises_environment_error()
    print("✅ test_provider_fallback passed (#75)")
