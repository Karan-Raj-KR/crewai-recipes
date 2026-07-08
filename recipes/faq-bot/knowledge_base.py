"""
FAQ Bot Recipe — knowledge_base.py

In-memory FAQ for "Orbitly" — a fictional B2B project management SaaS.
Each entry has a topic, question, and answer.

To extend: add more dicts to FAQ_KNOWLEDGE_BASE.
In production, swap this for a vector store (Chroma, Pinecone, pgvector).
"""

FAQ_KNOWLEDGE_BASE: list[dict[str, str]] = [
    {
        "topic": "pricing",
        "question": "How much does Orbitly cost?",
        "answer": (
            "Orbitly offers three plans: Solo ($0/month, 1 user, 3 projects), "
            "Team ($29/month per user, unlimited projects, priority support), "
            "and Enterprise (custom pricing, SSO, dedicated SLA, audit logs). "
            "Annual billing gives you 2 months free."
        ),
    },
    {
        "topic": "free trial",
        "question": "Can I try Orbitly before paying?",
        "answer": (
            "Yes! The Solo plan is free forever for one user. For team features, "
            "every account gets a 21-day free trial of the Team plan — no credit "
            "card required. Your trial auto-converts to Solo if you don't upgrade."
        ),
    },
    {
        "topic": "data import",
        "question": "Can I import my projects from Jira or Trello?",
        "answer": (
            "Absolutely. Go to Settings → Import and choose your source: "
            "Jira (Cloud or Server), Trello, Asana, or CSV. The import wizard "
            "maps fields automatically and lets you preview before confirming. "
            "Large imports (500+ issues) run in the background and email you when done."
        ),
    },
    {
        "topic": "integrations",
        "question": "Which tools does Orbitly integrate with?",
        "answer": (
            "Native integrations include Slack (notifications + /orbitly slash command), "
            "GitHub (link commits to tasks), Figma (embed designs), Google Drive, "
            "and Zapier (1,000+ apps). Webhooks and a REST API are available on "
            "Team and Enterprise plans. Full API docs at docs.orbitly.example.com."
        ),
    },
    {
        "topic": "security",
        "question": "Is my data secure? Is Orbitly GDPR compliant?",
        "answer": (
            "Yes. All data is encrypted in transit (TLS 1.3) and at rest (AES-256). "
            "Orbitly is SOC 2 Type II certified and fully GDPR compliant. "
            "EU customers' data is stored in EU data centres. "
            "You can export or delete all your data at any time from Settings → Privacy."
        ),
    },
    {
        "topic": "cancellation and refunds",
        "question": "What happens if I cancel? Do you offer refunds?",
        "answer": (
            "You can cancel anytime from Settings → Billing → Cancel Plan. "
            "Access continues until the end of your current billing period — "
            "we don't pro-rate or charge early cancellation fees. "
            "Refund requests within 14 days of a charge are honoured in full; "
            "after that, refunds are reviewed case-by-case. Email billing@orbitly.example.com."
        ),
    },
]


def get_knowledge_base_text() -> str:
    """Format the FAQ knowledge base as a plain-text block for agent context.

    Returns:
        A formatted string with all FAQ entries numbered and labelled.
    """
    lines: list[str] = ["=== ORBITLY FAQ KNOWLEDGE BASE ===\n"]
    for i, entry in enumerate(FAQ_KNOWLEDGE_BASE, 1):
        lines.append(f"[{i}] Topic: {entry['topic'].upper()}")
        lines.append(f"    Q: {entry['question']}")
        lines.append(f"    A: {entry['answer']}")
        lines.append("")
    lines.append("=== END OF KNOWLEDGE BASE ===")
    return "\n".join(lines)
