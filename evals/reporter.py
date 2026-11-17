"""Report generator for recipe benchmark results."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Dict, List

from evals.evaluators.base import EvaluationResult


@dataclass
class BenchmarkRunRecord:
    """Record of a single evaluation on a recipe test case."""

    recipe_name: str
    case_id: str
    results: List[EvaluationResult] = field(default_factory=list)
    latency_ms: float = 0.0
    passed: bool = True


class BenchmarkReporter:
    """Collects benchmark run records and formats summary reports."""

    def __init__(self):
        self.records: List[BenchmarkRunRecord] = []

    def add_record(self, record: BenchmarkRunRecord) -> None:
        self.records.append(record)

    def summary_stats(self) -> Dict[str, Any]:
        total_runs = len(self.records)
        if total_runs == 0:
            return {"total": 0, "passed": 0, "failed": 0, "pass_rate": 0.0, "avg_latency_ms": 0.0}

        passed_runs = sum(1 for r in self.records if r.passed)
        avg_latency = sum(r.latency_ms for r in self.records) / total_runs

        return {
            "total": total_runs,
            "passed": passed_runs,
            "failed": total_runs - passed_runs,
            "pass_rate": round(passed_runs / total_runs, 4),
            "avg_latency_ms": round(avg_latency, 2),
        }

    def to_markdown(self) -> str:
        stats = self.summary_stats()
        lines = [
            "# 📊 CrewAI Recipes Benchmark Report",
            "",
            "## Summary Metrics",
            f"- **Total Test Cases Evaluated**: {stats['total']}",
            f"- **Passed**: {stats['passed']} ({stats['pass_rate']:.1%})",
            f"- **Failed**: {stats['failed']}",
            f"- **Average Latency**: {stats['avg_latency_ms']:.1f} ms",
            "",
            "## Benchmark Results Table",
            "",
            "| Recipe | Case ID | Latency (ms) | Status | Metric Scores | Feedback |",
            "| :--- | :--- | :--- | :--- | :--- | :--- |",
        ]

        for r in self.records:
            status_badge = "✅ PASS" if r.passed else "❌ FAIL"
            scores_str = ", ".join(f"{res.metric_name}: {res.score:.2f}" for res in r.results)
            feedback_str = " | ".join(res.feedback for res in r.results if res.feedback)
            feedback_str = feedback_str.replace("\n", " ")[:100]
            lines.append(
                f"| `{r.recipe_name}` | `{r.case_id}` | {r.latency_ms:.1f} | {status_badge} | {scores_str} | {feedback_str} |"
            )

        lines.append("")
        return "\n".join(lines)

    def to_json(self) -> str:
        return json.dumps(
            {
                "summary": self.summary_stats(),
                "records": [
                    {
                        "recipe_name": r.recipe_name,
                        "case_id": r.case_id,
                        "passed": r.passed,
                        "latency_ms": r.latency_ms,
                        "results": [res.to_dict() for res in r.results],
                    }
                    for r in self.records
                ],
            },
            indent=2,
        )
