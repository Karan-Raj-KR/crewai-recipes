"""
Meeting Notes Summariser Recipe — main.py

Simulates processing a detailed meeting transcript and a vague one that is
missing owners and dates.

    python main.py
"""
from crew import build_crew  
from models import MeetingNotesResult  
from run import format_markdown  

from dotenv import load_dotenv

load_dotenv()

# ─── Sample Meeting Transcripts ──────────────────────────────────────────────
# Detailed transcript (clear decisions, owners, and dates)
SAMPLE_COMPLETE_MEETING = """\
Project Atlas — Weekly Sync, Thursday 29 October 2026
Attendees: Priya (PM), Marcus (Engineering), Elena (Design), Tom (QA)

Priya opened by confirming the beta launch is still targeted for 16 November.
Marcus reported that the new billing integration is about 80% done. He said he
can finish it by Wednesday 4 November, but only if the payment provider
delivers the sandbox credentials by Monday. They have been waiting on those for
a week and it is the biggest risk to the date.

Elena presented the updated onboarding flow. After some discussion the team
decided to drop the optional "invite teammates" step from the first release and
ship it in v1.1 instead. Elena will update the Figma files and hand them to
Marcus by Friday 30 October.

Tom raised that the test environment is flaky and has failed nightly runs three
times this week. He will investigate and report back on Tuesday 3 November.
Marcus noted that if the environment is not stable by 9 November, QA sign-off
will be at risk.

The group agreed to freeze new feature requests until after the beta launch.
Priya will communicate the freeze to stakeholders by end of day today.

Open questions: Who is responsible for the beta announcement blog post? Does
legal need to review the updated terms of service before launch? Nobody knew
whether the support team has been trained on the new billing screens.

Next sync is Thursday 5 November.
"""

# Vague transcript (no owners, no dates, few concrete decisions)
SAMPLE_VAGUE_MEETING = """\
Quick chat about the website stuff.

We talked about the homepage and how it feels a bit outdated. Someone said we
should probably refresh it at some point. Not sure about the budget. The
newsletter signup could be better too, maybe we look at that. Everyone seemed
fine with revisiting this later. Also the old blog posts might need cleaning up,
but we didn't decide anything.
"""


def main() -> None:
    """Process a sample meeting transcript through the summariser crew."""
    # Toggle between SAMPLE_COMPLETE_MEETING and SAMPLE_VAGUE_MEETING
    transcript = SAMPLE_COMPLETE_MEETING

    print("\n🚀  Meeting Notes Summariser — Incoming Transcript\n")
    print(f"   Words: {len(transcript.split())}\n")
    print("─" * 60)

    crew = build_crew(transcript=transcript)
    crew.kickoff()

    # kickoff() returns only the last task's output, so read each task directly.
    extract_task, draft_task = crew.tasks
    result = MeetingNotesResult(
        summary=extract_task.output.pydantic,
        email=draft_task.output.pydantic,
    )

    print("\n" + "═" * 60)
    print("📋  MEETING SUMMARY + FOLLOW-UP EMAIL")
    print("═" * 60)
    print(format_markdown(result))
    print("═" * 60 + "\n")


if __name__ == "__main__":
    main()