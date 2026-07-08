"""
Lead Qualification Recipe — tasks.py

Two sequential tasks:
  1. research_task  — deep-dives into the company from the provided description
  2. scoring_task   — scores the company against ICP criteria (0-100)
"""

from crewai import Agent, Task


def build_tasks(
    research_agent: Agent,
    scoring_agent: Agent,
    company: str,
    description: str,
) -> list[Task]:
    """Build the ordered task list for lead qualification.

    Args:
        research_agent: Agent that profiles the company.
        scoring_agent: Agent that scores the company.
        company: The company name.
        description: A short description of the company.

    Returns:
        An ordered list of [research_task, scoring_task].
    """
    research_task = Task(
        description=(
            f"Company Name: {company}\n"
            f"Description: {description}\n\n"
            "Using ONLY the information provided above (do not hallucinate "
            "external data), extract and summarise the following signals:\n\n"
            "1. **Industry & Vertical** — what sector is this company in?\n"
            "2. **Business Model** — B2B, B2C, marketplace, SaaS, services?\n"
            "3. **Company Size Estimate** — startup / SMB / mid-market / enterprise?\n"
            "4. **Growth Stage** — pre-product, early-stage, scaling, mature?\n"
            "5. **Likely Pain Points** — top 3 operational or strategic pains "
            "   this type of company typically faces.\n"
            "6. **Budget & Tech Signal** — any clues about spending power or "
            "   technical sophistication?\n\n"
            "Be concise. Use bullet points. Flag any ambiguity clearly."
        ),
        expected_output=(
            "A structured markdown research summary with six labelled "
            "sections as described. Maximum 300 words."
        ),
        agent=research_agent,
    )

    scoring_task = Task(
        description=(
            f"Using the research summary for **{company}**, score this lead "
            "against our ICP. Apply the following rubric:\n\n"
            "| Dimension            | Max pts | Scoring Guide |\n"
            "|----------------------|---------|---------------|\n"
            "| Industry Fit         | 25      | How well does the industry match a "
            "typical B2B SaaS buyer? |\n"
            "| Company Size Fit     | 25      | Does the size fit an SMB-to-mid-market "
            "sweet spot? |\n"
            "| Pain Point Acuity    | 25      | How acute and urgent are their "
            "identified pain points? |\n"
            "| Budget/Growth Signal | 25      | Do signals suggest willingness and "
            "ability to spend? |\n\n"
            "For each dimension: state the score (e.g. '18 / 25') and one sentence "
            "of reasoning. Then compute the total and give a verdict.\n\n"
            "**Verdict thresholds:** HOT = 75-100, WARM = 40-74, COLD = 0-39\n\n"
            "Close with a recommended next action in one sentence."
        ),
        expected_output=(
            "A markdown scorecard with:\n"
            "- A table of 4 dimensions with scores and rationale\n"
            "- Total score out of 100\n"
            "- Verdict (HOT / WARM / COLD)\n"
            "- Recommended next action"
        ),
        agent=scoring_agent,
        context=[research_task],
    )

    return [research_task, scoring_task]
