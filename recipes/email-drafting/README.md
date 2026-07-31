# ✉️ Recipe: Email Drafting Workflow

> ✅ **Status: Stable** — Fully working 2-agent crew that drafts complete emails from a brief and audits them for conciseness, tone matching, and key point inclusion.

A two-agent CrewAI crew that automates email drafting: Email Composition Specialist (Drafter) → Executive Email Editor & Auditor. Powered by NVIDIA NIM.

---

## What It Does

```
Email Brief (Recipient, Purpose, Key Points, Tone)
          │
          ▼
┌───────────────────────────┐
│  Drafter Agent            │  → Drafts full initial email
└─────────────┬─────────────┘
              │ initial email draft
              ▼
┌───────────────────────────┐
│  Editor Agent             │  → Verifies key points coverage
│                           │    Cuts fluff & checks tone
│                           │    Outputs final email + changelog
└─────────────┬─────────────┘
              │
              ▼
    Polished Email & Change Log
```

## Setup

```bash
cd recipes/email-drafting
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add your LLM_API_KEY
```

## Run

### Interactive / CLI mode
```bash
python run.py --recipient "Engineering Team" --purpose "Sprint Status & Deployment Update" --key_points "Completed 95% of tasks, deployment on Thursday 2 PM, all blocker tickets resolved" --tone "professional"
```

### Options
- `--recipient`: Recipient name or role (default: `Engineering Team`).
- `--purpose`: Main email purpose (default: `Weekly Sprint & Deployment Update`).
- `--key_points`, `--key-points`: Key points to cover (default: `Sprint completion 95%, production release Thursday at 2 PM EST`).
- `--tone`: Desired tone (`professional` / `friendly` / `formal` / `direct`, default: `professional`).

### Batch sample mode
```bash
python main.py
```

## Sample Output

```
📧  Email Drafting Workflow — Processing Brief

   Recipient  : Engineering Team
   Purpose    : Sprint Status & Deployment Update
   Key Points : Sprint completion reached 95%, production release scheduled for Thursday at 2:00 PM EST, no blocking security issues remaining
   Tone       : professional

────────────────────────────────────────────────────────────

============================================================
✉️   POLISHED EMAIL & EDITORIAL NOTES
============================================================
FINAL EMAIL:
Subject: Sprint Status Update & Thursday Production Deployment

Hi Engineering Team,

I wanted to share a quick update on our current sprint progress and upcoming production deployment:

- Sprint Progress: We have officially achieved 95% sprint completion.
- Production Deployment: Release is scheduled for Thursday at 2:00 PM EST.
- Security & Blockers: All blocking security tickets have been resolved.

Please double-check your remaining pull requests before Wednesday end-of-day to ensure a smooth deployment window.

Best regards,

Technical Program Management

EDITORIAL NOTES:
- Tone Check: Professional, clear, and action-oriented.
- Key Points Verified:
  1. 95% sprint completion (Included)
  2. Thursday 2:00 PM EST deployment (Included)
  3. Zero blocking security tickets (Included)
- Changes Made: Streamlined introductory paragraph and formatted key milestones into clear bullet points for faster reading.
============================================================
```

## Configuration

| Variable | Description | Required |
|----------|-------------|----------|
| `LLM_API_KEY` | Your NVIDIA API key | ✅ Yes |

## Architecture

| File | Purpose |
|------|---------|
| `agents.py` | Drafter and Editor agents |
| `tasks.py` | Two sequential processing tasks |
| `crew.py` | Crew assembly |
| `run.py` | CLI runner with argument parser |
| `main.py` | Sample batch test script |
