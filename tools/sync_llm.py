"""Propagate one recipe's llm.py to every other recipe.

Recipes are deliberately self-contained (docs/DECISIONS.md #7), so llm.py is
copied rather than imported — which is exactly how it drifted apart in #191 and
#193. Edit any one copy, run this, and they match again.

    python tools/sync_llm.py                    # source = the copy you just edited
    python tools/sync_llm.py --from faq-bot     # pick the source explicitly
    python tools/sync_llm.py --check            # report drift, change nothing

tests/test_recipe_contract.py enforces the same invariant in CI.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RECIPES = ROOT / "recipes"


def llm_files() -> list[Path]:
    return sorted(
        p for p in RECIPES.glob("*/llm.py") if not p.parent.name.startswith("_")
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--from", dest="source", metavar="RECIPE", help="recipe to copy from"
    )
    parser.add_argument(
        "--check", action="store_true", help="exit non-zero if copies differ"
    )
    args = parser.parse_args()

    files = llm_files()
    if not files:
        print("No recipes with an llm.py found.", file=sys.stderr)
        return 1

    if args.check:
        baseline, *rest = files
        odd = [p for p in rest if p.read_bytes() != baseline.read_bytes()]
        if not odd:
            print(f"✅ all {len(files)} llm.py copies are identical")
            return 0
        print(
            f"❌ llm.py differs from {baseline.relative_to(ROOT)} in:", file=sys.stderr
        )
        for p in odd:
            print(f"   {p.relative_to(ROOT)}", file=sys.stderr)
        print("\nFix with: python tools/sync_llm.py --from <recipe>", file=sys.stderr)
        return 1

    if args.source:
        source = RECIPES / args.source / "llm.py"
        if source not in files:
            print(f"No llm.py for recipe '{args.source}'.", file=sys.stderr)
            return 1
    else:
        # Default to the copy you just edited.
        source = max(files, key=lambda p: p.stat().st_mtime)
        print(f"Source: {source.relative_to(ROOT)} (most recently modified)")

    payload = source.read_bytes()
    changed = [p for p in files if p != source and p.read_bytes() != payload]
    for p in changed:
        p.write_bytes(payload)
        print(f"  updated {p.relative_to(ROOT)}")

    print(f"✅ {len(changed)} file(s) synced from {source.parent.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
