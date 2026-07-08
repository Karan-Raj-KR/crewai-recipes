"""
WhatsApp Action Sim Recipe — main.py

Simulates processing incoming WhatsApp messages through the action pipeline.

    python main.py
"""

from dotenv import load_dotenv

load_dotenv()

from crew import build_crew  # noqa: E402

# ─── Sample WhatsApp Messages ─────────────────────────────────────────────────
# Try different messages to see how the intent classifier and router behave
SAMPLE_MESSAGES: list[tuple[str, str]] = [
    ("Ravi", "Hey! Where's my order? It's been 3 days now 😤"),
    ("Sunita", "I want to book a demo for next week"),
    ("Tom", "What's your return policy?"),
    ("Ananya", "This is unacceptable! My package arrived damaged!"),
    ("Dev", "Great service btw, loved the packaging 🙌"),
    ("Guest", "Can I speak to a real person please?"),
    ("Sam", "asjdhajsdhkj"),  # UNKNOWN intent test
]


def main() -> None:
    """Process a sample WhatsApp message through the crew."""
    # Change the index to test different messages
    sender_name, message = SAMPLE_MESSAGES[0]

    print("\n📱  WhatsApp Action Sim — Incoming Message\n")
    print(f"   From    : {sender_name}")
    print(f"   Message : {message}\n")
    print("─" * 60)

    crew = build_crew(user_message=message, sender_name=sender_name)
    result = crew.kickoff()

    print("\n" + "═" * 60)
    print("📤  WHATSAPP REPLY")
    print("═" * 60)
    print(result)
    print("═" * 60 + "\n")


if __name__ == "__main__":
    main()
