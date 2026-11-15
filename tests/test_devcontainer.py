"""Tests to validate .devcontainer configuration."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_devcontainer_configuration_validity():
    devcontainer_file = ROOT / ".devcontainer" / "devcontainer.json"
    assert devcontainer_file.exists(), ".devcontainer/devcontainer.json must exist"

    data = json.loads(devcontainer_file.read_text(encoding="utf-8"))
    assert "name" in data, "devcontainer config must have a 'name' field"
    assert "image" in data, "devcontainer config must specify an 'image'"
    assert "python:3.12" in data["image"], "devcontainer should use Python 3.12"

    assert "customizations" in data
    vscode = data["customizations"].get("vscode", {})
    assert "extensions" in vscode
    assert "charliermarsh.ruff" in vscode["extensions"]

    assert "postCreateCommand" in data
