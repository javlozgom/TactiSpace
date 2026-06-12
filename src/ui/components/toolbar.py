from __future__ import annotations

from contextlib import contextmanager

import streamlit as st


@contextmanager
def render_toolbar():
    """Render one lightweight toolbar container."""
    with st.container(border=True):
        yield
