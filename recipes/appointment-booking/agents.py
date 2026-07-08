"""
Appointment Booking Recipe — agents.py

Three-agent crew that handles the full appointment booking flow:
  1. IntakeAgent     — collects and validates booking request details
  2. AvailabilityAgent — checks the calendar and suggests time slots
  3. ConfirmationAgent — drafts the confirmation message for the user
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
    return ChatGroq(model=model, api_key=api_key, temperature=0.3)


def build_agents() -> tuple[Agent, Agent, Agent]:
    """Build and return the appointment booking agents.

    Returns:
        A tuple of (intake_agent, availability_agent, confirmation_agent).
    """
    llm = _get_llm()

    intake_agent = Agent(
        role="Booking Intake Coordinator",
        goal=(
            "Extract and validate all required information from a booking "
            "request: the requester's name, contact details, preferred dates "
            "and times, meeting type, and any special requirements."
        ),
        backstory=(
            "You are a meticulous front-desk coordinator who has handled "
            "thousands of appointment requests. You know exactly which details "
            "are mandatory and flag any gaps clearly. You are polite, "
            "professional, and never assume missing information."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )

    availability_agent = Agent(
        role="Calendar & Availability Manager",
        goal=(
            "Based on the validated booking request, determine the best "
            "available time slots from the simulated calendar and propose "
            "two or three concrete options to the requester."
        ),
        backstory=(
            "You are a scheduling expert who manages a busy professional "
            "calendar. You work with a simulated set of available slots "
            "(provided in the task description) and always propose options "
            "that respect buffer times, time zones, and meeting duration "
            "requirements."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )

    confirmation_agent = Agent(
        role="Booking Confirmation Specialist",
        goal=(
            "Draft a warm, professional confirmation message that the host "
            "can send to the requester, summarising all booking details and "
            "including a polite call to action to confirm the chosen slot."
        ),
        backstory=(
            "You are a customer-experience specialist known for writing "
            "concise, friendly, and error-free booking confirmations. Your "
            "messages always include all necessary details (date, time, "
            "duration, location/link, and any prep notes) without being wordy."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )

    return intake_agent, availability_agent, confirmation_agent
