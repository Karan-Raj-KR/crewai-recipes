# Changelog

All notable changes to this project are documented here. Format loosely follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added
- Community infrastructure: `SECURITY.md`, PR template, issue template contact links, `CHANGELOG.md`.
- GitHub Discussions enabled for Q&A and recipe ideas.
- `LLM_MODEL` environment variable to switch models without editing code (defaults to `meta/llama-3.1-8b-instruct`).
- Retry with exponential backoff around NVIDIA NIM calls, so a single free-tier timeout/429 no longer fails a whole crew run.
- `docs/DECISIONS.md` (why the repo is set up the way it is) and `docs/writing-a-recipe.md` (contributor walkthrough).

### Changed
- Documented the honest default model everywhere: `meta/llama-3.1-8b-instruct` (fast, reliable on the free tier) with `meta/llama-3.3-70b-instruct` as an opt-in. Previous copy claimed 70B while the code ran 8B.
- Right-sized governance for a solo maintainer: removed `CODEOWNERS`, slimmed `SECURITY.md` to a practical API-key-hygiene note.

### Fixed
- CI (`ruff format --check`) was failing on every commit since the initial push; formatting has been corrected.

### Removed
- Stale `docs/groq-setup.md` — the project migrated to NVIDIA NIM; the Groq guide was dead and contradictory.

## [0.1.0] - 2026-07-08

### Added
- Initial release: `lead-qualification` and `faq-bot` recipes (stable, NVIDIA NIM + CrewAI).
- Scaffolds for `appointment-booking` and `whatsapp-action-sim` (open for contribution).
- `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, issue templates, CI workflow (Ruff lint + import checks).
- Docs: architecture overview, agent design patterns, NVIDIA NIM setup guide.
