"""
Content Pipeline Recipe — main.py

Simulates processing blog topic requests through the content pipeline.

    python main.py
"""

from dotenv import load_dotenv

load_dotenv()

from crew import build_crew  # noqa: E402

# ─── Sample Content Requests ──────────────────────────────────────────────────
SAMPLE_REQUESTS = [
    {
        "topic": "Why Multi-Agent Systems are Replacing Single Prompt AI Workflows",
        "target_audience": "Senior Engineering Managers & Developers",
        "keywords": "Multi-Agent Systems, CrewAI, LLM Orchestration",
    },
    {
        "topic": "Scaling Customer Support with Automated AI Workflows",
        "target_audience": "Customer Success Leaders",
        "keywords": "Customer Support, AI Automation, Efficiency",
    },
]


def main() -> None:
    """Process a sample topic request through the content pipeline crew."""
    request = SAMPLE_REQUESTS[0]

    print("\n📝  Content Production Pipeline — Incoming Request\n")
    print(f"   Topic           : {request['topic']}")
    print(f"   Target Audience : {request['target_audience']}")
    print(f"   Keywords        : {request['keywords']}\n")
    print("─" * 60)

    crew = build_crew(**request)
    result = crew.kickoff()

    print("\n" + "═" * 60)
    print("✨  SEO REVIEW & FINAL POLISHED ARTICLE")
    print("═" * 60)
    print(result)
    print("═" * 60 + "\n")


if __name__ == "__main__":
    main()
