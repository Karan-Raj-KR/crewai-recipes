# PR Review Assistant

Fetch GitHub pull request diffs via the GitHub REST API and run a sequential 4-agent CrewAI pipeline (Diff Analyst, Code Reviewer, Style Reviewer, PR Summarizer) to generate a structured, professional Markdown PR review comment ready for human copy-paste onto GitHub.

---

## 🔒 Security & Design Principles

- **No Automated Posting**: This recipe **never** posts comments automatically to GitHub. Output is strictly presented to stdout / JSON file for human review before copy-pasting.
- **No Diff Disk Persistence**: Fetched diffs and PR content remain strictly in-memory and are never stored or logged to disk.
- **Path Traversal Protection**: `--repo` parameters are strictly validated as `owner/name` strings (`^[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+$`). Path-like inputs (`..`, `/`, absolute paths) are rejected immediately before making API requests.

---

## Input / Output Schema

### Input Parameters

| Parameter | Type | Required | Description |
|---|---|---|---|
| `--repo` | String | Yes | GitHub repository in `owner/name` format (e.g. `Karan-Raj-KR/crewai-recipes`). |
| `--pr` | String/Int | Yes | Pull Request ID or number (e.g. `185`). |
| `--token` | String | No | Optional GitHub access token to avoid unauthenticated API rate limits. |
| `--pretty` | Flag | No | Output pretty-printed human-readable text instead of JSON. |

### Output JSON Schema (`PRReviewOutput`)

```json
{
  "repo": "Karan-Raj-KR/crewai-recipes",
  "pr_number": "185",
  "pr_title": "Pull Request #185",
  "summary": "Automated PR review for Karan-Raj-KR/crewai-recipes#185.",
  "findings": [],
  "markdown_comment": "## 🔍 Pull Request Review: #185\n\n### 📋 Overview\n..."
}
```

---

## Setup & Running

### 1. Configure Environment

Copy `.env.example` to `.env` and set your API key:

```bash
cp .env.example .env
```

Edit `.env`:

```env
LLM_API_KEY=your-api-key-here
# Optional: Higher GitHub API rate limits (5,000 req/hr vs 60 req/hr unauthenticated)
# GITHUB_TOKEN=ghp_your_github_token
```

### 2. Run Review on a Public PR

```bash
python run.py --repo Karan-Raj-KR/crewai-recipes --pr 187 --pretty
```

---

## GitHub API Rate Limits

- **Unauthenticated Requests**: Limited by GitHub to 60 requests per hour per IP.
- **Authenticated Requests**: Setting `GITHUB_TOKEN` increases your rate limit to 5,000 requests per hour.
- If rate limited, the CLI fails fast with a clear error:
  `GitHub API rate limit exceeded (60 requests/hr for unauthenticated calls). Fix: Set optional GITHUB_TOKEN in your .env file.`

---

## Testing

Run offline unit tests with stubbed diff fixtures:

```bash
pytest test_pr_review_assistant.py -v
```
