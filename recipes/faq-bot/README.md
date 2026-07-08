# 💬 Recipe: FAQ / Support Bot

Answer customer questions from a built-in knowledge base using a **single-agent CrewAI crew** powered by **NVIDIA NIM (Llama 3.1 8B Instruct)**.

**Time to first run: ~5 minutes** — clone, install, set key, run.

---

## What It Does

```
Customer Question (+ optional name)
          │
          ▼
┌──────────────────────────────┐
│  Orbitly Support Agent        │  ← Searches FAQ knowledge base
│  (no-hallucination rule)      │  ← If no match → graceful fallback
│                               │  ← Personalised reply using customer name
└──────────────────────────────┘
          │
          ▼
   Ready-to-send support reply (plain text, under 120 words)
```

**Product:** "Orbitly" — a fictional B2B project management SaaS  
**Knowledge base:** 6 hardcoded FAQ entries (pricing, trial, import, integrations, security, cancellation)  
**Model used:** `meta/llama-3.1-8b-instruct` via NVIDIA NIM  
**LLM calls:** 1  
**Typical run time:** ~5-15 seconds  

---

## Prerequisites

- Python 3.10–3.12 (recommended)
- An NVIDIA NIM API key (free — [get one here](https://build.nvidia.com/))

---

## Setup

```bash
# From the repo root
cd recipes/faq-bot

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate    # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure your API key
cp .env.example .env
# Edit .env → add: NVIDIA_API_KEY=nvapi-...
```

---

## Usage

```bash
python run.py --question "CUSTOMER QUESTION"
python run.py --question "CUSTOMER QUESTION" --name "Customer Name"
```

### Options

| Flag | Required | Default | Description |
|------|----------|---------|-------------|
| `--question` | ✅ Yes | — | The customer's question (wrap in quotes) |
| `--name` | No | `there` | Customer name for personalised greeting |
| `--help` | No | — | Show help and exit |

### Examples

```bash
# Basic pricing question
python run.py --question "How much does Orbitly cost?"

# Personalised question
python run.py --question "Do you offer refunds?" --name "Alex"

# Integration question
python run.py --question "Does Orbitly integrate with Slack?" --name "Priya"

# Test fallback (topic not in KB)
python run.py --question "Do you have a mobile app for Android?" --name "Jordan"
```

---

## Knowledge Base Topics

| # | Topic | Question |
|---|-------|---------|
| 1 | Pricing | How much does Orbitly cost? |
| 2 | Free Trial | Can I try Orbitly before paying? |
| 3 | Data Import | Can I import from Jira or Trello? |
| 4 | Integrations | Which tools does Orbitly integrate with? |
| 5 | Security | Is my data secure? Is Orbitly GDPR compliant? |
| 6 | Cancellation & Refunds | What happens if I cancel? Do you offer refunds? |

Questions outside these topics trigger a graceful fallback directing the customer to support@orbitly.example.com.

---

## Expected Output

The pricing question above, showing the **final result block** (the verbose
per-agent trace is omitted). Captured from a real call to NVIDIA NIM
`meta/llama-3.1-8b-instruct` on 2026-07-08:

```
🤖  Orbitly FAQ Bot — Starting
   Customer : Priya
   Question : How much does Orbitly cost?

════════════════════════════════════════════════════════════
💬  SUPPORT REPLY
════════════════════════════════════════════════════════════
Hi Priya,

Orbitly offers three plans: Solo ($0/month, 1 user, 3 projects), Team
($29/month per user, unlimited projects, priority support), and Enterprise
(custom pricing, SSO, dedicated SLA, audit logs). Annual billing gives you
2 months free.

Is there anything else I can help with?
════════════════════════════════════════════════════════════
```

> Exact wording varies slightly by model and run.

---

## Extending the Knowledge Base

Edit `knowledge_base.py` — add more dicts to `FAQ_KNOWLEDGE_BASE`:

```python
{
    "topic": "mobile app",
    "question": "Is there a mobile app?",
    "answer": "Yes! Orbitly is available on iOS and Android. Search 'Orbitly' in the App Store or Google Play.",
},
```

In production, swap the static list for a vector store:
```python
from langchain_community.vectorstores import Chroma
# ... embed your FAQ docs and query with similarity search
```

---

## File Structure

| File | Purpose |
|------|---------|
| `llm.py` | NVIDIA NIM LLM config — change model here |
| `agents.py` | Single Orbitly Support Specialist agent |
| `knowledge_base.py` | 6 hardcoded FAQ entries + text formatter |
| `tasks.py` | Single answer task with KB context and guidelines |
| `crew.py` | Single-agent crew assembly |
| `run.py` | CLI entry point (`argparse`) |
| `requirements.txt` | Python dependencies |
| `.env.example` | Template for NVIDIA_API_KEY |

---

## LLM Provider

This recipe uses **NVIDIA NIM** — a free, OpenAI-compatible inference API.

- Endpoint: `https://integrate.api.nvidia.com/v1`
- Default model: `meta/llama-3.1-8b-instruct` (fast, free tier)
- Upgrade model: `meta/llama-3.3-70b-instruct` (best quality)
- Docs: [build.nvidia.com](https://build.nvidia.com/)
