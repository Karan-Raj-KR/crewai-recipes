# Architecture Overview

This document explains how `crewai-recipes` is structured and how the recipes are designed to be composed and extended.

---

## Core Abstractions

Every recipe follows the same four-file pattern, mirroring CrewAI's own architecture:

```
recipe/
├── agents.py    # Who does the work
├── tasks.py     # What work gets done
├── crew.py      # How agents and tasks are assembled
├── llm.py       # LLM config — reads LLM_API_KEY, LLM_MODEL, LLM_BASE_URL
├── run.py       # CLI entry point (argparse + crew.kickoff)
└── main.py      # Interactive sample runner (edit-and-run)
```

### Why this structure?

- **Separation of concerns** — each file has one job. Agents define *who* acts; tasks define *what* they do; crew defines *how* they collaborate.
- **Testability** — you can unit-test `build_agents()` and `build_tasks()` independently.
- **Composability** — agents from one recipe can be imported into another.

---

## Agent Design Philosophy

All agents in this library follow three rules:

1. **Single responsibility** — each agent has a narrowly defined `role` and `goal`. Avoid "do everything" agents.
2. **Honest backstory** — the `backstory` sets the expert persona without overpromising. Agents are told *not* to hallucinate.
3. **Low temperature** — creativity is not the goal; accuracy is. Most recipes use `temperature=0.1–0.3`.

---

## Task Context Graph

Tasks communicate through CrewAI's `context` parameter, forming a directed acyclic graph (DAG):

```
Task A (Research)
    │
    ▼
Task B (Scoring)   ← context=[Task A]
    │
    ▼
Task C (Report)    ← context=[Task A, Task B]
```

This ensures each task receives the full upstream context it needs.

---

## LLM Configuration

All recipes use **NVIDIA NIM + LLaMA** as the default LLM, configured via `llm.py`:

```python
from llm import get_llm

llm = get_llm()  # reads LLM_API_KEY, LLM_MODEL, LLM_BASE_URL from env
```

`get_llm()` returns a `ResilientLLM` that retries transient NIM failures with exponential backoff. Defaults to `meta/llama-3.1-8b-instruct` via NVIDIA NIM. To swap provider or model, set `LLM_API_KEY`, `LLM_MODEL`, and `LLM_BASE_URL` in `.env` — no code changes needed. See [docs/providers.md](./providers.md) for examples.

---

## Process Types

Recipes use either:

| Process | When to use |
|---------|------------|
| `Process.sequential` | Tasks depend on previous results (most recipes) |
| `Process.hierarchical` | A manager agent orchestrates parallel workers (coming soon) |

---

## Adding Tools

Agents can be extended with custom tools:

```python
from crewai_tools import SerperDevTool, FileReadTool

agent = Agent(
    ...
    tools=[SerperDevTool(), FileReadTool()],
)
```

See the [CrewAI tools documentation](https://docs.crewai.com/concepts/tools) for the full tool catalogue.
