# Contributing to crewai-recipes

Thank you for your interest in contributing! `crewai-recipes` grows through community recipes — your workflow automation idea could help thousands of developers.

Please take a few minutes to read this guide before opening a PR.

---

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [How to Add a New Recipe](#how-to-add-a-new-recipe)
3. [Recipe Structure](#recipe-structure)
4. [Coding Style](#coding-style)
5. [Pull Request Process](#pull-request-process)
6. [Issue Labels](#issue-labels)
7. [Improving Existing Recipes](#improving-existing-recipes)

---

## Code of Conduct

This project follows the [Contributor Covenant](./CODE_OF_CONDUCT.md). By participating, you agree to uphold its standards. Please report unacceptable behaviour to the maintainers.

---

## How to Add a New Recipe

### 1. Open an issue first (for new recipes)

Before building a brand-new recipe, [open a "Recipe Proposal" issue](https://github.com/Karan-Raj-KR/crewai-recipes/issues/new?template=recipe_proposal.yml) so maintainers can:

- Confirm the idea fits the project scope
- Prevent duplicate effort
- Help shape the agent/task design early

You can skip this step for **bug fixes**, **documentation improvements**, or **minor enhancements** to existing recipes.

### 2. Fork & branch

```bash
# Fork on GitHub, then:
git clone https://github.com/<your-username>/crewai-recipes.git
cd crewai-recipes
git checkout -b recipe/my-awesome-recipe
```

### 3. Create your recipe directory

```
recipes/
└── my-awesome-recipe/
    ├── agents.py          # Agent definitions
    ├── tasks.py           # Task definitions
    ├── crew.py            # Crew assembly
    ├── main.py            # Entry point
    ├── tools/             # (optional) custom tools
    │   └── my_tool.py
    ├── knowledge/         # (optional) RAG documents, CSVs, etc.
    ├── requirements.txt   # Pinned dependencies
    ├── .env.example       # Required env vars (no real values!)
    └── README.md          # Recipe-level documentation
```

### 4. Write your recipe

Follow the [Recipe Structure](#recipe-structure) and [Coding Style](#coding-style) sections below.

### 5. Test it end-to-end

Run your recipe from a **fresh virtual environment** to make sure the `requirements.txt` is complete:

```bash
python -m venv test_venv
source test_venv/bin/activate
pip install -r recipes/my-awesome-recipe/requirements.txt
cd recipes/my-awesome-recipe
python main.py
```

### 6. Open a Pull Request

Push your branch and open a PR against `main`. Fill in the PR template completely.

---

## Recipe Structure

Every recipe **must** include:

| File | Purpose |
|------|---------|
| `agents.py` | Define all `Agent` objects with `role`, `goal`, `backstory`, and `llm` |
| `tasks.py` | Define all `Task` objects with `description`, `expected_output`, and `agent` |
| `crew.py` | Assemble the `Crew` with agents, tasks, and `process` |
| `main.py` | CLI entry point — accepts inputs and calls `crew.kickoff()` |
| `requirements.txt` | All dependencies with pinned versions |
| `.env.example` | List of required environment variables (values must be placeholders) |
| `README.md` | What the recipe does, inputs/outputs, sample run, and architecture diagram (ASCII is fine) |

**LLM requirement:** The default `llm` in every recipe must use **NVIDIA NIM + LLaMA** (e.g., `meta/llama-3.1-8b-instruct` or `meta/llama-3.3-70b-instruct`). Supporting other providers as optional is fine.

---

## Coding Style

### Python version

Require **Python 3.10+**. Use `python_requires = ">=3.10"` if you add a `pyproject.toml`.

### Type hints

All public functions and class methods **must** have type hints:

```python
def build_crew(lead_data: dict[str, str]) -> Crew:
    """Build and return the lead qualification crew."""
    ...
```

### Docstrings

Use Google-style docstrings for modules, classes, and functions:

```python
def score_lead(lead: dict[str, str]) -> float:
    """Score an inbound lead based on ICP fit.

    Args:
        lead: Dictionary containing lead attributes (name, company, role, etc.)

    Returns:
        A score between 0.0 and 1.0 where 1.0 is a perfect ICP match.

    Raises:
        ValueError: If required lead fields are missing.
    """
    ...
```

### General rules

- Use `f-strings` over `.format()` or `%` formatting.
- Prefer `pathlib.Path` over `os.path` for file operations.
- Load environment variables with `python-dotenv`; never hardcode API keys.
- Keep `main.py` thin — logic belongs in `agents.py`, `tasks.py`, or `crew.py`.
- Avoid global mutable state.
- Run `ruff check .` before opening a PR (install: `pip install ruff`).

### Linting / formatting

We use **[Ruff](https://github.com/astral-sh/ruff)** for linting and formatting:

```bash
pip install ruff
ruff check recipes/my-awesome-recipe/
ruff format recipes/my-awesome-recipe/
```

CI will block PRs that fail Ruff checks.

---

## Pull Request Process

1. **Target branch:** `main`
2. **PR title format:** `feat(recipe): add my-awesome-recipe` or `fix(lead-qualification): handle missing email field`
3. **Fill in the PR template** — incomplete PRs may be closed without review.
4. **One recipe per PR** — keeps reviews focused.
5. A maintainer will review within **7 days**. We may ask for changes; please respond within 14 days or the PR may be closed.
6. PRs are merged by a maintainer via **squash merge**.

---

## Issue Labels

| Label | Meaning |
|-------|---------|
| `bug` | Something in an existing recipe is broken |
| `enhancement` | Improvement to the project in general |
| `recipe: new` | Proposal for a brand-new recipe |
| `recipe: improvement` | Enhancement to an existing recipe |
| `documentation` | Documentation-only change |
| `docs` | Documentation improvements tied to a specific recipe or guide |
| `good first issue` | Great for first-time contributors |
| `help wanted` | Maintainers need community help |
| `question` | Further information is requested |
| `duplicate` | Already reported / being tracked elsewhere |
| `invalid` | This doesn't seem right |
| `wontfix` | Out of scope for this project |

---

## Improving Existing Recipes

- **Bug fixes** — open an issue, then PR. Link the issue in the PR.
- **Documentation** — PRs welcome without a prior issue.
- **Performance / prompt tuning** — include before/after sample outputs in the PR description so reviewers can evaluate the improvement.

---

Thank you for helping make `crewai-recipes` better! 🚀
