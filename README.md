<div align="center">

# 🤖 crewai-recipes

**See a multi-agent workflow run before you write one.**

A gallery of ready-to-run CrewAI workflows you can watch execute in your browser — then clone and run yourself. Powered by NVIDIA NIM (Llama 3.1 8B by default; swap to 70B with one env var: `LLM_MODEL`).

### ▶ [Watch a crew run →](https://karan-raj-kr.github.io/crewai-recipes/)

No install, no API key — real recorded agent traces, replayed in the browser.

[![CI](https://github.com/Karan-Raj-KR/crewai-recipes/actions/workflows/ci.yml/badge.svg)](https://github.com/Karan-Raj-KR/crewai-recipes/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
[![Python 3.10–3.12](https://img.shields.io/badge/python-3.10--3.12-blue.svg)](https://www.python.org/downloads/)
[![CrewAI](https://img.shields.io/badge/CrewAI-latest-green.svg)](https://github.com/joaomdmoura/crewAI)
[![NVIDIA NIM](https://img.shields.io/badge/LLM-NVIDIA%20NIM-76b900.svg)](https://build.nvidia.com/)
[![Docker](https://img.shields.io/badge/Docker-ready-2496ED?logo=docker&logoColor=white)](./docs/docker.md)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](./CONTRIBUTING.md)
[![Good First Issues](https://img.shields.io/github/issues/Karan-Raj-KR/crewai-recipes/good%20first%20issue?color=7057ff&label=good%20first%20issues)](https://github.com/Karan-Raj-KR/crewai-recipes/labels/good%20first%20issue)
[![Discussions](https://img.shields.io/badge/Discussions-join%20the%20conversation-blueviolet)](https://github.com/Karan-Raj-KR/crewai-recipes/discussions)

</div>

---

## 30-second start

```bash
git clone https://github.com/Karan-Raj-KR/crewai-recipes.git
cd crewai-recipes/recipes/lead-qualification
pip install -r requirements.txt
LLM_API_KEY=nvapi-YOUR_KEY python run.py --company "Acme Corp" --description "40-person B2B SaaS"
```

> **Free key:** Sign up at [build.nvidia.com](https://build.nvidia.com/) → browse models → **Get API Key**. The free tier gives generous monthly credits.
> **Windows:** Pass the key via `.env` file instead of the inline prefix — see [Quickstart](#-quickstart).

---

## What is this?

Most multi-agent examples are a wall of code and a screenshot. You can't tell whether the thing actually works, or what the agents *say to each other*, until you've installed it.

`crewai-recipes` fixes the order. Every workflow here has been run for real, its full agent trace captured, and replayed on the [gallery](https://karan-raj-kr.github.io/crewai-recipes/) — so you watch two agents argue their way to an ICP score *first*, and decide *then* whether to clone it.

What makes that possible is a small contract every recipe honours — `build_crew(**inputs)` plus an `inputs.json` describing them. Anything that satisfies it is automatically runnable from the CLI, from the local web playground, and in the gallery, with no glue code. See **[The recipe contract](#-the-recipe-contract)**.

Recipes default to **Llama 3.1 8B Instruct** — fast and reliable on the NIM free tier — and switch to 3.3 70B with a single environment variable (`LLM_MODEL`). Each one is a standalone Python project: clone, set one API key, run.

---

## 📐 The recipe contract

A recipe is any directory under `recipes/` with these files. Satisfy the contract and every tool in this repo picks your workflow up for free:

| File | Contract |
|---|---|
| `crew.py` | Exposes `build_crew(**inputs) -> Crew`. The only entry point tooling calls. |
| `inputs.json` | `[{"name", "label", "example"}, …]` — every field maps to a `build_crew` parameter. Drives the CLI flags, the playground form, and the gallery recording. |
| `llm.py` | Byte-identical across all recipes. Edit one, run `python tools/sync_llm.py`. |
| `agents.py` / `tasks.py` | Agent and task definitions. |
| `run.py` | `argparse` CLI entry point. |
| `requirements.txt`, `.env.example`, `README.md` | Self-contained setup. |

`pytest tests/test_recipe_contract.py` enforces all of it — including that `inputs.json` and your `build_crew` signature actually agree, which is the mismatch that silently 500s the playground. It's pure stdlib, so it runs in seconds with nothing installed:

```bash
pip install pytest && pytest tests/test_recipe_contract.py -v
```

New recipes are discovered automatically. No CI file to edit, no list to update.

---

## Why crewai-recipes?

| | Rolling your own | `crewai-recipes` |
|---|---|---|
| **Time to first run** | Write agent, task, crew, and LLM config from scratch | `git clone` → `pip install` → set one env var → run |
| **LLM / provider config** | Hardcode model, base URL, and API key in source | `LLM_API_KEY`, `LLM_MODEL`, `LLM_BASE_URL` env vars — swap providers without touching code |
| **Transient error handling** | Roll your own or skip it | `max_retries=3` pre-wired: exponential backoff on timeouts, 429s, and 5xx, honouring `Retry-After` |
| **CI validation** | Set up yourself | ruff lint, format check, and import-wiring assertions on every push to `main` |
| **Entry points** | Write from scratch | `run.py` (argparse CLI) and `main.py` (edit-and-run sample) included per recipe |
| **Local browser UI** | Build separately | `/playground` — FastAPI + HTML, runs locally, key never leaves your machine |
| **Seeing it work first** | Install, then find out | [Gallery](https://karan-raj-kr.github.io/crewai-recipes/) — watch the real agent trace before you clone |

---

## ⚡ Quickstart

```bash
# 1. Clone the repo
git clone https://github.com/Karan-Raj-KR/crewai-recipes.git
cd crewai-recipes

# 2. Create a virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 3. Install dependencies for a recipe (example: lead-qualification)
cd recipes/lead-qualification
pip install -r requirements.txt

# 4. Set your API key (free at https://build.nvidia.com/)
cp .env.example .env
# Edit .env and set: LLM_API_KEY=nvapi-...

# 5. Run the recipe
python run.py --company "Acme Corp" --description "A 40-person B2B SaaS..."
```

> **Tip:** Copy `.env.example` → `.env` inside each recipe folder and fill in your key — `python-dotenv` is pre-wired in every recipe.

> **Pick a model (optional):** Recipes default to `meta/llama-3.1-8b-instruct` (fast, reliable on the free tier). To use stronger reasoning, set `LLM_MODEL=meta/llama-3.3-70b-instruct` in your `.env` — no code changes needed. Note the 70B model can be slower and occasionally rate-limited on the free tier.

---

## 🎮 Local Playground

Want to test recipes in your browser instead of the CLI? The repo includes a lightweight, local-only web playground. **Your API key never leaves your machine.**

```bash
cd playground
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Start the playground server
uvicorn main:app --reload
```
Then open [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser.

---

## 🐳 Run with Docker

No Python setup required. The easiest way is via Docker Compose — it starts the full **web playground** with one command:

```bash
# 1. Set your API key
cp playground/.env.example playground/.env
# Edit playground/.env: LLM_API_KEY=nvapi-your-key-here

# 2. Start the playground (FastAPI + uvicorn on port 8000)
docker compose up playground
```

Then open **[http://localhost:8000](http://localhost:8000)** — all recipes are available in the UI. 🎉

Want to run a single recipe from the CLI instead?

```bash
docker build --build-arg MODE=recipe --build-arg RECIPE=lead-qualification -t crewai-lead .
docker run --rm --env-file recipes/lead-qualification/.env crewai-lead \
    --company "Acme Corp" --description "A 40-person B2B SaaS startup"
```

➡️ **Full Docker guide:** [docs/docker.md](./docs/docker.md)

---

## 📚 Recipes

| Recipe | Description | Status |
|--------|-------------|--------|
| [lead-qualification](./recipes/lead-qualification/) | Two-agent crew (Researcher + Scorer) that profiles a company and returns a 0-100 ICP score | ✅ Stable |
| [faq-bot](./recipes/faq-bot/) | Single-agent support bot that answers questions from an in-memory FAQ knowledge base | ✅ Stable |
| [appointment-booking](./recipes/appointment-booking/) | Agent crew that collects availability, checks a simulated calendar, and drafts a confirmation | ✅ Stable |
| [whatsapp-action-sim](./recipes/whatsapp-action-sim/) | Classifies WhatsApp-style messages by intent and routes to the correct downstream action | ✅ Stable |
| [customer-onboarding](./recipes/customer-onboarding/) | End-to-end onboarding: data collection → validation → welcome email draft | ✅ Stable |
| [email-drafting](./recipes/email-drafting/) | Three-agent crew that drafts, polishes, and formats professional emails | ✅ Stable |
| [support-escalation](./recipes/support-escalation/) | Tier-1 auto-resolve → escalate to human with full context summary | ✅ Stable |
| [content-pipeline](./recipes/content-pipeline/) | Blog ideation → research → draft → SEO review — fully automated crew | ✅ Stable |

**Status legend**

- ✅ **Stable** — tested, production-ready
- 🚧 **Scaffold** — structure in place, contributions welcome
- 💡 **Wanted** — open for contributions

---

## 🗂 Project Structure

```
crewai-recipes/
├── recipes/
│   ├── lead-qualification/      # Each recipe is self-contained
│   │   ├── agents.py            # Agent definitions
│   │   ├── tasks.py             # Task definitions
│   │   ├── crew.py              # Crew assembly
│   │   ├── run.py               # CLI entry point (argparse)
│   │   ├── llm.py               # LLM config (reads env vars)
│   │   ├── requirements.txt
│   │   ├── .env.example
│   │   └── README.md
│   ├── faq-bot/
│   ├── appointment-booking/
│   ├── whatsapp-action-sim/
│   └── customer-onboarding/
├── playground/                  # Local web UI for testing recipes
├── site/                        # The public gallery (playground UI + recorded runs)
├── tools/                       # record_runs.py, build_site.py, sync_llm.py
├── tests/                       # Recipe contract suite (stdlib only, no API key)
├── docs/                        # Deep-dive guides and architecture notes
├── .github/
│   ├── ISSUE_TEMPLATE/          # Bug report & recipe request templates
│   ├── workflows/               # CI + welcome-bot workflows
│   ├── PULL_REQUEST_TEMPLATE.md
│   └── dependabot.yml
├── CONTRIBUTING.md
├── CODE_OF_CONDUCT.md
├── SECURITY.md
├── CHANGELOG.md
└── README.md
```

---

## 🤝 Contributing

Contributions are very welcome! Whether you're fixing a bug, improving docs, or submitting a brand-new recipe — please read **[CONTRIBUTING.md](./CONTRIBUTING.md)** first.

Quick summary:
- Each recipe lives in its own directory under `recipes/` and satisfies [the recipe contract](#-the-recipe-contract)
- Must use CrewAI + NVIDIA NIM (default `meta/llama-3.1-8b-instruct`, 70B optional via `LLM_MODEL`); other models can be optional extras
- Open an issue first for major new recipes so we can align before you build

Before you push, run the checks CI runs — no API key needed for any of them:

```bash
pytest tests/test_recipe_contract.py   # your recipe satisfies the contract
python tools/sync_llm.py --check       # llm.py hasn't drifted
ruff check recipes/ playground/ tools/ tests/
ruff format --check recipes/ playground/ tools/ tests/
```

New to the project? Start with an issue labeled **[good first issue](https://github.com/Karan-Raj-KR/crewai-recipes/labels/good%20first%20issue)** — each one is scoped to be a self-contained, mergeable PR.

---

## 💬 Community

- 🙋 **New here?** Introduce yourself in [Discussions](https://github.com/Karan-Raj-KR/crewai-recipes/discussions)
- 💡 Have a recipe idea but want to talk it through first? → [Ideas](https://github.com/Karan-Raj-KR/crewai-recipes/discussions/categories/ideas)
- ❓ Stuck on setup or usage? → [Q&A](https://github.com/Karan-Raj-KR/crewai-recipes/discussions/categories/q-a)
- 🐛 Found a bug? → [open an issue](https://github.com/Karan-Raj-KR/crewai-recipes/issues/new/choose)
- 🔒 Found a security issue? → see [SECURITY.md](./SECURITY.md) — please don't file it publicly

### Contributors

<a href="https://github.com/Karan-Raj-KR/crewai-recipes/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=Karan-Raj-KR/crewai-recipes" alt="Contributors" />
</a>

---

## 📖 Documentation

Extended guides live in [`/docs`](./docs/):

- [Writing a New Recipe](./docs/writing-a-recipe.md) — step-by-step contributor walkthrough
- [The Gallery](./site/README.md) — how the public site records and replays runs
- [Changelog](./CHANGELOG.md) — what changed, when
- [Architecture Overview](./docs/architecture.md)
- [Agent Design Patterns](./docs/agent-patterns.md)
- [NVIDIA NIM + CrewAI Setup Guide](./docs/nim-setup.md)
- [Multi-provider LLM config](./docs/providers.md) — OpenAI, Anthropic, OpenRouter, and more
- [Project Decisions](./docs/DECISIONS.md) — why the repo is set up the way it is

---

## 🔔 Follow the Build

This project is being built in public. Follow along:

- 📸 Instagram: [@karan.rajkr](https://instagram.com/karan.rajkr) — behind-the-scenes, demos, and updates
- ✍️ Blog: [karanrajkr.hashnode.dev](https://karanrajkr.hashnode.dev) — deep-dives, tutorials, and build logs

---

## 📄 License

[MIT](./LICENSE) © 2026 Karan Raj K R

---

<div align="center">
  <sub>Made with ☕ and multi-agent enthusiasm. Star ⭐ this repo if it saves you time!</sub>
</div>
