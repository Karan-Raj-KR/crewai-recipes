"""Base evaluator contracts and result dataclasses for recipe evaluations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class EvaluationResult:
    """Standardized result produced by any evaluator."""

    metric_name: str
    passed: bool
    score: float  # Normalized score between 0.0 and 1.0
    feedback: str = ""
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert result to serializable dictionary."""
        return {
            "metric_name": self.metric_name,
            "passed": self.passed,
            "score": round(self.score, 4),
            "feedback": self.feedback,
            "details": self.details,
        }


class BaseEvaluator(ABC):
    """Abstract base contract for evaluation metrics."""

    def __init__(self, metric_name: str = "base_evaluator"):
        self.metric_name = metric_name

    @abstractmethod
    def evaluate(
        self,
        output: str,
        expected: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> EvaluationResult:
        """Evaluate the generated recipe output against expected criteria.

        Args:
            output: The string output produced by the recipe.
            expected: Optional dictionary of expected assertions, schemas, or keywords.
            **kwargs: Additional evaluation context.

        Returns:
            An EvaluationResult instance.
        """
