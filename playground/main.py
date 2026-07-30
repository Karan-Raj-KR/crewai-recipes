import importlib.util
import json
import os
import sys
import importlib.util
import logging
import time
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(title="CrewAI Recipes Playground")

RECIPES_DIR = Path(__file__).parent.parent / "recipes"


class RunRequest(BaseModel):
    recipe: str
    inputs: dict[str, str]


def get_recipe_description(recipe_dir: Path) -> str:
    readme_path = recipe_dir / "README.md"
    if not readme_path.exists():
        return recipe_dir.name.replace("-", " ").title()
    past_title = False
    for line in readme_path.read_text(encoding="utf-8").splitlines():
        if line.startswith("# "):
            past_title = True
            continue
        if past_title and line.strip():
            return line.strip()
    return recipe_dir.name.replace("-", " ").title()


@app.get("/recipes")
def list_recipes():
    recipes = []
    if not RECIPES_DIR.exists():
        return {"recipes": recipes}

    for entry in sorted(RECIPES_DIR.iterdir()):
        if not (
            entry.is_dir()
            and (entry / "crew.py").exists()
            and not entry.name.startswith("_")
        ):
            continue
        desc = get_recipe_description(entry)
        inputs_path = entry / "inputs.json"
        inputs = json.loads(inputs_path.read_text()) if inputs_path.exists() else []
        recipes.append({"id": entry.name, "description": desc, "inputs": inputs})
    return {"recipes": recipes}


@app.post("/run")
def run_recipe(req: RunRequest):
    start_time = time.time()
    
    sanitized_inputs = {
        k: ("***" if "key" in k.lower() or "secret" in k.lower() or "token" in k.lower() else v) 
        for k, v in req.inputs.items()
    }
    logger.info(f"Incoming request to run recipe '{req.recipe}' with inputs: {sanitized_inputs}")

    if not os.getenv("LLM_API_KEY") and not os.getenv("NVIDIA_API_KEY"):
        logger.error(f"Recipe '{req.recipe}' failed: Missing API keys (Execution time: {time.time() - start_time:.2f}s)")
        raise HTTPException(
            status_code=401, detail="LLM_API_KEY is not set in the environment."
        )

    recipe_dir = (RECIPES_DIR / req.recipe).resolve()
    if not recipe_dir.is_relative_to(RECIPES_DIR.resolve()):
        raise HTTPException(status_code=400, detail="Invalid recipe name")
    crew_path = recipe_dir / "crew.py"
    if not recipe_dir.exists() or not crew_path.exists():
        logger.error(f"Recipe '{req.recipe}' failed: Not found (Execution time: {time.time() - start_time:.2f}s)")
        raise HTTPException(status_code=404, detail="Recipe not found")

    original_sys_path = sys.path.copy()
    sys.path.insert(0, str(recipe_dir))

    try:
        spec = importlib.util.spec_from_file_location("recipe_crew", crew_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        if not hasattr(module, "build_crew"):
            logger.error(f"Recipe '{req.recipe}' failed: Could not find build_crew in crew.py (Execution time: {time.time() - start_time:.2f}s)")
            raise HTTPException(
                status_code=500, detail="Could not find build_crew in crew.py"
            )
        try:
            crew = module.build_crew(**req.inputs)
            crew.verbose = False
            result = crew.kickoff()
            exec_time = time.time() - start_time
            logger.info(f"Recipe '{req.recipe}' completed successfully in {exec_time:.2f}s")
            return {"output": str(result)}
        except Exception as e:
            exec_time = time.time() - start_time
            err_str = str(e)
            logger.error(f"Recipe '{req.recipe}' failed during execution in {exec_time:.2f}s. Error: {err_str}")
            if "API_KEY is not set" in err_str:
                raise HTTPException(
                    status_code=401,
                    detail="API Key is missing. Please check your .env file.",
                )
            raise HTTPException(status_code=500, detail=f"Execution error: {err_str}")

    finally:
        sys.path = original_sys_path


frontend_dir = Path(__file__).parent / "static"
frontend_dir.mkdir(exist_ok=True)
app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="static")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
