#!/bin/sh
# =============================================================
# crewai-recipes — container entrypoint
# =============================================================
# MODE=playground  → start uvicorn web UI on 0.0.0.0:8000
# MODE=recipe      → run the selected recipe via run.py,
#                    forwarding all docker-run args with proper
#                    quoting (e.g. --company "Acme Corp" works).
# =============================================================
set -e

if [ "$MODE" = "playground" ]; then
    exec uvicorn playground.main:app --host 0.0.0.0 --port 8000
else
    # cd into the recipe directory so relative imports work,
    # then exec python with "$@" to preserve argument quoting.
    cd "/app/recipes/${RECIPE}"
    exec python run.py "$@"
fi
