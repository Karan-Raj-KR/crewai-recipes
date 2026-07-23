# ============================================================
# crewai-recipes — Universal Dockerfile
# ============================================================
# Supports two modes controlled by the MODE build arg:
#
#   MODE=playground  (default)
#     Runs the FastAPI + uvicorn web playground on port 8000.
#     Build:  docker build --build-arg MODE=playground -t crewai-playground .
#     Run:    docker run --rm -p 8000:8000 --env-file playground/.env crewai-playground
#     Open:   http://localhost:8000
#
#   MODE=recipe
#     Runs a single CLI recipe (set RECIPE build arg).
#     Build:  docker build --build-arg MODE=recipe --build-arg RECIPE=lead-qualification -t crewai-lead .
#     Run:    docker run --rm --env-file recipes/lead-qualification/.env crewai-lead \
#                 --company "Acme Corp" --description "A 40-person B2B SaaS"
#
# See docs/docker.md for the full guide.
# ============================================================

ARG PYTHON_VERSION=3.12
FROM python:${PYTHON_VERSION}-slim AS base

# ---------- build-time arguments ----------
# MODE: "playground" (uvicorn web UI) | "recipe" (CLI run.py)
ARG MODE=playground
# RECIPE: only used when MODE=recipe (e.g. "lead-qualification")
ARG RECIPE=lead-qualification

ENV MODE=${MODE}
ENV RECIPE=${RECIPE}

# ---------- system deps ----------
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Run as a non-root user (security best practice)
RUN useradd --create-home --shell /bin/bash appuser

# ---------- working directory ----------
WORKDIR /app

# ---------- copy all sources ----------
# We copy playground/ and recipes/ together so that:
#   - playground mode can install deps from ALL recipes (it imports them dynamically)
#   - recipe mode has the specific recipe available
# entrypoint.sh is copied to / so it survives a USER switch.
COPY entrypoint.sh /entrypoint.sh
COPY playground/ ./playground/
COPY recipes/ ./recipes/

# ---------- install dependencies ----------
# playground mode: install playground deps + every recipe's requirements so
#   the playground can dynamically import any recipe's crew.py without
#   hitting missing-module errors at runtime. (Fix for dependency drift.)
#
# recipe mode: install only the selected recipe's requirements to keep the
#   image small and build fast.
RUN pip install --no-cache-dir --upgrade pip && \
    if [ "$MODE" = "playground" ]; then \
        pip install --no-cache-dir -r ./playground/requirements.txt && \
        find ./recipes -maxdepth 2 -name "requirements.txt" \
            | xargs -I{} pip install --no-cache-dir -r {}; \
    else \
        pip install --no-cache-dir -r ./recipes/${RECIPE}/requirements.txt; \
    fi

# Make the entrypoint executable after root operations
RUN chmod +x /entrypoint.sh

# ---------- switch to non-root user ----------
USER appuser

# ---------- expose port (playground only) ----------
EXPOSE 8000

# ---------- entry point ----------
# entrypoint.sh reads $MODE and $RECIPE at runtime.
#
# Playground:
#   docker run --rm -p 8000:8000 --env-file playground/.env crewai-playground
#
# Recipe (args are forwarded with correct quoting via "$@"):
#   docker run --rm --env-file recipes/lead-qualification/.env crewai-lead \
#       --company "Acme Corp" --description "A 40-person B2B SaaS"
ENTRYPOINT ["/entrypoint.sh"]
CMD []
