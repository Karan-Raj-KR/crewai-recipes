"""
Automated Incident Postmortem Recipe — run.py

CLI entry point for running the automated incident postmortem workflow.

Usage:
    python run.py --incident-title "Checkout Service 503 Spike" --raw-alert-logs "..."
"""

import argparse
import os
import sys

from dotenv import load_dotenv

load_dotenv()

from crew import build_crew  # noqa: E402


def check_env() -> None:
    """Preflight environment check for required API key."""
    provider = os.getenv("LLM_PROVIDER", "primary").lower()
    if provider in ("fallback", "secondary"):
        api_key = os.getenv("LLM_FALLBACK_API_KEY")
    else:
        api_key = (
            os.getenv("LLM_API_KEY")
            or os.getenv("NVIDIA_API_KEY")
            or os.getenv("LLM_FALLBACK_API_KEY")
        )
    if not api_key:
        print("❌ Error: Missing API key.", file=sys.stderr)
        print(
            "   Please set the API key for your selected provider in .env or the environment.",
            file=sys.stderr,
        )
        print(
            "   Use LLM_API_KEY (or NVIDIA_API_KEY) for primary, or LLM_FALLBACK_API_KEY for fallback.",
            file=sys.stderr,
        )
        sys.exit(1)


def main() -> None:
    """Parse CLI arguments and run the incident postmortem crew."""
    parser = argparse.ArgumentParser(
        description="Automated Incident Postmortem — SRE Timeline, Root Cause & Blameless Report Generator"
    )

    parser.add_argument(
        "--incident-title",
        type=str,
        default="Checkout Service 503 HTTP Spike during Flash Sale",
        help="Name or summary title of the incident",
    )
    parser.add_argument(
        "--raw-alert-logs",
        type=str,
        default=(
            "2026-11-10T14:02:11Z [CRIT] connection_pool_exhausted db_host=pg-primary-01 pool_size=100 active=100\n"
            "2026-11-10T14:03:45Z [ERR] HTTP 503 upstream connect timeout /api/v1/checkout rate=840req/s\n"
            "2026-11-10T14:18:20Z [INFO] hotfix deployment v2.14.1 rollback initiated by oncall\n"
            "2026-11-10T14:26:00Z [INFO] pool utilization returned to 18%, error rate 0.01%"
        ),
        help="Raw log lines, alert timestamps, and observability snippets",
    )
    parser.add_argument(
        "--recent-deployment-summary",
        type=str,
        default="Commit a1b2c3d: Added unindexed foreign key lookup on order_items table in checkout transaction flow.",
        help="Summary or git diff of recent deployments",
    )
    parser.add_argument(
        "--impact-metrics",
        type=str,
        default="Duration: 24 mins. 14,200 checkout requests failed (12.4% error rate). Estimated delayed GMV: $42,000.",
        help="Summary of duration, error rate, and business impact",
    )

    args = parser.parse_args()
    check_env()

    print("\n🚨  Automated Incident Postmortem — Multi-Agent SRE Reconstruction\n")
    print(f"   Incident Title: {args.incident_title}")
    print(f"   Impact Metrics: {args.impact_metrics}")
    print("─" * 70)

    crew = build_crew(
        incident_title=args.incident_title,
        raw_alert_logs=args.raw_alert_logs,
        recent_deployment_summary=args.recent_deployment_summary,
        impact_metrics=args.impact_metrics,
    )

    result = crew.kickoff()

    print("\n" + "═" * 70)
    print("📋  FINAL BLAMELESS POSTMORTEM REPORT")
    print("═" * 70 + "\n")
    print(result)


if __name__ == "__main__":
    main()
