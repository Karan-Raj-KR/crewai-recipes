import os
import pytest
from unittest.mock import patch
from llm import get_llm

def test_get_llm_raises_when_no_key():
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(EnvironmentError, match="LLM_API_KEY is not set"):
            get_llm()

def test_get_llm_nvidia_key_fallback(capsys):
    env_mock = {"NVIDIA_API_KEY": "nvapi-fallback"}
    with patch.dict(os.environ, env_mock, clear=True):
        llm = get_llm()
        assert llm.api_key == "nvapi-fallback"
        captured = capsys.readouterr()
        assert "WARNING: NVIDIA_API_KEY is deprecated" in captured.out

def test_get_llm_overrides():
    env_mock = {
        "LLM_API_KEY": "test-key",
        "LLM_MODEL": "custom-model",
        "LLM_BASE_URL": "http://custom-url"
    }
    with patch.dict(os.environ, env_mock, clear=True):
        llm = get_llm()
        assert llm.api_key == "test-key"
        assert llm.model == "custom-model"
        assert llm.base_url == "http://custom-url"

def test_get_llm_prefix():
    env_mock = {"LLM_API_KEY": "test-key", "LLM_MODEL": "llama-3"}
    with patch.dict(os.environ, env_mock, clear=True):
        llm = get_llm()
        assert llm.model == "llama-3"

    env_mock = {"LLM_API_KEY": "test-key", "LLM_MODEL": "openai/llama-3"}
    with patch.dict(os.environ, env_mock, clear=True):
        llm = get_llm()
        assert llm.model == "llama-3"

    env_mock = {"LLM_API_KEY": "test-key", "LLM_MODEL": "ollama/llama-3"}
    with patch.dict(os.environ, env_mock, clear=True):
        llm = get_llm()
        assert llm.model == "llama-3"

    env_mock = {"LLM_API_KEY": "test-key", "LLM_MODEL": "hosted_vllm/llama-3"}
    with patch.dict(os.environ, env_mock, clear=True):
        llm = get_llm()
        assert llm.model == "llama-3"
