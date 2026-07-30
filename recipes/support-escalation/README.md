# 🎧 Recipe: Support Ticket Escalation

> ✅ **Status: Stable** — Fully working 3-agent crew that triages tickets, attempts conservative Tier-1 auto-resolution against an in-memory knowledge base, or generates a structured human handoff summary for complex issues.

A three-agent CrewAI crew that handles customer support workflows: Triage Specialist → Tier-1 Automated Resolver → Human Handoff & Escalation Specialist. Powered by NVIDIA NIM.

---

## What It Does

```
Incoming Support Ticket
          │
          ▼
┌───────────────────────────┐
│  Triage Specialist Agent  │  → Category & Severity (LOW/MEDIUM/HIGH/CRITICAL)
└─────────────┬─────────────┘
              │ triage report
              ▼
┌───────────────────────────┐
│  Tier-1 Auto-Resolver     │  → Checks in-memory Knowledge Base
│                           │    Resolves simple issues OR flags ESCALATE
└─────────────┬─────────────┘
              │ audit & resolution status
              ▼
┌───────────────────────────┐
│  Escalation Specialist    │  → Auto-resolution instructions (if resolved)
│                           │    OR structured Human Handoff Brief (if escalated)
└─────────────┬─────────────┘
              │
              ▼
     Final Workflow Outcome
```

## Setup

```bash
cd recipes/support-escalation
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add your LLM_API_KEY
```

## Run

### Interactive / CLI mode
```bash
python run.py --ticket_text "Our custom SAML SSO integration is failing with HTTP 500 errors after key rotation" --customer_tier "enterprise" --previous_contacts "2"
```

### Options
- `--ticket_text`, `--ticket-text`, `--ticket`: Customer support issue text.
- `--customer_tier`, `--customer-tier`: Account tier (`free` / `pro` / `enterprise`, default: `enterprise`).
- `--previous_contacts`, `--previous-contacts`: Number of previous contact attempts (default: `2`).

### Batch sample mode
```bash
python main.py
```

## Sample Output

### Human Handoff Escalation (Complex Issue)

```
🎧  Support Ticket Workflow — Processing Ticket

   Ticket Text       : Our enterprise SAML SSO integration with Okta started failing with HTTP 500 error after certificate renewal.
   Customer Tier     : enterprise
   Previous Contacts : 2

────────────────────────────────────────────────────────────

============================================================
📋  SUPPORT TICKET WORKFLOW OUTCOME
============================================================
### HUMAN AGENT HANDOFF BRIEF

- **Customer Goal**: Restore enterprise SAML single sign-on (SSO) integration between Okta and internal application following a security certificate renewal.
- **Account & Severity Context**: Enterprise Tier | Severity Level: HIGH | Previous Contacts: 2.
- **Steps Attempted**: Automated Tier-1 resolution audited the ticket against standard KB entries (Password Reset, Billing Invoice, API Rate Limits). No matching Tier-1 automated resolution exists for custom SAML cert key exchange failures.
- **Blocking Issue**: Internal HTTP 500 server error occurring during SAML assertion parsing after certificate renewal.
- **Suggested Next Action**: Route ticket to Tier-2 Identity & Security Engineering team to inspect SAML assertion logs and re-upload the public X.509 certificate metadata.
============================================================
```

## Configuration

| Variable | Description | Required |
|----------|-------------|----------|
| `LLM_API_KEY` | Your NVIDIA API key | ✅ Yes |

## Architecture

| File | Purpose |
|------|---------|
| `agents.py` | Triage, Resolver, and Escalation agents |
| `knowledge_base.py` | In-memory verified Tier-1 support knowledge base |
| `tasks.py` | Three sequential processing tasks |
| `crew.py` | Crew assembly |
| `run.py` | CLI runner with argument parser |
| `main.py` | Sample batch test script |
