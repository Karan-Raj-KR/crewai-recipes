"""
Automated Incident Postmortem Recipe — crew.py

Assembles the 3-agent SRE postmortem workflow Crew.
"""

from agents import build_agents
from crewai import Crew, Process
from tasks import build_tasks


def build_crew(
    incident_title: str,
    raw_alert_logs: str,
    recent_deployment_summary: str = "",
    impact_metrics: str = "",
) -> Crew:
    """Build and return the automated incident postmortem workflow Crew.

    Args:
        incident_title: Name or summary title of the incident.
        raw_alert_logs: Raw log lines, alert timestamps, and observability snippets.
        recent_deployment_summary: Summary or git diff of recent deployments.
        impact_metrics: Metrics summarizing duration, error rate, and financial impact.

    Returns:
        A configured Crew instance ready to execute via .kickoff().
    """
    timeline_agent, diagnostician_agent, postmortem_agent = build_agents()
    tasks = build_tasks(
        timeline_agent=timeline_agent,
        diagnostician_agent=diagnostician_agent,
        postmortem_agent=postmortem_agent,
        incident_title=incident_title,
        raw_alert_logs=raw_alert_logs,
        recent_deployment_summary=recent_deployment_summary,
        impact_metrics=impact_metrics,
    )

    crew = Crew(
        agents=[timeline_agent, diagnostician_agent, postmortem_agent],
        tasks=tasks,
        process=Process.sequential,
        verbose=True,
    )
    return crew
