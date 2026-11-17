"""
Playground Agent Execution Telemetry Handler and Waterfall Timeline Data Engine.

Tracks step and task lifecycles, execution latencies, tool calls, and emits
structured telemetry events for real-time waterfall timeline inspection (#266).
"""

from __future__ import annotations

import time
from dataclasses import asdict, dataclass, field
from typing import Any, Callable, Dict, List, Optional


@dataclass
class TelemetryEvent:
    """Individual structured telemetry event emitted to frontend clients."""

    timestamp: float
    event: str  # task_started, step_completed, tool_started, tool_completed, task_completed, run_summary
    agent: str = "Agent"
    task: str = ""
    tool: Optional[str] = None
    tool_input: Optional[Any] = None
    duration_ms: float = 0.0
    status: str = "active"  # active, completed, failed, pending
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "telemetry",
            "data": {
                "timestamp": round(self.timestamp, 3),
                "event": self.event,
                "agent": self.agent,
                "task": self.task,
                "tool": self.tool,
                "tool_input": self.tool_input,
                "duration_ms": round(self.duration_ms, 2),
                "status": self.status,
                "details": self.details,
            },
        }


class PlaygroundTelemetryHandler:
    """Hooks into recipe execution to capture granular timeline metrics and waterfall traces."""

    def __init__(self, emit_callback: Optional[Callable[[Dict[str, Any]], None]] = None):
        self.emit_callback = emit_callback
        self.start_time: float = time.time()
        self.active_tasks: Dict[str, float] = {}
        self.events: List[TelemetryEvent] = []
        self.step_counter: int = 0

    def emit(self, event: TelemetryEvent) -> None:
        self.events.append(event)
        if self.emit_callback:
            try:
                self.emit_callback(event.to_dict())
            except Exception:
                pass

    def on_task_start(self, task_name: str, agent_name: str, description: str = "") -> TelemetryEvent:
        now = time.time()
        task_key = f"{agent_name}:{task_name}"
        self.active_tasks[task_key] = now

        ev = TelemetryEvent(
            timestamp=now,
            event="task_started",
            agent=agent_name,
            task=task_name,
            status="active",
            details={"description": description[:150]},
        )
        self.emit(ev)
        return ev

    def on_step(
        self,
        agent_name: str,
        thought: str = "",
        tool: Optional[str] = None,
        tool_input: Optional[Any] = None,
        result: Optional[Any] = None,
        duration_ms: float = 0.0,
    ) -> TelemetryEvent:
        now = time.time()
        self.step_counter += 1

        ev = TelemetryEvent(
            timestamp=now,
            event="step_completed",
            agent=agent_name,
            tool=tool,
            tool_input=tool_input,
            duration_ms=duration_ms,
            status="completed" if not result or "error" not in str(result).lower() else "failed",
            details={
                "step_index": self.step_counter,
                "thought_preview": thought[:120] if thought else "",
                "has_tool": bool(tool),
            },
        )
        self.emit(ev)
        return ev

    def on_task_end(
        self,
        task_name: str,
        agent_name: str,
        output: str = "",
        duration_ms: Optional[float] = None,
    ) -> TelemetryEvent:
        now = time.time()
        task_key = f"{agent_name}:{task_name}"
        if duration_ms is None:
            start = self.active_tasks.pop(task_key, self.start_time)
            duration_ms = (now - start) * 1000

        ev = TelemetryEvent(
            timestamp=now,
            event="task_completed",
            agent=agent_name,
            task=task_name,
            duration_ms=max(0.0, duration_ms),
            status="completed",
            details={"output_preview": output[:120] if output else ""},
        )
        self.emit(ev)
        return ev

    def on_run_summary(self, recipe_name: str, success: bool = True) -> TelemetryEvent:
        now = time.time()
        total_duration_ms = (now - self.start_time) * 1000

        ev = TelemetryEvent(
            timestamp=now,
            event="run_summary",
            task=recipe_name,
            duration_ms=total_duration_ms,
            status="completed" if success else "failed",
            details={
                "total_steps": self.step_counter,
                "total_events": len(self.events) + 1,
                "total_duration_ms": round(total_duration_ms, 2),
            },
        )
        self.emit(ev)
        return ev

    def get_waterfall_timeline(self) -> List[Dict[str, Any]]:
        """Return serialized list of all events for waterfall timeline rendering."""
        return [asdict(e) for e in self.events]
