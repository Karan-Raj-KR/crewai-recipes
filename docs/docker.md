# Running Recipes with Docker

Don't want to touch your system Python? Docker lets you run both the **web playground** and any **CLI recipe** in a fully isolated container — no virtual environments, no pip conflicts.

> **Your API key never leaves your machine.** The `.env` file is passed into the container at **runtime** and is never baked into the image.

---

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (Mac/Windows) or Docker Engine (Linux) — version **20.10+**
- A free NVIDIA NIM API key → [build.nvidia.com](https://build.nvidia.com/)

---

## Overview: Two Modes

The root `Dockerfile` supports two modes via the `MODE` build arg:

| `MODE` | What it runs | Entry point | Port |
|--------|-------------|-------------|------|
| `playground` *(default)* | FastAPI web UI for all recipes | `uvicorn playground.main:app` | `8000` |
| `recipe` | CLI runner for one specific recipe | `python run.py` | — |

---

## Option A: Docker Compose (recommended ✅)

The easiest way — one command to build and run.

### 1. Clone the repo

```bash
git clone https://github.com/Karan-Raj-KR/crewai-recipes.git
cd crewai-recipes
```

### 2. Set your API key

```bash
cp playground/.env.example playground/.env
# Open playground/.env and set:
#   LLM_API_KEY=nvapi-your-key-here
```

### 3. Build and start the playground

```bash
# First time (or after updating requirements.txt): use --build
docker compose up --build playground

# Subsequent runs (no code changes):
docker compose up playground
```

Then open **[http://localhost:8000](http://localhost:8000)** in your browser. 🎉

> The playground automatically discovers all recipes under `recipes/` — you can switch between them in the UI.

### Stop the playground

```bash
docker compose down
```

---

## Option B: Raw `docker build` + `docker run`

Useful if you don't want Docker Compose, or you're running in CI.

### Run the playground

```bash
# 1. Build
docker build --build-arg MODE=playground -t crewai-playground .

# 2. Set your API key
cp playground/.env.example playground/.env
# Edit playground/.env: LLM_API_KEY=nvapi-your-key-here

# 3. Run — pass playground/.env at runtime
docker run --rm \
    -p 8000:8000 \
    --env-file playground/.env \
    crewai-playground
```

**Windows (PowerShell):**
```powershell
docker run --rm `
    -p 8000:8000 `
    --env-file playground/.env `
    crewai-playground
```

Open **[http://localhost:8000](http://localhost:8000)** in your browser.

---

## Running a single CLI recipe with Docker

If you prefer running a specific recipe from the command line instead of the browser UI:

### Compose approach

```bash
# 1. Set your API key for the recipe
cp recipes/lead-qualification/.env.example recipes/lead-qualification/.env
# Edit: LLM_API_KEY=nvapi-your-key-here

# 2. Build and run — Linux / macOS / Git Bash
RECIPE=lead-qualification docker compose run --rm recipe \
    --company "Acme Corp" \
    --description "A 40-person B2B SaaS startup focused on HR automation"
```

**Windows (PowerShell):** The inline `RECIPE=...` syntax doesn't work in PowerShell. Set it first:

```powershell
$env:RECIPE = "lead-qualification"
docker compose run --rm recipe `
    --company "Acme Corp" `
    --description "A 40-person B2B SaaS startup focused on HR automation"
```

### Raw Docker approach

```bash
# 1. Build (RECIPE selects which recipe's requirements.txt to install)
docker build \
    --build-arg MODE=recipe \
    --build-arg RECIPE=lead-qualification \
    -t crewai-lead .

# 2. Set your API key
cp recipes/lead-qualification/.env.example recipes/lead-qualification/.env
# Edit: LLM_API_KEY=nvapi-your-key-here

# 3. Run — pass the recipe's .env at runtime
docker run --rm \
    --env-file recipes/lead-qualification/.env \
    crewai-lead \
    --company "Acme Corp" \
    --description "A 40-person B2B SaaS startup focused on HR automation"
```

**Get CLI help for a recipe:**
```bash
docker run --rm crewai-lead --help
```

---

## Passing environment variables

Three supported patterns — choose whichever fits your workflow:

### Pattern A — `--env-file` flag (recommended for `docker run`)

```bash
# Playground
docker run --rm -p 8000:8000 --env-file playground/.env crewai-playground

# CLI recipe
docker run --rm --env-file recipes/lead-qualification/.env crewai-lead --company "..."
```

The `.env` file is loaded at container start. It is **never copied into** the image.

### Pattern B — `env_file:` in `docker-compose.yml` (default for Compose)

Already wired up in the repo's `docker-compose.yml`. No extra flags needed — just `docker compose up playground`.

### Pattern C — individual `-e` flags (useful for CI/CD pipelines)

```bash
docker run --rm \
    -e LLM_API_KEY="nvapi-your-key" \
    -e LLM_MODEL="meta/llama-3.3-70b-instruct" \
    -p 8000:8000 \
    crewai-playground
```

> **Tip for CI:** Store `LLM_API_KEY` as a GitHub Actions secret and pass it with `-e LLM_API_KEY=${{ secrets.LLM_API_KEY }}`.

---

## Switching the LLM model

The playground and all CLI recipes respect the `LLM_MODEL` environment variable. Add it to your `.env`:

```dotenv
LLM_API_KEY=nvapi-your-key-here

# Optional — defaults to meta/llama-3.1-8b-instruct
# LLM_MODEL=meta/llama-3.3-70b-instruct
```

---

## Rebuild when dependencies change

If a `requirements.txt` is updated, rebuild with `--no-cache`:

```bash
# Playground
docker compose build --no-cache playground

# Or raw Docker
docker build --no-cache --build-arg MODE=playground -t crewai-playground .
```

---

## Troubleshooting

| Problem | Likely cause | Fix |
|---|---|---|
| `❌ LLM_API_KEY is not set` | `.env` not passed at runtime | Add `--env-file playground/.env` to your `docker run`, or check `playground/.env` exists |
| Browser shows connection refused | Container not started or wrong port | Ensure `-p 8000:8000` flag is present; check `docker ps` |
| `ModuleNotFoundError` | Wrong build arg used | Rebuild: `docker build --build-arg MODE=playground ...` |
| Recipe not appearing in UI | Recipe missing `crew.py` | Check `recipes/<name>/crew.py` exists |
| `docker: command not found` | Docker not installed | Install [Docker Desktop](https://www.docker.com/products/docker-desktop/) |
| Build fails on `requirements.txt` | Recipe name typo (MODE=recipe) | Check the exact folder name under `recipes/` |

---

## Security notes

- The image is built on `python:3.12-slim` — a minimal base with a small attack surface.
- The container runs as a **non-root user** (`appuser`).
- Secrets are **never baked into the image** — they are injected at runtime via `--env-file` or `-e`.
- `playground/.env` and `recipes/*/.env` are already in `.gitignore`.

---

## See also

- [Architecture Overview](./architecture.md)
- [NVIDIA NIM Setup Guide](./nim-setup.md)
- [Multi-provider LLM config](./providers.md)
- [Writing a New Recipe](./writing-a-recipe.md)
