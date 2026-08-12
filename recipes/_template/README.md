# 🚀 Template Recipe

> ⚠️ **This is a template.** Copy this entire directory to create your own recipe, then customize the files marked with `TODO` comments.

A minimal CrewAI recipe template. Use this as a starting point for your own multi-agent workflow.

---

## What It Does

```
Input
  │
  ▼
┌──────────────────────┐
│  Your Agent          │  → TODO: Describe what your agent(s) do
└──────┬───────────────┘
       │
       ▼
    Output
```

---

## Quick Start

```bash
cd recipes/_template
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add your LLM_API_KEY
```

---

## Run

### CLI mode
```bash
python run.py --your-param "value"
```

### In the Playground
Copy this directory to `recipes/my-new-recipe` and the playground will pick it up automatically.

```bash
cp -r recipes/_template recipes/my-new-recipe
cd recipes/my-new-recipe
# Edit agents.py, tasks.py, crew.py, inputs.json, and run.py
# Update README.md with your recipe details
```

---

## Architecture

### Files to customize (all marked with TODO comments)

| File | What to change |
|------|---|
| `agents.py` | Define your agent(s): role, goal, backstory |
| `tasks.py` | Define your task(s): description, expected output, agent |
| `crew.py` | Update build_crew() signature to match inputs.json keys |
| `run.py` | Add CLI arguments that match inputs.json and crew signature |
| `inputs.json` | Define playground input fields (names MUST match crew signature) |
| `README.md` | Document your recipe |

### Files to leave unchanged

| File | Why |
|------|-----|
| `llm.py` | ⚠️ **Do not edit.** Carries the `openai/` model prefix and `max_retries` wiring that CrewAI depends on. Copy it verbatim. |
| `.env.example` | Update only if you need new environment variables |
| `requirements.txt` | Update only if you need new dependencies |

---

## Key Links

- **How to write a recipe:** [docs/writing-a-recipe.md](../../docs/writing-a-recipe.md)
- **Recipe patterns & best practices:** [docs/agent-patterns.md](../../docs/agent-patterns.md)
- **Architecture deep-dive:** [docs/architecture.md](../../docs/architecture.md)
- **Contributing guide:** [CONTRIBUTING.md](../../CONTRIBUTING.md)

---

## Expected Output

TODO: Run your recipe and paste the final output here. (Not the verbose agent trace — just the result.)

```
[Your recipe output goes here]
```

---

## Tips

1. **The `build_crew()` signature matters.** The playground calls it as `build_crew(**req.inputs)`. Parameter names MUST match the "name" fields in `inputs.json`. See `crew.py` for a comment tying the two together.

2. **`llm.py` must be copied verbatim.** It sets up NVIDIA NIM + LLaMA and max_retries. Don't edit it — copy it as-is.

3. **Keep `run.py` thin.** Logic belongs in `agents.py`, `tasks.py`, and `crew.py`.

4. **Always test from a fresh venv.** This proves your `requirements.txt` is complete.

5. **Use type hints and docstrings.** See [CONTRIBUTING.md](../../CONTRIBUTING.md#coding-style) for the style guide.

---

## Troubleshooting

- **Module import error:** Did you `load_dotenv()` before importing crew in `run.py`? See the pattern in the template's `run.py`.
- **`TypeError: build_crew()` got unexpected keyword arguments:** The parameter names in `build_crew()` don't match the "name" fields in `inputs.json`. Fix the mismatch.
- **`EnvironmentError: LLM_API_KEY is not set`:** Add your NVIDIA API key to `.env` (copy from `.env.example`).

---

## Contributing

Please read [CONTRIBUTING.md](../../CONTRIBUTING.md) before opening a PR. All recipes must:

- ✅ Run end-to-end from a fresh venv
- ✅ Pass `ruff check` and `ruff format`
- ✅ Have a complete `README.md` with expected output
- ✅ Keep `llm.py` unchanged (copy verbatim)
- ✅ Align `build_crew()` signature with `inputs.json` keys
