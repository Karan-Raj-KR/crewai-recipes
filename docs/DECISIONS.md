# Project Decisions

Short log of deliberate choices about how this repo is run, so contributors
(and future me) understand the *why*. Newest first.

## The gallery replays recordings instead of running live (2026-08)

The playground is the most persuasive thing in this repo — you watch the agents
think — and it was only reachable by cloning, installing crewai, and getting a
NIM key. So it now also ships as a public gallery on GitHub Pages.

It replays recorded runs rather than executing live, for three reasons that are
not fixable by tightening a config:

1. **Cost.** `crew.kickoff()` bills the maintainer's key. A public Run button is
   an open invitation to spend someone else's credits, unbounded (see #181).
2. **Code execution.** The playground `exec_module()`s whatever is in `recipes/`.
   Those files arrive by pull request. A public deploy makes every merge a
   potential RCE on the host.
3. **Shape.** Runs block for 5–60s; free tiers fall over on exactly that profile.

`tools/record_runs.py` captures the same SSE events the live endpoint emits, and
`site/static-shim.js` patches `fetch` so the *unmodified* playground UI reads
them from JSON. One UI, two data sources — the deployed site cannot drift from
the local app, because it is built from the same file.

Recordings are real runs only: the recorder refuses to save a run that errored
or never completed, and the gallery banner says plainly that inputs are fixed to
what was recorded. Faking a trace would be the one thing that makes the whole
premise worthless.

**Live execution is deferred, not rejected.** Bring-your-own-key — the visitor
pastes their own free NIM key, with per-IP rate limiting and a recipe allowlist —
is the phase-2 design. Deferred until the gallery shows there's traffic worth
paying a server for.

## New recipes must not require editing CI (2026-08)

`ci.yml` had grown to 452 lines: nine near-identical hand-copied jobs, one per
recipe, plus the recipe list repeated three times in the lint step. Adding a
recipe meant copying 50 lines of YAML, and forgetting to meant your recipe was
never tested.

Replaced with a `discover` job that lists `recipes/*/crew.py` and feeds a matrix
(452 → 163 lines). The recipe list now lives in exactly one place: the
filesystem.

Paired with `tests/test_recipe_contract.py`, which walks the same directories and
asserts the contract — required files, `inputs.json` well-formed, and crucially
that `inputs.json` and the `build_crew` signature agree, since a mismatch there
is a runtime 500 in the playground with no earlier warning. Stdlib only: no
crewai, no API key, no install, so a contributor gets the verdict in seconds.

## llm.py stays copied, but drift is now a CI failure (2026-08)

Per-recipe isolation (#7 below) means `llm.py` is duplicated eight times, and it
drifted — #191 and #193 were both "recipe N is out of sync with recipe M". The
tempting fix is a shared module, which would break the property that makes a
recipe copy-pasteable on its own.

Kept the copies; made drift fail CI instead. `tools/sync_llm.py` propagates an
edit to every recipe, `--check` reports drift, and the contract suite asserts all
copies are byte-identical. The per-recipe name in the docstring — the only real
difference between the eight files at the time — was replaced with a line telling
you to run the sync tool.

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
default and expose 70B as an opt-in via the `LLM_MODEL` environment variable. No
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
