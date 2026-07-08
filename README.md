<div align="center">

# 🤖 crewai-recipes

**A public library of ready-to-run CrewAI multi-agent automation templates — powered by Groq LLaMA.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![CrewAI](https://img.shields.io/badge/CrewAI-latest-green.svg)](https://github.com/joaomdmoura/crewAI)
[![Groq](https://img.shields.io/badge/LLM-Groq%20LLaMA-purple.svg)](https://console.groq.com/)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](./CONTRIBUTING.md)

</div>

---

## What is this?

`crewai-recipes` is a community-driven cookbook of **self-contained, production-ready multi-agent workflows** built with [CrewAI](https://github.com/joaomdmoura/crewAI) and [Groq](https://groq.com/) (LLaMA 3 / LLaMA 3.1). Each recipe is a standalone Python project you can clone, configure with a single environment variable, and run in minutes.

No boilerplate hunting. No stitching together random blog posts. Just clone → set key → run.

---

## ⚡ Quickstart

```bash
# 1. Clone the repo
git clone https://github.com/karanrajkr/crewai-recipes.git
cd crewai-recipes

# 2. Create a virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 3. Install dependencies for a recipe (example: lead-qualification)
cd recipes/lead-qualification
pip install -r requirements.txt

# 4. Set your Groq API key (get one free at https://console.groq.com/)
export GROQ_API_KEY="gsk_..."   # Windows: set GROQ_API_KEY=gsk_...

# 5. Run the recipe
python main.py
```

> **Tip:** Copy `.env.example` → `.env` inside each recipe folder and fill in your key — `python-dotenv` is pre-wired in every recipe.

---

## 📚 Recipes

| Recipe | Description | Status |
|--------|-------------|--------|
| [lead-qualification](./recipes/lead-qualification/) | Multi-agent crew that scores, researches, and prioritises inbound sales leads | ✅ Stable |
| [appointment-booking](./recipes/appointment-booking/) | Conversational agent crew that collects availability, checks a calendar, and confirms bookings | ✅ Stable |
| [faq-bot](./recipes/faq-bot/) | RAG-powered FAQ agent that answers customer questions from a knowledge base with graceful fallback | ✅ Stable |
| [whatsapp-action-sim](./recipes/whatsapp-action-sim/) | Simulated WhatsApp-style message processor that routes intents and triggers downstream actions | 🚧 In Progress |
| customer-onboarding | End-to-end onboarding flow: data collection → validation → welcome email draft | 💡 Wanted |
| content-pipeline | Blog ideation → research → draft → SEO review — fully automated crew | 💡 Wanted |
| support-escalation | Tier-1 auto-resolve → escalate to human with full context summary | 💡 Wanted |

> **Legend:** ✅ Stable · 🚧 In Progress · 💡 Wanted (open for contributions!)

---

## 🗂 Project Structure

```
crewai-recipes/
├── recipes/
│   ├── lead-qualification/      # Each recipe is self-contained
│   │   ├── agents.py
│   │   ├── tasks.py
│   │   ├── crew.py
│   │   ├── main.py
│   │   ├── requirements.txt
│   │   ├── .env.example
│   │   └── README.md
│   ├── appointment-booking/
│   ├── faq-bot/
│   └── whatsapp-action-sim/
├── docs/                        # Deep-dive guides and architecture notes
├── .github/
│   ├── ISSUE_TEMPLATE/          # Bug report & feature request templates
│   └── workflows/               # CI workflows
├── CONTRIBUTING.md
├── CODE_OF_CONDUCT.md
└── README.md
```

---

## 🤝 Contributing

Contributions are very welcome! Whether you're fixing a bug, improving docs, or submitting a brand-new recipe — please read **[CONTRIBUTING.md](./CONTRIBUTING.md)** first.

Quick summary:
- Each recipe lives in its own directory under `recipes/`
- Must use CrewAI + Groq LLaMA (other models can be optional)
- Include a `README.md`, `requirements.txt`, and `.env.example`
- Open an issue first for major new recipes so we can align before you build

---

## 📖 Documentation

Extended guides live in [`/docs`](./docs/):

- [Architecture Overview](./docs/architecture.md)
- [Agent Design Patterns](./docs/agent-patterns.md)
- [Groq + CrewAI Setup Guide](./docs/groq-setup.md)

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
