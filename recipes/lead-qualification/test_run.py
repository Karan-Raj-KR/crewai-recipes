"""Unit tests for run.py CLI validation."""

import os
import sys
from unittest.mock import patch
import pytest

from run import main, preflight


def test_missing_args_exits(capsys: pytest.CaptureFixture[str]) -> None:
    """Test that missing required arguments raises SystemExit."""
    test_args = ["run.py"]
    with patch.object(sys, "argv", test_args):
        with pytest.raises(SystemExit) as exc:
            main()
        assert exc.value.code == 2
        captured = capsys.readouterr()
        assert "the following arguments are required: --company, --description" in captured.err


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
