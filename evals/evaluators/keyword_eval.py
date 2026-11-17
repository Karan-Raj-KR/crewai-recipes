"""Deterministic keyword, phrase, and regex presence evaluator."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from evals.evaluators.base import BaseEvaluator, EvaluationResult


class KeywordEvaluator(BaseEvaluator):
    """Evaluates whether required keywords are present and forbidden keywords are absent."""

    def __init__(self, metric_name: str = "keyword_presence"):
        super().__init__(metric_name=metric_name)

    @staticmethod
    def _matches_keyword(keyword: str, text: str) -> bool:
        """Match keyword with word boundaries if alphanumeric, else case-insensitive substring."""
        if re.match(r"^\w+$", keyword):
            return bool(re.search(r"\b" + re.escape(keyword) + r"\b", text, re.IGNORECASE))
        return keyword.lower() in text.lower()

    def evaluate(
        self,
        output: str,
        expected: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> EvaluationResult:
        expected = expected or {}
        must_include: List[str] = expected.get("must_include", [])
        must_not_include: List[str] = expected.get("must_not_include", [])
        regex_patterns: List[str] = expected.get("regex_patterns", [])

        missing_required = []
        for kw in must_include:
            if not self._matches_keyword(kw, output):
                missing_required.append(kw)

        present_forbidden = []
        for kw in must_not_include:
            if self._matches_keyword(kw, output):
                present_forbidden.append(kw)

        missing_regex = []
        for pat in regex_patterns:
            if not re.search(pat, output, re.IGNORECASE):
                missing_regex.append(pat)

        total_checks = len(must_include) + len(must_not_include) + len(regex_patterns)
        if total_checks == 0:
            return EvaluationResult(
                metric_name=self.metric_name,
                passed=True,
                score=1.0,
                feedback="No keyword assertions specified.",
            )

        failed_checks = len(missing_required) + len(present_forbidden) + len(missing_regex)
        score = max(0.0, (total_checks - failed_checks) / total_checks)
        passed = failed_checks == 0

        feedback_parts = []
        if missing_required:
            feedback_parts.append(f"Missing required keywords: {missing_required}")
        if present_forbidden:
            feedback_parts.append(f"Found forbidden terms: {present_forbidden}")
        if missing_regex:
            feedback_parts.append(f"Unmatched regex patterns: {missing_regex}")

        feedback = "; ".join(feedback_parts) if feedback_parts else "All keyword criteria satisfied."

        return EvaluationResult(
            metric_name=self.metric_name,
            passed=passed,
            score=round(score, 4),
            feedback=feedback,
            details={
                "missing_required": missing_required,
                "present_forbidden": present_forbidden,
                "missing_regex": missing_regex,
            },
        )
