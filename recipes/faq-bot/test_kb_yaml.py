"""Unit tests for faq-bot YAML knowledge base loading (#83)."""

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

# Ensure recipe dir is on sys.path
recipe_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(recipe_dir))

from knowledge_base import (  # noqa: E402
    FAQ_KNOWLEDGE_BASE,
    get_knowledge_base_text,
    load_knowledge_base,
)


def test_default_yaml_knowledge_base_loaded() -> None:
    """Test 1: Default YAML knowledge base contains 6 valid entries."""
    assert isinstance(FAQ_KNOWLEDGE_BASE, list)
    assert len(FAQ_KNOWLEDGE_BASE) == 6, f"Expected 6 FAQ entries, got {len(FAQ_KNOWLEDGE_BASE)}"

    topics = [entry["topic"] for entry in FAQ_KNOWLEDGE_BASE]
    assert "pricing" in topics
    assert "free trial" in topics
    assert "data import" in topics
    assert "integrations" in topics
    assert "security" in topics
    assert "cancellation and refunds" in topics


def test_get_knowledge_base_text_formatting() -> None:
    """Test 2: get_knowledge_base_text() output matches expected structure."""
    kb_text = get_knowledge_base_text()
    assert "=== ORBITLY FAQ KNOWLEDGE BASE ===" in kb_text
    assert "=== END OF KNOWLEDGE BASE ===" in kb_text
    assert "[1] Topic: PRICING" in kb_text
    assert "How much does Orbitly cost?" in kb_text


def test_custom_yaml_path_env_var() -> None:
    """Test 3: Custom YAML path via FAQ_KNOWLEDGE_BASE_PATH environment variable."""
    with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False, encoding="utf-8") as tmp:
        tmp.write(
            "- topic: custom topic\n"
            "  question: Custom question?\n"
            "  answer: Custom answer.\n"
        )
        tmp_path = tmp.name

    try:
        with patch.dict(os.environ, {"FAQ_KNOWLEDGE_BASE_PATH": tmp_path}):
            custom_kb = load_knowledge_base()
            assert len(custom_kb) == 1
            assert custom_kb[0]["topic"] == "custom topic"
            assert custom_kb[0]["question"] == "Custom question?"
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def test_missing_file_raises_file_not_found_error() -> None:
    """Test 4: Missing YAML file raises FileNotFoundError."""
    failed = False
    try:
        load_knowledge_base("/nonexistent/path/kb.yaml")
    except FileNotFoundError as e:
        failed = True
        assert "not found" in str(e).lower()
    assert failed, "Expected FileNotFoundError for missing file"


def test_malformed_schema_raises_value_error() -> None:
    """Test 5: Missing required fields in YAML entry raises ValueError."""
    with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False, encoding="utf-8") as tmp:
        tmp.write("- topic: missing question\n  answer: No question field\n")
        tmp_path = tmp.name

    try:
        failed = False
        try:
            load_knowledge_base(tmp_path)
        except ValueError as e:
            failed = True
            assert "missing required field 'question'" in str(e).lower()
        assert failed, "Expected ValueError for missing question field"
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


if __name__ == "__main__":
    test_default_yaml_knowledge_base_loaded()
    test_get_knowledge_base_text_formatting()
    test_custom_yaml_path_env_var()
    test_missing_file_raises_file_not_found_error()
    test_malformed_schema_raises_value_error()
    print("✅ faq-bot: test_kb_yaml passed (#83)")
