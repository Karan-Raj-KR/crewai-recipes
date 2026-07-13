"""Smoke test: main() runs without errors and build_crew signature is correct."""

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

os.environ.setdefault("LLM_API_KEY", "nvapi-test")
sys.path.insert(0, str(Path(__file__).parent))

import main as recipe_main  # noqa: E402


def test_main_runs() -> None:
    mock_output = MagicMock()
    mock_output.__str__ = lambda self: "WARM — 55/100\nFollow up within 48h."
    with patch("crewai.Crew.kickoff", return_value=mock_output):
        recipe_main.main()


if __name__ == "__main__":
    test_main_runs()
    print("✅ lead-qualification: main() smoke test passed")
