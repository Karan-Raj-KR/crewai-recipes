"""
WhatsApp Action Sim Recipe — agents.py

Defines the agents for the WhatsApp action simulation crew.
"""

from crewai import Agent
from llm import get_llm


def build_agents() -> tuple[Agent, Agent, Agent]:
    """Build and return the WhatsApp action simulation agents.

    Returns:
        A tuple of (intent_agent, router_agent, composer_agent).
    """
    llm = get_llm()

    intent_agent = Agent(
        role="WhatsApp Intent Classifier",
        goal=(
            "Classify incoming WhatsApp messages accurately into one of the "
            "supported intents."
        ),
        backstory=(
            "You are an expert NLP classification agent trained to detect user intent "
            "in short, informal WhatsApp messages, emojis, and slang."
        ),
        verbose=True,
        memory=False,
        llm=llm,
    )

    router_agent = Agent(
        role="Action Router & Dispatcher",
        goal=(
            "Map classified user intents to simulated system actions and "
            "return structured action payloads."
        ),
        backstory=(
            "You are a customer service integration router that translates user "
            "intents into backend API calls and payload summaries."
        ),
        verbose=True,
        memory=False,
        llm=llm,
    )

    composer_agent = Agent(
        role="WhatsApp Response Composer",
        goal=(
            "Draft warm, concise, and helpful WhatsApp responses based on "
            "action payloads."
        ),
        backstory=(
            "You are a friendly WhatsApp customer support specialist who writes "
            "clear, concise, emoji-friendly replies with mobile-optimized formatting."
        ),
        verbose=True,
        memory=False,
        llm=llm,
    )

    return intent_agent, router_agent, composer_agent
