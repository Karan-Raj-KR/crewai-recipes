"""github_client.py — GitHub REST API client for fetching pull request diffs and metadata.

Supports unauthenticated requests (up to 60 req/hr) and authenticated requests using optional
GITHUB_TOKEN env var (up to 5,000 req/hr). Never stores diffs to disk.
"""

import json
import re
import urllib.error
import urllib.request

REPO_REGEX = re.compile(r"^[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+$")


def validate_repo(repo_str: str) -> tuple[str, str]:
    """Validate and sanitize a repository input string.

    Args:
        repo_str: Input repository string (must be in 'owner/repo' format).

    Returns:
        Tuple of (owner, repo_name).

    Raises:
        ValueError: If repository string format is invalid or contains path traversal.
    """
    cleaned = repo_str.strip().strip("/")

    # Reject path traversal / directory paths
    if ".." in cleaned or cleaned.startswith(("/", "\\")) or ":" in cleaned:
        raise ValueError(
            f"Invalid repository format: '{repo_str}'. Must be in 'owner/name' format (e.g. 'Karan-Raj-KR/crewai-recipes')."
        )

    if not REPO_REGEX.match(cleaned):
        raise ValueError(
            f"Invalid repository format: '{repo_str}'. Must be in 'owner/name' format (e.g. 'Karan-Raj-KR/crewai-recipes')."
        )

    parts = cleaned.split("/")
    return parts[0], parts[1]


def fetch_pr_diff(
    repo: str,
    pr_number: int | str,
    github_token: str | None = None,
) -> tuple[dict, str]:
    """Fetch PR metadata JSON and unified diff text from GitHub API using urllib.

    Args:
        repo: Repository string in 'owner/name' format.
        pr_number: Pull request number.
        github_token: Optional GitHub API personal access token.

    Returns:
        Tuple of (pr_metadata_dict, raw_unified_diff_string).

    Raises:
        ValueError: If repository format is invalid.
        RuntimeError: If GitHub API returns 403 Rate Limit or 404 Not Found error.
    """
    owner, repo_name = validate_repo(repo)
    clean_pr_id = str(pr_number).strip().lstrip("#")

    if not clean_pr_id.isdigit():
        raise ValueError(f"PR number must be an integer, got '{pr_number}'.")

    meta_url = f"https://api.github.com/repos/{owner}/{repo_name}/pulls/{clean_pr_id}"

    headers = {
        "User-Agent": "crewai-recipes-pr-reviewer",
        "Accept": "application/vnd.github.v3+json",
    }
    if github_token:
        headers["Authorization"] = f"token {github_token}"

    # 1. Fetch Metadata JSON
    try:
        req = urllib.request.Request(meta_url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as resp:
            metadata = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code == 403:
            raise RuntimeError(
                "GitHub API rate limit exceeded (60 requests/hr for unauthenticated calls).\n"
                "  Fix: Set optional GITHUB_TOKEN in your .env file to get 5,000 requests/hr."
            ) from e
        elif e.code == 404:
            raise RuntimeError(
                f"Pull request #{clean_pr_id} or repository '{owner}/{repo_name}' not found."
            ) from e
        else:
            raise RuntimeError(f"GitHub API HTTP error {e.code}: {e.reason}") from e
    except urllib.error.URLError as e:
        raise RuntimeError(f"Failed to connect to GitHub API: {e.reason}") from e

    # 2. Fetch Raw Diff text
    diff_headers = headers.copy()
    diff_headers["Accept"] = "application/vnd.github.v3.diff"

    try:
        diff_req = urllib.request.Request(meta_url, headers=diff_headers)
        with urllib.request.urlopen(diff_req, timeout=15) as resp:
            raw_diff = resp.read().decode("utf-8", errors="ignore")
    except urllib.error.HTTPError as e:
        if e.code == 403:
            raise RuntimeError(
                "GitHub API rate limit exceeded while fetching diff.\n"
                "  Fix: Set optional GITHUB_TOKEN in your .env file."
            ) from e
        else:
            raise RuntimeError(
                f"GitHub API HTTP error while fetching diff: {e.code}"
            ) from e

    if not raw_diff.strip():
        raw_diff = (
            f"# No diff changes found for PR #{clean_pr_id} in {owner}/{repo_name}"
        )

    return metadata, raw_diff
