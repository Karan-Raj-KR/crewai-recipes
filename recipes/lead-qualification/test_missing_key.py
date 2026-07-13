"""Test case to verify run.py exit code and output message when NVIDIA_API_KEY is missing."""

import os
import subprocess
import sys
from pathlib import Path


def test_missing_key() -> None:
    # Set up environment without LLM_API_KEY and NVIDIA_API_KEY, and skip loading .env
    env = os.environ.copy()
    env["CREWAI_RECIPES_SKIP_DOTENV"] = "1"
    env.pop("LLM_API_KEY", None)
    env.pop("NVIDIA_API_KEY", None)

    run_py = Path(__file__).parent / "run.py"
    result = subprocess.run(
        [sys.executable, str(run_py), "--company", "Acme", "--description", "desc"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
    )

    # Verify exit code
    assert result.returncode == 1, f"Expected exit code 1, got {result.returncode}"

    # Verify output message
    expected_output = (
        "❌  LLM_API_KEY is not set.\n"
        "   1. Copy .env.example → .env\n"
        "   2. Add your key: LLM_API_KEY=your-key-here\n"
        "   3. Get a free key at https://build.nvidia.com/\n"
    )
    # Normalize newlines for cross-platform matching
    norm_stdout = result.stdout.replace("\r\n", "\n")
    assert expected_output in norm_stdout, f"Expected setup message, got:\n{result.stdout}"
    assert "Traceback" not in result.stderr, f"Traceback detected in stderr:\n{result.stderr}"


if __name__ == "__main__":
    test_missing_key()
    print("lead-qualification: test_missing_key passed")
