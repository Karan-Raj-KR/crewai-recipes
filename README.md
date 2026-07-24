<div align="center">

# 🤖 crewai-recipes

**A public library of ready-to-run CrewAI multi-agent workflows — powered by NVIDIA NIM (Llama 3.1 8B by default; swap to 70B with one env var: `LLM_MODEL`).**

[![CI](https://github.com/Karan-Raj-KR/crewai-recipes/actions/workflows/ci.yml/badge.svg)](https://github.com/Karan-Raj-KR/crewai-recipes/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
[![Python 3.10–3.12](https://img.shields.io/badge/python-3.10--3.12-blue.svg)](https://www.python.org/downloads/)
[![CrewAI](https://img.shields.io/badge/CrewAI-latest-green.svg)](https://github.com/joaomdmoura/crewAI)
[![NVIDIA NIM](https://img.shields.io/badge/LLM-NVIDIA%20NIM-76b900.svg)](https://build.nvidia.com/)
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

`crewai-recipes` is a community-driven cookbook of **self-contained, production-ready multi-agent workflows** built with [CrewAI](https://github.com/joaomdmoura/crewAI) and [NVIDIA NIM](https://build.nvidia.com/). Recipes default to **Llama 3.1 8B Instruct** — fast and reliable on the NIM free tier — and you can switch to the larger 3.3 70B model with a single environment variable (`LLM_MODEL`). Each recipe is a standalone Python project you can clone, configure with a single API key, and run in minutes.

No boilerplate hunting. No stitching together random blog posts. Just clone → set key → run.

---

## Why crewai-recipes?

| | Rolling your own | `crewai-recipe` |
|---|---|---|
| **Time to first run** | Write agent, task, crew, and LLM config from scratch | `git clone` → `pip install` → set one env var → run |
| **LLM / provider config** | Hardcode model, base URL, and API key in source | `LLM_API_KEY`, `LLM_MODEL`, `LLM_BASE_URL` env vars — swap providers without touching code |
| **Transient error handling** | Roll your own or skip it | `max_retries=3` pre-wired: exponential backoff on timeouts, 429s, and 5xx, honouring `Retry-After` |
| **CI validation** | Set up yourself | ruff lint, format check, and import-wiring assertions on every push to `main` |
| **Entry points** | Write from scratch | `run.py` (argparse CLI) and `main.py` (edit-and-run sample) included per recipe |
| **Local browser UI** | Build separately | `/playground` — FastAPI + HTML, runs locally, key never leaves your machine |

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

## 📚 Recipes

| Recipe | Description | Status |
|--------|-------------|--------|
| [lead-qualification](./recipes/lead-qualification/) | Two-agent crew (Researcher + Scorer) that profiles a company and returns a 0-100 ICP score | ✅ Stable |
| [faq-bot](./recipes/faq-bot/) | Single-agent support bot that answers questions from an in-memory FAQ knowledge base | ✅ Stable |
| [appointment-booking](./recipes/appointment-booking/) | Agent crew that collects availability, checks a simulated calendar, and drafts a confirmation | 🚧 Scaffold |
| [whatsapp-action-sim](./recipes/whatsapp-action-sim/) | Classifies WhatsApp-style messages by intent and routes to the correct downstream action | 🚧 Scaffold |
| [customer-onboarding](./recipes/customer-onboarding/) | End-to-end onboarding: data collection → validation → welcome email draft | ✅ Stable |
| content-pipeline | Blog ideation → research → draft → SEO review — fully automated crew | 💡 Wanted |
| support-escalation | Tier-1 auto-resolve → escalate to human with full context summary | 💡 Wanted |

> **Legend:** ✅ Stable (tested, production-ready) · 🚧 Scaffold (structure in place, contributions welcome) · 💡 Wanted (open for contributions!)

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
- Each recipe lives in its own directory under `recipes/`
- Must use CrewAI + NVIDIA NIM (default `meta/llama-3.1-8b-instruct`, 70B optional via `LLM_MODEL`); other models can be optional extras
- Include a `README.md`, `requirements.txt`, `run.py`, and `.env.example`
- Open an issue first for major new recipes so we can align before you build

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
