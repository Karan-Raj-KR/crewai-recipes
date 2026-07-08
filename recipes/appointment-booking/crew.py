"""
Appointment Booking Recipe — crew.py

Assembles the CrewAI Crew for appointment booking.
"""

from crewai import Crew, Process

from agents import build_agents
from tasks import build_tasks


def build_crew(booking_request: dict[str, str]) -> Crew:
    """Build and return the appointment booking Crew.

    Args:
        booking_request: Raw booking request data.
            Expected keys: name, email, meeting_type, preferred_times, notes.

    Returns:
        A configured Crew instance ready to call .kickoff().
    """
    intake_agent, availability_agent, confirmation_agent = build_agents()
    tasks = build_tasks(
        intake_agent, availability_agent, confirmation_agent, booking_request
    )

    crew = Crew(
        agents=[intake_agent, availability_agent, confirmation_agent],
        tasks=tasks,
        process=Process.sequential,
        verbose=True,
    )
    return crew
