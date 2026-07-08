"""
FAQ Bot Recipe — llm.py

Central LLM configuration using NVIDIA NIM (OpenAI-compatible endpoint).
Low temperature is intentional — factual Q&A should be deterministic.

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

NIM_BASE_URL = "https://integrate.api.nvidia.com/v1"

# Default: Llama 3.1 8B — fast and reliable on the NIM free tier.
# Override without editing code: export NIM_MODEL="meta/llama-3.3-70b-instruct"
DEFAULT_MODEL = "meta/llama-3.1-8b-instruct"

# Transient NIM failures worth retrying; imported defensively.
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

    Retries up to 3 times with exponential backoff (2s → 4s, capped at 10s)
    on free-tier timeouts / 429s before giving up.
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

    Returns:
        A retry-wrapped LLM instance.

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

    return ResilientLLM(
        model=f"openai/{model}",
        base_url=NIM_BASE_URL,
        api_key=api_key,
        temperature=0.1,  # Low temp — factual Q&A, not creative writing
        max_tokens=1024,
    )
