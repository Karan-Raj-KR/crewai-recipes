# Run a recipe nightly with GitHub Actions

The content-pipeline CLI accepts fixed inputs and writes its output to stdout.
This example runs it every day at **08:00 UTC (13:30 IST)** and saves that output
as an artifact. It generates an article about reviewing PRs; it does not fetch
or summarize your repository's new PRs. The existing
[PR review integration](../github-actions-integration.md) handles PR-event reviews.

## Set up your fork

1. Fork this repository, or copy its `recipes/content-pipeline/` directory into
   your own repository, preserving the path used below.
2. In **Settings → Secrets and variables → Actions → New repository secret**,
   create `LLM_API_KEY` with your provider key. Use a repository **secret**, not an
   Actions configuration variable. Never paste a key into YAML, commit a `.env`
   file, print it, or enable shell tracing. The secret is injected into the
   recipe step's environment only when it runs.
3. Copy [the complete workflow](../../examples/github-actions/nightly-content-workflow.yml)
   into `.github/workflows/nightly-content.yml` **in your fork**, then commit it
   to that fork's default branch. Enable Actions in the fork if prompted.
4. From **Actions → Nightly content pipeline → Run workflow**, run it manually
   first. Open the completed run and download its `nightly-content-<run ID>`
   artifact. `content.txt` contains the CLI's headings and generated article.

The example lives outside `.github/workflows/` in this repository and cannot
schedule runs here. Scheduled runs use the downstream repository's default
branch and can be delayed at busy times; this is not an exact-time guarantee.
Public repositories can have inactive schedules disabled after 60 days.

## Complete workflow

```yaml
# Example only: copy to .github/workflows/nightly-content.yml in your fork.
name: Nightly content pipeline

on:
  schedule:
    - cron: '0 8 * * *'
  workflow_dispatch:

permissions:
  contents: read

concurrency:
  group: nightly-content-${{ github.ref }}
  cancel-in-progress: false

jobs:
  content:
    runs-on: ubuntu-latest
    timeout-minutes: 20
    steps:
      - uses: actions/checkout@v4
        with:
          persist-credentials: false
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
          cache: pip
          cache-dependency-path: recipes/content-pipeline/requirements.txt
      - name: Install recipe dependencies
        run: python -m pip install -r recipes/content-pipeline/requirements.txt
      - name: Run fixed-input recipe
        working-directory: recipes/content-pipeline
        env:
          LLM_API_KEY: ${{ secrets.LLM_API_KEY }}
        run: |
          if [ -z "$LLM_API_KEY" ]; then
            echo '::error::Add the LLM_API_KEY repository secret before running this workflow.'
            exit 1
          fi
          mkdir -p "$GITHUB_WORKSPACE/artifacts"
          python -u run.py \
            --topic "A practical guide to reviewing pull requests" \
            --target-audience "Open source maintainers" \
            --keywords "pull requests, code review, collaboration" \
            > "$GITHUB_WORKSPACE/artifacts/content.txt"
          test -s "$GITHUB_WORKSPACE/artifacts/content.txt"
      - name: Upload recipe output
        uses: actions/upload-artifact@v4
        with:
          name: nightly-content-${{ github.run_id }}
          path: artifacts/content.txt
          if-no-files-found: error
          retention-days: 7
```

The explicit cache path keys pip's download cache on this recipe's requirements;
installation still runs on every job. The recipe's version ranges are preserved,
so the cache is not a dependency lockfile. Read-only repository access is enough;
this workflow does not post comments or modify PRs.

## Failures and provider limits

A missing secret fails before invoking the recipe. Recipe errors and empty
output fail the job; failed jobs do not publish a success artifact. The run has
a 20-minute ceiling, and concurrency queues overlapping runs on the same ref.
Use the job log to diagnose failures without printing credentials. Artifacts can
contain provider output, so review repository/artifact access before using
private inputs; retention is seven days.

GitHub-hosted runners share IP pools. NVIDIA NIM and other providers may return
HTTP 429 even when the workflow is valid. This repository's LLM helper already
configures up to three retries and a per-request timeout. Wait for the provider's
rate-limit window and rerun manually after checking its quota/status; repeated
whole-workflow retries can spend additional tokens. For another provider, see
[provider configuration](../providers.md) and keep its key in Secrets too.

Before submitting changes to this example, run it in a personal fork. Record the
run URL and whether it used a real configured provider or an offline fixture.
A fixture can verify shell paths, fixed CLI arguments and artifact handling,
but cannot verify provider authentication or generated content quality.

References: [scheduled workflow events](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule),
[Python dependency caching](https://github.com/actions/setup-python#caching-packages-dependencies),
and [Actions secrets](https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-secrets).
