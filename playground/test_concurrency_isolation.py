"""Regression test for Issue #262: Verifies that overlapping concurrent recipe runs

in the Playground do not cross-contaminate module imports or cache wrong results.
"""

from __future__ import annotations

import os
import sys
import tempfile
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

# Ensure playground directory is on sys.path
playground_dir = Path(__file__).parent.resolve()
if str(playground_dir) not in sys.path:
    sys.path.insert(0, str(playground_dir))

import main  # noqa: E402


def test_concurrent_run_recipe_isolation() -> None:
    """Verify concurrent /run executions do not cross-import another recipe's modules (#262)."""
    os.environ["LLM_API_KEY"] = "offline-test-key"
    main.response_cache.clear()

    a_started = threading.Event()
    b_imported = threading.Event()
    a_imported = threading.Event()

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        for label in ("alpha", "beta"):
            d = root / label
            d.mkdir()
            (d / "agents.py").write_text(f"LABEL = {label!r}\n")
            if label == "alpha":
                source = """import __main__
def build_crew(**inputs):
    __main__.a_started.set()
    assert __main__.b_imported.wait(5), "Timed out waiting for beta to import"
    from agents import LABEL
    __main__.a_imported.set()
    return type("Crew", (), {"kickoff": lambda self: LABEL})()
"""
            else:
                source = """import __main__
def build_crew(**inputs):
    from agents import LABEL
    __main__.b_imported.set()
    assert __main__.a_imported.wait(5), "Timed out waiting for alpha to import"
    return type("Crew", (), {"kickoff": lambda self: LABEL})()
"""
            (d / "crew.py").write_text(source)

        orig_recipes_dir = main.RECIPES_DIR
        main.RECIPES_DIR = root
        main.get_client_ip = lambda request: "offline-test-ip"

        try:
            # Bind events on __main__ so temporary recipe source can find them
            main_mod = sys.modules["__main__"]
            main_mod.a_started = a_started
            main_mod.b_imported = b_imported
            main_mod.a_imported = a_imported

            def run(label: str):
                request = main.RunRequest(recipe=label, inputs={}, no_cache=True)
                return main.run_recipe(request, object())

            with ThreadPoolExecutor(max_workers=2) as pool:
                future_a = pool.submit(run, "alpha")
                assert a_started.wait(5), "alpha did not start in time"
                future_b = pool.submit(run, "beta")

                res_a = future_a.result(timeout=10)
                res_b = future_b.result(timeout=10)

            assert res_a == {"output": "alpha", "cached": False}, (
                f"Unexpected alpha result: {res_a}"
            )
            assert res_b == {"output": "beta", "cached": False}, (
                f"Unexpected beta result: {res_b}"
            )

            # Verify response_cache holds correct outputs under respective keys
            assert main.response_cache.get("alpha", {}) == "alpha"
            assert main.response_cache.get("beta", {}) == "beta"

            # Subsequent cached runs should return the correct cached values
            cached_req_a = main.RunRequest(recipe="alpha", inputs={}, no_cache=False)
            cached_res_a = main.run_recipe(cached_req_a, object())
            assert cached_res_a == {"output": "alpha", "cached": True}

            cached_req_b = main.RunRequest(recipe="beta", inputs={}, no_cache=False)
            cached_res_b = main.run_recipe(cached_req_b, object())
            assert cached_res_b == {"output": "beta", "cached": True}

            # Verify no leftover recipe-local modules in sys.modules
            assert "agents" not in sys.modules
            assert "recipe_crew" not in sys.modules
            assert not any(k.startswith("_recipe_") for k in sys.modules)

        finally:
            main.RECIPES_DIR = orig_recipes_dir
            main.response_cache.clear()
            main_mod = sys.modules["__main__"]
            for attr in ("a_started", "b_imported", "a_imported"):
                if hasattr(main_mod, attr):
                    delattr(main_mod, attr)


def test_concurrent_execute_recipe_stream_isolation() -> None:
    """Verify concurrent streaming executions (SSE/WS) do not cross-import modules (#262)."""
    os.environ["LLM_API_KEY"] = "offline-test-key"
    main.response_cache.clear()

    stream_a_started = threading.Event()
    stream_b_imported = threading.Event()
    stream_a_imported = threading.Event()

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        for label in ("stream_alpha", "stream_beta"):
            d = root / label
            d.mkdir()
            (d / "agents.py").write_text(f"LABEL = {label!r}\n")
            if label == "stream_alpha":
                source = """import __main__
def build_crew(**inputs):
    __main__.stream_a_started.set()
    assert __main__.stream_b_imported.wait(5), "Timed out waiting for stream_beta to import"
    from agents import LABEL
    __main__.stream_a_imported.set()
    return type("Crew", (), {"kickoff": lambda self: LABEL})()
"""
            else:
                source = """import __main__
def build_crew(**inputs):
    from agents import LABEL
    __main__.stream_b_imported.set()
    assert __main__.stream_a_imported.wait(5), "Timed out waiting for stream_alpha to import"
    return type("Crew", (), {"kickoff": lambda self: LABEL})()
"""
            (d / "crew.py").write_text(source)

        orig_recipes_dir = main.RECIPES_DIR
        main.RECIPES_DIR = root

        try:
            main_mod = sys.modules["__main__"]
            main_mod.stream_a_started = stream_a_started
            main_mod.stream_b_imported = stream_b_imported
            main_mod.stream_a_imported = stream_a_imported

            events_a: list[dict] = []
            events_b: list[dict] = []

            stop_a = threading.Event()
            stop_b = threading.Event()

            t_a = threading.Thread(
                target=main.execute_recipe_stream,
                args=("stream_alpha", {}, events_a.append, stop_a),
            )
            t_b = threading.Thread(
                target=main.execute_recipe_stream,
                args=("stream_beta", {}, events_b.append, stop_b),
            )

            t_a.start()
            assert stream_a_started.wait(5), "stream_alpha did not start in time"
            t_b.start()

            t_a.join(timeout=10)
            t_b.join(timeout=10)

            complete_a = [e for e in events_a if e.get("type") == "complete"]
            complete_b = [e for e in events_b if e.get("type") == "complete"]

            assert complete_a, f"No complete event for stream_alpha: {events_a}"
            assert complete_b, f"No complete event for stream_beta: {events_b}"

            assert complete_a[0]["output"] == "stream_alpha"
            assert complete_b[0]["output"] == "stream_beta"

            assert "agents" not in sys.modules
            assert not any(k.startswith("_recipe_") for k in sys.modules)

        finally:
            main.RECIPES_DIR = orig_recipes_dir
            main.response_cache.clear()
            main_mod = sys.modules["__main__"]
            for attr in ("stream_a_started", "stream_b_imported", "stream_a_imported"):
                if hasattr(main_mod, attr):
                    delattr(main_mod, attr)


if __name__ == "__main__":
    test_concurrent_run_recipe_isolation()
    test_concurrent_execute_recipe_stream_isolation()
    print("All concurrency isolation tests passed!")
