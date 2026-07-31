"""
Email Drafting Recipe — tasks.py

Two tasks: initial email drafting → editing, auditing & polish.
"""

from crewai import Agent, Task


def build_tasks(
    drafter_agent: Agent,
    editor_agent: Agent,
    recipient: str,
    purpose: str,
    key_points: str,
    tone: str = "professional",
) -> list[Task]:
    """Build the email drafting task list.

    Args:
        drafter_agent: Drafts the initial email.
        editor_agent: Audits key points, tightens tone, and logs edits.
        recipient: Recipient name or role.
        purpose: Main purpose of the email.
        key_points: Key points to include.
        tone: Desired tone (professional / friendly / formal / direct).

    Returns:
        An ordered list of 2 Task objects.
    """
    draft_task = Task(
        description=(
            f"Draft an email based on the following brief:\n\n"
            f"- Recipient: {recipient}\n"
            f"- Purpose: {purpose}\n"
            f"- Key Points to Cover: {key_points}\n"
            f"- Desired Tone: {tone}\n\n"
            "Guidelines:\n"
            "1. Write an appropriate subject line.\n"
            "2. Ensure every single key point mentioned is addressed.\n"
            "3. Structure the email logically with clear paragraphs.\n"
            "4. Match the requested tone: " + tone + "."
        ),
        expected_output=(
            "An Initial Email Draft with:\n"
            "- Subject: <subject line>\n"
            "- Body: <complete draft text>"
        ),
        agent=drafter_agent,
    )

    edit_task = Task(
        description=(
            "Review and refine the email draft from the previous step.\n\n"
            "Audit & Edit Guidelines:\n"
            "1. Key Points Verification: Check that ALL key points ("
            + key_points
            + ") "
            "   are explicitly covered in the email. Flag any missing points.\n"
            "2. Tone Consistency: Ensure the tone strictly matches '" + tone + "'.\n"
            "3. Conciseness: Cut redundant fluff and wordy phrasing.\n"
            "4. Output Structure:\n"
            "   - Final Polished Email (Subject & Body)\n"
            "   - Editorial Notes (short summary of changes made and key points verification)"
        ),
        expected_output=(
            "A final response containing:\n\n"
            "FINAL EMAIL:\n"
            "Subject: <polished subject line>\n\n"
            "Dear <Recipient>,\n"
            "<polished email body>\n\n"
            "EDITORIAL NOTES:\n"
            "- Tone Check: <tone validation>\n"
            "- Key Points Verified: <list of verified key points>\n"
            "- Changes Made: <brief list of edits/padding cut>"
        ),
        agent=editor_agent,
        context=[draft_task],
    )

    return [draft_task, edit_task]
