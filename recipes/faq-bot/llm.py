"""
FAQ Bot Recipe — llm.py

Central LLM configuration using NVIDIA NIM (OpenAI-compatible endpoint).
Low temperature is intentional — factual Q&A should be deterministic.

CrewAI 1.x uses LiteLLM under the hood. For OpenAI-compatible endpoints,
the model string must be prefixed with "openai/" so LiteLLM routes correctly.
"""

import os

from crewai import LLM

NIM_BASE_URL = "https://integrate.api.nvidia.com/v1"
NIM_MODEL = "meta/llama-3.1-8b-instruct"  # default: fast & reliable on free tier
# NIM_MODEL = "meta/llama-3.3-70b-instruct"  # upgrade for best quality


def get_llm() -> LLM:
    """Return a CrewAI LLM configured to use NVIDIA NIM.

    Returns:
        A configured LLM instance.

    Raises:
        EnvironmentError: If NVIDIA_API_KEY is not set.
    """
    api_key = os.getenv("NVIDIA_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "NVIDIA_API_KEY is not set.\n"
            "  1. Copy .env.example → .env\n"
            "  2. Add your key: NVIDIA_API_KEY=nvapi-...\n"
            "  3. Get a free key at https://build.nvidia.com/"
        )

    return LLM(
        model=f"openai/{NIM_MODEL}",
        base_url=NIM_BASE_URL,
        api_key=api_key,
        temperature=0.1,  # Low temp — factual Q&A, not creative writing
        max_tokens=1024,
    )
