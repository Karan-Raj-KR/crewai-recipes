# 💬 Recipe: FAQ / Support Bot

A two-agent CrewAI crew that answers customer questions from a built-in knowledge base — with graceful fallback when no answer is found. Powered by Groq LLaMA.

---

## What It Does

```
Customer Question
      │
      ▼
┌──────────────────────────┐
│  Knowledge Retriever      │  ← Searches the FAQ knowledge base
│  (no hallucination rule)  │
└─────────────┬────────────┘
              │  Matched entries (or "no match")
              ▼
┌──────────────────────────┐
│  Response Drafter         │  ← Writes warm, customer-facing reply
│  (graceful fallback)      │  ← Escalates to human if no answer
└──────────────────────────┘
              │
              ▼
     Ready-to-send Support Response
```

## Setup

```bash
cd recipes/faq-bot
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add your GROQ_API_KEY
```

## Run

```bash
python main.py
```

Edit `SAMPLE_QUESTIONS` in `main.py` and change the list index to test different questions.

## Extending With a Real Knowledge Base

The static `knowledge_base.py` can be swapped for a vector store:

```python
# Example: Chroma vector store
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings

vectorstore = Chroma(persist_directory="./kb_store", embedding_function=...)
retriever = vectorstore.as_retriever()
```

## Knowledge Base Topics Covered

| Topic | Summary |
|-------|---------|
| Pricing | Plan tiers and trial info |
| Free Trial | How to start, no CC required |
| Cancellation | Self-serve, no fees |
| Data Export | CSV/JSON export steps |
| Integrations | Slack, HubSpot, Salesforce, Zapier |
| Security | AES-256, TLS 1.3, SOC 2, GDPR |
| Support | Channels by plan tier |
| Refunds | 7-day policy |

## Configuration

| Variable | Description | Required |
|----------|-------------|----------|
| `GROQ_API_KEY` | Your Groq API key | ✅ Yes |

## Architecture

| File | Purpose |
|------|---------|
| `agents.py` | Retriever and Response Drafter agents |
| `knowledge_base.py` | Static FAQ entries + formatter |
| `tasks.py` | Retrieval and response tasks |
| `crew.py` | Crew assembly |
| `main.py` | CLI entry point |
