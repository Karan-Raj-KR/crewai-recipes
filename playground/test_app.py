import subprocess
import time
import requests
import sys

def main():
    print("Starting uvicorn...")
    proc = subprocess.Popen([".venv/bin/python", "-m", "uvicorn", "main:app", "--port", "8000"])
    
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
        
    proc.terminate()
    proc.wait()
    print("Test finished.")

if __name__ == "__main__":
    main()
