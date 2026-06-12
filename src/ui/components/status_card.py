from __future__ import annotations

from src.ui.components.cards import render_info_box


def render_status_card(title: str, body: str, *, tone: str = "info") -> None:
    """Render one reusable status or warning card."""
    render_info_box(title, body, tone=tone)
