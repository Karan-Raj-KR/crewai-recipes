import os
import sys
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
    # Ensure LLM key is set globally
    if not os.getenv("LLM_API_KEY") and not os.getenv("NVIDIA_API_KEY"):
        raise HTTPException(status_code=401, detail="LLM_API_KEY is not set in the environment.")

    recipe_dir = RECIPES_DIR / req.recipe
    crew_path = recipe_dir / "crew.py"
    if not recipe_dir.exists() or not crew_path.exists():
        raise HTTPException(status_code=404, detail="Recipe not found")

    original_sys_path = sys.path.copy()
    sys.path.insert(0, str(recipe_dir))
    
    try:
        spec = importlib.util.spec_from_file_location("recipe_crew", crew_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        if not hasattr(module, "build_crew"):
            raise HTTPException(status_code=500, detail="Could not find build_crew in crew.py")
        
        try:
            # We map front-end inputs to kwargs
            crew = module.build_crew(**req.inputs)
            # Disable verbose output for the API response
            crew.verbose = False
            result = crew.kickoff()
            
            return {"output": str(result)}
            
        except Exception as e:
            err_str = str(e)
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
