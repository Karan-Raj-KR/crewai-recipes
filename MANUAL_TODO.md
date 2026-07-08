# Manual To-Do

This file tracks items that genuinely need your judgment or a one-time manual step — everything that could be automated has been.

## Actions Required (only you can do these)

- [ ] **Verify Social Links**: Confirm the Instagram (`https://instagram.com/karan.rajkr`) and Hashnode (`https://karanrajkr.hashnode.dev`) links in `README.md` are correct and are ones you want publicly attached to this project.
- [ ] **Review NVIDIA NIM Network Issue**: The `llama-3.3-70b-instruct` model occasionally times out on direct API calls; `llama-3.1-8b-instruct` is reliable. This may be a free-tier rate limit — worth a quick check on your NVIDIA account if you want 70B as the default.
- [ ] **Pin the welcome Discussion**: I posted and would have pinned an intro thread at [discussions/9](https://github.com/Karan-Raj-KR/crewai-recipes/discussions/9), but pinning isn't exposed via the GitHub API — 2 clicks in the UI (`Pin discussion` from the `...` menu).
- [ ] **GitHub Project board**: I couldn't create one — the `gh` CLI token is missing the `project` scope. Run `gh auth refresh -s project,read:project` (this is a token permission change, so it's left to you) and I can build the roadmap board, or you can create one manually and I'll populate it from the issue tracker.
- [ ] **Decide on `hacktoberfest` topic**: I added it to the repo topics for extra visibility during October, but it also invites low-effort PRs from people farming the event. Remove it from repo topics (Settings → General) if you'd rather not deal with that.
- [ ] **Prioritize/triage the 8 open issues**: All are labeled `good first issue` and intentionally left unimplemented for contributors — I did not solve them myself, since that would defeat the point of an inviting first-issue queue.

## What was automated this session

- **CI was red on every commit** since day one (`ruff format --check` failing on 3 files) — fixed and pushed; badge is now green.
- Added `SECURITY.md`, PR template, issue-template contact links (Discussions + private security reporting), `CODEOWNERS`, `CHANGELOG.md`, `dependabot.yml` (weekly pip + Actions updates).
- Fixed a stale label table in `CONTRIBUTING.md` that no longer matched the repo's actual labels, and a wrong-case issue link.
- Added a first-interaction welcome-bot workflow that greets first-time issue/PR authors.
- Enabled GitHub Discussions (default categories: Announcements, General, Ideas, Polls, Q&A, Show and tell) and posted a pinned-intent welcome thread.
- Set repository topics (`crewai`, `ai-agents`, `multi-agent-systems`, `llm`, `nvidia-nim`, `python`, `automation`, `open-source`, `good-first-issue`, `agentic-ai`, `hacktoberfest`) for discoverability.
- Turned on Dependabot security updates + vulnerability alerts, auto-delete of merged branches, and "always suggest updating pull request branches."
- Added lightweight branch protection on `main`: CI must pass before merge, but admin (you) can still push directly — nothing is blocked for you, only for random write-access pushes bypassing CI.
- Polished README: CI badge, good-first-issue count badge, Discussions badge, a Community section, and a contributors gallery.

## Notes

- All Groq references have been successfully migrated to NVIDIA NIM across the codebase, documentation, and issue templates.
- The default LLM across all active recipes and scaffolds is `meta/llama-3.1-8b-instruct` for reliability and speed, but can easily be swapped to `meta/llama-3.3-70b-instruct` as per the inline comments in the `llm.py` configurations.
