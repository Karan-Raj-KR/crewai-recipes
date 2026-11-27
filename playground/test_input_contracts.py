from __future__ import annotations

from pathlib import Path

from contracts import (
    FieldContract,
    InputContract,
    load_contract_for_recipe,
    validate_recipe_inputs,
)
from fastapi.testclient import TestClient
from main import app, execute_recipe_stream, response_cache

client = TestClient(app)
RECIPES_DIR = Path(__file__).parent.parent / "recipes"


def test_field_contract_serialization() -> None:
    fc = FieldContract(
        name="topic",
        type="string",
        required=True,
        min_length=2,
        max_length=50,
        enum=["tech", "finance"],
        description="Select topic",
    )
    d = fc.to_dict()
    assert d["name"] == "topic"
    assert d["type"] == "string"
    assert d["required"] is True
    assert d["min_length"] == 2
    assert d["max_length"] == 50
    assert d["enum"] == ["tech", "finance"]

    restored = FieldContract.from_dict(d)
    assert restored.name == fc.name
    assert restored.min_length == fc.min_length
    assert restored.enum == fc.enum


def test_input_contract_serialization() -> None:
    ic = InputContract(
        version="1.0",
        recipe="sample-recipe",
        fields=[
            FieldContract(name="query", type="string", required=True),
            FieldContract(name="limit", type="integer", required=False, default=10),
        ],
        allow_unknown=False,
    )
    d = ic.to_dict()
    assert d["version"] == "1.0"
    assert d["recipe"] == "sample-recipe"
    assert len(d["fields"]) == 2
    assert d["allow_unknown"] is False

    restored = InputContract.from_dict(d)
    assert restored.recipe == "sample-recipe"
    assert len(restored.fields) == 2
    assert restored.fields[1].default == 10


def test_load_contract_for_recipe_with_contract_json() -> None:
    contract = load_contract_for_recipe(RECIPES_DIR / "faq-bot")
    assert contract is not None
    assert contract.recipe == "faq-bot"
    assert contract.allow_unknown is False
    assert any(f.name == "question" and f.required for f in contract.fields)
    assert any(f.name == "customer_name" and not f.required for f in contract.fields)


def test_load_contract_for_recipe_legacy_adaptation() -> None:
    # customer-feedback-summariser uses legacy inputs.json
    contract = load_contract_for_recipe(RECIPES_DIR / "customer-feedback-summariser")
    assert contract is not None
    assert contract.version == "1.0-compat"
    assert contract.allow_unknown is True
    assert len(contract.fields) > 0


def test_validate_recipe_inputs_required_and_defaults() -> None:
    contract = InputContract(
        version="1.0",
        fields=[
            FieldContract(name="title", type="string", required=True),
            FieldContract(
                name="author", type="string", required=False, default="Anonymous"
            ),
        ],
        allow_unknown=False,
    )

    # Missing required
    clean, errors = validate_recipe_inputs(contract, {})
    assert len(errors) == 1
    assert "Missing required field: 'title'" in errors[0]

    # Empty required string
    clean, errors = validate_recipe_inputs(contract, {"title": "   "})
    assert any("cannot be empty" in e for e in errors)

    # Valid with default filled in
    clean, errors = validate_recipe_inputs(contract, {"title": "My Post"})
    assert not errors
    assert clean["title"] == "My Post"
    assert clean["author"] == "Anonymous"


def test_validate_recipe_inputs_types_and_bounds() -> None:
    contract = InputContract(
        version="1.0",
        fields=[
            FieldContract(name="code", type="string", min_length=3, max_length=5),
            FieldContract(name="count", type="integer", required=True),
            FieldContract(name="ratio", type="float", required=True),
            FieldContract(name="enabled", type="boolean", required=True),
            FieldContract(name="category", type="string", enum=["A", "B"]),
        ],
        allow_unknown=True,
    )

    # Invalid bounds and types
    raw = {
        "code": "AB",  # too short (<3)
        "count": "not-an-int",
        "ratio": "not-a-float",
        "enabled": "maybe",
        "category": "C",  # not in enum
    }
    _, errors = validate_recipe_inputs(contract, raw)
    assert len(errors) == 5
    assert any("shorter than minimum" in e for e in errors)
    assert any("must be an integer" in e for e in errors)
    assert any("must be a number" in e for e in errors)
    assert any("must be a boolean" in e for e in errors)
    assert any("must be one of" in e for e in errors)

    # Valid conversion
    valid_raw = {
        "code": "ABC",
        "count": "42",
        "ratio": "3.14",
        "enabled": "yes",
        "category": "A",
    }
    clean, errors = validate_recipe_inputs(contract, valid_raw)
    assert not errors
    assert clean["count"] == 42
    assert clean["ratio"] == 3.14
    assert clean["enabled"] is True


def test_unknown_fields_rejection() -> None:
    contract = InputContract(
        version="1.0",
        fields=[FieldContract(name="query", type="string", required=True)],
        allow_unknown=False,
    )

    _, errors = validate_recipe_inputs(
        contract, {"query": "test", "extra_bad_field": 123}
    )
    assert len(errors) == 1
    assert "Unknown input field 'extra_bad_field'" in errors[0]


def test_run_endpoint_validation_failure_returns_422() -> None:
    # faq-bot has contract.json with allow_unknown=False and question min_length=1
    payload = {
        "recipe": "faq-bot",
        "inputs": {"question": "", "customer_name": "Test"},  # empty required question
    }
    response = client.post("/run", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
    assert any("cannot be empty" in err for err in data["detail"]["errors"])


def test_run_endpoint_rejects_unknown_fields_with_422() -> None:
    payload = {
        "recipe": "faq-bot",
        "inputs": {"question": "Valid Question?", "unsupported_field_xyz": "value"},
    }
    response = client.post("/run", json=payload)
    assert response.status_code == 422
    assert any(
        "unsupported_field_xyz" in err for err in response.json()["detail"]["errors"]
    )


def test_validation_prevents_cache_pollution() -> None:
    response_cache.clear()
    invalid_inputs = {"question": "", "customer_name": "Test"}
    payload = {
        "recipe": "faq-bot",
        "inputs": invalid_inputs,
    }
    response = client.post("/run", json=payload)
    assert response.status_code == 422
    # Verify response cache was never populated
    assert response_cache.get("faq-bot", invalid_inputs) is None


def test_stream_endpoint_validation_failure_returns_422() -> None:
    payload = {
        "recipe": "faq-bot",
        "inputs": {"question": ""},
    }
    response = client.post("/run/stream", json=payload)
    assert response.status_code == 422
    assert "Input validation failed" in response.json()["detail"]["message"]


def test_execute_recipe_stream_pushes_error_event_on_invalid_inputs() -> None:
    events = []

    def mock_push(event):
        events.append(event)

    import threading

    stop = threading.Event()
    execute_recipe_stream(
        "faq-bot",
        {"question": ""},  # empty required field
        push_event=mock_push,
        stop_event=stop,
    )

    assert len(events) == 1
    assert events[0]["type"] == "error"
    assert "Input validation failed" in events[0]["error"]
    assert "details" in events[0]
