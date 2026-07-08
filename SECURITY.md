# Security Policy

## Supported Versions

`crewai-recipes` is a collection of standalone recipes rather than a versioned library. There is no LTS branch — security fixes are applied to `main` only, and everyone should track `main`.

## Reporting a Vulnerability

If you find a security issue (e.g. a way a recipe could leak an API key, execute untrusted input unsafely, or a vulnerable dependency), please **do not open a public issue**.

Instead, report it privately via [GitHub Security Advisories](https://github.com/Karan-Raj-KR/crewai-recipes/security/advisories/new) for this repository. You can expect an initial response within **5 days**.

Please include:
- A description of the issue and its potential impact
- Steps to reproduce (a minimal recipe or code snippet is ideal)
- Any suggested fix, if you have one

We'll credit reporters in the fix's release notes unless you'd prefer to stay anonymous.

## Scope Notes

- **API keys**: Recipes read secrets from environment variables via `.env` files, which are git-ignored. Never commit a real `NVIDIA_API_KEY` — if you accidentally do, rotate it immediately at [build.nvidia.com](https://build.nvidia.com/) and let us know so we can scrub history if needed.
- **Untrusted input**: Several recipes (e.g. `whatsapp-action-sim`) parse free-text input and route it to actions. If you find a prompt-injection path that causes an agent to take an unintended action, that's a valid report.
- **Dependencies**: Each recipe pins its own `requirements.txt`. Dependabot-style reports for outdated/vulnerable packages are welcome as regular issues (not sensitive) unless actively exploitable.
