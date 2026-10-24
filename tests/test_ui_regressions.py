"""Regression checks for the shared Streamlit UI shell."""

import re
from pathlib import Path


UI_SOURCE = Path(__file__).parents[1] / "qshield" / "ui.py"


def test_shared_shell_keeps_main_content_in_a_scrollport():
    """The main flex child must be able to scroll within Streamlit's viewport."""
    source = UI_SOURCE.read_text()

    assert ".main .block-container" in source
    assert '[data-testid="stAppViewContainer"] > .main' in source
    assert "overflow-y: auto" in source
    assert "min-height: 0" in source
    assert "overflow: visible !important" not in source
    assert "height: auto !important" not in source


def test_decorative_layers_cannot_capture_pointer_input():
    """Fixed ambient decoration must remain non-interactive."""
    source = UI_SOURCE.read_text()

    assert ".qs-cyber-background" in source
    assert "pointer-events: none" in source


def test_shared_sidebar_hides_duplicate_streamlit_navigation():
    """Only the custom Q-Shield navigation should appear in the sidebar."""
    source = UI_SOURCE.read_text()

    assert '[data-testid="stSidebarNav"]' in source
    assert "display: none" in source


def test_tab_panels_have_inner_spacing_and_wrap_on_small_screens():
    source = UI_SOURCE.read_text()

    assert 'div[data-testid="stTabs"] [role="tabpanel"]' in source
    assert "padding: 16px clamp(14px, 2.5vw, 24px) 22px" in source
    assert 'div[data-testid="stTabs"] [role="tablist"] { flex-wrap: wrap; }' in source


def test_dataframes_do_not_clip_their_scroll_or_focus_layer():
    """Table wrappers must not hide native grid scrollbars or focus rings."""
    source = UI_SOURCE.read_text()
    match = re.search(r'div\[data-testid="stDataFrame"\]\s*\{([^}]*)\}', source)

    assert match is not None
    assert "overflow: hidden" not in match.group(1)
