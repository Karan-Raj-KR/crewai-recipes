# 🚀 Recipe: Customer Onboarding Workflow

> ✅ **Status: Stable** — Fully working three-agent crew that structures signup data, audits profile completeness/consistency, and drafts a personalized welcome or follow-up email.

A three-agent CrewAI crew that automates customer onboarding: Data Collector → Onboarding Auditor & Validator → Welcome Email Composer. Powered by NVIDIA NIM.

---

## What It Does

```
Customer Signup Information
          │
          ▼
┌───────────────────────────┐
│  Data Collector Agent     │  → Standardizes raw signup details
└─────────────┬─────────────┘
              │ structured profile
              ▼
┌───────────────────────────┐
│  Onboarding Validator     │  → Audits completeness & consistency
│                           │    Flags missing/vague fields
│                           │    Assigns Status: READY / INCOMPLETE
└─────────────┬─────────────┘
              │ audit report & status
              ▼
┌───────────────────────────┐
│  Welcome Email Composer   │  → Drafts tailored welcome email (if READY)
│                           │    OR polite follow-up request (if INCOMPLETE)
└─────────────┬─────────────┘
              │
              ▼
      Outbound Onboarding Email
```

## Setup

```bash
cd recipes/customer-onboarding
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add your LLM_API_KEY
```

## Run

### Interactive / CLI mode
```bash
python run.py --customer_name "Sarah Connor" --company "Cyberdyne Systems" --role "Chief Security Officer" --use_case "Threat intelligence aggregation" --team_size "50"
```

### Options
- `--customer_name`, `--customer-name`, `--name`: Customer's full name (default: `Alice Smith`).
- `--company`: Company name (default: `TechCorp Solutions`).
- `--role`: Job role or title (default: `Head of DevOps`).
- `--use_case`, `--use-case`: Primary use case or goal (default: `Automating infrastructure provisioning`).
- `--team_size`, `--team-size`: Team size (default: `25`).

### Batch sample mode
```bash
python main.py
```

## Sample Output

### 1. Complete Profile Output (Status: READY)

```
🚀  Customer Onboarding Workflow — Processing Signup

   Customer Name : Sarah Connor
   Company       : Cyberdyne Systems
   Role          : Chief Security Officer
   Use Case      : Automating threat intelligence aggregation and incident response
   Team Size     : 50

────────────────────────────────────────────────────────────

============================================================
📧  ONBOARDING EMAIL OUTPUT
============================================================
Subject: Welcome to the Platform, Sarah! Let's elevate Cyberdyne Systems' threat intelligence

Hi Sarah,

Welcome aboard! We are thrilled to partner with Cyberdyne Systems as your team of 50 scales your threat intelligence aggregation and incident response workflows.

As Chief Security Officer, we know how critical it is to streamline incident detection and response times. Here are a few tailored resources to help you get started right away:

1. Security & Incident Response Guide: https://docs.example.com/security-playbook
2. Single Sign-On & Admin Setup: https://docs.example.com/admin-sso
3. Schedule your Technical Kickoff Call: https://calendly.com/onboarding/tech-kickoff

Our dedicated Security Onboarding Team is on standby to assist with your initial setup. Please feel free to reply directly to this email if you have any questions!

Best regards,

The Customer Success Team
============================================================
```

### 2. Incomplete Profile Output (Status: INCOMPLETE)

```
Subject: Thanks for signing up, John! One quick detail to complete your onboarding

Hi John,

Thank you for signing up with us! We noticed a couple of missing details in your registration for Unknown LLC that will help us customize your onboarding experience:

- Primary Use Case / Goal: Please let us know what key goals or workflows you plan to automate.
- Role / Title: Could you share your current title so we can tailor the right setup guides for you?

Simply reply to this email with those details and we will get your account fully configured!

Best regards,

The Customer Success Team
```

## Configuration

| Variable | Description | Required |
|----------|-------------|----------|
| `LLM_API_KEY` | Your NVIDIA API key | ✅ Yes |

## Architecture

| File | Purpose |
|------|---------|
| `agents.py` | Collector, Validator, and Composer agents |
| `tasks.py` | Three sequential processing tasks |
| `crew.py` | Crew assembly |
| `run.py` | CLI runner with argument parser |
| `main.py` | Sample batch test script |
