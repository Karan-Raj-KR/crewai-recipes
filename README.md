<div align="center">

# 🤖 crewai-recipes

**A public library of ready-to-run CrewAI multi-agent automation templates — powered by NVIDIA NIM (Llama 3.3 70B).**

[![CI](https://github.com/Karan-Raj-KR/crewai-recipes/actions/workflows/ci.yml/badge.svg)](https://github.com/Karan-Raj-KR/crewai-recipes/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![CrewAI](https://img.shields.io/badge/CrewAI-latest-green.svg)](https://github.com/joaomdmoura/crewAI)
[![NVIDIA NIM](https://img.shields.io/badge/LLM-NVIDIA%20NIM-76b900.svg)](https://build.nvidia.com/)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](./CONTRIBUTING.md)
[![Good First Issues](https://img.shields.io/github/issues/Karan-Raj-KR/crewai-recipes/good%20first%20issue?color=7057ff&label=good%20first%20issues)](https://github.com/Karan-Raj-KR/crewai-recipes/labels/good%20first%20issue)
[![Discussions](https://img.shields.io/badge/Discussions-join%20the%20conversation-blueviolet)](https://github.com/Karan-Raj-KR/crewai-recipes/discussions)

</div>

---

## What is this?

`crewai-recipes` is a community-driven cookbook of **self-contained, production-ready multi-agent workflows** built with [CrewAI](https://github.com/joaomdmoura/crewAI) and [NVIDIA NIM](https://build.nvidia.com/) (Llama 3.3 70B Instruct). Each recipe is a standalone Python project you can clone, configure with a single environment variable, and run in minutes.

No boilerplate hunting. No stitching together random blog posts. Just clone → set key → run.

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

# 4. Set your NVIDIA API key (free at https://build.nvidia.com/)
cp .env.example .env
# Edit .env and set: NVIDIA_API_KEY=nvapi-...

# 5. Run the recipe
python run.py --company "Acme Corp" --description "A 40-person B2B SaaS..."
```

> **Get an API key:** Sign up free at [build.nvidia.com](https://build.nvidia.com/), browse models, and click **Get API Key**. The free tier gives generous monthly credits.

> **Tip:** Copy `.env.example` → `.env` inside each recipe folder and fill in your key — `python-dotenv` is pre-wired in every recipe.

---

## 📚 Recipes

| Recipe | Description | Status |
|--------|-------------|--------|
| [lead-qualification](./recipes/lead-qualification/) | Two-agent crew (Researcher + Scorer) that profiles a company and returns a 0-100 ICP score | ✅ Stable |
| [faq-bot](./recipes/faq-bot/) | Single-agent support bot that answers questions from an in-memory FAQ knowledge base | ✅ Stable |
| [appointment-booking](./recipes/appointment-booking/) | Agent crew that collects availability, checks a simulated calendar, and drafts a confirmation | 🚧 Scaffold |
| [whatsapp-action-sim](./recipes/whatsapp-action-sim/) | Classifies WhatsApp-style messages by intent and routes to the correct downstream action | 🚧 Scaffold |
| customer-onboarding | End-to-end onboarding: data collection → validation → welcome email draft | 💡 Wanted |
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
│   │   ├── llm.py               # NVIDIA NIM LLM config
│   │   ├── requirements.txt
│   │   ├── .env.example
│   │   └── README.md
│   ├── faq-bot/
│   ├── appointment-booking/
│   └── whatsapp-action-sim/
├── docs/                        # Deep-dive guides and architecture notes
├── .github/
│   ├── ISSUE_TEMPLATE/          # Bug report & recipe request templates
│   ├── workflows/               # CI + welcome-bot workflows
│   ├── PULL_REQUEST_TEMPLATE.md
│   ├── CODEOWNERS
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
- Must use CrewAI + NVIDIA NIM (Llama 3.3 70B or similar); other models can be optional extras
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

- [Architecture Overview](./docs/architecture.md)
- [Agent Design Patterns](./docs/agent-patterns.md)
- [NVIDIA NIM + CrewAI Setup Guide](./docs/nim-setup.md)

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
  <sub>Made with ☕ and multi-agent enthusiasm. Star ⭐ the repo if it saves you time!</sub>
</div>
