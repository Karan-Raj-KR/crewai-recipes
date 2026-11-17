"""
Automated Incident Postmortem Recipe — tasks.py

Defines 3 sequential tasks with explicit context chaining:
1. Reconstruct incident chronological timeline
2. Perform root-cause diagnosis & Five Whys investigation
3. Author blameless postmortem report with prioritized action items
"""

from crewai import Agent, Task


def build_tasks(
    timeline_agent: Agent,
    diagnostician_agent: Agent,
    postmortem_agent: Agent,
    incident_title: str,
    raw_alert_logs: str,
    recent_deployment_summary: str = "",
    impact_metrics: str = "",
) -> list[Task]:
    """Build the incident postmortem task sequence with explicit context chaining.

    Args:
        timeline_agent: Reconstructs chronological event sequence.
        diagnostician_agent: Determines root cause and Five Whys analysis.
        postmortem_agent: Synthesizes final blameless postmortem report.
        incident_title: Name or summary title of the incident.
        raw_alert_logs: Raw log lines, alert timestamps, and observability snippets.
        recent_deployment_summary: Summary or git diff of recent deployments.
        impact_metrics: Metrics summarizing duration, error rate, and financial impact.

    Returns:
        An ordered list of 3 Task objects.
    """
    deployment_info = recent_deployment_summary or "No deployment information provided."
    impact_info = impact_metrics or "Not specified."

    timeline_task = Task(
        description=(
            f"Analyze the technical telemetry and alerts for incident '{incident_title}':\n\n"
            f"  Incident Title: {incident_title}\n"
            f"  Raw Alert & System Logs:\n{raw_alert_logs}\n\n"
            f"  Recent Deployment / Code Changes:\n{deployment_info}\n\n"
            f"  Observed Impact Metrics:\n{impact_info}\n\n"
            "Timeline Reconstruction Requirements:\n"
            "1. Extract all explicit or implied timestamps and sort events chronologically.\n"
            "2. Identify key operational phases: T-0 (First Anomaly), Detection (Alert Trigger), "
            "Investigation, Mitigation Action (e.g. Rollback / Restart), and Full Recovery.\n"
            "3. Highlight duration intervals between detection, response, and stabilization."
        ),
        expected_output=(
            "A structured Markdown Chronological Incident Timeline with:\n"
            "- Milestone timestamps (UTC or relative)\n"
            "- Event classification (Detection, Impact, Mitigation, Resolution)\n"
            "- Component affected and event synopsis"
        ),
        agent=timeline_agent,
    )

    diagnose_task = Task(
        description=(
            "Using the reconstructed timeline and deployment details, investigate the direct technical "
            "root cause and underlying system vulnerabilities.\n\n"
            "Investigation Requirements:\n"
            "1. Identify the direct failure trigger (e.g. unindexed query, missing connection limit, null pointer).\n"
            "2. Examine contributing factors (e.g. lack of load testing, insufficient circuit breaker, missing canary deploy).\n"
            "3. Conduct a rigorous Five Whys root cause analysis, drilling down from user-visible symptom to organizational/architectural root."
        ),
        expected_output=(
            "A Root Cause Analysis Report containing:\n"
            "- Primary Technical Failure Mode\n"
            "- Triggering Mechanism & Blast Radius\n"
            "- Rigorous Five Whys Analysis (Why 1 through Why 5)\n"
            "- Contributing System & Process Factors"
        ),
        agent=diagnostician_agent,
        context=[timeline_task],
    )

    postmortem_task = Task(
        description=(
            f"Synthesize the chronological timeline and root cause findings for '{incident_title}' "
            "into a comprehensive, industry-standard, blameless Markdown postmortem report.\n\n"
            "Postmortem Report Structure:\n"
            "1. **Title & Incident Overview**: Severity, Date, Duration, Leads/On-Call.\n"
            "2. **Executive Summary & User Impact**: Plain-language synopsis, error rates, financial impact.\n"
            "3. **Incident Timeline**: Clean table of chronological events from T-0 to resolution.\n"
            "4. **Root Cause Analysis & Five Whys**: Technical explanation and Five Whys breakdown.\n"
            "5. **Lessons Learned**: 'What went well', 'What went wrong', and 'Where we got lucky'.\n"
            "6. **Preventative Action Items**: Priority matrix (P0: Immediate fix, P1: Hardening next sprint, "
            "P2: Long-term architectural improvement) with assigned Owner Roles."
        ),
        expected_output=(
            "A complete, blameless Markdown Postmortem document ready for engineering review, "
            "adhering to best practices from Google SRE and standard industry postmortem formats."
        ),
        agent=postmortem_agent,
        context=[timeline_task, diagnose_task],
    )

    return [timeline_task, diagnose_task, postmortem_task]
