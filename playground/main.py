import asyncio
import importlib.util
import json
import os
import sys
import threading
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

load_dotenv()

app = FastAPI(title="CrewAI Recipes Playground")

RECIPES_DIR = Path(__file__).parent.parent / "recipes"


class RunRequest(BaseModel):
    recipe: str
    inputs: dict[str, str]


class ThreadSafeStreamRedirector:
    """Redirects stdout writes to a callback while preventing re-entrant logging loops."""

    def __init__(self, original_stdout, callback):
        self.original_stdout = original_stdout
        self.callback = callback
        self.buffer = ""
        self._in_write = False

    def write(self, text):
        self.original_stdout.write(text)
        if self._in_write:
            return
        self._in_write = True
        try:
            self.buffer += text
            while "\n" in self.buffer:
                line, self.buffer = self.buffer.split("\n", 1)
                line_clean = line.strip()
                if line_clean:
                    self.callback(line_clean)
        finally:
            self._in_write = False

    def flush(self):
        self.original_stdout.flush()
        if self._in_write:
            return
        self._in_write = True
        try:
            if self.buffer.strip():
                self.callback(self.buffer.strip())
                self.buffer = ""
        finally:
            self._in_write = False


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
    if not os.getenv("LLM_API_KEY") and not os.getenv("NVIDIA_API_KEY"):
        raise HTTPException(
            status_code=401, detail="LLM_API_KEY is not set in the environment."
        )

    recipe_dir = (RECIPES_DIR / req.recipe).resolve()
    if not recipe_dir.is_relative_to(RECIPES_DIR.resolve()):
        raise HTTPException(status_code=400, detail="Invalid recipe name")
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
            raise HTTPException(
                status_code=500, detail="Could not find build_crew in crew.py"
            )

        try:
            crew = module.build_crew(**req.inputs)
            crew.verbose = False
            result = crew.kickoff()
            return {"output": str(result)}
        except Exception as e:
            err_str = str(e)
            if "API_KEY is not set" in err_str:
                raise HTTPException(
                    status_code=401,
                    detail="API Key is missing. Please check your .env file.",
                )
            raise HTTPException(status_code=500, detail=f"Execution error: {err_str}")

    finally:
        sys.path = original_sys_path


def execute_recipe_stream(recipe_name: str, inputs: dict, push_event, stop_event: threading.Event):
    """Executes crew.kickoff() in a worker thread, capturing step/task callbacks and stdout logs."""
    if not os.getenv("LLM_API_KEY") and not os.getenv("NVIDIA_API_KEY"):
        push_event({
            "type": "error",
            "error": "API Key is missing. Please check your .env file."
        })
        return

    recipe_dir = (RECIPES_DIR / recipe_name).resolve()
    if not recipe_dir.is_relative_to(RECIPES_DIR.resolve()):
        push_event({"type": "error", "error": "Invalid recipe name"})
        return
    crew_path = recipe_dir / "crew.py"
    if not recipe_dir.exists() or not crew_path.exists():
        push_event({"type": "error", "error": "Recipe not found"})
        return

    original_sys_path = sys.path.copy()
    sys.path.insert(0, str(recipe_dir))

    try:
        spec = importlib.util.spec_from_file_location("recipe_crew", crew_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        if not hasattr(module, "build_crew"):
            push_event({"type": "error", "error": "Could not find build_crew in crew.py"})
            return

        try:
            crew = module.build_crew(**inputs)
            crew.verbose = True

            def step_cb(step):
                if stop_event.is_set():
                    raise InterruptedError("Client disconnected")
                agent_name = getattr(step, "agent", None) or "Agent"
                thought = getattr(step, "thought", "") or getattr(step, "text", "")
                tool = getattr(step, "tool", None)
                tool_input = getattr(step, "tool_input", None)
                result = getattr(step, "result", None)
                push_event({
                    "type": "agent_step",
                    "agent": str(agent_name),
                    "thought": str(thought) if thought else "",
                    "tool": str(tool) if tool else None,
                    "tool_input": str(tool_input) if tool_input else None,
                    "result": str(result) if result else None,
                })

            def task_cb(task_output):
                if stop_event.is_set():
                    raise InterruptedError("Client disconnected")
                agent_name = getattr(task_output, "agent", None) or "Agent"
                description = getattr(task_output, "description", "") or getattr(task_output, "name", "")
                raw_output = getattr(task_output, "raw", "") or str(task_output)
                push_event({
                    "type": "task_complete",
                    "agent": str(agent_name),
                    "description": str(description),
                    "output": str(raw_output),
                })

            crew.step_callback = step_cb
            crew.task_callback = task_cb

            def log_cb(text):
                push_event({
                    "type": "log",
                    "text": text,
                })

            old_stdout = sys.stdout
            redirector = ThreadSafeStreamRedirector(old_stdout, log_cb)
            sys.stdout = redirector
            try:
                result = crew.kickoff()
                if not stop_event.is_set():
                    push_event({"type": "complete", "output": str(result)})
            finally:
                sys.stdout = old_stdout

        except Exception as e:
            if stop_event.is_set() or isinstance(e, InterruptedError):
                return
            err_str = str(e)
            if "API_KEY is not set" in err_str:
                push_event({
                    "type": "error",
                    "error": "API Key is missing. Please check your .env file."
                })
            else:
                push_event({"type": "error", "error": f"Execution error: {err_str}"})

    finally:
        sys.path = original_sys_path


@app.post("/run/stream")
async def run_recipe_stream(req: RunRequest, request: Request):
    """Server-Sent Events (SSE) endpoint to stream CrewAI execution progress in real time."""
    loop = asyncio.get_running_loop()
    queue = asyncio.Queue()
    stop_event = threading.Event()

    def push_event(event):
        loop.call_soon_threadsafe(queue.put_nowait, event)

    async def event_generator():
        push_event({"type": "start", "recipe": req.recipe})
        
        def worker():
            try:
                execute_recipe_stream(req.recipe, req.inputs, push_event, stop_event)
            finally:
                push_event(None)  # Sentinel to close stream

        worker_task = asyncio.create_task(asyncio.to_thread(worker))

        try:
            while True:
                if await request.is_disconnected():
                    stop_event.set()
                    break

                try:
                    event = await asyncio.wait_for(queue.get(), timeout=0.5)
                except asyncio.TimeoutError:
                    continue

                if event is None:
                    break

                yield f"data: {json.dumps(event)}\n\n"
        finally:
            stop_event.set()
            await worker_task

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.websocket("/run/ws")
async def run_recipe_ws(websocket: WebSocket):
    """WebSocket endpoint to stream CrewAI execution progress in real time."""
    await websocket.accept()
    loop = asyncio.get_running_loop()
    queue = asyncio.Queue()
    stop_event = threading.Event()

    def push_event(event):
        loop.call_soon_threadsafe(queue.put_nowait, event)

    try:
        data = await websocket.receive_json()
        recipe = data.get("recipe", "")
        inputs = data.get("inputs", {})

        push_event({"type": "start", "recipe": recipe})

        def worker():
            try:
                execute_recipe_stream(recipe, inputs, push_event, stop_event)
            finally:
                push_event(None)

        worker_task = asyncio.create_task(asyncio.to_thread(worker))

        try:
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=0.5)
                except asyncio.TimeoutError:
                    continue

                if event is None:
                    break

                await websocket.send_json(event)
        finally:
            stop_event.set()
            await worker_task

    except WebSocketDisconnect:
        stop_event.set()
    except Exception as e:
        await websocket.send_json({"type": "error", "error": str(e)})


frontend_dir = Path(__file__).parent / "static"
frontend_dir.mkdir(exist_ok=True)
app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="static")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)

