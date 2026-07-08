"""
WhatsApp Action Sim Recipe — llm.py

Central LLM configuration using NVIDIA NIM (OpenAI-compatible endpoint).
"""

import os
from crewai import LLM

NIM_BASE_URL = "https://integrate.api.nvidia.com/v1"
NIM_MODEL = "meta/llama-3.1-8b-instruct"

def get_llm() -> LLM:
    """Return a CrewAI LLM configured to use NVIDIA NIM."""
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
        temperature=0.2,
        max_tokens=1024,
    )
