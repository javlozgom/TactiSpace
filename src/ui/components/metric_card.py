from __future__ import annotations

from src.ui.components.kpis import render_kpi_card, render_kpi_grid


def render_metric_card(
    *,
    label: str,
    value: object,
    help_text: str | None = None,
    tone: str = "neutral",
    icon: str | None = None,
) -> None:
    """Render one standardized metric card."""
    render_kpi_card(label=label, value=value, help_text=help_text, tone=tone, icon=icon)


def render_metric_cards(items: list[dict]) -> None:
    """Render one standardized metric-card grid."""
    render_kpi_grid(items)
