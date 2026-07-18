import os
import sys
import time
import logging
import importlib.util
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List

# Ensure environment variables are loaded
from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(title="CrewAI Recipes Playground")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

RECIPES_DIR = Path(__file__).parent.parent / "recipes"

class RunRequest(BaseModel):
    recipe: str
    inputs: Dict[str, str]

def get_recipe_description(recipe_dir: Path) -> str:
    readme_path = recipe_dir / "README.md"
    if readme_path.exists():
        with open(readme_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("# "):
                    continue
                line = line.strip()
                if line and not line.startswith("[") and not line.startswith("!") and not line.startswith("="):
                    return line
    return "No description available."

@app.get("/recipes")
def list_recipes():
    recipes = []
    if not RECIPES_DIR.exists():
        return {"recipes": recipes}

    for entry in RECIPES_DIR.iterdir():
        if entry.is_dir() and (entry / "crew.py").exists() and not entry.name.startswith("_"):
            desc = get_recipe_description(entry)
            
            inputs = []
            if entry.name == "lead-qualification":
                inputs = [{"name": "company", "label": "Company"}, {"name": "description", "label": "Description"}]
            elif entry.name == "faq-bot":
                inputs = [{"name": "question", "label": "Question"}, {"name": "customer_name", "label": "Customer Name"}]
            elif entry.name == "appointment-booking":
                inputs = [{"name": "customer_details", "label": "Customer Details"}]
            elif entry.name == "whatsapp-action-sim":
                inputs = [{"name": "message", "label": "Message"}]

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

    # Ensure LLM key is set globally
    if not os.getenv("LLM_API_KEY") and not os.getenv("NVIDIA_API_KEY"):
        logger.error(f"Recipe '{req.recipe}' failed: Missing API keys (Execution time: {time.time() - start_time:.2f}s)")
        raise HTTPException(status_code=401, detail="LLM_API_KEY is not set in the environment.")

    recipe_dir = RECIPES_DIR / req.recipe
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
            raise HTTPException(status_code=500, detail="Could not find build_crew in crew.py")
        
        try:
            # We map front-end inputs to kwargs
            crew = module.build_crew(**req.inputs)
            # Disable verbose output for the API response
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
                raise HTTPException(status_code=401, detail="API Key is missing. Please check your .env file.")
            raise HTTPException(status_code=500, detail=f"Execution error: {err_str}")
            
    finally:
        sys.path = original_sys_path

frontend_dir = Path(__file__).parent / "static"
frontend_dir.mkdir(exist_ok=True)
app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
