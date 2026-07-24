"""
Customer Onboarding Recipe — tasks.py

Three tasks: data collection → validation & audit → email composition.
"""

from crewai import Agent, Task


def build_tasks(
    collector_agent: Agent,
    validator_agent: Agent,
    composer_agent: Agent,
    customer_name: str,
    company: str,
    role: str,
    use_case: str,
    team_size: str,
) -> list[Task]:
    """Build the customer onboarding task pipeline list.

    Args:
        collector_agent: Structures signup inputs.
        validator_agent: Audits profile completeness and consistency.
        composer_agent: Drafts tailored welcome or follow-up email.
        customer_name: Customer's full name.
        company: Customer's company name.
        role: Customer's job role or title.
        use_case: Stated primary use case or goal.
        team_size: Size of the team/organization.

    Returns:
        An ordered list of Task objects.
    """
    collector_task = Task(
        description=(
            f"Process incoming customer signup details:\n\n"
            f"- Customer Name: {customer_name}\n"
            f"- Company: {company}\n"
            f"- Job Role / Title: {role}\n"
            f"- Primary Use Case: {use_case}\n"
            f"- Team Size: {team_size}\n\n"
            "Organize these details into a standardized, structured customer profile report. "
            "Highlight any fields that are blank, 'N/A', vague, or missing."
        ),
        expected_output=(
            "A structured Customer Profile Summary with:\n"
            "- Customer Name: <name>\n"
            "- Company: <company>\n"
            "- Role: <role>\n"
            "- Primary Use Case: <use_case>\n"
            "- Team Size: <team_size>\n"
            "- Initial Observations: note any missing or sparse fields"
        ),
        agent=collector_agent,
    )

    validator_task = Task(
        description=(
            "Audit the customer profile structured in the previous step.\n\n"
            "Validation Rules:\n"
            "1. Check if all required details (name, company, role, use_case, team_size) "
            "   are provided and meaningful.\n"
            "2. Flag fields that are vague (e.g. 'stuff', 'test'), missing, or contradictory.\n"
            "3. DO NOT invent or fabricate missing details.\n"
            "4. Assign an Onboarding Status: READY (all essential data present and valid) or "
            "   INCOMPLETE (one or more essential fields missing or unclear).\n"
            "5. List specific missing/vague fields and recommended follow-up questions if INCOMPLETE."
        ),
        expected_output=(
            "An Onboarding Audit Report with:\n"
            "- Status: READY or INCOMPLETE\n"
            "- Completeness Score: High / Medium / Low\n"
            "- Missing or Vague Fields: list of fields requiring clarification (or None)\n"
            "- Recommendation: Proceed to onboarding OR request missing details"
        ),
        agent=validator_agent,
        context=[collector_task],
    )

    composer_task = Task(
        description=(
            "Draft an outbound onboarding email for the customer based on the audit results.\n\n"
            "Composition Rules:\n"
            "1. If Status is READY:\n"
            "   - Draft a warm, personalized welcome email addressed to the customer.\n"
            "   - Reference their specific company, role, and use case.\n"
            "   - Provide relevant, tailored next steps (e.g. documentation, kickoff call, setup guide).\n"
            "2. If Status is INCOMPLETE:\n"
            "   - Draft a polite, helpful email thanking them for signing up.\n"
            "   - Clearly ask for the specific missing or vague information needed to complete onboarding.\n"
            "   - Keep the tone encouraging, professional, and supportive.\n\n"
            "Output ONLY the complete email (Subject line and Body) — no meta explanations or markdown tags."
        ),
        expected_output=(
            "A ready-to-send email with:\n"
            "Subject: <engaging subject line>\n"
            "Body: <personalized email body with appropriate greeting and signature>"
        ),
        agent=composer_agent,
        context=[collector_task, validator_task],
    )

    return [collector_task, validator_task, composer_task]
