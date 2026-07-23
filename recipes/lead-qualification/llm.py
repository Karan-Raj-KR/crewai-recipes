"""
lead-qualification — llm.py

Central LLM configuration using OpenAI-compatible endpoints.
All agents import from here so changing the model is a one-line edit — or,
better, an environment variable (LLM_MODEL) so you don't touch code at all.

By default, this is wired for NVIDIA NIM (Llama 3.1 8B).
CrewAI routes an "openai/"-prefixed model with a custom base_url to its native
OpenAI provider, which is why the prefix below matters — see get_llm().
"""

import os

from crewai import LLM

# Default to NVIDIA NIM if not provided
DEFAULT_BASE_URL = "https://integrate.api.nvidia.com/v1"
DEFAULT_MODEL = "meta/llama-3.1-8b-instruct"

# Free tiers occasionally return timeouts or 429s under load. The OpenAI SDK
# retries those (plus 5xx and connection errors) with exponential backoff and
# honours Retry-After headers, so one flaky call doesn't fail a whole crew run.
MAX_RETRIES = 3


def get_llm() -> LLM:
    """Return a CrewAI LLM configured via environment variables.

    Reads LLM_API_KEY from the environment (or .env file) and, optionally,
    LLM_MODEL and LLM_BASE_URL. Call load_dotenv() in your entry point (run.py)
    before importing this.

    Returns:
        An LLM configured to retry transient API failures, ready for use in
        CrewAI agents.

    Raises:
        EnvironmentError: If LLM_API_KEY is not set.
    """
    api_key = os.getenv("LLM_API_KEY")
    if not api_key:
        api_key = os.getenv("NVIDIA_API_KEY")  # Backwards compatibility
        if api_key:
            print(
                "WARNING: NVIDIA_API_KEY is deprecated. Please use LLM_API_KEY instead."
            )
        else:
            raise EnvironmentError(
                "LLM_API_KEY is not set.\n"
                "  1. Copy .env.example → .env\n"
                "  2. Add your key: LLM_API_KEY=your-key-here\n"
            )

    model = os.getenv("LLM_MODEL", os.getenv("NIM_MODEL", DEFAULT_MODEL))
    base_url = os.getenv("LLM_BASE_URL", DEFAULT_BASE_URL)

    # The "openai/" prefix routes this through CrewAI's native OpenAI-compatible
    # provider, pointed at base_url. That provider forwards max_retries to the
    # OpenAI SDK client, which is what actually performs the backoff.
    return LLM(
        model=f"openai/{model}",
        base_url=base_url,
        api_key=api_key,
        temperature=0.2,
        max_tokens=2048,
        max_retries=MAX_RETRIES,
    )
