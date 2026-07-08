# 🎯 Recipe: Lead Qualification

Score and profile inbound sales leads using a two-agent CrewAI crew powered by **NVIDIA NIM** (defaults to `meta/llama-3.1-8b-instruct`; set `NIM_MODEL` for 70B).

**Time to first run: ~5 minutes** — clone, install, set key, run.

---

## What It Does

```
Input: company name + short description
            │
            ▼
┌─────────────────────────┐
│  Company Research Agent  │  ← Extracts industry, size, pain points,
│                          │    business model, growth stage from desc.
└────────────┬────────────┘
             │ structured research summary
             ▼
┌─────────────────────────┐
│  ICP Scoring Agent       │  ← Scores across 4 dimensions (25 pts each)
│                          │    Industry Fit · Size Fit · Pain Point ·
│                          │    Budget/Growth Signal
└─────────────────────────┘
             │
             ▼
Output: 0-100 score + HOT/WARM/COLD verdict + next action
```

**Default model:** `meta/llama-3.1-8b-instruct` via NVIDIA NIM (set `NIM_MODEL=meta/llama-3.3-70b-instruct` for stronger reasoning)  
**LLM calls:** 2 (one per agent)  
**Typical run time:** ~20-40 seconds

---

## Prerequisites

- Python 3.10–3.12 (recommended)
- An NVIDIA NIM API key (free — [get one here](https://build.nvidia.com/))

---

## Setup

```bash
# From the repo root
cd recipes/lead-qualification

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate    # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure your API key
cp .env.example .env
# Edit .env → add: NVIDIA_API_KEY=nvapi-...
```

---

## Usage

```bash
python run.py --company "COMPANY NAME" --description "SHORT DESCRIPTION"
```

### Options

| Flag | Required | Description |
|------|----------|-------------|
| `--company` | ✅ Yes | Company name (e.g. `"Acme Corp"`) |
| `--description` | ✅ Yes | Description of the company — more detail = better score |
| `--help` | No | Show help and exit |

### Examples

```bash
# Basic usage
python run.py \
  --company "Notion" \
  --description "Series C note-taking and wiki tool for teams. \
Used by 50,000+ companies. Primarily SMB and mid-market, strong B2B growth."

# Startup example
python run.py \
  --company "FleetTrackr" \
  --description "Early-stage logistics SaaS for last-mile delivery \
companies. 8-person team, pre-seed, targeting small courier businesses."
```

---

## Expected Output

The block below is the **final result** from a real end-to-end run (the verbose
per-agent trace is omitted for brevity). Exact scores vary by input and model:

```
$ python run.py \
  --company "FleetTrackr" \
  --description "Early-stage logistics SaaS for last-mile delivery companies.
   12-person team, seed-stage, targeting small courier businesses with 10-50
   drivers. Route optimization and proof-of-delivery. Customers are frustrated
   with spreadsheets and WhatsApp for dispatch."

🎯  Lead Qualification Crew — Starting
   Company    : FleetTrackr
   Description: Early-stage logistics SaaS for last-mile delivery...

════════════════════════════════════════════════════════════
📊  QUALIFICATION RESULT
════════════════════════════════════════════════════════════
**FleetTrackr ICP Scorecard**

| Dimension            | Score      | Rationale |
|----------------------|------------|-----------|
| Industry Fit         | 22 / 25    | Targets last-mile delivery companies, aligning closely with our B2B SaaS buyer profile. |
| Company Size Fit     | 12 / 25    | Early-stage startup; team size may not reflect SMB-to-mid-market sweet spot. |
| Pain Point Acuity    | 20 / 25    | Manual processes and inefficient routing are acute, urgent pain points. |
| Budget/Growth Signal | 15 / 25    | Limited spending power at seed stage; growth potential present but early. |

**Total Score:** 69 / 100
**Verdict:** WARM

**Recommended Next Action:** Schedule a discovery call to discuss specific
pain points and assess readiness for a B2B SaaS solution.
════════════════════════════════════════════════════════════
```

> ✅ **Verified:** Real call to NVIDIA NIM `meta/llama-3.1-8b-instruct` on 2026-07-08.

---

## File Structure

| File | Purpose |
|------|---------|
| `llm.py` | NVIDIA NIM LLM configuration — change model here |
| `agents.py` | Research Agent and Scoring Agent definitions |
| `tasks.py` | Task descriptions with ICP scoring rubric |
| `crew.py` | Crew assembly (sequential process) |
| `run.py` | CLI entry point (`argparse`) |
| `requirements.txt` | Python dependencies |
| `.env.example` | Template for environment variables |

---

## Customising the ICP

Edit `tasks.py` — the `scoring_task` description contains the scoring rubric table. Adjust the dimensions, weights, or thresholds to match your sales team's ICP definition.

---

## LLM Provider

This recipe uses **NVIDIA NIM** — a free, OpenAI-compatible inference API for NVIDIA-optimised models.

- Endpoint: `https://integrate.api.nvidia.com/v1`
- Default model: `meta/llama-3.1-8b-instruct` (fast, reliable on the free tier)
- Upgrade model: `meta/llama-3.3-70b-instruct` (stronger reasoning; slower, may be rate-limited on the free tier)
- Docs: [build.nvidia.com](https://build.nvidia.com/)

To swap models, set `NIM_MODEL` in your `.env` (no code change needed), or edit `DEFAULT_MODEL` in `llm.py`.
