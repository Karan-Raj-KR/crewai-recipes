# 📅 Recipe: Appointment Booking

A three-agent CrewAI crew that processes booking requests, matches them to available calendar slots, and drafts a confirmation email — all powered by NVIDIA NIM.

---

## What It Does

```
Booking Request (name, email, type, preferences)
      │
      ▼
┌──────────────────────┐
│   Intake Agent        │  ← Validates and structures the request
└─────────┬────────────┘
          │
          ▼
┌──────────────────────┐
│ Availability Agent    │  ← Matches to simulated calendar slots
└─────────┬────────────┘
          │
          ▼
┌──────────────────────┐
│ Confirmation Agent    │  ← Drafts ready-to-send confirmation email
└──────────────────────┘
          │
          ▼
  Email Draft (subject + body + slot options)
```

## Setup

```bash
cd recipes/appointment-booking
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add your LLM_API_KEY
```

## Run

```bash
python main.py
```

Edit `SAMPLE_REQUEST` in `main.py` with the requester's details.

## Extending With a Real Calendar

The simulated slots in `tasks.py` (`SIMULATED_AVAILABLE_SLOTS`) can be replaced with a real calendar API call:

```python
# Example: fetch free slots from Google Calendar
from googleapiclient.discovery import build
# ... build your slots list and pass into tasks.py
```

## Configuration

| Variable | Description | Required |
|----------|-------------|----------|
| `LLM_API_KEY` | Your NVIDIA API key | ✅ Yes |

## Architecture

| File | Purpose |
|------|---------|
| `agents.py` | Intake, Availability, and Confirmation agents |
| `tasks.py` | Three sequential tasks + simulated calendar slots |
| `crew.py` | Crew assembly |
| `main.py` | CLI entry point |
