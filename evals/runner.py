"""CLI and programmatic benchmark runner for CrewAI recipes."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from evals.evaluators.base import BaseEvaluator
from evals.evaluators.keyword_eval import KeywordEvaluator
from evals.evaluators.rubric_eval import RubricEvaluator
from evals.evaluators.schema_eval import SchemaEvaluator
from evals.reporter import BenchmarkReporter, BenchmarkRunRecord

DATASETS_DIR = Path(__file__).resolve().parent / "datasets"


def get_default_evaluators(metric_filter: Optional[str] = None) -> List[BaseEvaluator]:
    evaluators: List[BaseEvaluator] = [
        SchemaEvaluator(),
        KeywordEvaluator(),
        RubricEvaluator(),
    ]
    if metric_filter:
        metric_filter = metric_filter.lower()
        evaluators = [e for e in evaluators if metric_filter in e.metric_name.lower()]
    return evaluators


def run_benchmark_case(
    case: Dict[str, Any],
    recipe_name: str,
    evaluators: List[BaseEvaluator],
    live: bool = False,
) -> BenchmarkRunRecord:
    case_id = case.get("id", "anonymous-case")
    expected = case.get("expected", {})

    output = ""
    start_time = time.perf_counter()

    if live:
        # In live mode, dynamically import the recipe build_crew and kickoff
        try:
            recipes_dir = Path(__file__).resolve().parent.parent / "recipes"
            recipe_path = recipes_dir / recipe_name
            if not recipe_path.exists():
                raise FileNotFoundError(f"Recipe '{recipe_name}' not found in {recipes_dir}")

            sys.path.insert(0, str(recipe_path))
            from crew import build_crew  # type: ignore

            inputs = case.get("inputs", {})
            crew = build_crew(**inputs)
            kickoff_res = crew.kickoff()
            output = str(kickoff_res)
        except Exception as exc:
            duration_ms = (time.perf_counter() - start_time) * 1000
            failed_res = SchemaEvaluator().evaluate(
                output="",
                expected={"format": "error"},
            )
            failed_res.passed = False
            failed_res.score = 0.0
            failed_res.feedback = f"Execution failed: {exc}"
            return BenchmarkRunRecord(
                recipe_name=recipe_name,
                case_id=case_id,
                results=[failed_res],
                latency_ms=duration_ms,
                passed=False,
            )
    else:
        # Hermetic offline mode: evaluate against recorded reference sample output
        output = case.get("sample_output", "")

    duration_ms = (time.perf_counter() - start_time) * 1000

    results = []
    case_passed = True
    for ev in evaluators:
        res = ev.evaluate(output=output, expected=expected)
        results.append(res)
        if not res.passed:
            case_passed = False

    return BenchmarkRunRecord(
        recipe_name=recipe_name,
        case_id=case_id,
        results=results,
        latency_ms=duration_ms,
        passed=case_passed,
    )


def run_evaluations(
    recipe_name: Optional[str] = None,
    dataset_path: Optional[Path] = None,
    metric_filter: Optional[str] = None,
    live: bool = False,
) -> BenchmarkReporter:
    reporter = BenchmarkReporter()
    evaluators = get_default_evaluators(metric_filter=metric_filter)

    dataset_files: List[Path] = []
    if dataset_path:
        dataset_files = [dataset_path]
    elif recipe_name and recipe_name != "all":
        target = DATASETS_DIR / f"{recipe_name}.json"
        if target.exists():
            dataset_files = [target]
        else:
            print(f"Warning: Dataset not found for recipe '{recipe_name}' at {target}", file=sys.stderr)
    else:
        dataset_files = sorted(DATASETS_DIR.glob("*.json"))

    for d_path in dataset_files:
        current_recipe = d_path.stem
        try:
            cases = json.loads(d_path.read_text(encoding="utf-8"))
        except Exception as exc:
            print(f"Error loading dataset {d_path}: {exc}", file=sys.stderr)
            continue

        for case in cases:
            rec = run_benchmark_case(
                case=case,
                recipe_name=current_recipe,
                evaluators=evaluators,
                live=live,
            )
            reporter.add_record(rec)

    return reporter


def main() -> None:
    parser = argparse.ArgumentParser(description="CrewAI Recipes Evaluation & Benchmark Runner")
    parser.add_argument("--recipe", type=str, default="all", help="Recipe name to evaluate (or 'all')")
    parser.add_argument("--all", action="store_true", help="Evaluate all recipes with available datasets")
    parser.add_argument("--dataset", type=Path, default=None, help="Path to custom evaluation dataset JSON")
    parser.add_argument("--metric", type=str, default=None, help="Filter metric ('schema', 'keyword', 'rubric')")
    parser.add_argument("--live", action="store_true", help="Run live crew execution instead of offline evaluation")
    parser.add_argument("--format", choices=["markdown", "json", "summary"], default="markdown", help="Output format")

    args = parser.parse_args()

    recipe = "all" if args.all else args.recipe
    reporter = run_evaluations(
        recipe_name=recipe,
        dataset_path=args.dataset,
        metric_filter=args.metric,
        live=args.live,
    )

    if args.format == "json":
        print(reporter.to_json())
    else:
        print(reporter.to_markdown())

    stats = reporter.summary_stats()
    if stats["failed"] > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
