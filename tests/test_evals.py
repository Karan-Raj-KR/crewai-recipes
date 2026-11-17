"""Unit tests for the recipe evaluation and benchmark harness."""

import json
from pathlib import Path

import pytest

from evals.evaluators.keyword_eval import KeywordEvaluator
from evals.evaluators.rubric_eval import RubricEvaluator
from evals.evaluators.schema_eval import SchemaEvaluator
from evals.reporter import BenchmarkReporter, BenchmarkRunRecord
from evals.runner import run_evaluations


def test_schema_evaluator_valid_json() -> None:
    evaluator = SchemaEvaluator()
    output = '{"name": "test", "score": 95, "status": "active"}'
    expected = {"format": "json", "required_keys": ["name", "score"]}

    result = evaluator.evaluate(output=output, expected=expected)
    assert result.passed is True
    assert result.score == 1.0


def test_schema_evaluator_markdown_json_block() -> None:
    evaluator = SchemaEvaluator()
    output = "Here is the response:\n```json\n{\"lead\": \"Acme\", \"qualified\": true}\n```"
    expected = {"format": "json", "required_keys": ["lead", "qualified"]}

    result = evaluator.evaluate(output=output, expected=expected)
    assert result.passed is True
    assert result.score == 1.0


def test_schema_evaluator_missing_keys() -> None:
    evaluator = SchemaEvaluator()
    output = '{"name": "test"}'
    expected = {"format": "json", "required_keys": ["name", "missing_key"]}

    result = evaluator.evaluate(output=output, expected=expected)
    assert result.passed is False
    assert result.score == 0.5
    assert "missing_key" in result.feedback


def test_schema_evaluator_markdown_structure() -> None:
    evaluator = SchemaEvaluator()
    output = "# Incident Overview\n\n## Timeline\n- 14:00 Start\n\n## Action Items\n- Fix issue"
    expected = {"format": "markdown", "required_sections": ["# Incident Overview", "## Timeline", "## Action Items"]}

    result = evaluator.evaluate(output=output, expected=expected)
    assert result.passed is True
    assert result.score == 1.0


def test_keyword_evaluator_presence_and_forbidden() -> None:
    evaluator = KeywordEvaluator()
    output = "The customer requested a refund for billing charges. Status: RESOLVED."

    # Both must_include present, forbidden absent
    expected = {
        "must_include": ["refund", "billing"],
        "must_not_include": ["DISQUALIFIED", "ERROR"],
    }
    result = evaluator.evaluate(output=output, expected=expected)
    assert result.passed is True
    assert result.score == 1.0

    # Forbidden term found
    bad_expected = {
        "must_include": ["refund"],
        "must_not_include": ["RESOLVED"],
    }
    bad_result = evaluator.evaluate(output=output, expected=bad_expected)
    assert bad_result.passed is False
    assert "RESOLVED" in bad_result.feedback


def test_keyword_evaluator_regex() -> None:
    evaluator = KeywordEvaluator()
    output = "Incident tracked under ID: INC-2026-9901."
    expected = {"regex_patterns": [r"INC-\d{4}-\d{4}"]}

    result = evaluator.evaluate(output=output, expected=expected)
    assert result.passed is True
    assert result.score == 1.0


def test_rubric_evaluator() -> None:
    evaluator = RubricEvaluator()
    output = "We recommend the following immediate action item: schedule a technical architecture review with the sales team."
    expected = {
        "rubric": {
            "actionability": {"weight": 0.5, "keywords": ["action", "recommend"]},
            "context": {"weight": 0.5, "keywords": ["architecture", "sales"]},
        },
        "passing_threshold": 0.7,
    }

    result = evaluator.evaluate(output=output, expected=expected)
    assert result.passed is True
    assert result.score == 1.0


def test_benchmark_reporter_outputs() -> None:
    reporter = BenchmarkReporter()
    record = BenchmarkRunRecord(
        recipe_name="test-recipe",
        case_id="case-01",
        results=[SchemaEvaluator().evaluate(output='{"key": "val"}', expected={"format": "json"})],
        latency_ms=14.5,
        passed=True,
    )
    reporter.add_record(record)

    md = reporter.to_markdown()
    assert "CrewAI Recipes Benchmark Report" in md
    assert "test-recipe" in md
    assert "✅ PASS" in md

    json_str = reporter.to_json()
    data = json.loads(json_str)
    assert data["summary"]["total"] == 1
    assert data["summary"]["passed"] == 1


def test_runner_offline_execution() -> None:
    reporter = run_evaluations(recipe_name="all")
    stats = reporter.summary_stats()
    assert stats["total"] >= 3
    assert stats["passed"] == stats["total"]
    assert stats["failed"] == 0
