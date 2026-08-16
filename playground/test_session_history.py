"""Unit tests for Issue #71: Playground session-based run history sidebar UI elements."""

import sys
from pathlib import Path

from fastapi.testclient import TestClient

playground_dir = Path(__file__).parent.resolve()
if str(playground_dir) not in sys.path:
    sys.path.insert(0, str(playground_dir))

from main import app  # noqa: E402 (import after sys.path/mocks are set up)

client = TestClient(app)


def test_index_html_contains_history_sidebar_elements() -> None:
    """Verify that index.html contains the Session History sidebar markup and scripts."""
    res = client.get("/")
    assert res.status_code == 200
    html = res.text

    # Verify Sidebar container and elements
    assert 'id="history-sidebar"' in html
    assert 'class="history-sidebar"' in html
    assert "Session History" in html
    assert 'id="history-count"' in html
    assert 'id="clear-history-btn"' in html
    assert 'id="history-list"' in html

    # Verify sessionStorage JS functions
    assert (
        "sessionStorage.getItem(HISTORY_STORAGE_KEY)" in html
        or "sessionStorage.getItem" in html
    )
    assert "sessionStorage.setItem" in html
    assert "sessionStorage.removeItem" in html
    assert "MAX_HISTORY_ENTRIES = 10" in html

    # Verify event handler restoration and clear history
    assert "restoreHistoryEntry" in html
    assert "addHistoryEntry" in html
    assert "clearHistory" in html
