from __future__ import annotations

from src.ui.components.cards import render_info_box


def render_insight_card(title: str, body: str, *, tone: str = "neutral") -> None:
    """Render one reusable interpretative card."""
    render_info_box(title, body, tone=tone)
