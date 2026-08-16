"""Every recipe must satisfy the recipe contract.

The contract is what makes a recipe interchangeable: the playground, the CLI,
and the gallery recorder all drive a recipe purely through `build_crew(**inputs)`
and `inputs.json`. If those disagree, the playground 500s at runtime with no
warning — so they are checked here instead.

Pure stdlib on purpose: no crewai, no API key, no install. A contributor adding
a recipe gets this feedback in seconds, and any recipe added later is covered
automatically without touching CI.

    pytest tests/test_recipe_contract.py -v
"""

from __future__ import annotations

import ast
import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
RECIPES = ROOT / "recipes"

REQUIRED_FILES = [
    "agents.py",
    "crew.py",
    "tasks.py",
    "llm.py",
    "run.py",
    "inputs.json",
    "requirements.txt",
    ".env.example",
    "README.md",
]


def recipe_dirs() -> list[Path]:
    """Directories that present themselves as recipes (leading _ = template/scaffold)."""
    return sorted(
        d
        for d in RECIPES.iterdir()
        if d.is_dir() and not d.name.startswith("_") and (d / "crew.py").exists()
    )


RECIPE_IDS = [d.name for d in recipe_dirs()]
recipes = pytest.mark.parametrize("recipe", recipe_dirs(), ids=RECIPE_IDS)


def build_crew_signature(recipe: Path) -> tuple[list[str], set[str]]:
    """Return (all params, required params) of build_crew without importing crewai."""
    tree = ast.parse((recipe / "crew.py").read_text(encoding="utf-8"))
    fn = next(
        (
            n
            for n in tree.body
            if isinstance(n, ast.FunctionDef) and n.name == "build_crew"
        ),
        None,
    )
    assert fn is not None, f"{recipe.name}/crew.py must define build_crew()"
    params = [a.arg for a in fn.args.args]
    required = set(params[: len(params) - len(fn.args.defaults)])
    return params, required


def test_at_least_one_recipe():
    assert RECIPE_IDS, "no recipes discovered — the contract suite would silently pass"


@recipes
def test_required_files_present(recipe: Path):
    missing = [f for f in REQUIRED_FILES if not (recipe / f).exists()]
    assert not missing, f"{recipe.name} is missing {missing}"


@recipes
def test_inputs_json_is_well_formed(recipe: Path):
    fields = json.loads((recipe / "inputs.json").read_text(encoding="utf-8"))
    assert isinstance(fields, list) and fields, (
        f"{recipe.name}/inputs.json must be a non-empty list"
    )

    for field in fields:
        for key in ("name", "label", "example"):
            assert field.get(key), (
                f"{recipe.name}/inputs.json: field {field!r} needs a non-empty {key!r}"
            )
        assert isinstance(field["example"], str), (
            f"{recipe.name}/inputs.json: {field['name']}.example must be a string — "
            "it is submitted straight through the run form"
        )

    names = [f["name"] for f in fields]
    assert len(names) == len(set(names)), (
        f"{recipe.name}/inputs.json has duplicate field names"
    )


@recipes
def test_inputs_json_matches_build_crew(recipe: Path):
    """The playground calls build_crew(**inputs) built from inputs.json."""
    params, required = build_crew_signature(recipe)
    declared = {
        f["name"]
        for f in json.loads((recipe / "inputs.json").read_text(encoding="utf-8"))
    }

    unknown = declared - set(params)
    assert not unknown, (
        f"{recipe.name}: inputs.json declares {sorted(unknown)}, which build_crew() "
        f"does not accept — a run from the playground would raise TypeError"
    )

    unfilled = required - declared
    assert not unfilled, (
        f"{recipe.name}: build_crew() requires {sorted(unfilled)}, which inputs.json "
        f"does not collect — a run from the playground would raise TypeError"
    )


@recipes
def test_llm_py_is_in_sync(recipe: Path):
    """Recipes are self-contained, so llm.py is copied — copies must not drift (#191, #193)."""
    baseline = recipe_dirs()[0] / "llm.py"
    assert (recipe / "llm.py").read_bytes() == baseline.read_bytes(), (
        f"{recipe.name}/llm.py differs from {baseline.parent.name}/llm.py.\n"
        f"Fix with: python tools/sync_llm.py --from {recipe.name}"
    )


@recipes
def test_env_example_documents_the_api_key(recipe: Path):
    text = (recipe / ".env.example").read_text(encoding="utf-8")
    assert "LLM_API_KEY" in text, (
        f"{recipe.name}/.env.example must document LLM_API_KEY"
    )


@recipes
def test_readme_is_not_a_stub(recipe: Path):
    text = (recipe / "README.md").read_text(encoding="utf-8")
    assert text.lstrip().startswith("#"), (
        f"{recipe.name}/README.md must open with a title"
    )
    assert len(text) > 400, (
        f"{recipe.name}/README.md looks like a stub ({len(text)} chars)"
    )


@recipes
def test_no_secrets_committed(recipe: Path):
    """A real key in .env.example is the one mistake that actually costs someone money.

    NIM keys are long and mixed-case; placeholders like nvapi-YOUR_KEY_HERE are
    short or SCREAMING_SNAKE_CASE, so anything long and not all-caps is suspect.
    """
    text = (recipe / ".env.example").read_text(encoding="utf-8")
    leaked = [
        token
        for token in re.findall(r"nvapi-[A-Za-z0-9_-]{20,}", text)
        if not token[len("nvapi-") :].replace("_", "").replace("-", "").isupper()
    ]
    assert not leaked, (
        f"{recipe.name}/.env.example appears to contain a real NVIDIA key"
    )
