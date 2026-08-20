"""Unit tests for Issue #180: Playground dark mode toggle (localStorage-persisted, respects prefers-color-scheme)."""

import re
from pathlib import Path

PLAYGROUND_STATIC_INDEX = Path(__file__).parent / "static" / "index.html"


def get_index_html() -> str:
    """Read the index.html content."""
    assert PLAYGROUND_STATIC_INDEX.exists(), "playground/static/index.html must exist"
    return PLAYGROUND_STATIC_INDEX.read_text(encoding="utf-8")


def test_theme_css_tokens_defined() -> None:
    """Verify index.html defines required CSS custom properties for light and dark palettes."""
    html = get_index_html()

    # Core CSS tokens in :root
    for token in [
        "--bg-color",
        "--surface-color",
        "--surface-2",
        "--text-color",
        "--text-muted",
        "--border",
        "--primary",
        "--primary-hover",
        "--error",
        "--success",
        "--warning",
    ]:
        assert token in html, f"CSS token {token} should be present in index.html"

    # Verify prefers-color-scheme: dark media query
    assert "@media (prefers-color-scheme: dark)" in html

    # Verify data-theme selector overrides
    assert '[data-theme="dark"]' in html
    assert '[data-theme="light"]' in html


def test_theme_toggle_elements_present() -> None:
    """Verify markup contains the theme toggle button and controls."""
    html = get_index_html()

    assert 'id="theme-toggle-btn"' in html
    assert 'id="theme-toggle-icon"' in html
    assert 'class="theme-toggle-btn"' in html
    assert "Toggle color theme" in html


def test_localstorage_persistence_and_fouc_prevention() -> None:
    """Verify localStorage key and early theme script to avoid FOUC."""
    html = get_index_html()

    # Required storage key as specified in issue #180
    assert "crewai-playground-theme" in html

    # Early script in <head>
    head_match = re.search(r"<head>(.*?)</head>", html, re.DOTALL)
    assert head_match is not None
    head_content = head_match.group(1)
    assert "localStorage.getItem('crewai-playground-theme')" in head_content
    assert "setAttribute('data-theme'" in head_content


def test_theme_toggle_js_logic() -> None:
    """Verify JavaScript includes functions to toggle, persist, and update theme."""
    html = get_index_html()

    assert "toggleTheme" in html
    assert "applyTheme" in html
    assert "getCurrentTheme" in html
    assert "updateThemeUI" in html
    assert "prefers-color-scheme: dark" in html


def test_no_inline_colors_in_markup() -> None:
    """Verify no hardcoded color values (#hex or rgb/rgba) remain in inline style attributes."""
    html = get_index_html()

    # Extract all style="..." attributes in HTML outside the <style> tags
    body_match = re.search(r"<body>(.*?)</body>", html, re.DOTALL)
    assert body_match is not None
    body_content = body_match.group(1)

    inline_styles = re.findall(r'style="([^"]*)"', body_content)
    for style_str in inline_styles:
        # Check for hardcoded hex colors or direct rgb/rgba values in inline styles
        hex_colors = re.findall(r"#[0-9a-fA-F]{3,8}", style_str)
        assert not hex_colors, (
            f"Found hardcoded hex color {hex_colors} in inline style: {style_str}"
        )

        rgba_colors = re.findall(r"rgba?\(", style_str)
        assert not rgba_colors, f"Found hardcoded rgb/rgba in inline style: {style_str}"
