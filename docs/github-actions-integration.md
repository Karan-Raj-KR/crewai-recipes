# GitHub Actions Integration Guide

This guide explains how to integrate `crewai-recipes` workflows into your CI/CD pipeline using GitHub Actions. Specifically, it demonstrates automating pull request code reviews using the `pr-review-assistant` recipe.

---

## 🎯 Overview

The `pr-review-assistant` recipe uses a multi-agent team (Diff Analyst, Code Quality Reviewer, Style & Conventions Reviewer, and Review Synthesizer) to examine incoming git diffs and produce structured review feedback.

By invoking this recipe directly from a GitHub Actions workflow, your repository can automatically comment on incoming pull requests with detailed architectural and code quality feedback.

---

## 🚀 Setup Steps

### 1. Configure Repository Secrets

The recipe requires access to an LLM provider API key (such as NVIDIA NIM or OpenRouter).

1. Navigate to your repository on GitHub: **Settings** → **Secrets and variables** → **Actions**.
2. Click **New repository secret**.
3. Set the name to `LLM_API_KEY` and paste your API key (e.g. `nvapi-...`).

### 2. Copy the Workflow File

Copy the template from `examples/github-actions/pr-review-workflow.yml` into `.github/workflows/pr-review.yml` in your repository.

```bash
mkdir -p .github/workflows
cp examples/github-actions/pr-review-workflow.yml .github/workflows/pr-review.yml
```

### 3. Grant Pull Request Permissions

GitHub Actions requires write permissions to publish comments on pull requests:

```yaml
permissions:
  contents: read
  pull-requests: write
```

The default `GITHUB_TOKEN` provided by GitHub Actions has sufficient rights when these permissions are declared in the workflow YAML.

---

## ⚙️ Workflow Breakdown

```yaml
name: Automated PR Review

on:
  pull_request:
    types: [opened, synchronize, reopened]
  workflow_dispatch:

permissions:
  contents: read
  pull-requests: write

jobs:
  review:
    name: Multi-Agent PR Review
    runs-on: ubuntu-latest
    if: github.actor != 'dependabot[bot]'
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install dependencies
        run: |
          pip install -r recipes/pr-review-assistant/requirements.txt

      - name: Extract PR diff
        run: |
          git diff origin/${{ github.base_ref }}...HEAD > pr_diff.txt

      - name: Run Review Assistant Crew
        env:
          LLM_API_KEY: ${{ secrets.LLM_API_KEY }}
          LLM_MODEL: meta/llama-3.1-8b-instruct
        run: |
          python recipes/pr-review-assistant/run.py \
            --diff-path pr_diff.txt \
            --output-path pr_review.md

      - name: Post Review Comment
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          gh pr comment ${{ github.event.pull_request.number }} --body-file pr_review.md
```

---

## 💡 Best Practices & Tips

- **Ignore Bot PRs**: The workflow uses `if: github.actor != 'dependabot[bot]'` to prevent unnecessary reviews on automated dependency upgrades.
- **Model Selection**: For fast reviews, use `LLM_MODEL: meta/llama-3.1-8b-instruct`. For deeper architectural analysis, specify `LLM_MODEL: meta/llama-3.3-70b-instruct`.
- **Large Diffs**: If a PR contains large generated files (e.g. lockfiles or minified assets), consider filtering them out using `.gitattributes` or passing a path filter in the `git diff` step.
