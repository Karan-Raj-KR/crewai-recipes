"""
Meeting Notes Summariser Recipe — tasks.py

Two sequential tasks:
  1. extract_task — turns the raw transcript into a structured MeetingSummary.
  2. draft_task   — turns that summary into a FollowUpEmail (via context chaining).

The transcript is passed into build_tasks() and embedded directly in the
extractor task's description, so the crew works with a plain `crew.kickoff()`.
"""

from crewai import Agent, Task

from models import FollowUpEmail, MeetingSummary


def build_tasks(
    extractor_agent: Agent, drafter_agent: Agent, transcript: str
) -> list[Task]:
    """Build and return the ordered task list for the crew.

    Args:
        extractor_agent: The Meeting Notes Extractor from agents.py.
        drafter_agent: The Email Drafter from agents.py.
        transcript: The raw meeting notes / transcript text.

    Returns:
        [extract_task, draft_task], in execution order.
    """

    extract_task = Task(
        description=(
            "Read the meeting transcript below and extract the following:\n"
            "- decisions: every decision that was taken\n"
            "- action_items: each with a task, an owner, and a due_date\n"
            "- risks_blockers: risks and blockers that were raised\n"
            "- open_questions: questions that were left unresolved\n\n"
            "Rules:\n"
            "- Use only information present in the transcript. Do not invent "
            "decisions, owners, or dates.\n"
            "- If an action item has no stated owner or due date, leave that "
            "field null rather than guessing.\n"
            "- Keep each entry to one short, self-contained sentence.\n"
            "- If a category has nothing, return an empty list.\n\n"
            "TRANSCRIPT:\n" + transcript
        ),
        expected_output=(
            "A MeetingSummary object with decisions, action_items "
            "(task, owner, due_date), risks_blockers, and open_questions."
        ),
        agent=extractor_agent,
        output_pydantic=MeetingSummary,
    )

    draft_task = Task(
        description=(
            "Using the extracted meeting summary from the previous task, write a "
            "short follow-up email to the attendees.\n\n"
            "The email must:\n"
            "1. Briefly recap the decisions taken.\n"
            "2. List every action item with its owner and due date. If the owner "
            "or due date is missing, write 'owner TBD' or 'due date TBD'.\n"
            "3. Surface any open questions that still need answers.\n\n"
            "Rules:\n"
            "- Keep it concise: under 200 words in the body.\n"
            "- Professional, friendly tone. Plain text, no markdown.\n"
            "- Do not add decisions, owners, or dates that are not in the summary.\n"
            "- Omit a section entirely if it has no content."
        ),
        expected_output=(
            "A FollowUpEmail object with a specific subject line and a plain-text "
            "body covering decisions, action items with owners and due dates, "
            "and open questions."
        ),
        agent=drafter_agent,
        context=[extract_task],
        output_pydantic=FollowUpEmail,
    )

    return [extract_task, draft_task]