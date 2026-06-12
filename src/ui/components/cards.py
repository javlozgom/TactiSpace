from __future__ import annotations

from src.ui.components.html import html_text, render_html_block, tone_class
from src.ui.components.page_header import resolve_tone_icon
from src.ui.components.icons import icon_svg


def render_info_box(
    title: str,
    body: str,
    tone: str = "info",
    *,
    allow_html: bool = False,
    icon: str | None = None,
) -> None:
    """Render one reusable informational box."""
    tone_map = {
        "info": "blue",
        "neutral": "neutral",
        "success": "green",
        "warning": "orange",
        "danger": "red",
    }
    resolved_tone = tone_class(tone_map.get(tone, tone))
    body_html = str(body) if allow_html else html_text(body)
    resolved_icon = icon or resolve_tone_icon(resolved_tone)

    render_html_block(
        f"""
        <div class="fea-info-box info-box fea-info-{resolved_tone}">
            <div class="fea-info-icon">{icon_svg(resolved_icon)}</div>
            <div class="fea-info-copy">
                <div class="fea-info-title">{html_text(title)}</div>
                <div class="fea-info-body">{body_html}</div>
            </div>
        </div>
        """
    )


def render_empty_state(message: str, hint: str | None = None) -> None:
    """Render a concrete empty state with an optional follow-up hint."""
    body = html_text(message) if not hint else f'{html_text(message)}<br><span class="fea-empty-hint">{html_text(hint)}</span>'
    render_info_box("Sin resultados", body, tone="neutral", allow_html=True, icon="search")
