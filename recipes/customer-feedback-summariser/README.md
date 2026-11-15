# 💬 Recipe: Customer Feedback Summariser

Turn raw customer feedback into a structured summary with themes, sentiment, concerns, and action items — using a two-agent CrewAI crew powered by **NVIDIA NIM** (defaults to `meta/llama-3.1-8b-instruct`; set `LLM_MODEL` for 70B).

**Time to first run: ~5 minutes** — clone, install, set key, run.

---

## What It Does

```
Input: raw customer feedback text
            │
            ▼
┌──────────────────────────────┐
│  Customer Feedback Analyst   │  ← Identifies themes, classifies sentiment,
│                              │    and extracts key customer concerns
└──────────────┬───────────────┘
               │ structured analysis
               ▼
┌──────────────────────────────┐
│  Action Summariser           │  ← Converts concerns into concrete action
│                              │    items; produces final structured summary
└──────────────────────────────┘
               │
               ▼
Output: sentiment · themes · key concerns · suggested actions
```

**Default model:** `meta/llama-3.1-8b-instruct` via NVIDIA NIM (set `LLM_MODEL=meta/llama-3.3-70b-instruct` for stronger reasoning)  
**LLM calls:** 2 (one per agent)  
**Typical run time:** ~20–40 seconds

---

## Prerequisites

- Python 3.10–3.12 (recommended)
- An NVIDIA NIM API key (free — [get one here](https://build.nvidia.com/))

---

## Setup

```bash
# From the repo root
cd recipes/customer-feedback-summariser

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate    # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure your API key
cp .env.example .env
# Edit .env → add: LLM_API_KEY=nvapi-...
```

---

## Usage

```bash
python run.py --feedback "YOUR CUSTOMER FEEDBACK HERE"
```

### Options

| Flag | Required | Description |
|------|----------|-------------|
| `--feedback` | ✅ Yes | Raw customer feedback text (reviews, survey responses, support comments) |
| `--verbose` | No | Enable verbose CrewAI execution trace |
| `--json` | No | Output result as structured JSON (matches `FeedbackSummary` schema) |
| `--help` | No | Show help and exit |

### Examples

```bash
# Basic usage
python run.py --feedback "Checkout is easy to use, but the payment page is slow. I also wish there was an option to save multiple cards."

# Multiple feedback items separated by newlines
python run.py --feedback "Login is confusing. Had to reset my password twice.
The dashboard loads instantly though — love that.
Would be great to have dark mode."

# Structured JSON output
python run.py \
  --feedback "Checkout is easy but the payment page is slow. No option to save cards." \
  --json
```

---

## Expected Output

### Human-readable (default)

```
💬  Customer Feedback Summariser — Starting
   Feedback: Checkout is easy to use, but the payment page is slow. I also...

────────────────────────────────────────────────────────────

════════════════════════════════════════════════════════════
📋  FEEDBACK SUMMARY
════════════════════════════════════════════════════════════
## Overall Sentiment
Mixed

## Themes
- Checkout experience
- Payment performance
- Saved payment methods

## Key Concerns
- The payment page loads slowly, creating friction at a critical conversion step.
- Users cannot save multiple payment cards, reducing convenience for repeat customers.

## Suggested Actions
- Investigate payment-page load time and optimise third-party payment script loading.
- Evaluate adding support for multiple saved payment methods in the user account settings.
════════════════════════════════════════════════════════════
```

### JSON output (`--json`)

```json
{
  "sentiment": "mixed",
  "themes": ["Checkout experience", "Payment performance", "Saved payment methods"],
  "concerns": [
    "Payment page loads slowly",
    "Users cannot save multiple cards"
  ],
  "actions": [
    "Investigate payment-page performance.",
    "Consider supporting multiple saved payment methods."
  ]
}
```

> ✅ **Schema:** The JSON output is validated against the `FeedbackSummary` Pydantic model defined in `tasks.py`.

---

## Structured Output Schema

When using `--json`, the output matches the `FeedbackSummary` model:

| Field | Type | Values |
|-------|------|--------|
| `sentiment` | `Literal` | `"positive"`, `"neutral"`, `"negative"`, `"mixed"` |
| `themes` | `list[str]` | 2–6 main topics identified in the feedback |
| `concerns` | `list[str]` | 1–5 important customer issues |
| `actions` | `list[str]` | 1–5 concrete action items for the team |

---

## File Structure

| File | Purpose |
|------|---------|
| `llm.py` | NVIDIA NIM LLM configuration — change model here |
| `agents.py` | Feedback Analyst and Action Summariser agent definitions |
| `tasks.py` | Task descriptions + `FeedbackSummary` Pydantic output model |
| `crew.py` | Crew assembly (sequential process) |
| `run.py` | CLI entry point (`argparse`) |
| `requirements.txt` | Python dependencies |
| `.env.example` | Template for environment variables |

---

## Customising

- **Add more sentiment labels:** Edit the `Literal` type in `tasks.py` → `FeedbackSummary.sentiment`.
- **Change the number of themes/actions:** Adjust the min/max hints in the task `description` strings in `tasks.py`.
- **Batch multiple feedback sources:** Concatenate them with clear delimiters before passing via `--feedback`.

---

## LLM Provider

This recipe uses **NVIDIA NIM** — a free, OpenAI-compatible inference API for NVIDIA-optimised models.

- Endpoint: `https://integrate.api.nvidia.com/v1`
- Default model: `meta/llama-3.1-8b-instruct` (fast, reliable on the free tier)
- Upgrade model: `meta/llama-3.3-70b-instruct` (stronger reasoning; slower, may be rate-limited on the free tier)
- Docs: [build.nvidia.com](https://build.nvidia.com/)

To swap models, set `LLM_MODEL` in your `.env` (no code change needed), or edit `DEFAULT_MODEL` in `llm.py`.
