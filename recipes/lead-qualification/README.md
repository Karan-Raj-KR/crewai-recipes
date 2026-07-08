# 🎯 Recipe: Lead Qualification

Automatically **research, score, and summarise** inbound sales leads using a three-agent CrewAI crew powered by Groq LLaMA.

---

## What It Does

```
Inbound Lead Data
      │
      ▼
┌─────────────────────┐
│  Research Agent     │  ← Profiles the lead and company
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  ICP Scoring Agent  │  ← Scores across 4 dimensions (0–100)
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  Report Writer      │  ← Produces CRM-ready qualification report
└─────────────────────┘
         │
         ▼
  Qualification Report
  (score · verdict · next action · talking points)
```

## Setup

```bash
# From the repo root
cd recipes/lead-qualification
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # then add your GROQ_API_KEY
```

## Run

```bash
python main.py
```

Edit the `SAMPLE_LEAD` dict in `main.py` with your lead's details.

## Sample Output

```
═══════════════════════════════════════════════════════════
📋  QUALIFICATION REPORT
═══════════════════════════════════════════════════════════

## Lead Snapshot
- **Name:** Jordan Lee
- **Role:** Head of Revenue Operations @ Acme SaaS Co.
- **Score:** 82 / 100 — 🔥 HOT

## Top 3 Talking Points
1. Their spreadsheet-based pipeline is a growth bottleneck at 40 reps.
2. Series B velocity means they need scalable processes now.
3. RevOps hiring signals imminent tool consolidation.

## Recommended Next Action
**CALL NOW** — High ICP fit + active vendor evaluation = short buying window.

## Personalisation Angle
Reference their growth from 5 → 40 reps to show you've done your homework.

═══════════════════════════════════════════════════════════
```

## Configuration

| Variable | Description | Required |
|----------|-------------|----------|
| `GROQ_API_KEY` | Your Groq API key | ✅ Yes |

## Architecture

| File | Purpose |
|------|---------|
| `agents.py` | Defines Research, Scoring, and Report agents |
| `tasks.py` | Defines the three sequential tasks |
| `crew.py` | Assembles the Crew with sequential process |
| `main.py` | CLI entry point |
