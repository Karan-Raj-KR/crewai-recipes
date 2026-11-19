"""Rubric-based multi-criteria evaluator with deterministic offline scoring and LLM support."""

from __future__ import annotations

import re
from typing import Any

from evals.evaluators.base import BaseEvaluator, EvaluationResult


class RubricEvaluator(BaseEvaluator):
    """Scores outputs against a weighted rubric dictionary."""

    def __init__(self, metric_name: str = "rubric_score"):
        super().__init__(metric_name=metric_name)

    def evaluate(
        self,
        output: str,
        expected: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> EvaluationResult:
        expected = expected or {}
        rubric: dict[str, dict[str, Any]] = expected.get("rubric", {})

        if not rubric:
            return EvaluationResult(
                metric_name=self.metric_name,
                passed=True,
                score=1.0,
                feedback="No rubric defined for this test case.",
            )

        total_weight = 0.0
        weighted_score = 0.0
        criteria_scores: dict[str, float] = {}
        criteria_feedback: list[str] = []

        word_count = len(output.split())

        for criterion_name, spec in rubric.items():
            weight = float(spec.get("weight", 1.0))
            total_weight += weight

            crit_score = 1.0
            crit_reasons = []

            min_words = spec.get("min_words")
            if min_words and word_count < min_words:
                factor = max(0.0, word_count / min_words)
                crit_score = min(crit_score, factor)
                crit_reasons.append(f"Word count {word_count} < required {min_words}")

            keywords = spec.get("keywords", [])
            if keywords:
                found = sum(
                    1
                    for kw in keywords
                    if re.search(r"\b" + re.escape(kw) + r"\b", output, re.IGNORECASE)
                )
                kw_factor = found / len(keywords)
                crit_score = min(crit_score, kw_factor)
                if kw_factor < 1.0:
                    crit_reasons.append(
                        f"Only {found}/{len(keywords)} expected keywords found"
                    )

            criteria_scores[criterion_name] = round(crit_score, 4)
            weighted_score += crit_score * weight

            if crit_reasons:
                criteria_feedback.append(f"{criterion_name}: {'; '.join(crit_reasons)}")

        final_score = weighted_score / total_weight if total_weight > 0 else 1.0
        threshold = float(expected.get("passing_threshold", 0.70))
        passed = final_score >= threshold

        feedback = f"Rubric score: {final_score:.2%} (threshold: {threshold:.2%}). " + (
            "; ".join(criteria_feedback)
            if criteria_feedback
            else "All criteria passed."
        )

        return EvaluationResult(
            metric_name=self.metric_name,
            passed=passed,
            score=round(final_score, 4),
            feedback=feedback,
            details={
                "criteria_scores": criteria_scores,
                "passing_threshold": threshold,
            },
        )
