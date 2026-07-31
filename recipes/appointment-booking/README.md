# 📅 Recipe: Appointment Booking

A three-agent CrewAI crew that processes appointment booking requests, matches preferences against available calendar slots, and drafts a professional confirmation email — all powered by **NVIDIA NIM (Llama 3.1 8B Instruct)**.

**Time to first run: ~5 minutes** — clone, install, set key, run.

---

## What It Does

```
Booking Request (name, email, meeting type, preferred times, notes)
      │
      ▼
┌──────────────────────────┐
│ Intake Agent             │  ← Validates and structures request details
└──────────┬───────────────┘
           │
           ▼
┌──────────────────────────┐
│ Availability Agent       │  ← Matches to simulated calendar slots
└──────────┬───────────────┘
           │
           ▼
┌──────────────────────────┐
│ Confirmation Agent       │  ← Drafts ready-to-send confirmation email
└──────────────────────────┘
           │
           ▼
   Email Draft (subject + greeting + 2–3 slot options + sign-off)
```

**Model used:** `meta/llama-3.1-8b-instruct` via NVIDIA NIM  
**LLM calls:** 3 (one per task/agent)  
**Typical run time:** ~15–30 seconds  

---

## Prerequisites

- Python 3.10–3.12 (recommended)
- An NVIDIA NIM API key (free — [get one here](https://build.nvidia.com/))

---

## Setup

```bash
# From the repo root
cd recipes/appointment-booking

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate    # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure your API key
cp .env.example .env
# Edit .env → add: LLM_API_KEY=nvapi-...
```

---

## Usage

```bash
python run.py --name "Priya Sharma" \
  --email "priya.sharma@example.com" \
  --meeting-type "Product Demo" \
  --preferred-times "Any morning slot this week, preferably before noon IST"
```

### Options

| Flag | Required | Default | Description |
|------|----------|---------|-------------|
| `--name` | ✅ Yes | — | Requester's full name |
| `--email` | ✅ Yes | — | Requester's email address |
| `--meeting-type` | ✅ Yes | — | Type of meeting requested (e.g., "Product Demo") |
| `--preferred-times` | ✅ Yes | — | Preferred days/times stated by the requester |
| `--notes` | No | `None` | Optional context or special requests |
| `--help` | No | — | Show help and exit |

---

## Expected Output

Example output from running `python run.py` (showing the **final result block**):

```
📅  Appointment Booking Crew — Starting
   Requester : Priya Sharma (priya.sharma@example.com)
   Meeting   : Product Demo
   Preferred : Any morning slot this week, preferably before noon IST
   Notes     : Evaluating for 15-person team

────────────────────────────────────────────────────────────

════════════════════════════════════════════════════════════
📨  CONFIRMATION EMAIL DRAFT
════════════════════════════════════════════════════════════
Subject: Product Demo - Slot Options for Priya Sharma

Hi Priya,

Thank you for requesting a 30-minute Product Demo for your 15-person team! 
Based on your preference for a morning slot this week, here are a few options:

1. Monday 14 Jul 2026 — 10:00 AM IST (30 min)
   • Fits your preference for a morning slot before noon IST.

2. Tuesday 15 Jul 2026 — 11:00 AM IST (30 min)
   • A strong morning alternative right before noon.

Please reply with the slot that works best for you, and I will confirm the calendar invite right away.

Best regards,
[Host Name]
[Title]
════════════════════════════════════════════════════════════
```

---

## Extending With a Real Calendar

The simulated slots in `tasks.py` (`SIMULATED_AVAILABLE_SLOTS`) can be replaced with a real calendar API integration (Google Calendar, Calendly, Office 365, etc.):

```python
# Example: fetch free slots from Google Calendar API
from googleapiclient.discovery import build
# ... fetch slots and pass into tasks.py build_tasks()
```

---

## File Structure

| File | Purpose |
|------|---------|
| `agents.py` | Intake, Availability, and Confirmation agents |
| `tasks.py` | Three sequential tasks + simulated calendar slots |
| `crew.py` | Crew assembly with keyword arguments signature matching `inputs.json` |
| `main.py` | Script entry point with `SAMPLE_REQUEST` |
| `run.py` | CLI entry point (`argparse`) |
| `test_main.py` | Smoke test for execution and signature compatibility |
| `inputs.json` | Definition of playground UI inputs |
| `requirements.txt` | Python dependencies |
| `.env.example` | Template for `LLM_API_KEY` |
