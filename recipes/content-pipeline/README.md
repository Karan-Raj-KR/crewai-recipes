# 📝 Recipe: Content Production Pipeline

> ✅ **Status: Stable** — Fully working 4-agent crew that automates blog ideation, section outlining, short-form drafting, and actionable SEO review.

A four-agent CrewAI crew that automates blog content creation: Ideator Agent → Content Outline & Research Architect → Writer Agent → SEO & Quality Reviewer. Powered by NVIDIA NIM.

---

## What It Does

```
Blog Topic & Keywords
          │
          ▼
┌───────────────────────────┐
│  Content Ideator Agent    │  → 3 headline options & main angle
└─────────────┬─────────────┘
              │ ideation brief
              ▼
┌───────────────────────────┐
│  Research Architect       │  → Section-by-section outline
│                           │    Flags unverified claims
└─────────────┬─────────────┘
              │ article outline
              ▼
┌───────────────────────────┐
│  Blog Writer Agent        │  → Concise short-form draft (<500 words)
└─────────────┬─────────────┘
              │ raw draft
              ▼
┌───────────────────────────┐
│  SEO Reviewer Agent       │  → Concrete edit recommendations
│                           │    Polished final markdown article
└─────────────┬─────────────┘
              │
              ▼
     Final Article & SEO Report
```

## Token Budget & Model Optimization Note

`llm.py` defaults to `meta/llama-3.1-8b-instruct` with `max_tokens=2048`. To ensure complete generation across all 4 sequential agents without mid-sentence truncation, the Writer agent is explicitly scoped to produce a concise short-form blog post (under 500 words).

## Setup

```bash
cd recipes/content-pipeline
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add your LLM_API_KEY
```

## Run

### Interactive / CLI mode
```bash
python run.py --topic "Why Multi-Agent Systems are Replacing Single Prompt AI Workflows" --target_audience "Senior Developers & Architects" --keywords "Multi-Agent Systems, CrewAI, LLM Orchestration"
```

### Options
- `--topic`: Core blog topic or theme (default: `Autonomous AI Agents in Enterprise Software`).
- `--target_audience`, `--target-audience`, `--audience`: Target readership profile (default: `Software Architects & Tech Leaders`).
- `--keywords`: Comma-separated target keywords (default: `AI Agents, CrewAI, Workflow Automation`).

### Batch sample mode
```bash
python main.py
```

## Sample Output

```
📝  Content Production Pipeline — Generating Article

   Topic           : Why Multi-Agent Systems are Replacing Single Prompt AI Workflows
   Target Audience : Senior Developers & Architects
   Keywords        : Multi-Agent Systems, CrewAI, LLM Orchestration

────────────────────────────────────────────────────────────

============================================================
✨  SEO REVIEW & FINAL POLISHED ARTICLE
============================================================
### Actionable SEO & Readability Edits
- **Primary Keyword Integration**: Moved 'Multi-Agent Systems' into the main H1 headline and opening paragraph for early SEO signal.
- **Heading Optimization**: Enhanced H2 headers to include secondary keywords ('CrewAI', 'LLM Orchestration').
- **Readability**: Formatted technical comparisons into concise bullet points for scanability.

---

# Why Multi-Agent Systems are Replacing Single Prompt AI Workflows

Single-prompt AI interactions have reached their natural limit in complex software workflows. While a single prompt can summarize text or generate code snippets, building enterprise-grade automations requires orchestration, specialized roles, and error recovery—giving rise to **Multi-Agent Systems**.

## The Limits of Monolithic Prompts

Relying on a single prompt for complex tasks often leads to context degradation, hallucinated details, and unpredictable outputs. When an LLM is forced to plan, execute, and self-correct in a single pass, quality declines rapidly.

## Enter Multi-Agent Systems with CrewAI

Multi-agent architectures solve monolithic prompt limitations by breaking complex goals into discrete, specialized agent roles:

- **Role Specialization**: Agents act as narrow domain experts (e.g. Researchers, Coders, Validators).
- **Context Chaining**: Outputs from one task feed directly as structured context into the next.
- **LLM Orchestration**: Frameworks like **CrewAI** manage execution order, error retries, and fallback handling automatically.

## Conclusion

The shift from single-prompt experiments to robust multi-agent orchestration represents the next evolution in AI engineering. By combining specialized agents with structured workflows, teams can build reliable, production-ready AI applications.
============================================================
```

## Configuration

| Variable | Description | Required |
|----------|-------------|----------|
| `LLM_API_KEY` | Your NVIDIA API key | ✅ Yes |

## Architecture

| File | Purpose |
|------|---------|
| `agents.py` | Ideator, Researcher, Writer, and SEO Reviewer agents |
| `tasks.py` | Four sequential processing tasks |
| `crew.py` | Crew assembly |
| `run.py` | CLI runner with argument parser |
| `main.py` | Sample batch test script |
