from __future__ import annotations

from src.ui.components.html import html_text, render_html_block, tone_class
from src.ui.components.page_header import resolve_tone_icon
from src.ui.components.icons import icon_svg


def _kpi_card_html(
    label: object,
    value: object,
    help_text: object | None,
    tone: str,
    icon: str,
) -> str:
    """Build compact KPI card HTML without Markdown indentation side effects."""
    help_html = f'<div class="fea-kpi-sub">{html_text(help_text)}</div>' if help_text else ""
    return (
        f'<div class="fea-kpi-card kpi-card fea-kpi-{tone_class(tone)}">'
        f'<div class="fea-kpi-top"><div class="fea-kpi-icon">{icon_svg(icon)}</div>'
        f'<div class="fea-kpi-label">{html_text(label)}</div></div>'
        f'<div class="fea-kpi-value">{html_text(value)}</div>{help_html}</div>'
    )


def render_kpi_card(
    label: str,
    value: object,
    help_text: str | None = None,
    tone: str = "neutral",
    *,
    sublabel: str | None = None,
    accent_class: str | None = None,
    icon: str | None = None,
) -> None:
    """Render one reusable KPI card."""
    resolved_tone = tone_class(accent_class or tone)
    resolved_help = help_text if help_text is not None else sublabel
    resolved_icon = icon or resolve_tone_icon(resolved_tone)
    render_html_block(_kpi_card_html(label, value, resolved_help, resolved_tone, resolved_icon))


def render_kpi_grid(items: list[dict]) -> None:
    """Render one row of reusable KPI cards."""
    if not items:
        return

    cards_html = []
    for item in items:
        resolved_tone = tone_class(str(item.get("tone") or item.get("accent", "neutral")))
        resolved_icon = str(item.get("icon") or resolve_tone_icon(resolved_tone))
        cards_html.append(
            _kpi_card_html(
                label=str(item.get("label", "")),
                value=item.get("value", "-"),
                help_text=item.get("help") or item.get("sub"),
                tone=resolved_tone,
                icon=resolved_icon,
            )
        )
    render_html_block(f'<div class="fea-kpi-grid">{"".join(cards_html)}</div>')


def render_kpi_row(metrics: list[dict]) -> None:
    """Backward-compatible alias for one row of KPI cards."""
    render_kpi_grid(metrics)
