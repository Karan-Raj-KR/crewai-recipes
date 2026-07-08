# Security

This is a small, solo-maintained collection of example recipes — no formal
advisory process, but a few things genuinely matter here because every recipe
uses an API key.

## API keys

- Recipes read `NVIDIA_API_KEY` from a git-ignored `.env` file. **Never commit a real key.**
- If you accidentally commit one, rotate it immediately at [build.nvidia.com](https://build.nvidia.com/) — assume anything pushed to GitHub is compromised — and let the maintainer know so history can be scrubbed.
- `.env.example` files must only ever contain placeholders (e.g. `nvapi-your-key-here`).

## Reporting something sensitive

If you find a vulnerability (a way a recipe leaks a key, runs untrusted input
unsafely, or a genuinely exploitable dependency), please **don't open a public
issue**. Use a private [GitHub Security Advisory](https://github.com/Karan-Raj-KR/crewai-recipes/security/advisories/new)
instead. Non-sensitive dependency bumps can go through normal issues/PRs.
