"""Deterministic JSON and Markdown schema validator."""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional

from evals.evaluators.base import BaseEvaluator, EvaluationResult


class SchemaEvaluator(BaseEvaluator):
    """Validates structural compliance of recipe output (JSON schema or Markdown structure)."""

    def __init__(self, metric_name: str = "schema_compliance"):
        super().__init__(metric_name=metric_name)

    @staticmethod
    def extract_json(text: str) -> Optional[Any]:
        """Extract first valid JSON object or list from text or markdown code fence."""
        # Check direct parse
        text = text.strip()
        try:
            return json.loads(text)
        except Exception:
            pass

        # Check markdown ```json ... ``` blocks
        matches = re.findall(r"```(?:json)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
        for block in matches:
            try:
                return json.loads(block.strip())
            except Exception:
                continue

        # Look for raw balanced braces
        brace_match = re.search(r"(\{[\s\S]*\}|\[[\s\S]*\])", text)
        if brace_match:
            try:
                return json.loads(brace_match.group(1).strip())
            except Exception:
                pass

        return None

    def evaluate(
        self,
        output: str,
        expected: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> EvaluationResult:
        expected = expected or {}
        output_format = expected.get("format", "json").lower()
        required_keys: List[str] = expected.get("required_keys", [])
        required_sections: List[str] = expected.get("required_sections", [])

        if output_format == "json":
            parsed = self.extract_json(output)
            if parsed is None:
                return EvaluationResult(
                    metric_name=self.metric_name,
                    passed=False,
                    score=0.0,
                    feedback="Output does not contain valid JSON.",
                    details={"error": "JSONDecodeError"},
                )

            if isinstance(parsed, dict) and required_keys:
                missing = [k for k in required_keys if k not in parsed]
                if missing:
                    score = (len(required_keys) - len(missing)) / len(required_keys)
                    return EvaluationResult(
                        metric_name=self.metric_name,
                        passed=False,
                        score=round(score, 4),
                        feedback=f"Missing required JSON keys: {missing}",
                        details={"missing_keys": missing, "present_keys": list(parsed.keys())},
                    )

            return EvaluationResult(
                metric_name=self.metric_name,
                passed=True,
                score=1.0,
                feedback="Output complies with expected JSON schema.",
                details={"parsed_type": type(parsed).__name__},
            )

        elif output_format in ("markdown", "text"):
            # Check required markdown sections/headers (e.g. "## Timeline", "# Summary")
            if required_sections:
                missing_sections = [
                    sec for sec in required_sections if not re.search(re.escape(sec), output, re.IGNORECASE)
                ]
                if missing_sections:
                    score = (len(required_sections) - len(missing_sections)) / len(required_sections)
                    return EvaluationResult(
                        metric_name=self.metric_name,
                        passed=False,
                        score=round(score, 4),
                        feedback=f"Missing required Markdown sections: {missing_sections}",
                        details={"missing_sections": missing_sections},
                    )

            return EvaluationResult(
                metric_name=self.metric_name,
                passed=True,
                score=1.0,
                feedback="Output complies with expected Markdown structure.",
            )

        return EvaluationResult(
            metric_name=self.metric_name,
            passed=True,
            score=1.0,
            feedback=f"Unrecognized format '{output_format}'; defaulted to pass.",
        )
