"""
Meeting Notes Summariser Recipe — models.py

Pydantic models for structured output.

  - MeetingSummary  -> output of the extractor task
  - FollowUpEmail   -> output of the drafter task
  - MeetingNotesResult -> combined object returned by `run.py --json`
"""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

# Values an LLM tends to emit when a field is missing. Normalised to None so
# downstream code never has to special-case strings like "N/A".
_MISSING = {"", "not specified", "n/a", "na", "none", "unknown", "tbd", "null", "-"}


def _none_if_missing(value: object) -> object:
    if isinstance(value, str) and value.strip().lower() in _MISSING:
        return None
    return value.strip() if isinstance(value, str) else value


def _clean_list(values: list[str]) -> list[str]:
    """Strip whitespace, drop blanks, and remove duplicates (order preserved)."""
    seen: set[str] = set()
    out: list[str] = []
    for v in values:
        v = v.strip()
        if v and v.lower() not in seen:
            seen.add(v.lower())
            out.append(v)
    return out


class ActionItem(BaseModel):
    task: str = Field(..., min_length=1, description="What needs to be done.")
    owner: str | None = Field(
        default=None,
        description="Person responsible. Null if not stated in the notes.",
    )
    due_date: str | None = Field(
        default=None,
        description=(
            "Due date exactly as stated (e.g. '2026-11-07' or 'next Friday'). "
            "Null if not stated. Kept as a string because notes are often relative."
        ),
    )

    @field_validator("owner", "due_date", mode="before")
    @classmethod
    def _normalise_missing(cls, v: object) -> object:
        return _none_if_missing(v)

    @field_validator("task")
    @classmethod
    def _strip_task(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("task must not be blank")
        return v


class MeetingSummary(BaseModel):
    """Structured extraction from the meeting notes (extractor agent output)."""

    decisions: list[str] = Field(default_factory=list, description="Decisions taken.")
    action_items: list[ActionItem] = Field(default_factory=list)
    risks_blockers: list[str] = Field(
        default_factory=list, description="Risks and blockers raised."
    )
    open_questions: list[str] = Field(
        default_factory=list, description="Questions left unresolved."
    )

    @field_validator("decisions", "risks_blockers", "open_questions")
    @classmethod
    def _clean(cls, v: list[str]) -> list[str]:
        return _clean_list(v)


class FollowUpEmail(BaseModel):
    """Follow-up email draft (drafter agent output)."""

    subject: str = Field(..., min_length=1, description="Short, specific subject line.")
    body: str = Field(
        ...,
        min_length=1,
        description="Plain-text body: decisions, action items with owners, open questions.",
    )

    @field_validator("subject", "body")
    @classmethod
    def _strip(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("must not be blank")
        return v


class MeetingNotesResult(BaseModel):
    """Final combined result, serialised by `run.py --json`."""

    summary: MeetingSummary
    email: FollowUpEmail