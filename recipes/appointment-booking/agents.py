"""
Appointment Booking Recipe — agents.py

Defines the agents for the appointment booking crew.
(Scaffold - implement this)
"""

from crewai import Agent
from llm import get_llm

def build_agents() -> tuple[Agent, Agent, Agent]:
    """Build and return the appointment booking crew agents.

    Returns:
        A tuple of (intake_agent, availability_agent, confirmation_agent).
    """
    llm = get_llm()

    intake_agent = Agent(
        role="Appointment Intake Specialist",
        goal=(
            "Parse, validate, and structure appointment requests, "
            "flagging missing or ambiguous information."
        ),
        backstory=(
            "You are a meticulous appointment intake coordinator who reviews "
            "incoming meeting requests, ensures all necessary details are present, "
            "and structures them clearly for scheduling."
        ),
        llm=llm,
        verbose=True,
    )

    availability_agent = Agent(
        role="Calendar & Availability Coordinator",
        goal=(
            "Match requester preferences against available calendar slots and "
            "select the best options."
        ),
        backstory=(
            "You are an efficient calendar manager who cross-references requested "
            "meeting times with current schedule availability, selecting optimal "
            "slots and explaining why they fit."
        ),
        llm=llm,
        verbose=True,
    )

    confirmation_agent = Agent(
        role="Booking Confirmation Specialist",
        goal="Draft clear, professional, and friendly appointment confirmation emails.",
        backstory=(
            "You are a courteous communications specialist who converts selected "
            "meeting slots and booking details into warm, polished confirmation emails "
            "ready to send to clients."
        ),
        llm=llm,
        verbose=True,
    )

    return intake_agent, availability_agent, confirmation_agent

