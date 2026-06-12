from __future__ import annotations

import streamlit as st

from src.ui.components import render_section_header


def render_section_title(title: str, subtitle: str | None = None) -> None:
    """Render one common section header."""
    render_section_header(title, subtitle)


def render_section(title: str, subtitle: str | None = None) -> None:
    """Alias for the common section header."""
    render_section_header(title, subtitle)


def render_section_divider() -> None:
    """Render one conservative divider between major blocks."""
    st.divider()
