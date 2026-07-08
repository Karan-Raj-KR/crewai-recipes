"""
Lead Qualification Recipe — llm.py

Central LLM configuration using NVIDIA NIM (OpenAI-compatible endpoint).
All agents import from here so changing the model is a one-line edit.

CrewAI 1.x uses LiteLLM under the hood. For OpenAI-compatible endpoints,
the model string must be prefixed with "openai/" so LiteLLM routes correctly.
"""

import os

from crewai import LLM

# NVIDIA NIM base URL — OpenAI-compatible REST API
NIM_BASE_URL = "https://integrate.api.nvidia.com/v1"

# Model slug on NVIDIA NIM. Prefix with "openai/" for LiteLLM routing.
# Full list: https://build.nvidia.com/
# Use llama-3.1-8b-instruct for fast/free tier; upgrade to llama-3.3-70b-instruct for best quality.
NIM_MODEL = "meta/llama-3.1-8b-instruct"  # default: fast & reliable on free tier
# NIM_MODEL = "meta/llama-3.3-70b-instruct"  # upgrade for better reasoning


def get_llm() -> LLM:
    """Return a CrewAI LLM configured to use NVIDIA NIM.

    Reads NVIDIA_API_KEY from the environment (or .env file).
    Call load_dotenv() in your entry point (run.py) before importing this.

    Returns:
        A configured LLM instance ready for use in CrewAI agents.

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

    # The "openai/" prefix tells LiteLLM (used by CrewAI) to route
    # this call to the OpenAI-compatible endpoint at base_url.
    return LLM(
        model=f"openai/{NIM_MODEL}",
        base_url=NIM_BASE_URL,
        api_key=api_key,
        temperature=0.2,
        max_tokens=2048,
    )
