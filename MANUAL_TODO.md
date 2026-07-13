# Manual To-Do

Last updated: 2026-07-13 (pre-launch quality pass, commit `95cf230`).

---

## ✅ Done — pre-launch quality pass (2026-07-13)

**CI fixed (was red on main):**
- `ruff format` failures in all four `llm.py` files — reformatted, CI now green.
- CI import-check env updated from deprecated `NVIDIA_API_KEY` to `LLM_API_KEY`.

**Claim/reality mismatches fixed:**
- `README.md`, `docs/nim-setup.md`, `docs/writing-a-recipe.md`, `docs/architecture.md`,
  and recipe entry points: all references to deprecated `NVIDIA_API_KEY` / `NIM_MODEL`
  updated to canonical `LLM_API_KEY` / `LLM_MODEL` — now consistent with `.env.example`.
- `docs/architecture.md`: LLM config example rewritten to show the actual `get_llm()`
  pattern instead of hardcoded boilerplate; file-tree expanded to include `llm.py` and `run.py`.

**Hygiene:**
- Deleted `.github/workflows/greet.yml` — exact duplicate of `welcome.yml`; was
  double-welcoming every first-time contributor.
  **Note:** dependabot PR #12 (`actions/first-interaction-3`) now targets `welcome.yml`.
  Merge it when you handle the 15 dependabot PRs.
- Removed broken `./screenshot.png` reference from `playground/README.md`.
- Added `.ruff_cache/` to `.gitignore`.
- Committed `playground/test_app.py` (was untracked; useful integration smoke test).

**PART 2 — N/A:** No user-authored open PRs found. All 15 open PRs are from dependabot.
Nothing to convert to issues.

**PART 3 — ECSoC Sentinel labels created:**
- `ECSoC26` (#FF6B35) — event tag
- `ECSoC26-L1` (#00C49A) — easy
- `ECSoC26-L2` (#F7B731) — medium
- `ECSoC26-L3` (#E84393) — hard
- `good-issue` (#7057FF) — bonus XP: well-formed issue
- `good-pr` (#0E8A16) — bonus XP: clean PR
- `good-ui` (#15919B) — bonus XP: UI improvement
- `good-backend` (#0B2E59) — bonus XP: backend improvement

---

## ✅ Done — previous passes (all on `main`, CI was green through commit `cb51ce9`)

**Safety (verified clean):**
- Scanned the **full git history** for secrets — no real `nvapi-` key in any commit.
- `.env` is git-ignored and has never been tracked.
- PII scan: no local paths, phone numbers, or real emails in tracked files.
  The only emails are `@example.com` sample data (RFC 2606 reserved — safe by design).

**Fixed what was broken / dishonest:**
- Model claim mismatch fixed: 8B is the documented default everywhere, 70B a one-line opt-in.
- Added `ResilientLLM` (retries NIM timeouts/429s 3× with exponential backoff) to all recipes.
- Deleted stale `docs/groq-setup.md` (project migrated to NIM; it was dead and contradictory).
- CI hardened: per-recipe requirements install, pinned Python 3.12, run-cancellation, import checks.

**Contributor experience:**
- `docs/writing-a-recipe.md`, `docs/DECISIONS.md`, `docs/providers.md`, `docs/agent-patterns.md`.
- Real Expected Output blocks in both stable recipe READMEs (captured from live NIM runs).
- Right-sized governance: removed solo-maintainer `CODEOWNERS`, slimmed `SECURITY.md`.
- Multi-provider LLM config: `LLM_BASE_URL`, `LLM_MODEL`, `LLM_API_KEY`.
- Local web playground (`/playground`): FastAPI backend + vanilla HTML/JS frontend.

---

## 🙋 Needs you (with exact commands)

### High priority

1. **Install ECSoC Sentinel GitHub App yourself** — check its permission scopes carefully
   before granting write access. Labels are already created and waiting.
   Do **not** grant write access to workflows/secrets unless you've reviewed the app's
   changelog.

2. **Merge or close the 15 dependabot PRs** — they're piling up (all from 2026-07-08).
   Safe batch strategy:
   ```bash
   # Merge the four GitHub Actions bumps (low risk):
   gh pr merge 48 --merge  # actions/labeler 5→6
   gh pr merge 47 --merge  # actions/stale 9→10
   gh pr merge 12 --merge  # actions/first-interaction 1→3 (now targets welcome.yml)
   gh pr merge 11 --merge  # actions/setup-python 5→6
   gh pr merge 10 --merge  # actions/checkout 4→7
   # For the pip bumps (litellm, openai, python-dotenv, tenacity):
   # review one per recipe then merge — they're minor version bumps.
   ```

3. **Rotate your NVIDIA API key** — a real `nvapi-*` key is present in the local
   `.env` file (git-ignored, never committed). Before any screen-sharing or laptop
   demo, regenerate it at build.nvidia.com and update your local `.env`.

### Lower priority

4. **Verify your public links** in `README.md`:
   `https://instagram.com/karan.rajkr` and `https://karanrajkr.hashnode.dev`.

5. **Pin the welcome Discussion** (GitHub UI only — 2 clicks):
   Open <https://github.com/Karan-Raj-KR/crewai-recipes/discussions/9> → `•••` → **Pin discussion**.

6. **(Optional) GitHub Project board** — my `gh` token lacks the `project` scope. Run:
   ```bash
   gh auth refresh -s project,read:project
   ```

7. **(Optional) Decide on the `hacktoberfest` topic** — invites low-effort PRs. To remove:
   ```bash
   gh repo edit Karan-Raj-KR/crewai-recipes --remove-topic hacktoberfest
   ```

8. **(Optional) Enforce CI on yourself** — enable "Include administrators" in branch
   protection settings so your own pushes also require green CI.

9. **Add a real screenshot to `playground/README.md`** — the broken placeholder was
   removed; add `./screenshot.png` once you have a real screenshot of the playground running.

---

## Notes on intentional decisions

**`faq-bot/run.py` — `args.name.strip() or "there"` guard (NOT removed)**
- `argparse` passes `--name ""` as an empty string; `.strip() or "there"` is reachable.
- Verified: `python -c "import argparse; p=argparse.ArgumentParser(); p.add_argument('--name', default='there'); print(repr(p.parse_args(['--name', '']).name))"` → `''`
- Removing it would make an empty `--name ""` silently break the task description. Kept.

---

## 🎯 Top 3 highest-impact next actions for attracting contributors

1. **Ship `recipes/_template/` folder (issue #8).** A copy-paste scaffold is the single
   biggest lever on "time to first PR." 30 minutes of work, massive contributor unlock.

2. **Add a demo GIF to the README top (issue #5).** A repo that *shows* a crew running
   in the first screen converts far better than one that only describes it.
   Record `lead-qualification` producing a scorecard; link via issue #5.

3. **Keep the good-first-issue queue full.** Contributors arrive in bursts (blog post,
   HN mention); an empty queue wastes that traffic. Good candidates: unit tests (#3, #4),
   missing-key error handling (#7), email-drafting recipe (#6).

---

## 📊 Current state (as of 2026-07-13)

- **Open issues:** 30 (at the 30-issue cap — create new issues only after closing old ones)
- **Open PRs:** 15 (all dependabot — no user-authored PRs pending)
- **Branches:** main only (no stale feature branches)
- **CI:** green on `main` (commit `95cf230`) — ruff lint, ruff format, import checks all pass
- **Labels created:** 8 ECSoC + bonus-XP labels ready for scoring bot
- **Recipes:** 2 stable (faq-bot, lead-qualification) + 2 scaffolds (appointment-booking, whatsapp-action-sim)
- **Default LLM:** `meta/llama-3.1-8b-instruct` via NVIDIA NIM (override: `LLM_MODEL` env var)
