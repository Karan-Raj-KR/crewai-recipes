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
└── main.py      # Entry point + sample inputs
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

All recipes use **NVIDIA NIM + LLaMA** as the default LLM:

```python
from crewai import LLM
import os

llm = LLM(
    model="openai/meta/llama-3.1-8b-instruct",  # or meta/llama-3.3-70b-instruct for more power
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=os.getenv("NVIDIA_API_KEY"),
    temperature=0.2,
)
```

To swap for a different provider (OpenAI, Anthropic, etc.), update the `model` string according to CrewAI / LiteLLM documentation, and update `requirements.txt` if necessary.

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
