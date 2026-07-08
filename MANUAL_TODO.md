# Manual To-Do

Status after the autonomous audit/upgrade pass. Everything that could be
automated safely was. This file is now just: what's done, what needs *you*,
and where to point next.

---

## ✅ Done this pass (all pushed to `main`, CI green)

**Safety (verified clean):**
- Scanned the **full git history** for secrets — no real `nvapi-` key or hardcoded credential in any commit; only placeholders (`nvapi-your-key-here`, `nvapi-test`).
- `.env` is git-ignored and has never been tracked.
- PII scan: no local paths, phone numbers, or real emails in tracked files. The only emails are `@example.com` sample data (RFC 2606 reserved — safe by design).

**Fixed what was broken / dishonest:**
- **Model claim mismatch** — docs/badges/description claimed "Llama 3.3 70B" while the code ran 3.1 8B. Now 8B is the documented default everywhere, with 70B a one-line opt-in via the `NIM_MODEL` env var. Zero contradictions left.
- **Resilience** — added `ResilientLLM` (retries NIM timeouts/429s 3× with exponential backoff) to all four recipes.
- **Stale Groq guide** — deleted `docs/groq-setup.md` (project migrated to NIM; it was dead and contradictory).
- **CI hardening** — per-recipe requirements install, pinned Python 3.12, run-cancellation, and import checks now assert the resilient LLM + 8B default wiring.

**Contributor experience:**
- New `docs/writing-a-recipe.md` (step-by-step), `docs/DECISIONS.md` (why the repo is set up as it is).
- Real, clean **Expected Output** blocks in both stable recipe READMEs (captured from live NIM runs, not fabricated).
- Right-sized governance: removed the solo-maintainer `CODEOWNERS`, slimmed `SECURITY.md` to a practical API-key note.
- Commented on issue **#8** with the new guide; left it open for a contributor to add the `recipes/_template/` folder.

**Verified end-to-end:**
- Fresh `git clone` in a clean venv → `pip install` → run: succeeds through every step and fails **only** at the API-auth call with a placeholder key (403 Forbidden), exactly as intended.
- Live run of `faq-bot` against NIM 8B produced a clean answer (also confirms the retry wrapper doesn't break real calls).
- CI is **green** on `main` (commit `b1d9b8c`).

---

## 🙋 Needs you (with exact commands)

1. **Verify your public links** in `README.md` are ones you want attached:
   `https://instagram.com/karan.rajkr` and `https://karanrajkr.hashnode.dev`.

2. **Pin the welcome Discussion** (the API can't do this — 2 clicks):
   Open <https://github.com/Karan-Raj-KR/crewai-recipes/discussions/9> → `•••` menu → **Pin discussion**.

3. **(Optional) GitHub Project board** — my `gh` token lacks the `project` scope. If you want a roadmap/triage board, run then tell me:
   ```bash
   gh auth refresh -s project,read:project
   ```

4. **(Optional) Decide on the `hacktoberfest` topic** — it's currently set for visibility, but invites low-effort PRs. To remove:
   ```bash
   gh repo edit Karan-Raj-KR/crewai-recipes --remove-topic hacktoberfest
   ```

5. **(Optional) Enforce CI on yourself too** — branch protection currently lets admins (you) bypass required checks. To make even your own pushes wait for green CI, enable "Include administrators" in branch protection settings.

---

## 🎯 Top 3 highest-impact next actions for attracting contributors

1. **Ship one 30-minute win: the `recipes/_template/` folder (issue #8).** A copy-paste scaffold is the single biggest lever on "time to first PR." Pair it with a short Loom/GIF of building a recipe and link it in the README quickstart.

2. **Add a demo GIF to the top of the README (issue #5).** A repo that *shows* a crew running in the first screen converts far better than one that only describes it. Record `lead-qualification` producing a scorecard.

3. **Seed 3–5 more `good first issue`s and keep the queue full.** Contributors arrive in bursts (a blog post, an HN mention); an empty issue queue wastes that traffic. Good candidates: unit tests per recipe (#3, #4), the missing-key error-handling polish (#7), and one new small recipe (e.g. email-drafting, #6). Then post the build in your Instagram/blog to drive the first wave.

---

## Notes

- Default LLM across all recipes: `meta/llama-3.1-8b-instruct` (fast, reliable on the free tier). Override anywhere with `NIM_MODEL=meta/llama-3.3-70b-instruct` in `.env` — no code change.
- The 70B model still occasionally times out on the free tier; the retry wrapper softens this but doesn't eliminate it. If you want 70B as the default, check your NIM account's rate limits first.
