"""Record a real run of each recipe into site/runs/ for the static gallery.

The gallery on GitHub Pages has no server, so it replays traces captured here.
Every trace is a genuine run against a real LLM — nothing is synthesised.

    LLM_API_KEY=nvapi-... python tools/record_runs.py            # all recipes
    LLM_API_KEY=nvapi-... python tools/record_runs.py faq-bot    # just one

Inputs come from each recipe's inputs.json "example" fields, so the gallery
always demos the same values the playground pre-fills.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RECIPES = ROOT / "recipes"
OUT = ROOT / "site" / "runs"

sys.path.insert(0, str(ROOT / "playground"))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(ROOT / "playground" / ".env")

from main import execute_recipe_stream, get_recipe_description  # noqa: E402


def recipe_dirs() -> list[Path]:
    return sorted(
        d
        for d in RECIPES.iterdir()
        if (d / "crew.py").exists() and not d.name.startswith("_")
    )


def example_inputs(recipe: Path) -> dict[str, str]:
    """Read the demo inputs out of the recipe contract."""
    fields = json.loads((recipe / "inputs.json").read_text())
    missing = [f["name"] for f in fields if not f.get("example")]
    if missing:
        raise SystemExit(
            f"{recipe.name}: inputs.json is missing 'example' for {missing}"
        )
    return {f["name"]: f["example"] for f in fields}


def record(recipe: Path) -> dict:
    inputs = example_inputs(recipe)
    events: list[dict] = []
    start = time.monotonic()

    def push(event: dict) -> None:
        events.append({**event, "t": round(time.monotonic() - start, 2)})

    push({"type": "start", "recipe": recipe.name})
    execute_recipe_stream(recipe.name, inputs, push, threading.Event())

    kinds = {e["type"] for e in events}
    if "error" in kinds:
        errs = [e["error"] for e in events if e["type"] == "error"]
        raise SystemExit(f"{recipe.name}: run failed, refusing to record — {errs[0]}")
    if "complete" not in kinds:
        raise SystemExit(
            f"{recipe.name}: run produced no 'complete' event, refusing to record"
        )

    return {
        "recipe": recipe.name,
        "description": get_recipe_description(recipe),
        "inputs": inputs,
        "model": os.getenv("LLM_MODEL", "meta/llama-3.1-8b-instruct"),
        "recorded_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "duration_s": round(time.monotonic() - start, 1),
        "events": events,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("recipes", nargs="*", help="recipe names (default: all)")
    args = parser.parse_args()

    if not (os.getenv("LLM_API_KEY") or os.getenv("NVIDIA_API_KEY")):
        raise SystemExit(
            "LLM_API_KEY is not set — recordings must come from real runs."
        )

    targets = recipe_dirs()
    if args.recipes:
        by_name = {d.name: d for d in targets}
        unknown = [n for n in args.recipes if n not in by_name]
        if unknown:
            raise SystemExit(
                f"Unknown recipe(s): {unknown}. Available: {sorted(by_name)}"
            )
        targets = [by_name[n] for n in args.recipes]

    OUT.mkdir(parents=True, exist_ok=True)
    for recipe in targets:
        print(f"\n▶ recording {recipe.name} …", flush=True)
        run = record(recipe)
        (OUT / f"{recipe.name}.json").write_text(
            json.dumps(run, indent=1, ensure_ascii=False)
        )
        print(f"✅ {recipe.name}: {len(run['events'])} events in {run['duration_s']}s")

    # Manifest the gallery serves in place of the playground's /recipes endpoint.
    manifest = []
    for recipe in recipe_dirs():
        path = OUT / f"{recipe.name}.json"
        if not path.exists():
            print(f"⚠️  no recording for {recipe.name} — omitted from the gallery")
            continue
        run = json.loads(path.read_text())
        manifest.append(
            {
                "id": recipe.name,
                "description": run["description"],
                "inputs": json.loads((recipe / "inputs.json").read_text()),
                "recorded_at": run["recorded_at"],
                "model": run["model"],
            }
        )
    (OUT / "index.json").write_text(
        json.dumps({"recipes": manifest}, indent=1, ensure_ascii=False)
    )
    print(f"\n📦 site/runs/index.json — {len(manifest)} recipe(s) in the gallery")


if __name__ == "__main__":
    main()
