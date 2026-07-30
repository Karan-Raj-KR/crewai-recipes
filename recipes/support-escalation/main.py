"""
Support Escalation Recipe — main.py

Simulates processing support tickets through auto-resolution and human escalation paths.

    python main.py
"""

from dotenv import load_dotenv

load_dotenv()

from crew import build_crew  # noqa: E402

# ─── Sample Support Tickets ──────────────────────────────────────────────────
# Scenario 1: Auto-resolvable Tier-1 issue (billing invoice download)
SAMPLE_AUTO_RESOLVED_TICKET = {
    "ticket_text": "Hi team, where can I download my billing invoice for last month?",
    "customer_tier": "pro",
    "previous_contacts": "0",
}

# Scenario 2: Complex Tier-2 issue requiring human escalation (custom SSO failure)
SAMPLE_ESCALATION_TICKET = {
    "ticket_text": "Our enterprise SAML SSO integration with Okta started failing with HTTP 500 error after certificate renewal.",
    "customer_tier": "enterprise",
    "previous_contacts": "2",
}


def main() -> None:
    """Process a sample support ticket through the escalation crew."""
    # Toggle between SAMPLE_AUTO_RESOLVED_TICKET and SAMPLE_ESCALATION_TICKET
    ticket = SAMPLE_ESCALATION_TICKET

    print("\n🎧  Support Ticket Workflow — Processing Ticket\n")
    print(f"   Ticket Text       : {ticket['ticket_text']}")
    print(f"   Customer Tier     : {ticket['customer_tier']}")
    print(f"   Previous Contacts : {ticket['previous_contacts']}\n")
    print("─" * 60)

    crew = build_crew(**ticket)
    result = crew.kickoff()

    print("\n" + "═" * 60)
    print("📋  SUPPORT TICKET WORKFLOW OUTCOME")
    print("═" * 60)
    print(result)
    print("═" * 60 + "\n")


if __name__ == "__main__":
    main()
