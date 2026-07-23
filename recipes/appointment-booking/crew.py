"""
Appointment Booking Recipe — crew.py

Assembles the CrewAI Crew for appointment booking.
"""

from crewai import Crew, Process

from agents import build_agents
from tasks import build_tasks


def build_crew(
    name: str,
    email: str,
    meeting_type: str,
    preferred_times: str,
    notes: str = "None",
) -> Crew:
    """Build and return the appointment booking Crew.

    Args:
        name: Requester's full name.
        email: Requester's email address.
        meeting_type: Type/purpose of the meeting (e.g. Product Demo).
        preferred_times: Time/date preferences stated by the requester.
        notes: Optional additional context or special requests.

    Returns:
        A configured Crew instance ready to call .kickoff().
    """
    intake_agent, availability_agent, confirmation_agent = build_agents()
    tasks = build_tasks(
        intake_agent,
        availability_agent,
        confirmation_agent,
        name=name,
        email=email,
        meeting_type=meeting_type,
        preferred_times=preferred_times,
        notes=notes,
    )

    return Crew(
        agents=[intake_agent, availability_agent, confirmation_agent],
        tasks=tasks,
        process=Process.sequential,
        verbose=True,
    )

