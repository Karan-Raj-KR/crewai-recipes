"""Versioned input contracts schema, adapter, and validator for CrewAI recipes."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class FieldContract:
    """Schema specification for a single recipe input field."""

    name: str
    type: str = "string"  # "string", "integer", "float", "boolean", "list"
    required: bool = True
    default: Any = None
    min_length: int | None = None
    max_length: int | None = None
    enum: list[str] | None = None
    description: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> FieldContract:
        return cls(
            name=data["name"],
            type=str(data.get("type", "string")).lower(),
            required=bool(data.get("required", True)),
            default=data.get("default", None),
            min_length=data.get("min_length"),
            max_length=data.get("max_length"),
            enum=data.get("enum"),
            description=str(data.get("description", "")),
        )

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "name": self.name,
            "type": self.type,
            "required": self.required,
            "description": self.description,
        }
        if self.default is not None:
            result["default"] = self.default
        if self.min_length is not None:
            result["min_length"] = self.min_length
        if self.max_length is not None:
            result["max_length"] = self.max_length
        if self.enum is not None:
            result["enum"] = self.enum
        return result


@dataclass
class InputContract:
    """Versioned contract for all inputs accepted by a recipe."""

    version: str = "1.0"
    recipe: str = ""
    fields: list[FieldContract] = field(default_factory=list)
    allow_unknown: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> InputContract:
        fields = [
            FieldContract.from_dict(f)
            for f in data.get("fields", [])
            if isinstance(f, dict)
        ]
        return cls(
            version=str(data.get("version", "1.0")),
            recipe=str(data.get("recipe", "")),
            fields=fields,
            allow_unknown=bool(data.get("allow_unknown", False)),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "recipe": self.recipe,
            "allow_unknown": self.allow_unknown,
            "fields": [f.to_dict() for f in self.fields],
        }


def load_contract_for_recipe(recipe_dir: Path) -> InputContract | None:
    """Load recipe input contract from contract.json, or adapt legacy inputs.json."""
    contract_file = recipe_dir / "contract.json"
    if contract_file.exists():
        try:
            data = json.loads(contract_file.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                contract = InputContract.from_dict(data)
                if not contract.recipe:
                    contract.recipe = recipe_dir.name
                return contract
        except (json.JSONDecodeError, OSError, KeyError):
            pass

    inputs_file = recipe_dir / "inputs.json"
    if inputs_file.exists():
        try:
            data = json.loads(inputs_file.read_text(encoding="utf-8"))
            if isinstance(data, list):
                fields: list[FieldContract] = []
                for item in data:
                    if not isinstance(item, dict) or "name" not in item:
                        continue
                    name = str(item["name"])
                    label = str(item.get("label", ""))
                    is_optional = (
                        item.get("optional") is True
                        or item.get("required") is False
                        or "(optional)" in label.lower()
                    )
                    default = item.get("default", "" if is_optional else None)
                    fields.append(
                        FieldContract(
                            name=name,
                            type="string",
                            required=not is_optional,
                            default=default,
                            description=label,
                        )
                    )
                return InputContract(
                    version="1.0-compat",
                    recipe=recipe_dir.name,
                    fields=fields,
                    allow_unknown=True,  # Legacy adapter allows unmodeled extra inputs
                )
        except (json.JSONDecodeError, OSError):
            pass

    return None


def validate_recipe_inputs(
    contract: InputContract, raw_inputs: dict[str, Any]
) -> tuple[dict[str, Any], list[str]]:
    """Validate and normalize raw input dictionary against the recipe's input contract.

    Returns:
        tuple of (clean_inputs, errors)
    """
    clean_inputs: dict[str, Any] = {}
    errors: list[str] = []

    known_field_names: set[str] = {f.name for f in contract.fields}

    # 1. Validate defined contract fields
    for f in contract.fields:
        if f.name not in raw_inputs or raw_inputs[f.name] is None:
            if f.required:
                errors.append(f"Missing required field: '{f.name}'")
            else:
                clean_inputs[f.name] = f.default if f.default is not None else ""
            continue

        raw_val = raw_inputs[f.name]

        # String validation
        if f.type in ("string", "str", "text"):
            val_str = str(raw_val)
            if f.required and not val_str.strip():
                errors.append(f"Field '{f.name}' cannot be empty")
            elif f.min_length is not None and len(val_str) < f.min_length:
                errors.append(
                    f"Field '{f.name}' length ({len(val_str)}) is shorter than minimum {f.min_length}"
                )
            elif f.max_length is not None and len(val_str) > f.max_length:
                errors.append(
                    f"Field '{f.name}' length ({len(val_str)}) exceeds maximum {f.max_length}"
                )
            elif f.enum is not None and val_str not in f.enum:
                errors.append(
                    f"Field '{f.name}' value '{val_str}' must be one of: {', '.join(f.enum)}"
                )
            else:
                clean_inputs[f.name] = val_str

        # Integer validation
        elif f.type in ("integer", "int"):
            try:
                clean_inputs[f.name] = int(raw_val)
            except (ValueError, TypeError):
                errors.append(f"Field '{f.name}' must be an integer, got '{raw_val}'")

        # Float validation
        elif f.type in ("float", "number"):
            try:
                clean_inputs[f.name] = float(raw_val)
            except (ValueError, TypeError):
                errors.append(f"Field '{f.name}' must be a number, got '{raw_val}'")

        # Boolean validation
        elif f.type in ("boolean", "bool"):
            if isinstance(raw_val, bool):
                clean_inputs[f.name] = raw_val
            elif isinstance(raw_val, str) and raw_val.lower() in (
                "true",
                "1",
                "yes",
                "on",
            ):
                clean_inputs[f.name] = True
            elif isinstance(raw_val, str) and raw_val.lower() in (
                "false",
                "0",
                "no",
                "off",
                "",
            ):
                clean_inputs[f.name] = False
            else:
                errors.append(f"Field '{f.name}' must be a boolean, got '{raw_val}'")

        # List validation
        elif f.type in ("list", "array"):
            if isinstance(raw_val, list):
                clean_inputs[f.name] = raw_val
            else:
                errors.append(
                    f"Field '{f.name}' must be a list, got '{type(raw_val).__name__}'"
                )

        else:
            # Fallback for untyped fields
            clean_inputs[f.name] = raw_val

    # 2. Check for unknown fields policy
    for k, v in raw_inputs.items():
        if k not in known_field_names:
            if not contract.allow_unknown:
                errors.append(
                    f"Unknown input field '{k}' not permitted by recipe contract"
                )
            else:
                clean_inputs[k] = v

    return clean_inputs, errors
