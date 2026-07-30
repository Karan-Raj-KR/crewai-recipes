"""
FAQ Bot Recipe — knowledge_base.py

Loads FAQ entries from knowledge_base.yaml (or custom path via FAQ_KNOWLEDGE_BASE_PATH).
Each entry has a topic, question, and answer.
"""

import os
from pathlib import Path

import yaml

DEFAULT_YAML_PATH = Path(__file__).parent / "knowledge_base.yaml"


def load_knowledge_base(path: str | Path | None = None) -> list[dict[str, str]]:
    """Load and validate FAQ knowledge base entries from a YAML file.

    Args:
        path: Path to the YAML file. Defaults to FAQ_KNOWLEDGE_BASE_PATH env var
            or knowledge_base.yaml beside this module.

    Returns:
        List of FAQ dict entries with topic, question, and answer strings.

    Raises:
        FileNotFoundError: If the YAML file does not exist.
        ValueError: If YAML is malformed or entries miss topic/question/answer.
    """
    if path is None:
        path = os.getenv("FAQ_KNOWLEDGE_BASE_PATH", DEFAULT_YAML_PATH)

    yaml_path = Path(path)
    if not yaml_path.exists():
        raise FileNotFoundError(f"FAQ Knowledge Base YAML file not found: {yaml_path}")

    try:
        with open(yaml_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except Exception as err:
        raise ValueError(
            f"Failed to parse FAQ Knowledge Base YAML from {yaml_path}: {err}"
        ) from err

    if not isinstance(data, list):
        raise ValueError(
            f"FAQ Knowledge Base in {yaml_path} must be a YAML list of entries."
        )

    validated: list[dict[str, str]] = []
    for idx, entry in enumerate(data, 1):
        if not isinstance(entry, dict):
            raise ValueError(f"Entry {idx} in {yaml_path} is not a valid dict.")
        for required_key in ("topic", "question", "answer"):
            if required_key not in entry or not entry[required_key]:
                raise ValueError(
                    f"Entry {idx} in {yaml_path} is missing required field '{required_key}'."
                )
        validated.append(
            {
                "topic": str(entry["topic"]).strip(),
                "question": str(entry["question"]).strip(),
                "answer": str(entry["answer"]).strip(),
            }
        )

    return validated


# Global knowledge base list loaded at import time for backward compatibility
FAQ_KNOWLEDGE_BASE: list[dict[str, str]] = load_knowledge_base()


def get_knowledge_base_text() -> str:
    """Format the FAQ knowledge base as a plain-text block for agent context.

    Returns:
        A formatted string with all FAQ entries numbered and labelled.
    """
    lines: list[str] = ["=== ORBITLY FAQ KNOWLEDGE BASE ===\n"]
    for i, entry in enumerate(FAQ_KNOWLEDGE_BASE, 1):
        lines.append(f"[{i}] Topic: {entry['topic'].upper()}")
        lines.append(f"    Q: {entry['question']}")
        lines.append(f"    A: {entry['answer']}")
        lines.append("")
    lines.append("=== END OF KNOWLEDGE BASE ===")
    return "\n".join(lines)
