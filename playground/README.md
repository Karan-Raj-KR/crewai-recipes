# CrewAI Recipes Playground

A local, lightweight web interface to test your recipes. **This runs entirely on your local machine; your API key never leaves your device.**

![Playground Screenshot Placeholder](./screenshot.png)

## Quickstart

1. Navigate to the playground directory:
   ```bash
   cd playground
   ```
2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
3. Set your LLM API Key:
   ```bash
   cp .env.example .env
   # Edit .env and add: LLM_API_KEY=nvapi-...
   ```
4. Start the server:
   ```bash
   uvicorn main:app --reload
   ```
5. Open [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser.
