"""
Content Pipeline Recipe — tasks.py

Four tasks: ideation → outline research → drafting → SEO review.
"""

from crewai import Agent, Task


def build_tasks(
    ideator_agent: Agent,
    researcher_agent: Agent,
    writer_agent: Agent,
    seo_agent: Agent,
    topic: str,
    target_audience: str = "General Tech Audience",
    keywords: str = "AI, Automation",
) -> list[Task]:
    """Build the content production pipeline task list.

    Args:
        ideator_agent: Brainstorms headlines and angles.
        researcher_agent: Builds structured article outline.
        writer_agent: Drafts concise short-form post.
        seo_agent: Performs SEO review and edit suggestions.
        topic: Core topic or theme.
        target_audience: Target readership profile.
        keywords: Comma-separated target keywords.

    Returns:
        An ordered list of 4 Task objects.
    """
    ideator_task = Task(
        description=(
            f"Brainstorm content angles for the topic:\n\n"
            f"  Topic: {topic}\n"
            f"  Target Audience: {target_audience}\n"
            f"  Target Keywords: {keywords}\n\n"
            "Tasks:\n"
            "1. Generate 3 catchy, high-converting headline options.\n"
            "2. Propose a main editorial angle / hook.\n"
            "3. Identify 3 core sub-topics to cover."
        ),
        expected_output=(
            "An Ideation Brief containing:\n"
            "- Headline Options: 3 numbered headlines\n"
            "- Core Editorial Angle: description of main angle\n"
            "- Key Sub-topics: list of 3 sub-topics"
        ),
        agent=ideator_agent,
    )

    researcher_task = Task(
        description=(
            "Using the ideation brief from the previous step, construct a structured "
            "article outline.\n\n"
            "Outline Requirements:\n"
            "1. Introduction: Hook + thesis statement.\n"
            "2. Section 1 (H2): Key argument and core concepts.\n"
            "3. Section 2 (H2): Practical application / real-world relevance.\n"
            "4. Conclusion: Summary + key takeaway.\n"
            "5. Flag any unverified external claims or statistics with [Needs Verification]."
        ),
        expected_output=(
            "A structured Article Outline with H1 title, section H2 headings, "
            "bulleted core talking points, and verification notes."
        ),
        agent=researcher_agent,
        context=[ideator_task],
    )

    writer_task = Task(
        description=(
            "Draft a short-form blog post based on the outline from the previous step.\n\n"
            "Writing Guidelines:\n"
            "1. Keep total length under 500 words to ensure complete generation.\n"
            "2. Use H1 for the selected title and H2 for main section headers.\n"
            "3. Integrate target keywords naturally: " + keywords + ".\n"
            "4. Write in a clear, engaging tone appropriate for " + target_audience + ".\n"
            "5. End with a clear concluding thought or call to action."
        ),
        expected_output=(
            "A complete short-form blog post draft in markdown format with title, "
            "section headings, and body paragraphs."
        ),
        agent=writer_agent,
        context=[ideator_task, researcher_task],
    )

    seo_task = Task(
        description=(
            "Review the article draft from the previous step for SEO alignment and quality.\n\n"
            "Review Guidelines:\n"
            "1. Keyword Placement: Verify target keywords (" + keywords + ") appear in title/intro.\n"
            "2. Structural Clarity: Assess heading hierarchy and section flow.\n"
            "3. Concrete Edit Suggestions: List specific, actionable edits (e.g. 'Reword H2 to include keyword X').\n"
            "4. Final Polish: Provide an updated, polished version of the blog post incorporating the edits.\n\n"
            "Do NOT return a numerical score; focus entirely on concrete improvements."
        ),
        expected_output=(
            "An SEO Review Report & Final Polish containing:\n"
            "1. Actionable SEO & Readability Edits (bulleted list)\n"
            "2. Final Polished Article (complete markdown text)"
        ),
        agent=seo_agent,
        context=[writer_task],
    )

    return [ideator_task, researcher_task, writer_task, seo_task]
