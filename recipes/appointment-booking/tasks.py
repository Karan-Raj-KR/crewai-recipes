"""
Appointment Booking Recipe — tasks.py

Defines the three tasks in the booking workflow.
"""

from crewai import Agent, Task

# Simulated available calendar slots — in a real system, this would come
# from a Google Calendar / Calendly / CRM API integration.
SIMULATED_AVAILABLE_SLOTS: list[str] = [
    "Monday 14 Jul 2026 — 10:00 AM IST (30 min)",
    "Monday 14 Jul 2026 — 3:00 PM IST (30 min)",
    "Tuesday 15 Jul 2026 — 11:00 AM IST (30 min)",
    "Wednesday 16 Jul 2026 — 2:00 PM IST (30 min)",
    "Thursday 17 Jul 2026 — 9:00 AM IST (30 min)",
]


def build_tasks(
    intake_agent: Agent,
    availability_agent: Agent,
    confirmation_agent: Agent,
    name: str,
    email: str,
    meeting_type: str,
    preferred_times: str,
    notes: str = "None",
) -> list[Task]:
    """Build the ordered task list for the appointment booking crew.

    Args:
        intake_agent: Agent that validates the booking request.
        availability_agent: Agent that checks available slots.
        confirmation_agent: Agent that drafts the confirmation.
        name: Requester's full name.
        email: Requester's email address.
        meeting_type: Type of meeting requested.
        preferred_times: Preferred days/times stated by the requester.
        notes: Optional additional notes or context.

    Returns:
        An ordered list of Task objects.
    """
    notes_str = notes if notes and notes.strip() else "None"


    intake_task = Task(
        description=(
            f"Process the following appointment booking request:\n\n"
            f"  Name        : {name}\n"
            f"  Email       : {email}\n"
            f"  Meeting Type: {meeting_type}\n"
            f"  Preferred   : {preferred_times}\n"
            f"  Notes       : {notes_str}\n\n"
            "Validate that all required fields are present. "
            "If anything is ambiguous, note it clearly. "
            "Summarise the validated request in a structured format."
        ),
        expected_output=(
            "A validated booking summary in markdown with sections: "
            "Requester Details, Meeting Requirements, Preferred Times, "
            "and a Validation Status (COMPLETE / NEEDS CLARIFICATION with "
            "specific gaps listed)."
        ),
        agent=intake_agent,
    )

    availability_task = Task(
        description=(
            "Using the validated booking request and the following list of "
            "currently available calendar slots, identify the best 2–3 options "
            "that match the requester's preferences:\n\n"
            + "\n".join(f"  • {slot}" for slot in SIMULATED_AVAILABLE_SLOTS)
            + "\n\nPrioritise slots that align with the requester's stated "
            "preferences. If no slot perfectly matches, explain the closest "
            "alternatives. Include the meeting duration in your suggestion."
        ),
        expected_output=(
            "A ranked list of 2–3 suggested slots in markdown, each with: "
            "the date/time, duration, and a one-line reason why it suits the "
            "requester's stated preferences."
        ),
        agent=availability_agent,
        context=[intake_task],
    )

    confirmation_task = Task(
        description=(
            f"Draft a professional booking confirmation email to {name} "
            f"({email}) presenting the suggested time slots. The email should:\n\n"
            "1. Open with a warm, personalised greeting.\n"
            "2. Briefly confirm the meeting type and purpose.\n"
            "3. Present the 2–3 time slot options clearly.\n"
            "4. Ask them to reply with their preferred slot.\n"
            "5. Include a friendly closing and the host's signature line "
            "(use placeholder: [Host Name], [Title]).\n\n"
            "Keep it under 150 words. Professional but human."
        ),
        expected_output=(
            "A complete, ready-to-send email in plain text (not markdown), "
            "including subject line, greeting, body, and sign-off."
        ),
        agent=confirmation_agent,
        context=[intake_task, availability_task],
    )

    return [intake_task, availability_task, confirmation_task]
