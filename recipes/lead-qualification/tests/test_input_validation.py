"""CLI input validation for lead-qualification (no API key required)."""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "run.py"


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(RUN), *args],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        env={**dict(**__import__("os").environ), "CREWAI_RECIPES_SKIP_DOTENV": "1"},
    )


def test_rejects_too_short_description_before_api():
    proc = _run("--company", "Acme", "--description", "tiny")
    assert proc.returncode != 0
    assert "too short" in (proc.stdout + proc.stderr).lower() or "❌" in proc.stdout


def test_accepts_long_enough_description_shape():
    # Will still fail preflight without API key — but not for description length.
    desc = (
        "A 40-person B2B SaaS company selling workflow automation to mid-market "
        "ops teams with growing ARR."
    )
    proc = _run("--company", "Acme", "--description", desc)
    out = proc.stdout + proc.stderr
    assert "too short" not in out.lower()
    assert "too long" not in out.lower()
