# 📊 Multi-Agent Recipe Evaluation & Benchmark Harness

The `evals/` benchmark engine provides standardized, deterministic validation and quality profiling for multi-agent recipes across different LLM backends and prompt configurations.

---

## Capabilities

1. **Schema Compliance (`SchemaEvaluator`):** Validates that recipes emit valid JSON or structured Markdown conforming to required keys, sections, and types.
2. **Keyword & Ground-Truth Verification (`KeywordEvaluator`):** Asserts the presence of mandatory technical terminology and absence of hallucinations or forbidden placeholder strings (`TODO`, `undefined`).
3. **Rubric-Based Scoring (`RubricEvaluator`):** Multi-dimensional weighted scoring assessing completeness, actionability, and detail depth.
4. **Hermetic Offline Testing:** Standard evaluations run instantaneously using reference output benchmarks without incurring API costs or requiring network access in CI.

---

## Running Benchmarks

### 1. Run All Benchmarks (Offline)

```bash
python -m evals.runner --all
```

### 2. Run for a Specific Recipe

```bash
python -m evals.runner --recipe lead-qualification
```

### 3. Filter by Specific Evaluation Metric

```bash
python -m evals.runner --all --metric schema
```

### 4. Output as JSON

```bash
python -m evals.runner --all --format json
```

---

## Adding Evaluation Datasets

To benchmark a new recipe, add a JSON dataset under `evals/datasets/<recipe-name>.json`:

```json
[
  {
    "id": "sample-case-1",
    "description": "Clear description of test scenario",
    "inputs": {
      "input_arg": "example value"
    },
    "sample_output": "{\"status\": \"OK\"}",
    "expected": {
      "format": "json",
      "required_keys": ["status"],
      "must_include": ["OK"],
      "must_not_include": ["FAIL"]
    }
  }
]
```

---

## Running Automated Tests

```bash
pytest tests/test_evals.py -v
```
