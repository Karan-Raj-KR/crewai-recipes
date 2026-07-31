"""
Support Ticket Escalation Recipe — knowledge_base.py

In-memory knowledge base containing verified Tier-1 support resolutions.
"""

# Known issue KB mappings
KNOWN_ISSUES_KB: dict[str, dict[str, str]] = {
    "PASSWORD_RESET": {
        "title": "Password Reset Procedure",
        "resolution": (
            "Navigate to Account Settings > Security > Reset Password. "
            "Click 'Send Email Reset Link' and check your inbox/spam folder for the verification link."
        ),
    },
    "BILLING_INVOICE": {
        "title": "Downloading Billing Invoices",
        "resolution": (
            "Invoices are available under Billing & Subscriptions > Payment History. "
            "Click 'Download PDF' next to the corresponding billing cycle."
        ),
    },
    "RATE_LIMITS": {
        "title": "API Rate Limit Thresholds",
        "resolution": (
            "Free Tier is limited to 60 requests/min. Pro Tier provides 1,000 requests/min. "
            "Enterprise Tier offers custom throughput limits."
        ),
    },
}


def get_kb_summary() -> str:
    """Format the knowledge base entries as a summary text block."""
    lines = []
    for key, data in KNOWN_ISSUES_KB.items():
        lines.append(f"[{key}] {data['title']}: {data['resolution']}")
    return "\n".join(lines)
