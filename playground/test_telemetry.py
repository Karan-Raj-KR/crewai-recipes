"""Unit tests for the playground telemetry and execution waterfall tracking engine."""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock

playground_dir = Path(__file__).parent.resolve()
if str(playground_dir) not in sys.path:
    sys.path.insert(0, str(playground_dir))

try:
    from telemetry import PlaygroundTelemetryHandler, TelemetryEvent
except ImportError:
    from playground.telemetry import PlaygroundTelemetryHandler, TelemetryEvent


def test_telemetry_event_to_dict() -> None:
    event = TelemetryEvent(
        timestamp=1731500000.123,
        event="step_completed",
        agent="Research Agent",
        task="Market Research Task",
        tool="SearchTool",
        tool_input={"query": "test query"},
        duration_ms=450.5,
        status="completed",
        details={"has_tool": True},
    )

    data = event.to_dict()
    assert data["type"] == "telemetry"
    inner = data["data"]
    assert inner["event"] == "step_completed"
    assert inner["agent"] == "Research Agent"
    assert inner["task"] == "Market Research Task"
    assert inner["tool"] == "SearchTool"
    assert inner["duration_ms"] == 450.5
    assert inner["status"] == "completed"
    assert inner["details"]["has_tool"] is True


def test_telemetry_handler_task_lifecycle() -> None:
    emitted = []
    handler = PlaygroundTelemetryHandler(emit_callback=emitted.append)

    ev_start = handler.on_task_start(
        task_name="Market Analysis",
        agent_name="Analyst Agent",
        description="Analyze market competitors",
    )
    assert ev_start.event == "task_started"
    assert ev_start.status == "active"
    assert len(emitted) == 1

    ev_end = handler.on_task_end(
        task_name="Market Analysis",
        agent_name="Analyst Agent",
        output="Market analysis complete.",
    )
    assert ev_end.event == "task_completed"
    assert ev_end.status == "completed"
    assert ev_end.duration_ms >= 0.0
    assert len(emitted) == 2


def test_telemetry_handler_step_tracking() -> None:
    emitted = []
    handler = PlaygroundTelemetryHandler(emit_callback=emitted.append)

    step_ev = handler.on_step(
        agent_name="Searcher",
        thought="I should search for competitors",
        tool="WebSearch",
        tool_input={"q": "competitors"},
        result="Found 3 results",
        duration_ms=120.0,
    )

    assert step_ev.event == "step_completed"
    assert step_ev.agent == "Searcher"
    assert step_ev.tool == "WebSearch"
    assert step_ev.status == "completed"
    assert step_ev.details["step_index"] == 1
    assert step_ev.details["has_tool"] is True
    assert len(emitted) == 1


def test_telemetry_handler_run_summary() -> None:
    emitted = []
    handler = PlaygroundTelemetryHandler(emit_callback=emitted.append)

    handler.on_step(agent_name="Agent 1", thought="Thinking")
    summary = handler.on_run_summary(recipe_name="lead-qualification", success=True)

    assert summary.event == "run_summary"
    assert summary.status == "completed"
    assert summary.details["total_steps"] == 1
    assert summary.details["total_events"] == 2
    assert len(emitted) == 2

    timeline = handler.get_waterfall_timeline()
    assert len(timeline) == 2
