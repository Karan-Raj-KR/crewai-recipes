"""
WhatsApp Action Sim Recipe — agents.py

Three-agent crew simulating a WhatsApp-style message processor:
  1. IntentClassifierAgent — identifies the user's intent from a message
  2. ActionRouterAgent     — maps the intent to the correct downstream action
  3. ResponseComposerAgent — drafts the reply message in WhatsApp style
"""

import os

from crewai import Agent
from langchain_groq import ChatGroq


def _get_llm(model: str = "llama-3.1-8b-instant") -> ChatGroq:
    """Instantiate the Groq LLaMA LLM.

    Args:
        model: Groq model identifier.

    Returns:
        A configured ChatGroq instance.

    Raises:
        EnvironmentError: If GROQ_API_KEY is not set.
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "GROQ_API_KEY is not set. "
            "Export it or add it to your .env file."
        )
    return ChatGroq(model=model, api_key=api_key, temperature=0.2)


def build_agents() -> tuple[Agent, Agent, Agent]:
    """Build and return the WhatsApp action sim agents.

    Returns:
        A tuple of (intent_agent, router_agent, composer_agent).
    """
    llm = _get_llm()

    intent_agent = Agent(
        role="Message Intent Classifier",
        goal=(
            "Analyse an incoming WhatsApp message and classify the user's "
            "primary intent into one of the supported categories: "
            "ORDER_STATUS, BOOK_APPOINTMENT, FAQ, COMPLAINT, FEEDBACK, "
            "HUMAN_ESCALATION, or UNKNOWN."
        ),
        backstory=(
            "You are an NLP specialist who has trained intent classifiers "
            "for conversational commerce platforms. You understand colloquial "
            "language, abbreviations, and the informal tone common in messaging "
            "apps. You classify intents with high confidence and always flag "
            "ambiguous messages rather than guessing."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )

    router_agent = Agent(
        role="Action Router & Executor",
        goal=(
            "Given the classified intent, determine and execute the appropriate "
            "downstream action using the simulated action registry. "
            "Return the action name, parameters, and a simulated response payload."
        ),
        backstory=(
            "You are a backend integration specialist who maintains the action "
            "registry for a multi-channel customer engagement platform. You know "
            "exactly which API endpoint or internal function each intent maps to, "
            "and you construct well-formed action payloads with proper parameters."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )

    composer_agent = Agent(
        role="WhatsApp Response Composer",
        goal=(
            "Compose a natural, concise WhatsApp reply based on the action "
            "result. Responses should feel human, not robotic — use "
            "appropriate emoji, line breaks, and a conversational tone. "
            "Keep replies under 160 characters where possible."
        ),
        backstory=(
            "You are a conversational UX designer who has crafted WhatsApp "
            "business message templates for e-commerce and service companies. "
            "You know that brevity wins on mobile, emojis add warmth, and "
            "a clear call-to-action at the end improves engagement."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )

    return intent_agent, router_agent, composer_agent
