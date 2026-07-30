# 📱 Recipe: WhatsApp Action Sim

> ✅ **Status: Stable** — Fully working three-agent crew with intent classification, simulated action routing, and WhatsApp response composition.

A three-agent CrewAI crew that simulates a WhatsApp business automation pipeline: classify the user's intent → route to the correct action → compose a natural WhatsApp reply. Powered by NVIDIA NIM.

---

## What It Does

```
Incoming WhatsApp Message
          │
          ▼
┌──────────────────────────┐
│  Intent Classifier Agent │  → ORDER_STATUS / BOOK_APPOINTMENT /
│                          │    FAQ / COMPLAINT / FEEDBACK /
│                          │    HUMAN_ESCALATION / UNKNOWN
└────────────┬─────────────┘
             │ classified intent + entities
             ▼
┌──────────────────────────┐
│  Action Router Agent     │  → Calls simulated action registry
│                          │    Returns structured payload
└────────────┬─────────────┘
             │ action result payload
             ▼
┌──────────────────────────┐
│  Response Composer Agent │  → Natural, emoji-friendly WhatsApp reply
└────────────┬─────────────┘
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

### Interactive / CLI mode
```bash
python run.py --user_message "Where is my order 12345?" --sender_name "Ravi"
```

### Options
- `--user_message`, `--user-message`, `--message`: The WhatsApp message text to process.
- `--sender_name`, `--sender-name`: Display name of the sender (default: `Ravi`).

### Batch sample mode
```bash
python main.py
```

## Sample Output

```
📱  WhatsApp Action Sim — Processing Message

   From    : Ravi
   Message : Hey! Where's my order? It's been 3 days now 😤

────────────────────────────────────────────────────────────

============================================================
📤  WHATSAPP REPLY
============================================================
Hi Ravi! 📦 Your order ORD-78421 is Out for Delivery via BlueDart and estimated to arrive today by 6:00 PM. 

Track live here: https://track.example.com/ORD-78421 🚚
============================================================
```

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
| `run.py` | CLI runner with argument parser |
| `main.py` | Sample batch test script |
