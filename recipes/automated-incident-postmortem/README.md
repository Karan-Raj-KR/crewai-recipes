# 🚨 Recipe: Automated Incident Postmortem

> ✅ **Status: Stable** — A multi-agent DevSecOps / SRE workflow that automates technical incident reconstruction, Five Whys root cause diagnosis, and blameless postmortem generation. Powered by NVIDIA NIM and CrewAI.

A three-agent CrewAI workflow: **SRE Incident Chronologist** → **Systems & Software Root Cause Investigator** → **Lead Technical Incident Documentarian**.

---

## What It Does

```text
Alert Logs, Observability Traces & Commit Diffs
                       │
                       ▼
┌──────────────────────────────────────────────┐
│       SRE Incident Chronologist Agent        │  → Chronological Event Timeline (T-0 to recovery)
└──────────────────────┬───────────────────────┘
                       │ normalized timeline
                       ▼
┌──────────────────────────────────────────────┐
│   Systems & Root Cause Investigator Agent    │  → Technical failure mode & Five Whys analysis
└──────────────────────┬───────────────────────┘
                       │ timeline + root cause findings
                       ▼
┌──────────────────────────────────────────────┐
│    Lead Technical Documentarian Agent        │  → Executive Summary, Lessons Learned &
└──────────────────────┬───────────────────────┘    Prioritized Action Items Matrix (P0/P1/P2)
                       │
                       ▼
    Blameless Engineering Postmortem Document
```

---

## Quickstart

### 1. Setup

```bash
cd recipes/automated-incident-postmortem
python -m venv .venv
# Linux / macOS:
source .venv/bin/activate
# Windows PowerShell:
.\.venv\Scripts\Activate.ps1

pip install -r requirements.txt
cp .env.example .env   # Add your LLM_API_KEY (NVIDIA NIM or OpenAI compatible)
```

### 2. Run CLI

```bash
python run.py \
  --incident-title "Checkout Service 503 HTTP Spike during Flash Sale" \
  --raw-alert-logs "2026-11-10T14:02:11Z [CRIT] connection_pool_exhausted db_host=pg-primary-01 pool_size=100 active=100\n2026-11-10T14:03:45Z [ERR] HTTP 503 upstream connect timeout /api/v1/checkout rate=840req/s\n2026-11-10T14:18:20Z [INFO] hotfix deployment v2.14.1 rollback initiated by oncall\n2026-11-10T14:26:00Z [INFO] pool utilization returned to 18%, error rate 0.01%" \
  --recent-deployment-summary "Commit a1b2c3d: Added unindexed foreign key lookup on order_items table in checkout transaction flow." \
  --impact-metrics "Duration: 24 mins. 14,200 checkout requests failed (12.4% error rate). Estimated delayed GMV: $42,000."
```

### CLI Options

| Argument | Description | Default |
| :--- | :--- | :--- |
| `--incident-title` | Title or summary name of the technical incident | Flash sale checkout spike |
| `--raw-alert-logs` | Multi-line raw logs, alert messages, and timestamps | Sample connection pool logs |
| `--recent-deployment-summary` | Summary of recent deployments, PRs, or git diffs | Unindexed foreign key commit |
| `--impact-metrics` | Summary of duration, error counts, and business impact | 24m duration, 14.2k failures |

---

## Testing

Run offline unit and contract tests:

```bash
pytest test_main.py -v
```

Run root contract validation across all recipes:

```bash
pytest ../../tests/test_recipe_contract.py -v
```
