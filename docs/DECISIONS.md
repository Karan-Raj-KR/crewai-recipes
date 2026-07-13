# Project Decisions

Short log of deliberate choices about how this repo is run, so contributors
(and future me) understand the *why*. Newest first.

## Contributor-experience conventions (adopted 2026-07)

Surveyed a handful of well-run cookbook/template repos (openai-cookbook,
LangChain/LlamaIndex cookbooks, the GitHub OSS Guides, and Sonatype's
"documents that welcome contributors") to decide what's worth copying for a
small solo-maintained project. Adopted:

1. **Task-first README** — what it is, quickstart, recipe table with status, then contributing. A newcomer reaches "run it" in the first screen.
2. **Structured issue forms** (`.github/ISSUE_TEMPLATE/*.yml`) over free-text, plus a `config.yml` routing questions to Discussions and security reports away from public issues.
3. **A single PR template** with a "no secrets / runs locally / README updated" checklist — the three things that actually block merges here.
4. **`good first issue` as a first-class funnel** — every one is scoped to a self-contained, mergeable PR, surfaced with a README badge and count.
5. **Badges reflect reality only** — CI status, supported Python range, license, PRs-welcome. No vanity/stat badges.
6. **Honest capability claims** — docs state the *actual* default model (Llama 3.1 8B), with the bigger model as a documented opt-in. See below.
7. **Per-recipe isolation** — each recipe owns its `requirements.txt`, `.env.example`, and README; CI installs each one independently.
8. **Docs are guides, not governance** — architecture, agent patterns, NIM setup, and a "write a recipe" walkthrough. No committees.
9. **Discussions for open-ended, Issues for actionable** — questions and ideas go to Discussions; bugs and scoped work go to Issues.
10. **Right-sized process** — see the deliberate omissions below.

## Deliberately *not* adopted (right-sizing for a solo maintainer)

- **No `GOVERNANCE.md` / steering committees** — one maintainer; a governance doc would be theater.
- **Removed `CODEOWNERS`** — a solo `* @owner` line only auto-requests review from the one person who merges everything. It adds nothing; dropped it.
- **`SECURITY.md` kept but slimmed** — no formal advisory SLA or multi-tier process. It's a short, honest note about API-key hygiene and how to report privately, which *is* relevant since every recipe handles a key. Reconsider a fuller policy only if the project grows past one maintainer.
- **No mandatory test framework yet** — recipes are small and LLM-backed (hard to assert exact output). CI does lint + import/structure checks; unit tests are invited via `good first issue`s, not gated.

## Model default: honesty over marketing (2026-07)

Early copy claimed "Llama 3.3 70B." In practice the 70B model times out often on
the NIM free tier, so every recipe actually defaults to **`meta/llama-3.1-8b-instruct`**
(fast, reliable, free). Rather than paper over that, the docs now state 8B as the
default and expose 70B as an opt-in via the `NIM_MODEL` environment variable. No
contradictory claims left in code, docs, badges, or the repo description.

## README structure: fastest path first (2026-07)

Moved the "30-second start" block to the very top of the README — immediately after
the one-line description and badges, before "What is this?" and before the full
Quickstart. Rationale: a first-time visitor who arrives from a LinkedIn post or a
search result makes a go/no-go decision in the first scroll. If the first thing they
see is a 5-step guide, many bounce. The inline `LLM_API_KEY=... python run.py ...`
block takes four lines, works without a `.env` file, and proves the repo actually
runs — immediately.

Added a "Why crewai-recipes?" comparison table (rolling-your-own vs. recipe) after
the description. Each row was verified against the code before writing — no row claims
a feature that doesn't exist. The CI row says "lint + import-wiring assertions", not
"unit tests", because that's what CI currently does.

Also fixed two stale references uncovered during the audit:
- `CODEOWNERS` removed from the project structure tree (was deleted in a prior pass).
- `NIM_MODEL` in the Contributing summary replaced with `LLM_MODEL` (the current name).
Added `docs/providers.md` to the Documentation link list (it exists but wasn't linked).

## Playground Frontend: Plain HTML/JS (2026-07)

For the local web playground, a vanilla HTML/CSS/JS frontend was chosen over React/Vite.
**Why?**
- **Zero build step:** Contributors can edit `index.html` and refresh the browser instantly without running Node.js or `npm install`.
- **Minimal dependencies:** The backend is Python (FastAPI). Forcing users to install a JS toolchain just to run the local playground raises the barrier to entry significantly.
- **Longevity:** Plain HTML/JS doesn't suffer from dependency rot. It will work identically 5 years from now.
