from __future__ import annotations

from src.ui.components import render_page_header


def render_page_shell(
    title: str,
    subtitle: str | None = None,
    *,
    eyebrow: str | None = None,
    tone: str | None = None,
) -> None:
    """Render one standardized page header shell."""
    render_page_header(title, subtitle, eyebrow=eyebrow, tone=tone)
