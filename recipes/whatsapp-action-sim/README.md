# 📱 Recipe: WhatsApp Action Sim

> 🚧 **Status: In Progress** — Core functionality works; real webhook integration and multi-turn conversation support are coming.

A three-agent CrewAI crew that simulates a WhatsApp business automation pipeline: classify the user's intent → route to the correct action → compose a natural WhatsApp reply. Powered by NVIDIA NIM.

---

## What It Does

```
Incoming WhatsApp Message
          │
          ▼
┌──────────────────────────┐
│  Intent Classifier Agent  │  → ORDER_STATUS / BOOK_APPOINTMENT /
│                           │    FAQ / COMPLAINT / FEEDBACK /
│                           │    HUMAN_ESCALATION / UNKNOWN
└────────────┬─────────────┘
             │ classified intent + entities
             ▼
┌──────────────────────────┐
│  Action Router Agent      │  → Calls simulated action registry
│                           │    Returns structured payload
└────────────┬─────────────┘
             │ action result payload
             ▼
┌──────────────────────────┐
│  Response Composer Agent  │  → Natural, emoji-friendly WhatsApp reply
└──────────────────────────┘
             │
             ▼
     Outbound WhatsApp Message
```

## Supported Intents

| Intent | Simulated Action |
|--------|-----------------|
| `ORDER_STATUS` | Returns mock order tracking info |
| `BOOK_APPOINTMENT` | Presents available time slots |
| `FAQ` | Returns relevant knowledge base answer |
| `COMPLAINT` | Creates a support ticket |
| `FEEDBACK` | Logs feedback and sends reward |
| `HUMAN_ESCALATION` | Routes to live agent queue |
| `UNKNOWN` | Graceful fallback + clarification request |

## Setup

```bash
cd recipes/whatsapp-action-sim
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add your LLM_API_KEY
```

## Run

```bash
python main.py
```

Edit `SAMPLE_MESSAGES` in `main.py` and change the index to test different intents.

## Roadmap

- [ ] Real WhatsApp webhook integration (Meta Cloud API)
- [ ] Multi-turn conversation state management
- [ ] Tool-based action execution (replace simulated registry)
- [ ] Persistent conversation history with Redis

## Configuration

| Variable | Description | Required |
|----------|-------------|----------|
| `LLM_API_KEY` | Your NVIDIA API key | ✅ Yes |

## Architecture

| File | Purpose |
|------|---------|
| `agents.py` | Intent, Router, and Composer agents |
| `action_registry.py` | Simulated action responses by intent |
| `tasks.py` | Three sequential processing tasks |
| `crew.py` | Crew assembly |
| `main.py` | CLI entry point |
