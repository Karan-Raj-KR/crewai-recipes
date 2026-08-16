# The gallery

The public gallery at **https://karan-raj-kr.github.io/crewai-recipes/** — the
playground UI, running with no backend, replaying real recorded runs.

## Why recordings instead of a live server

The playground executes each recipe's Python in-process and calls a real LLM.
Deploying that publicly would mean every visitor spending the maintainer's API
credits, and running whatever code landed in `recipes/` in the last merge. So
the gallery replays runs that already happened:

| | Local playground | Gallery |
|---|---|---|
| Runs your inputs | ✅ | ❌ — replays the recorded ones |
| Needs an API key | ✅ | ❌ |
| Needs a server | ✅ | ❌ — static files |
| Costs money per visitor | ✅ | ❌ |

Every trace is a genuine run against Llama 3.1 8B on NVIDIA NIM. Nothing here is
hand-written or simulated — `record_runs.py` refuses to save a run that errored.

## Files

| Path | What it is |
|---|---|
| `static-shim.js` | Patches `fetch` so `/recipes` and `/run/stream` resolve to `runs/*.json` |
| `runs/*.json` | One recorded run per recipe, plus `index.json` (the gallery's recipe list) |
| `test_static_shim.mjs` | `node site/test_static_shim.mjs` — routing, pacing, abort, 404 |
| `index.html` | **Generated** by `tools/build_site.py`; not committed |

## Refreshing the recordings

Re-record when a recipe's agents, tasks, or prompts change — otherwise the
gallery shows a trace the code no longer produces.

```bash
LLM_API_KEY=nvapi-... python tools/record_runs.py                 # all recipes
LLM_API_KEY=nvapi-... python tools/record_runs.py faq-bot          # just one
python tools/build_site.py && cd site && python -m http.server 8899
```

Commit the updated `site/runs/*.json`; pushing to `main` redeploys via
`.github/workflows/pages.yml`.
