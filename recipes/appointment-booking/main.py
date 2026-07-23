"""
Appointment Booking Recipe — main.py

Entry point. Edit SAMPLE_REQUEST below with your booking details and run:
    python main.py
"""

from dotenv import load_dotenv

load_dotenv()

from crew import build_crew  # noqa: E402


# ─── Sample Booking Request — edit to test your own requests ──────────────────
SAMPLE_REQUEST: dict[str, str] = {
    "name": "Priya Sharma",
    "email": "priya.sharma@example.com",
    "meeting_type": "Product Demo",
    "preferred_times": "Any morning slot this week, preferably before noon IST",
    "notes": "Priya is evaluating our product for her 15-person team. 30-min demo requested.",
}


def main() -> None:
    """Run the appointment booking crew and print the confirmation email."""
    print("\n📅  Starting Appointment Booking Crew...\n")
    print(f"   Requester : {SAMPLE_REQUEST['name']}")
    print(f"   Meeting   : {SAMPLE_REQUEST['meeting_type']}")
    print(f"   Preferred : {SAMPLE_REQUEST['preferred_times']}\n")
    print("─" * 60)

    crew = build_crew(**SAMPLE_REQUEST)
    result = crew.kickoff()

    print("\n" + "═" * 60)
    print("📨  CONFIRMATION EMAIL DRAFT")
    print("═" * 60)
    print(result)
    print("═" * 60 + "\n")


if __name__ == "__main__":
    main()
