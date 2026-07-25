# Using Different LLM Providers

`crewai-recipes` defaults to **NVIDIA NIM** (Llama 3.1 8B), but you can easily swap to any OpenAI-compatible provider by setting three environment variables:

1. `LLM_BASE_URL`: The OpenAI-compatible API endpoint.
2. `LLM_MODEL`: The model name as expected by the provider.
3. `LLM_API_KEY`: Your authentication key for the provider.

No code changes are required.

---

## Secondary & Fallback LLM Provider Configuration (#75)

You can also configure an optional **secondary / fallback provider** to switch providers seamlessly without changing code or editing primary credentials.

### Secondary Provider Environment Variables:
- `LLM_FALLBACK_API_KEY`: Authentication key for the secondary provider.
- `LLM_FALLBACK_MODEL`: Model name as expected by the secondary provider.
- `LLM_FALLBACK_BASE_URL`: OpenAI-compatible API endpoint for the secondary provider.
- `LLM_PROVIDER`: Optional provider selection (`primary` or `fallback`, default: `primary`).

### Worked Example: Primary (NVIDIA NIM) + Fallback (OpenRouter)

```env
# Primary Provider (NVIDIA NIM)
LLM_BASE_URL=https://integrate.api.nvidia.com/v1
LLM_MODEL=meta/llama-3.1-8b-instruct
LLM_API_KEY=nvapi-...

# Secondary / Fallback Provider (OpenRouter)
LLM_FALLBACK_BASE_URL=https://openrouter.ai/api/v1
LLM_FALLBACK_MODEL=meta-llama/llama-3.1-8b-instruct:free
LLM_FALLBACK_API_KEY=sk-or-v1-...
```

### Behavior:
1. **Default Mode (`LLM_PROVIDER=primary` or unset)**:
   - Uses `LLM_API_KEY` with `LLM_BASE_URL` and `LLM_MODEL`.
   - If `LLM_API_KEY` is missing/unset but `LLM_FALLBACK_API_KEY` is present, `get_llm()` automatically falls back to the secondary provider configuration.
2. **Explicit Fallback Mode (`LLM_PROVIDER=fallback`)**:
   - Explicitly instructs `get_llm()` to construct the LLM object using the secondary provider configuration (`LLM_FALLBACK_*`).
3. **Programmatic Selection**:
   - Recipe scripts can pass `get_llm(provider="fallback")` directly.

---

## NVIDIA NIM (Default)
NVIDIA provides a generous free tier for top open-source models.
- **Get a key**: [build.nvidia.com](https://build.nvidia.com)
- **Environment**:
  ```env
  LLM_BASE_URL=https://integrate.api.nvidia.com/v1
  LLM_MODEL=meta/llama-3.1-8b-instruct
  LLM_API_KEY=nvapi-...
  ```

## Cerebras
Cerebras offers insanely fast inference for Llama models.
- **Get a key**: [cloud.cerebras.ai](https://cloud.cerebras.ai)
- **Environment**:
  ```env
  LLM_BASE_URL=https://api.cerebras.ai/v1
  LLM_MODEL=llama3.1-8b
  LLM_API_KEY=csk-...
  ```

## OpenRouter
OpenRouter aggregates hundreds of models, often with free tiers.
- **Get a key**: [openrouter.ai](https://openrouter.ai)
- **Environment**:
  ```env
  LLM_BASE_URL=https://openrouter.ai/api/v1
  LLM_MODEL=meta-llama/llama-3.1-8b-instruct:free
  LLM_API_KEY=sk-or-v1-...
  ```

## GitHub Models
GitHub provides a free tier for developers to test models via their marketplace.
- **Get a key**: [github.com/marketplace/models](https://github.com/marketplace/models) (Use a classic Personal Access Token or fine-grained token)
- **Environment**:
  ```env
  LLM_BASE_URL=https://models.inference.ai.azure.com
  LLM_MODEL=Llama-3.3-70B-Instruct
  LLM_API_KEY=ghp_...
  ```

## Google Gemini (OpenAI Compatible)
Google's Gemini API now supports OpenAI-compatible endpoints natively.
- **Get a key**: [aistudio.google.com](https://aistudio.google.com)
- **Environment**:
  ```env
  LLM_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
  LLM_MODEL=gemini-2.5-flash
  LLM_API_KEY=AIza...
  ```

> **Note**: For backward compatibility, `NVIDIA_API_KEY` is still supported but will trigger a deprecation warning in the console. Please migrate to `LLM_API_KEY`.
