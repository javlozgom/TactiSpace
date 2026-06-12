from __future__ import annotations

from contextlib import contextmanager

import streamlit as st

from src.ui.components import render_info_box, render_section_header


@contextmanager
def render_card(*, title: str | None = None, description: str | None = None, border: bool = True):
    """Render one reusable visual card shell."""
    if border:
        with st.container(border=True):
            if title:
                render_section_header(title, description)
            yield
        return

    if title:
        render_section_header(title, description)
    yield


def render_card_intro(title: str, body: str, *, tone: str = "neutral") -> None:
    """Render one short explanatory card."""
    render_info_box(title, body, tone=tone)
