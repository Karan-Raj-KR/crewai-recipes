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
#                 --company "Acme" --description "A 40-person B2B SaaS"
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

# ---------- install dependencies ----------
# Copy only the relevant requirements.txt first to maximise layer caching.
# The layer is only rebuilt when requirements.txt changes.
RUN if [ "$MODE" = "playground" ]; then \
        echo "MODE=playground: will install playground/requirements.txt"; \
    else \
        echo "MODE=recipe (${RECIPE}): will install recipes/${RECIPE}/requirements.txt"; \
    fi

COPY playground/requirements.txt ./playground-requirements.txt
COPY recipes/${RECIPE}/requirements.txt ./recipe-requirements.txt

RUN pip install --no-cache-dir --upgrade pip && \
    if [ "$MODE" = "playground" ]; then \
        pip install --no-cache-dir -r ./playground-requirements.txt; \
    else \
        pip install --no-cache-dir -r ./recipe-requirements.txt; \
    fi

# ---------- copy source ----------
# Playground needs both playground/ and recipes/ (it dynamically loads crews).
# A single CLI recipe only needs its own folder.
COPY playground/ ./playground/
COPY recipes/ ./recipes/

# ---------- switch to non-root user ----------
USER appuser

# ---------- expose port (playground only) ----------
EXPOSE 8000

# ---------- entry point ----------
# Playground: uvicorn serves main.py on 0.0.0.0:8000
# Recipe:     ENTRYPOINT=python run.py; override CMD at `docker run` time with recipe args.
#
# Playground example:
#   docker run --rm -p 8000:8000 --env-file playground/.env crewai-playground
#
# Recipe example:
#   docker run --rm --env-file recipes/lead-qualification/.env crewai-lead \
#       --company "Acme" --description "40-person B2B SaaS"

CMD if [ "$MODE" = "playground" ]; then \
        uvicorn playground.main:app --host 0.0.0.0 --port 8000; \
    else \
        exec sh -c "cd /app/recipes/${RECIPE} && python run.py $*" -- "$@"; \
    fi
