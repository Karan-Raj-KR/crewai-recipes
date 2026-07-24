"""
Customer Onboarding Recipe — llm.py

NVIDIA NIM LLM configuration.
Copied verbatim across recipes to preserve provider-routing and retry behavior.
"""

import os
from crewai import LLM

# Default model on the NVIDIA NIM free tier (fast, 1k calls/mo free)
DEFAULT_MODEL = "meta/llama-3.1-8b-instruct"
DEFAULT_BASE_URL = "https://integrate.api.nvidia.com/v1"
MAX_RETRIES = 3


def get_llm() -> LLM:
    """Instantiate and return the configured CrewAI LLM object.

    Reads from environment variables:
        LLM_API_KEY: NVIDIA API key (or set NVIDIA_API_KEY as fallback)
        LLM_MODEL:   Override default model (e.g. meta/llama-3.3-70b-instruct)
        LLM_BASE_URL: Override default base URL

    Returns:
        LLM instance pre-configured for NVIDIA NIM.

    Raises:
        EnvironmentError: If neither LLM_API_KEY nor NVIDIA_API_KEY is set.
    """
    api_key = os.getenv("LLM_API_KEY") or os.getenv("NVIDIA_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "Missing API key. Set LLM_API_KEY or NVIDIA_API_KEY in your environment or .env file.\n"
            "Get a free key at https://build.nvidia.com"
        )

    model = os.getenv("LLM_MODEL", DEFAULT_MODEL)
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
        max_retries=MAX_RETRIES,
        temperature=0.2,
    )
