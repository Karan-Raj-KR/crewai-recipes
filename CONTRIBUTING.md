# Contributing to crewai-recipes

Thank you for your interest in contributing! `crewai-recipes` grows through community recipes — your workflow automation idea could help thousands of developers.

Please take a few minutes to read this guide before opening a PR.

---

## Table of Contents

1. [First time contributing to open source? Start here](#first-time-contributing-to-open-source-start-here)
2. [Code of Conduct](#code-of-conduct)
3. [How to Add a New Recipe](#how-to-add-a-new-recipe)
4. [Recipe Structure](#recipe-structure)
5. [Coding Style](#coding-style)
6. [Running Recipes with Docker](#running-recipes-with-docker)
7. [Pull Request Process](#pull-request-process)
8. [Issue Labels](#issue-labels)
9. [Improving Existing Recipes](#improving-existing-recipes)

---

## First time contributing to open source? Start here

Welcome — you're very much in the right place. This project is intentionally beginner-friendly, and you don't need any prior open-source experience to land your first PR. If you've never done this before, use the path below; every step is short and safe to try.

### The absolute-beginner path (≈ 30 minutes end-to-end)

1. **Pick an issue that says `good first issue`.** [Browse the list here.](https://github.com/Karan-Raj-KR/crewai-recipes/labels/good%20first%20issue) Read the whole issue — every `good first issue` in this repo lists the exact files to touch and what "done" looks like.
2. **Comment on the issue to claim it** (something like "I'd like to try this — assigning myself"). A bot will assign you within ~30 seconds and drop a welcome comment with the links you'll need. You can only have **2 open assignments at a time** — this is a soft cap so nothing gets stuck.
3. **Fork the repo** — click the "Fork" button at the top-right of the [repo page](https://github.com/Karan-Raj-KR/crewai-recipes). GitHub makes a copy under your own account that you're allowed to push to.
4. **Clone your fork** and make a branch:
   ```bash
   git clone https://github.com/<your-username>/crewai-recipes.git
   cd crewai-recipes
   git checkout -b fix/issue-<number>-short-description
   ```
5. **Make the change.** Follow the "what to change" section of the issue. If you get stuck, comment on the issue — that's exactly what the comments are for, and nobody will judge a question.
6. **Test it locally.** For a docs/typo fix, just re-read the file. For a code change, follow the "Test it end-to-end" step below (or the pytest snippet at the bottom of the issue if it has one).
7. **Commit and push:**
   ```bash
   git add .
   git commit -m "fix(<area>): short imperative summary"
   git push -u origin fix/issue-<number>-short-description
   ```
8. **Open the pull request.** GitHub will show a big green button when you push — click it, and it'll open a PR draft against `Karan-Raj-KR/crewai-recipes:main`. Fill in the template — the `Closes #<number>` line is important: it auto-closes the issue when the PR merges.
9. **CI will run automatically.** If something turns red, click the failing job to see the error — most first-time failures are ruff formatting (`ruff format recipes/<recipe>/` fixes it) or an unpinned dependency. A maintainer will help if it's not obvious.
10. **A maintainer reviews within 7 days.** If they ask for changes, push another commit to the same branch — the PR updates itself. Nothing to re-open.

That's the whole flow. Every open-source PR you ever ship will follow roughly the same 10 steps.

### If you get stuck

- **"I don't understand what the issue wants."** Comment on the issue — literally paste the sentence that confused you.
- **"CI is red and I don't know why."** Post the failing job's error in the PR — a maintainer will unblock you.
- **"My branch is behind main."** From your branch: `git fetch upstream main && git merge upstream/main` (`upstream` is the original repo — set with `git remote add upstream https://github.com/Karan-Raj-KR/crewai-recipes.git` once).
- **"I opened a PR but want to change my mind."** Just comment on the PR saying so — closing it is one click, no explanation needed.

### First-timer-friendly labels

| Label | What it means |
|-------|---------------|
| `good first issue` | Fully scoped, small, safe to learn on. Start here. |
| `ECSoC26-L1` | Absolute-beginner effort (docs, small edits, single-file changes). |
| `ECSoC26-L2` | Intermediate (touches multiple files or needs reading existing code). |
| `documentation` / `docs` | No Python needed — perfect for a first PR. |

You do **not** need to read the whole contributing guide below to send your first PR. The next sections are for people writing new recipes or making larger changes — come back to them when you need them.

---

## Code of Conduct

This project follows the [Contributor Covenant](./CODE_OF_CONDUCT.md). By participating, you agree to uphold its standards. Please report unacceptable behavior to the maintainers.

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

Follow the [Recipe Structure](#recipe-structure) and [Coding Style](#coding-style) sections below. For a full step-by-step walkthrough (copying an existing recipe, wiring up `llm.py`, running from a fresh venv), see **[docs/writing-a-recipe.md](./docs/writing-a-recipe.md)**.

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

**LLM requirement:** The default `llm` in every recipe must use **NVIDIA NIM + LLaMA**. Default to `meta/llama-3.1-8b-instruct` (fast and reliable on the free tier) and make the model overridable via the `LLM_MODEL` environment variable (so users can opt into `meta/llama-3.3-70b-instruct` without editing code). Copy the `get_llm()` pattern from an existing recipe's `llm.py` unchanged — it keeps the `openai/` model prefix and `max_retries` wiring that CrewAI's provider routing depends on. Supporting other providers as optional extras is fine.

---

## Running Recipes with Docker

Prefer not to touch your system Python? Every recipe can be run inside a Docker container — no virtual environments needed.

**Recommended — start the web playground (all recipes in one UI):**

```bash
# 1. Set your API key
cp playground/.env.example playground/.env
# Edit playground/.env: LLM_API_KEY=nvapi-your-key-here

# 2. Build and run
docker compose up playground
# Open http://localhost:8000
```

**Alternative — run a single CLI recipe:**

```bash
# Build (MODE=recipe + RECIPE=<name>)
docker build \
    --build-arg MODE=recipe \
    --build-arg RECIPE=lead-qualification \
    -t crewai-lead .

# Run — pass your .env at runtime (secrets never enter the image)
docker run --rm \
    --env-file recipes/lead-qualification/.env \
    crewai-lead \
    --company "Acme Corp" --description "A 40-person B2B SaaS startup"
```

For the full guide — Docker Compose, switching recipes, CI/CD tips, and troubleshooting — see **[docs/docker.md](./docs/docker.md)**.

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

### Testing

We use `pytest` for unit and integration tests. Run tests locally from within the recipe directory:

```bash
pip install pytest pytest-mock
cd recipes/my-awesome-recipe
pytest -v
```

CI will block PRs if any test fails.

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
