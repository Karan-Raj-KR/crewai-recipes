"""Tests to validate LLM providers documentation and OpenRouter guide."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_providers_doc_contains_openrouter_walkthrough():
    providers_file = ROOT / "docs" / "providers.md"
    assert providers_file.exists(), "docs/providers.md must exist"

    text = providers_file.read_text(encoding="utf-8")
    assert "## OpenRouter (Worked Example)" in text
    assert "LLM_BASE_URL=https://openrouter.ai/api/v1" in text
    assert "LLM_MODEL=meta-llama/llama-3.1-8b-instruct:free" in text
    assert "LLM_API_KEY=sk-or-v1-YOUR_KEY_HERE" in text
    assert "LLM_FALLBACK_BASE_URL=https://openrouter.ai/api/v1" in text
    assert "LLM_FALLBACK_API_KEY=sk-or-v1-YOUR_OPENROUTER_KEY_HERE" in text
    assert "One-Run Walkthrough" in text
