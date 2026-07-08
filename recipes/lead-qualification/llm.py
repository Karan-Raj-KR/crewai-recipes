"""
lead-qualification — llm.py

Central LLM configuration using OpenAI-compatible endpoints.
All agents import from here so changing the model is a one-line edit — or,
better, an environment variable (LLM_MODEL) so you don't touch code at all.

By default, this is wired for NVIDIA NIM (Llama 3.1 8B).
CrewAI 1.x uses LiteLLM under the hood. For OpenAI-compatible endpoints,
the model string must be prefixed with "openai/" so LiteLLM routes correctly.
"""

import os

from crewai import LLM
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

# Default to NVIDIA NIM if not provided
DEFAULT_BASE_URL = "https://integrate.api.nvidia.com/v1"
DEFAULT_MODEL = "meta/llama-3.1-8b-instruct"

try:
    import litellm

    _RETRYABLE_ERRORS: tuple[type[Exception], ...] = (
        litellm.exceptions.Timeout,
        litellm.exceptions.RateLimitError,
        litellm.exceptions.APIConnectionError,
        litellm.exceptions.ServiceUnavailableError,
        litellm.exceptions.InternalServerError,
    )
except Exception:  # pragma: no cover
    _RETRYABLE_ERRORS = (Exception,)


class ResilientLLM(LLM):
    """A CrewAI LLM that retries transient API failures with backoff.

    Free tiers occasionally return timeouts or 429s under load. Rather
    than fail an entire crew run on one flaky call, retry up to 3 times with
    exponential backoff (2s → 4s, capped at 10s) before giving up.
    """

    @retry(
        retry=retry_if_exception_type(_RETRYABLE_ERRORS),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        stop=stop_after_attempt(3),
        reraise=True,
    )
    def call(self, *args: object, **kwargs: object) -> object:
        return super().call(*args, **kwargs)


def get_llm() -> LLM:
    """Return a CrewAI LLM configured via environment variables.

    Reads LLM_API_KEY from the environment (or .env file) and, optionally,
    LLM_MODEL and LLM_BASE_URL. Call load_dotenv() in your entry point (run.py)
    before importing this.

    Returns:
        A retry-wrapped LLM instance ready for use in CrewAI agents.

    Raises:
        EnvironmentError: If LLM_API_KEY is not set.
    """
    api_key = os.getenv("LLM_API_KEY")
    if not api_key:
        api_key = os.getenv("NVIDIA_API_KEY") # Backwards compatibility
        if api_key:
            print("WARNING: NVIDIA_API_KEY is deprecated. Please use LLM_API_KEY instead.")
        else:
            raise EnvironmentError(
                "LLM_API_KEY is not set.\n"
                "  1. Copy .env.example → .env\n"
                "  2. Add your key: LLM_API_KEY=your-key-here\n"
            )

    model = os.getenv("LLM_MODEL", os.getenv("NIM_MODEL", DEFAULT_MODEL))
    base_url = os.getenv("LLM_BASE_URL", DEFAULT_BASE_URL)

    # The "openai/" prefix tells LiteLLM (used by CrewAI) to route
    # this call to the OpenAI-compatible endpoint at base_url.
    return ResilientLLM(
        model=f"openai/{model}",
        base_url=base_url,
        api_key=api_key,
        temperature=0.2,
        max_tokens=2048,
    )
