"""
Support Escalation Recipe — tasks.py

Three tasks: triage & severity classification → KB resolution attempt → resolution/escalation handoff.
"""

from crewai import Agent, Task
from knowledge_base import get_kb_summary


def build_tasks(
    triage_agent: Agent,
    resolver_agent: Agent,
    escalation_agent: Agent,
    ticket_text: str,
    customer_tier: str = "pro",
    previous_contacts: str = "0",
) -> list[Task]:
    """Build the support ticket escalation task list.

    Args:
        triage_agent: Classifies ticket category and severity.
        resolver_agent: Checks knowledge base and attempts Tier-1 resolution.
        escalation_agent: Formats resolution or structured human handoff brief.
        ticket_text: Description of the customer support issue.
        customer_tier: Account tier (free, pro, enterprise).
        previous_contacts: Number of previous contact attempts.

    Returns:
        An ordered list of 3 Task objects.
    """
    kb_text = get_kb_summary()

    triage_task = Task(
        description=(
            f"Analyze the incoming customer support ticket:\n\n"
            f"  Ticket Issue: {ticket_text}\n"
            f"  Customer Tier: {customer_tier}\n"
            f"  Previous Contacts: {previous_contacts}\n\n"
            "Triage Rules:\n"
            "1. Categorize the issue (e.g. Account Security, Billing, API Usage, Complex Integration, Outage).\n"
            "2. Assign a Severity Level: MUST be EXACTLY ONE of [LOW, MEDIUM, HIGH, CRITICAL].\n"
            "3. Assess if this issue appears resolvable by Tier-1 standard procedures or requires specialized human escalation."
        ),
        expected_output=(
            "A Triage Report with:\n"
            "- Category: <category>\n"
            "- Severity: LOW / MEDIUM / HIGH / CRITICAL\n"
            "- Initial Assessment: TIER1_CANDIDATE or TIER2_ESCALATION"
        ),
        agent=triage_agent,
    )

    resolver_task = Task(
        description=(
            "Using the triage report from the previous task, attempt to resolve the issue "
            "strictly using the following verified knowledge base entries:\n\n"
            f"```\n{kb_text}\n```\n\n"
            "Resolution Rules:\n"
            "1. If a clear, verified match exists in the KB, output Status: AUTO_RESOLVED "
            "   and include the exact resolution steps.\n"
            "2. If no clear KB match exists or the issue is complex/custom, output Status: ESCALATE_TO_HUMAN.\n"
            "3. DO NOT speculate, invent workarounds, or fabricate answers."
        ),
        expected_output=(
            "A Resolution Attempt Report with:\n"
            "- Status: AUTO_RESOLVED or ESCALATE_TO_HUMAN\n"
            "- KB Match: <KB key name or None>\n"
            "- Attempted Solution: <KB solution details or explanation of why escalation is required>"
        ),
        agent=resolver_agent,
        context=[triage_task],
    )

    escalation_task = Task(
        description=(
            "Produce the final support response based on the previous audit results.\n\n"
            "Output Rules:\n"
            "1. If Resolution Status is AUTO_RESOLVED:\n"
            "   - Format a helpful, professional resolution message for the customer with step-by-step instructions.\n"
            "2. If Resolution Status is ESCALATE_TO_HUMAN:\n"
            "   - Produce a structured Human Agent Handoff Summary containing:\n"
            "     - Customer Goal: What the customer is trying to accomplish\n"
            "     - Account & Severity Context: Customer Tier and Severity Level\n"
            "     - Steps Attempted: What automated Tier-1 checks were performed\n"
            "     - Blocking Issue: Why Tier-1 could not resolve the ticket\n"
            "     - Suggested Next Action for Human Specialist"
        ),
        expected_output=(
            "A final support outcome containing either:\n"
            "A) AUTO-RESOLUTION RESPONSE (Customer facing steps)\n"
            "OR\n"
            "B) HUMAN HANDOFF BRIEF with sections: Customer Goal, Context, Steps Attempted, "
            "Blocking Issue, and Suggested Next Action."
        ),
        agent=escalation_agent,
        context=[triage_task, resolver_task],
    )

    return [triage_task, resolver_task, escalation_task]
