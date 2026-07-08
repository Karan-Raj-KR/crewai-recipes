# Groq + CrewAI Setup Guide

A step-by-step guide to getting your development environment ready for any recipe in this library.

---

## 1. Get a Groq API Key

1. Go to [console.groq.com](https://console.groq.com/) and sign up (it's free).
2. Navigate to **API Keys** in the sidebar.
3. Click **Create API Key**, name it (e.g. `crewai-recipes-dev`), and copy the key.

Keep this key secret — never commit it to version control.

---

## 2. Python Environment

We recommend Python **3.10 or higher**.

```bash
# Check your Python version
python --version

# Create a virtual environment (inside the recipe directory)
python -m venv .venv
source .venv/bin/activate    # Windows: .venv\Scripts\activate
```

---

## 3. Install Dependencies

Each recipe has its own `requirements.txt`. Install from within the recipe directory:

```bash
cd recipes/lead-qualification
pip install -r requirements.txt
```

---

## 4. Set Your API Key

**Option A — Environment variable (recommended for CI/CD):**
```bash
export GROQ_API_KEY="gsk_..."    # Linux/macOS
set GROQ_API_KEY=gsk_...         # Windows CMD
$env:GROQ_API_KEY="gsk_..."      # Windows PowerShell
```

**Option B — .env file (recommended for local dev):**
```bash
cp .env.example .env
# Edit .env and replace the placeholder with your real key
```

Every recipe loads `.env` automatically via `python-dotenv`.

---

## 5. Choose a Model

| Model | Speed | Quality | Best for |
|-------|-------|---------|----------|
| `llama-3.1-8b-instant` | ⚡⚡⚡ | Good | Development, testing |
| `llama3-70b-8192` | ⚡⚡ | Excellent | Production, complex reasoning |
| `mixtral-8x7b-32768` | ⚡⚡ | Very Good | Long-context tasks |

Change the model in `agents.py`:

```python
def _get_llm(model: str = "llama3-70b-8192") -> ChatGroq:
    ...
```

---

## 6. Run a Recipe

```bash
cd recipes/lead-qualification
python main.py
```

You should see CrewAI's verbose output as each agent works through its tasks, followed by the final result.

---

## Troubleshooting

| Error | Solution |
|-------|---------|
| `EnvironmentError: GROQ_API_KEY is not set` | Export the key or check your `.env` file |
| `RateLimitError` | You've hit Groq's free tier limit — wait a moment or upgrade |
| `ModuleNotFoundError: crewai` | Run `pip install -r requirements.txt` in the recipe directory |
| `ValidationError` | Check that your CrewAI version matches `requirements.txt` |
