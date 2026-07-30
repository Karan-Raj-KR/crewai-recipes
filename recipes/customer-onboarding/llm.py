"""
customer-onboarding — llm.py

Central LLM configuration using OpenAI-compatible endpoints.
Supports primary provider (LLM_API_KEY, LLM_MODEL, LLM_BASE_URL) and optional
secondary/fallback provider (LLM_FALLBACK_API_KEY, LLM_FALLBACK_MODEL, LLM_FALLBACK_BASE_URL).
"""

import os
from typing import Optional

from crewai import LLM

# Default to NVIDIA NIM if not provided
DEFAULT_BASE_URL = "https://integrate.api.nvidia.com/v1"
DEFAULT_MODEL = "meta/llama-3.1-8b-instruct"
MAX_RETRIES = 3


def get_llm(provider: Optional[str] = None) -> LLM:
    """Return a CrewAI LLM configured via environment variables.

    Supports primary provider configuration:
        LLM_API_KEY (or NVIDIA_API_KEY), LLM_MODEL, LLM_BASE_URL

    And optional secondary/fallback provider configuration:
        LLM_FALLBACK_API_KEY, LLM_FALLBACK_MODEL, LLM_FALLBACK_BASE_URL

    Args:
        provider: Optional explicit provider selection ("primary" or "fallback").
            If None, checks the LLM_PROVIDER environment variable (default: "primary").

    Returns:
        An LLM instance configured for the selected provider with retries enabled.

    Raises:
        EnvironmentError: If required API keys are missing.
    """
    if provider is None:
        provider = os.getenv("LLM_PROVIDER", "primary").lower()

    if provider in ("fallback", "secondary"):
        api_key = os.getenv("LLM_FALLBACK_API_KEY")
        if not api_key:
            raise EnvironmentError(
                "LLM_FALLBACK_API_KEY is not set.\n"
                "  1. Add LLM_FALLBACK_API_KEY=sk-or-... to your .env file\n"
                "  2. Optionally set LLM_FALLBACK_MODEL and LLM_FALLBACK_BASE_URL\n"
            )
        model = os.getenv("LLM_FALLBACK_MODEL", DEFAULT_MODEL)
        base_url = os.getenv("LLM_FALLBACK_BASE_URL", DEFAULT_BASE_URL)
    else:
        api_key = os.getenv("LLM_API_KEY")
        if not api_key:
            api_key = os.getenv("NVIDIA_API_KEY")
            if api_key:
                print(
                    "WARNING: NVIDIA_API_KEY is deprecated. Please use LLM_API_KEY instead."
                )

        # Auto-fallback to secondary provider if primary key is missing but fallback key exists
        if not api_key and os.getenv("LLM_FALLBACK_API_KEY"):
            api_key = os.getenv("LLM_FALLBACK_API_KEY")
            model = os.getenv("LLM_FALLBACK_MODEL", DEFAULT_MODEL)
            base_url = os.getenv("LLM_FALLBACK_BASE_URL", DEFAULT_BASE_URL)
        elif not api_key:
            raise EnvironmentError(
                "LLM_API_KEY is not set.\n"
                "  1. Copy .env.example → .env\n"
                "  2. Add your key: LLM_API_KEY=your-key-here\n"
            )
        else:
            model = os.getenv("LLM_MODEL", os.getenv("NIM_MODEL", DEFAULT_MODEL))
            base_url = os.getenv("LLM_BASE_URL", DEFAULT_BASE_URL)

    # Ensure model starts with provider prefix for LiteLLM routing
    if not (
        model.startswith("openai/")
        or model.startswith("hosted_vllm/")
        or model.startswith("ollama/")
    ):
        full_model = f"openai/{model}"
    else:
        full_model = model

    return LLM(
        model=full_model,
        base_url=base_url,
        api_key=api_key,
        temperature=0.2,
        max_tokens=2048,
        max_retries=MAX_RETRIES,
    )
