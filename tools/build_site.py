"""Build the static gallery from the playground UI.

The gallery is the playground's own index.html with one <script> injected ahead
of the app code — see site/static-shim.js. Keeping it a build step (rather than
a forked copy) means the deployed site can never drift from the local UI.

    python tools/build_site.py     # writes site/index.html

Recordings in site/runs/ are produced separately by tools/record_runs.py and
are committed, so a deploy never needs an API key.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "playground" / "static" / "index.html"
SITE = ROOT / "site"
ANCHOR = "\n<script>"
SHIM = '\n<script src="static-shim.js"></script>\n<script>'


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--require-runs",
        action="store_true",
        help="fail if there are no recordings (used by the deploy workflow, so "
        "an empty gallery is never published)",
    )
    args = parser.parse_args()

    html = SOURCE.read_text(encoding="utf-8")

    if html.count(ANCHOR) != 1:
        print(
            f"❌ expected exactly one app <script> in {SOURCE.relative_to(ROOT)}, "
            f"found {html.count(ANCHOR)}. Update ANCHOR in tools/build_site.py.",
            file=sys.stderr,
        )
        return 1

    runs = SITE / "runs" / "index.json"
    if not runs.exists():
        message = (
            "site/runs/index.json is missing — record real runs first:\n"
            "    LLM_API_KEY=nvapi-... python tools/record_runs.py"
        )
        if args.require_runs:
            print(f"❌ {message}", file=sys.stderr)
            return 1
        print(f"⚠️  {message}\n   Building anyway; the gallery will be empty.")

    out = SITE / "index.html"
    out.write_text(html.replace(ANCHOR, SHIM, 1), encoding="utf-8")
    print(f"✅ {out.relative_to(ROOT)} built from {SOURCE.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
