"""
Lead Qualification Recipe — llm.py

Central LLM configuration using NVIDIA NIM (OpenAI-compatible endpoint).
All agents import from here so changing the model is a one-line edit — or,
better, an environment variable (NIM_MODEL) so you don't touch code at all.

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

# NVIDIA NIM base URL — OpenAI-compatible REST API
NIM_BASE_URL = "https://integrate.api.nvidia.com/v1"

# Default model: Llama 3.1 8B is fast and reliable on the NIM free tier.
# Override without editing code by exporting NIM_MODEL, e.g.:
#   export NIM_MODEL="meta/llama-3.3-70b-instruct"   # stronger reasoning, slower
# Full catalogue: https://build.nvidia.com/
DEFAULT_MODEL = "meta/llama-3.1-8b-instruct"

# Transient NIM failures worth retrying (free-tier timeouts, 429s, upstream
# hiccups). Imported defensively so a shift in litellm's internals can't break
# import — we fall back to retrying any exception in that unlikely case.
try:
    import litellm

    _RETRYABLE_ERRORS: tuple[type[Exception], ...] = (
        litellm.exceptions.Timeout,
        litellm.exceptions.RateLimitError,
        litellm.exceptions.APIConnectionError,
        litellm.exceptions.ServiceUnavailableError,
        litellm.exceptions.InternalServerError,
    )
except Exception:  # pragma: no cover - fallback if litellm layout changes
    _RETRYABLE_ERRORS = (Exception,)


class ResilientLLM(LLM):
    """A CrewAI LLM that retries transient NVIDIA NIM failures with backoff.

    The free NIM tier occasionally returns timeouts or 429s under load. Rather
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
    """Return a CrewAI LLM configured to use NVIDIA NIM.

    Reads NVIDIA_API_KEY from the environment (or .env file) and, optionally,
    NIM_MODEL to pick a model. Call load_dotenv() in your entry point (run.py)
    before importing this.

    Returns:
        A retry-wrapped LLM instance ready for use in CrewAI agents.

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

    model = os.getenv("NIM_MODEL", DEFAULT_MODEL)

    # The "openai/" prefix tells LiteLLM (used by CrewAI) to route
    # this call to the OpenAI-compatible endpoint at base_url.
    return ResilientLLM(
        model=f"openai/{model}",
        base_url=NIM_BASE_URL,
        api_key=api_key,
        temperature=0.2,
        max_tokens=2048,
    )
