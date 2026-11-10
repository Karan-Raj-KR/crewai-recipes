"""
Meeting Notes Summariser Recipe — agents.py

Two crew agents:
  1. Meeting Notes Extractor — extracts key decisions, action items, risks,
     blockers, and open questions from meeting notes.
  2. Email Drafter — drafts a concise follow-up email from that extraction.
"""

from crewai import Agent

from llm import get_llm


def build_agents(verbose: bool = False) -> tuple[Agent, Agent]:
    """Build the extractor and drafter agents."""
    llm = get_llm()
    llm.max_tokens = 8192

    extractor_agent = Agent(
        role="Meeting Notes Extractor",
        goal=(
            "Read meeting notes and produce a concise, structured summary containing: "
            "key decisions, action items (with owner and due date when mentioned), "
            "risks, blockers, and open questions. "
            "Never invent owners or due dates; write 'Not specified' if they are absent."
        ),
        backstory=(
            "You are an experienced meeting analyst who turns messy notes into "
            "clear, accurate, structured summaries without adding details that "
            "were not in the notes."
        ),
        verbose=verbose,
        memory=False,
        llm=llm,
    )

    drafter_agent = Agent(
        role="Email Drafter",
        goal=(
            "Draft a short follow-up email from the extracted meeting notes that "
            "recaps decisions taken, lists each action item with owner and due date, "
            "and highlights open questions that need to be addressed."
        ),
        backstory=(
            "You are an experienced professional with 10 years of writing concise, "
            "well-structured follow-up emails that make next steps unmistakable."
        ),
        verbose=verbose,
        memory=False,
        llm=llm,
    )

    return extractor_agent, drafter_agent