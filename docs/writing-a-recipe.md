# Writing a New Recipe

A hands-on walkthrough for building your first `crewai-recipes` recipe. It
should take about 30–45 minutes end to end. If anything here is unclear, that's
a docs bug — [open an issue](https://github.com/Karan-Raj-KR/crewai-recipes/issues/new/choose).

By the end you'll have a self-contained recipe that clones, installs, and runs
with a single API key — the bar every recipe in this repo meets.

---

## 0. Propose it first (for brand-new recipes)

Open a [Recipe Proposal issue](https://github.com/Karan-Raj-KR/crewai-recipes/issues/new?template=recipe_proposal.yml)
before writing much code. It takes two minutes, prevents duplicate effort, and
lets a maintainer help shape the agent/task design early. (Bug fixes and small
improvements don't need this.)

---

## 1. Start from an existing recipe

Don't start from a blank folder — copy the closest working recipe and adapt it.
Two good starting points:

| If your recipe is… | Copy | Why |
|--------------------|------|-----|
| **one agent, one task** (classify, answer, summarize) | [`recipes/faq-bot/`](../recipes/faq-bot/) | Minimal single-agent shape |
| **multiple agents in sequence** (research → act) | [`recipes/lead-qualification/`](../recipes/lead-qualification/) | Two agents passing context |

```bash
cp -r recipes/faq-bot recipes/my-awesome-recipe
cd recipes/my-awesome-recipe
```

---

## 2. Know the file layout

Every recipe is **self-contained** — it owns all of its files and never imports
from another recipe:

| File | What it holds |
|------|---------------|
| `llm.py` | NVIDIA NIM config. **Copy this file as-is** — see step 3. |
| `agents.py` | `Agent` objects (`role`, `goal`, `backstory`, `llm`) |
| `tasks.py` | `Task` objects (`description`, `expected_output`, `agent`) |
| `crew.py` | Assembles the `Crew` (agents + tasks + `process`) |
| `run.py` | CLI entry point — `argparse`, `load_dotenv()`, `crew.kickoff()` |
| `requirements.txt` | Pinned deps (start from the copied one) |
| `.env.example` | `NVIDIA_API_KEY` + optional `NIM_MODEL` placeholders — **no real keys** |
| `README.md` | What it does, setup, usage, a real Expected Output block |

See [architecture.md](./architecture.md) for the reasoning behind this split.

---

## 3. Keep `llm.py` exactly as-is

Every recipe uses the same `llm.py`: it defaults to `meta/llama-3.1-8b-instruct`,
lets users pick a model via the `NIM_MODEL` env var, and wraps calls in
`ResilientLLM` (retries transient NIM timeouts/429s with exponential backoff).
**Copy it unchanged** — only adjust `temperature`/`max_tokens` if your task needs it.

```python
# in agents.py
from llm import get_llm

llm = get_llm()
agent = Agent(role="…", goal="…", backstory="…", llm=llm)
```

There's no reason to hand-roll LLM config or retries — reuse the shared pattern.

---

## 4. Define agents, tasks, and the crew

- **Agents** (`agents.py`): give each a narrow `role` and `goal`. One job per agent — avoid "do everything" agents. See [agent-patterns.md](./agent-patterns.md).
- **Tasks** (`tasks.py`): set a precise `expected_output` — it's the biggest lever on output quality. Chain steps with `context=[previous_task]`.
- **Crew** (`crew.py`): assemble with `Process.sequential` unless you specifically need a manager agent.

Keep `run.py` thin: parse args, `load_dotenv()` **before** importing `crew`, kick off, print the result.

```python
from dotenv import load_dotenv
load_dotenv()                    # must run before importing crew/llm
from crew import build_crew      # noqa: E402
```

---

## 5. Run it from a fresh virtual environment

This is how you prove `requirements.txt` is complete — the #1 thing that breaks
recipes for other people:

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # then add your NVIDIA_API_KEY
python run.py --help
python run.py ...                # a real invocation
```

Paste the **final result block** of a real run into your README's *Expected
Output* section — the final output only, not the verbose per-agent trace.

---

## 6. Lint and format

CI runs [Ruff](https://github.com/astral-sh/ruff); match it locally before pushing:

```bash
pip install ruff
ruff check recipes/my-awesome-recipe/
ruff format recipes/my-awesome-recipe/
```

Add type hints and Google-style docstrings on public functions (see
[CONTRIBUTING.md](../CONTRIBUTING.md#coding-style)).

---

## 7. Wire it into the repo

- Add a row to the **Recipes** table in the [top-level README](../README.md) with the right status (🚧 Scaffold or ✅ Stable).
- If it needs a new CI import check, mirror the existing jobs in [`.github/workflows/ci.yml`](../.github/workflows/ci.yml).

---

## 8. Open the PR

Push your branch and open a PR against `main`. Fill in the
[PR template](../.github/PULL_REQUEST_TEMPLATE.md) checklist: runs locally,
README updated, no secrets, one recipe per PR. A maintainer reviews within ~7 days.

---

That's it — you've shipped a recipe. 🎉 If any step tripped you up, improving this
guide is itself a great first contribution.
