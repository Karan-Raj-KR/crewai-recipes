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

## 🤖 Contributor Automation & Backlog Expansion (Autonomous Update)

**Judgment Calls Made:**
- **Labeler Setup:** For the labeler workflow, I mapped `docs/**` to the `docs` label, `.github/**` to `ci`, and `recipes/**` to `recipe: improvement`. This ensures any change in recipes gets attention without incorrectly labeling bug fixes as new recipes.
- **Stale Bot:** Configured to mark issues and PRs stale after 45 days, but leaves them open indefinitely (`days-before-close: -1`) to avoid losing valid community context. It exempts `level: advanced` issues and anything assigned to a user.
- **Welcome Message:** First-time contributors get a warm automated welcome via `actions/first-interaction`, nudging them to check `CONTRIBUTING.md` and `good first issue`s.

**How to Enable CodeRabbit AI (Free Open-Source Tier)**
CodeRabbit provides AI-assisted PR reviews, which saves maintainer time. It requires GitHub authorization, so you must install it manually:
1. Go to the [CodeRabbit App on GitHub Marketplace](https://github.com/marketplace/coderabbitai) or [coderabbit.ai](https://coderabbit.ai).
2. Click **Install for Free** (it's free for public OSS).
3. Select this repository (`Karan-Raj-KR/crewai-recipes`) to grant access.
4. Once installed, it will automatically review new PRs and leave inline comments.

### 📝 New Issues Added

**Beginner (Great for new contributors):**
- [Issue #28: Add `--json` output flag to run.py in lead-qualification recipe](https://github.com/Karan-Raj-KR/crewai-recipes/issues/28)
- [Issue #29: Add input validation with helpful errors to lead-qualification recipe](https://github.com/Karan-Raj-KR/crewai-recipes/issues/29)
- [Issue #30: Make faq-bot knowledge base loadable from a YAML file](https://github.com/Karan-Raj-KR/crewai-recipes/issues/30)
- [Issue #31: Add Pytest smoke tests mocking LLM call for lead-qualification](https://github.com/Karan-Raj-KR/crewai-recipes/issues/31)
- [Issue #32: Add Pytest smoke tests mocking LLM call for faq-bot](https://github.com/Karan-Raj-KR/crewai-recipes/issues/32)
- [Issue #34: Add rich colored CLI output to recipes using Rich](https://github.com/Karan-Raj-KR/crewai-recipes/issues/34)
- [Issue #39: Document how to run recipes using Docker](https://github.com/Karan-Raj-KR/crewai-recipes/issues/39)

**Intermediate (Requires some familiarity with CrewAI/Python):**
- [Issue #25: Build out Customer Onboarding workflow recipe](https://github.com/Karan-Raj-KR/crewai-recipes/issues/25)
- [Issue #33: Add a top-level Makefile or Justfile for common developer commands](https://github.com/Karan-Raj-KR/crewai-recipes/issues/33)
- [Issue #35: Add a `--verbose` flag to toggle CrewAI trace output](https://github.com/Karan-Raj-KR/crewai-recipes/issues/35)
- [Issue #36: Add a CI job to run mocked pytest smoke tests](https://github.com/Karan-Raj-KR/crewai-recipes/issues/36)
- [Issue #37: Matrix-test Python 3.10, 3.11, and 3.12 in CI](https://github.com/Karan-Raj-KR/crewai-recipes/issues/37)

**Advanced (Complex integrations or multi-agent architectures):**
- [Issue #26: Build out Content Production Pipeline recipe](https://github.com/Karan-Raj-KR/crewai-recipes/issues/26)
- [Issue #27: Build out Support Ticket Escalation recipe](https://github.com/Karan-Raj-KR/crewai-recipes/issues/27)
- [Issue #38: Add optional support for a second OpenAI-compatible provider via env config](https://github.com/Karan-Raj-KR/crewai-recipes/issues/38)
