"""
Lead Qualification Recipe — tasks.py

Defines the three sequential tasks for the lead qualification crew.
"""

from crewai import Agent, Task


def build_tasks(
    research_agent: Agent,
    scoring_agent: Agent,
    summary_agent: Agent,
    lead_data: dict[str, str],
) -> list[Task]:
    """Build and return the ordered task list for lead qualification.

    Args:
        research_agent: Agent responsible for research.
        scoring_agent: Agent responsible for ICP scoring.
        summary_agent: Agent responsible for writing the final report.
        lead_data: Dictionary containing raw lead information.
            Expected keys: name, company, role, email, notes (optional).

    Returns:
        An ordered list of Task objects to be executed sequentially.
    """
    name = lead_data.get("name", "Unknown")
    company = lead_data.get("company", "Unknown Company")
    role = lead_data.get("role", "Unknown Role")
    notes = lead_data.get("notes", "No additional notes provided.")

    research_task = Task(
        description=(
            f"Research the lead: {name} ({role} at {company}).\n\n"
            f"Additional context from the submitter: {notes}\n\n"
            "Using ONLY the information provided (do not hallucinate external "
            "data), infer and summarise:\n"
            "1. Company overview: industry, estimated size, business model.\n"
            "2. The lead's likely seniority and decision-making authority.\n"
            "3. Potential pain points this type of company typically faces.\n"
            "4. Any timing signals or urgency indicators in the notes."
        ),
        expected_output=(
            "A structured research summary in markdown with four clearly "
            "labelled sections: Company Overview, Lead Profile, Likely Pain "
            "Points, and Timing Signals."
        ),
        agent=research_agent,
    )

    scoring_task = Task(
        description=(
            "Using the research summary from the previous task, score this "
            f"lead ({name} at {company}) against our ICP across four "
            "dimensions. For each dimension, provide a score out of 25 and "
            "a one-sentence rationale:\n\n"
            "1. Company Fit (0–25): Industry, size, and business model match.\n"
            "2. Role Fit (0–25): Seniority and purchasing authority.\n"
            "3. Timing Signals (0–25): Urgency, pain acuity, buying signals.\n"
            "4. Engagement Potential (0–25): Likelihood of responding and "
            "progressing through the funnel.\n\n"
            "Total score = sum of all four dimensions (max 100)."
        ),
        expected_output=(
            "A markdown scorecard with a table of the four dimensions "
            "(dimension | score | rationale), a total score out of 100, and "
            "a single-line verdict: HOT (80–100), WARM (50–79), COLD (0–49)."
        ),
        agent=scoring_agent,
        context=[research_task],
    )

    summary_task = Task(
        description=(
            "Write a concise lead qualification report for the sales team "
            f"covering {name} at {company}. The report must be scannable in "
            "under 2 minutes and include:\n\n"
            "1. Lead snapshot (name, role, company, score, verdict).\n"
            "2. Top 3 talking points for the first outreach.\n"
            "3. Recommended next action: CALL NOW / ADD TO NURTURE / "
            "DISQUALIFY — with a one-sentence justification.\n"
            "4. One suggested personalisation angle for the opening line."
        ),
        expected_output=(
            "A clean, markdown-formatted qualification report following the "
            "structure above. Suitable for pasting directly into a CRM note."
        ),
        agent=summary_agent,
        context=[research_task, scoring_task],
    )

    return [research_task, scoring_task, summary_task]
