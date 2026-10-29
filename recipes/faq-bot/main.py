"""
FAQ Bot Recipe — main.py

Entry point. Edit SAMPLE_QUESTIONS below to test different inputs.

    python main.py
"""

from dotenv import load_dotenv

load_dotenv()

from crew import build_crew  # noqa: E402

# Rich renders the markdown reply and a spinner; plain print() without it.
try:
    from rich.console import Console
    from rich.markdown import Markdown
    from rich.rule import Rule
except ImportError:
    Console = None

# ─── Sample Questions — try different ones to see graceful fallback ────────────
SAMPLE_QUESTIONS: list[tuple[str, str]] = [
    ("Rahul", "Do you offer a free trial? Do I need a credit card?"),
    ("Maria", "What happens to my data if I cancel?"),
    ("Chen", "Do you support GDPR compliance?"),
    ("Alex", "Can I get a refund if I'm not happy?"),
    # This one should trigger the graceful fallback:
    ("Jamie", "Do you have a mobile app for iOS?"),
]


def main() -> None:
    """Run the FAQ bot crew against a sample question."""
    # Pick the first question — change the index to try others
    customer_name, question = SAMPLE_QUESTIONS[0]

    print("\n🤖  Starting FAQ Bot Crew...\n")
    print(f"   Customer : {customer_name}")
    print(f"   Question : {question}\n")
    print("─" * 60)

    crew = build_crew(question=question, customer_name=customer_name)

    if Console is None:
        result = crew.kickoff()
        print("\n" + "═" * 60)
        print("💬  SUPPORT RESPONSE")
        print("═" * 60)
        print(result)
        print("═" * 60 + "\n")
        return

    console = Console()
    with console.status("Answering question…"):
        result = crew.kickoff()

    console.print()
    console.print(Rule("💬  SUPPORT RESPONSE"))
    console.print(Markdown(str(result)))
    console.print(Rule())
    console.print()


if __name__ == "__main__":
    main()
