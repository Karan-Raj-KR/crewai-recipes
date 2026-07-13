"""
Lead Qualification Recipe — main.py

Entry point. Run this file to qualify a lead.

Usage:
    python main.py

Edit the SAMPLE_LEAD dict below or pipe in your own data to get started.
"""

from dotenv import load_dotenv

load_dotenv()  # Load LLM_API_KEY from .env if present

from crew import build_crew  # noqa: E402 (import after load_dotenv)


# ─── Sample Lead — edit this to test your own leads ───────────────────────────
SAMPLE_LEAD: dict[str, str] = {
    "name": "Jordan Lee",
    "company": "Acme SaaS Co.",
    "role": "Head of Revenue Operations",
    "email": "jordan.lee@acmesaas.example.com",
    "notes": (
        "Inbound form submission. Jordan mentioned they're 'evaluating "
        "automation vendors' and their team has grown from 5 to 40 reps "
        "in the last 18 months. They're currently using spreadsheets for "
        "pipeline management. Series B, ~$12M raised."
    ),
}


def main() -> None:
    """Run the lead qualification crew and print the final report."""
    print("\n🚀  Starting Lead Qualification Crew...\n")
    print(f"   Lead  : {SAMPLE_LEAD['name']}")
    print(f"   Role  : {SAMPLE_LEAD['role']}")
    print(f"   Company: {SAMPLE_LEAD['company']}\n")
    print("─" * 60)

    crew = build_crew(SAMPLE_LEAD)
    result = crew.kickoff()

    print("\n" + "═" * 60)
    print("📋  QUALIFICATION REPORT")
    print("═" * 60)
    print(result)
    print("═" * 60 + "\n")


if __name__ == "__main__":
    main()
