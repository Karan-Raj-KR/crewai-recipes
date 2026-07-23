# NVIDIA NIM + CrewAI Setup Guide

A step-by-step guide to getting your development environment ready for any recipe in this library.

---

## 1. Get an NVIDIA NIM API Key

1. Go to [build.nvidia.com](https://build.nvidia.com/) and sign up (it's free).
2. Browse to any model (e.g., [Llama 3.1 8B Instruct](https://build.nvidia.com/meta/llama-3.1-8b-instruct) — the default these recipes use).
3. Click **"Get API Key"** in the top right — you'll get an `nvapi-...` key.
4. The free tier includes generous monthly credits. No credit card required.

Keep this key secret — never commit it to version control. The `.gitignore` in this repo already blocks `.env` files.

---

## 2. Python Environment

We recommend Python **3.10–3.12** (Python 3.14 has limited wheel availability for some dependencies).

```bash
# Check your Python version
python --version

# Create a virtual environment (inside the recipe directory)
python -m venv .venv
source .venv/bin/activate    # Windows: .venv\Scripts\activate
```

---

## 3. Install Dependencies

Each recipe has its own `requirements.txt`. Install from within the recipe directory:

```bash
cd recipes/lead-qualification
pip install -r requirements.txt
```

---

## 4. Set Your API Key

**Option A — .env file (recommended for local dev):**
```bash
cp .env.example .env
# Edit .env and add your key:
# LLM_API_KEY=nvapi-...
```

**Option B — Environment variable (recommended for CI/CD):**
```bash
export LLM_API_KEY="nvapi-..."    # Linux/macOS
set LLM_API_KEY=nvapi-...         # Windows CMD
$env:LLM_API_KEY="nvapi-..."      # Windows PowerShell
```

Every recipe loads `.env` automatically via `python-dotenv`.

---

## 5. How NIM Works With CrewAI

NVIDIA NIM exposes an **OpenAI-compatible REST API** at:
```
https://integrate.api.nvidia.com/v1
```

CrewAI's `LLM` class accepts a custom `base_url`, so we configure it like this:

```python
import os
from crewai import LLM

# All recipes use get_llm() from llm.py — reads LLM_API_KEY, LLM_MODEL,
# and LLM_BASE_URL from the environment so you can switch providers or models
# without editing code.
from llm import get_llm

llm = get_llm()  # returns an LLM pre-configured from env vars, with retries
```

No additional adapter libraries needed — just `crewai` and `openai`.

---

## 6. Choose a Model

| Model | Context | Best for |
|-------|---------|----------|
| `meta/llama-3.1-8b-instruct` | 128K | **Default** — fast, reliable on the free tier |
| `meta/llama-3.3-70b-instruct` | 128K | Stronger reasoning (slower; may be rate-limited on the free tier) |
| `nvidia/llama-3.1-nemotron-70b-instruct` | 128K | Enterprise-grade instruction following |
| `meta/llama-3.2-3b-instruct` | 128K | Ultra-fast, lower quality |

Pick a model **without editing code** by setting `LLM_MODEL` in your `.env` (or exporting it):

```bash
# .env
LLM_MODEL=meta/llama-3.3-70b-instruct
```

Or change the baked-in default via `DEFAULT_MODEL` in a recipe's `llm.py`.

---

## 7. Run a Recipe

```bash
cd recipes/lead-qualification
python run.py --company "Acme Corp" --description "A 50-person B2B SaaS startup..."
```

You should see CrewAI's verbose output as each agent works, followed by the final result.

---

## Troubleshooting

| Error | Solution |
|-------|---------|
| `EnvironmentError: LLM_API_KEY is not set` | Check your `.env` file or export the variable |
| `401 Unauthorized` | Key may be expired or wrong — regenerate at build.nvidia.com |
| `404 Not Found` on model | Use the exact model ID from the [NIM catalogue](https://build.nvidia.com/) |
| `ModuleNotFoundError: crewai` | Run `pip install -r requirements.txt` in the recipe directory |
| `Python 3.14` wheel errors | Use Python 3.10–3.12 for best compatibility |
