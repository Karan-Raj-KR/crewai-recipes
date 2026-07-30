"""
Customer Onboarding Recipe — main.py

Simulates processing complete and incomplete customer signup profiles.

    python main.py
"""

from dotenv import load_dotenv

load_dotenv()

from crew import build_crew  # noqa: E402

# ─── Sample Customer Signup Profiles ─────────────────────────────────────────
# Complete profile (valid onboarding)
SAMPLE_COMPLETE_CUSTOMER = {
    "customer_name": "Sarah Connor",
    "company": "Cyberdyne Systems",
    "role": "Chief Security Officer",
    "use_case": "Automating threat intelligence aggregation and incident response",
    "team_size": "50",
}

# Incomplete profile (missing use_case / vague role)
SAMPLE_INCOMPLETE_CUSTOMER = {
    "customer_name": "John Doe",
    "company": "Unknown LLC",
    "role": "N/A",
    "use_case": "stuff",
    "team_size": "1",
}


def main() -> None:
    """Process a sample customer signup profile through the onboarding crew."""
    # Toggle between SAMPLE_COMPLETE_CUSTOMER and SAMPLE_INCOMPLETE_CUSTOMER
    profile = SAMPLE_COMPLETE_CUSTOMER

    print("\n🚀  Customer Onboarding Workflow — Incoming Signup\n")
    print(f"   Name      : {profile['customer_name']}")
    print(f"   Company   : {profile['company']}")
    print(f"   Role      : {profile['role']}")
    print(f"   Use Case  : {profile['use_case']}")
    print(f"   Team Size : {profile['team_size']}\n")
    print("─" * 60)

    crew = build_crew(**profile)
    result = crew.kickoff()

    print("\n" + "═" * 60)
    print("📧  ONBOARDING EMAIL OUTPUT")
    print("═" * 60)
    print(result)
    print("═" * 60 + "\n")


if __name__ == "__main__":
    main()
