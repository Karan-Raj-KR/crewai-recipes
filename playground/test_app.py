import os
import subprocess
import sys
import time
from pathlib import Path

import requests


def main():
    playground_dir = Path(__file__).parent
    print("Starting uvicorn...")
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--port", "8000"],
        cwd=playground_dir,
    )
    
    # Wait for server to start
    started = False
    for i in range(20):
        try:
            res = requests.get("http://127.0.0.1:8000/recipes")
            if res.status_code == 200:
                started = True
                break
        except requests.exceptions.ConnectionError:
            pass
        time.sleep(1)
        
    if not started:
        print("Failed to start server")
        proc.terminate()
        sys.exit(1)
        
    print("Server started. Recipes:")
    print(requests.get("http://127.0.0.1:8000/recipes").json())
    
    print("\nTesting /run ...")
    payload = {
        "recipe": "faq-bot",
        "inputs": {
            "question": "How much does Orbitly cost?",
            "customer_name": "Alex"
        }
    }
    res = requests.post("http://127.0.0.1:8000/run", json=payload)
    print("Run response status:", res.status_code)
    try:
        print("Run response JSON:", res.json())
    except:
        print("Run response TEXT:", res.text)

    print("\nTesting /run/stream (SSE) ...")
    res_stream = requests.post("http://127.0.0.1:8000/run/stream", json=payload, stream=True)
    print("Run stream status:", res_stream.status_code)
    lines_received = 0
    for line in res_stream.iter_lines():
        if line:
            lines_received += 1
            print("Stream event line:", line.decode("utf-8"))
            if lines_received >= 5:
                break
        
    proc.terminate()
    proc.wait()
    print("Test finished.")

if __name__ == "__main__":
    main()
