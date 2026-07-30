"""
Email Drafting Recipe — main.py

Simulates processing email briefs through the email drafting crew.

    python main.py
"""

from dotenv import load_dotenv

load_dotenv()

from crew import build_crew  # noqa: E402

# ─── Sample Email Briefs ──────────────────────────────────────────────────────
SAMPLE_BRIEFS = [
    {
        "recipient": "Design Team Lead",
        "purpose": "Requesting design review for mobile checkout flow",
        "key_points": "New checkout mocks are ready in Figma, review needed by Wednesday EOD, priority on payment step UX",
        "tone": "friendly",
    },
    {
        "recipient": "Board Members",
        "purpose": "Q3 Performance Summary",
        "key_points": "ARR grew 28% YoY, gross margin expanded to 74%, enterprise customer count reached 150",
        "tone": "formal",
    },
]


def main() -> None:
    """Process a sample brief through the email drafting crew."""
    brief = SAMPLE_BRIEFS[0]

    print("\n📧  Email Drafting Workflow — Processing Brief\n")
    print(f"   Recipient  : {brief['recipient']}")
    print(f"   Purpose    : {brief['purpose']}")
    print(f"   Key Points : {brief['key_points']}")
    print(f"   Tone       : {brief['tone']}\n")
    print("─" * 60)

    crew = build_crew(**brief)
    result = crew.kickoff()

    print("\n" + "═" * 60)
    print("✉️   POLISHED EMAIL & EDITORIAL NOTES")
    print("═" * 60)
    print(result)
    print("═" * 60 + "\n")


if __name__ == "__main__":
    main()
