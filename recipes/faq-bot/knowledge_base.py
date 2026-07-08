"""
FAQ Bot Recipe — knowledge_base.py

A static, in-memory FAQ knowledge base.
In production, replace this with a vector store (e.g. Chroma, Pinecone, pgvector)
or a document loader from a CMS / Notion / Confluence page.
"""

FAQ_KNOWLEDGE_BASE: list[dict[str, str]] = [
    {
        "topic": "pricing",
        "question": "How much does the product cost?",
        "answer": (
            "We offer three plans: Starter ($29/month), Growth ($79/month), "
            "and Enterprise (custom pricing). All plans include a 14-day free "
            "trial — no credit card required. Annual billing saves 20%."
        ),
    },
    {
        "topic": "free trial",
        "question": "How do I start a free trial?",
        "answer": (
            "Sign up at our website, choose any plan, and you'll automatically "
            "start your 14-day free trial. No credit card is needed to start. "
            "You'll receive a welcome email with onboarding steps."
        ),
    },
    {
        "topic": "cancellation",
        "question": "Can I cancel my subscription at any time?",
        "answer": (
            "Yes, you can cancel at any time from your account settings under "
            "Billing > Cancel Subscription. Your access continues until the "
            "end of your current billing period. We do not charge cancellation fees."
        ),
    },
    {
        "topic": "data export",
        "question": "Can I export my data?",
        "answer": (
            "Absolutely. Navigate to Settings > Data > Export. You can export "
            "all your data as CSV or JSON. Enterprise customers also have "
            "access to the bulk export API."
        ),
    },
    {
        "topic": "integrations",
        "question": "Which third-party tools do you integrate with?",
        "answer": (
            "We integrate natively with Slack, HubSpot, Salesforce, Zapier, "
            "and Google Workspace. Over 1,000 additional apps are available "
            "via our Zapier integration. API documentation is at /docs/api."
        ),
    },
    {
        "topic": "security",
        "question": "Is my data secure?",
        "answer": (
            "We take security seriously. All data is encrypted at rest (AES-256) "
            "and in transit (TLS 1.3). We are SOC 2 Type II certified and GDPR "
            "compliant. Two-factor authentication is available on all plans."
        ),
    },
    {
        "topic": "support",
        "question": "How do I contact support?",
        "answer": (
            "Starter and Growth customers can reach support via in-app chat "
            "(Mon–Fri, 9am–6pm IST) and email (support@example.com). "
            "Enterprise customers have 24/7 dedicated support with a named "
            "account manager."
        ),
    },
    {
        "topic": "refunds",
        "question": "Do you offer refunds?",
        "answer": (
            "We offer a full refund within 7 days of your first charge if you "
            "are not satisfied. After 7 days, refunds are reviewed case-by-case. "
            "Contact support@example.com to initiate a refund request."
        ),
    },
]


def get_knowledge_base_text() -> str:
    """Format the knowledge base as a readable text block for agent context.

    Returns:
        A formatted string containing all FAQ entries.
    """
    lines: list[str] = ["=== KNOWLEDGE BASE ===\n"]
    for i, entry in enumerate(FAQ_KNOWLEDGE_BASE, 1):
        lines.append(f"[Entry {i}] Topic: {entry['topic'].upper()}")
        lines.append(f"Q: {entry['question']}")
        lines.append(f"A: {entry['answer']}")
        lines.append("")
    lines.append("=== END OF KNOWLEDGE BASE ===")
    return "\n".join(lines)
