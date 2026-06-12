from __future__ import annotations

import streamlit as st

from src.ui.components.html import display_text, html_text, render_html_block, tone_class
from src.ui.components.icons import icon_svg

PAGE_META = {
    "Inicio": ("home", "blue"),
    "Resumen": ("bar-chart", "blue"),
    "MÃ©tricas especÃ­ficas": ("gauge", "teal"),
    "Comparativa": ("scale", "purple"),
    "PÃ©rdidas": ("alert-triangle", "red"),
    "Voronoi, Delaunay y sugerencia de pase": ("map", "teal"),
    "Eventos": ("list", "blue"),
    "Mapa de calor": ("activity", "orange"),
    "Datos brutos": ("database", "neutral"),
    "GuÃ­a de uso": ("help-circle", "teal"),
}

VIEW_META = {
    "Inicio": {
        "title": "TactiSpace",
        "badge": "src/ui/home_view.py",
        "description": "Landing page del TFG: resumen del proyecto, arquitectura, datasets, mÃ©tricas de contexto, accesos rÃ¡pidos y orientaciÃ³n para la demo.",
    },
    "Resumen": {
        "title": "Resumen del contexto",
        "badge": "src/ui/summary_view.py",
        "description": "VisiÃ³n general del contexto filtrado: eventos, pases, conducciones, tiros, eventos especiales, jugadores y mapas prioritarios por posiciÃ³n.",
    },
    "MÃ©tricas especÃ­ficas": {
        "title": "MÃ©tricas especÃ­ficas",
        "badge": "src/ui/specific_metrics_view.py Â· src/event_metrics.py",
        "description": "AnÃ¡lisis de eventos concretos con KPIs especÃ­ficos, filtros internos, tabla de mÃ©tricas y visualizaciÃ³n contextual.",
    },
    "Comparativa": {
        "title": "Comparativa",
        "badge": "src/ui/comparative_view.py Â· basic Â· advanced Â· percentiles",
        "description": "ComparaciÃ³n bÃ¡sica, avanzada y percentiles con interpretaciÃ³n semÃ¡ntica de mÃ©tricas: volumen, eficiencia, riesgo y direcciÃ³n Ã³ptima.",
    },
    "PÃ©rdidas": {
        "title": "PÃ©rdidas y pases fallidos",
        "badge": "src/ui/losses_view.py Â· src/failed_passes.py",
        "description": "PÃ©rdidas generales y anÃ¡lisis especÃ­fico de pases fallidos integrado en la misma pestaÃ±a, sin pestaÃ±a separada.",
    },
    "Voronoi, Delaunay y sugerencia de pase": {
        "title": "Voronoi, Delaunay y sugerencia de pase",
        "badge": "src/ui/views/spatial.py Â· spatial_voronoi Â· spatial_delaunay Â· spatial_layout",
        "description": "La vista diferencial del TFG: pase fallido, freeze-frame, Voronoi, Delaunay, recomendaciÃ³n Delaunay y recomendaciÃ³n por scoring.",
    },
    "Eventos": {
        "title": "Eventos",
        "badge": "src/ui/events_view.py Â· src/visualizations.py",
        "description": "ExploraciÃ³n visual de eventos sobre el campo con leyenda, tipos ploteables y contexto temporal.",
    },
    "Mapa de calor": {
        "title": "Mapa de calor",
        "badge": "src/ui/heatmap_view.py Â· MAX_PLOT_EVENTS = 600",
        "description": "ConcentraciÃ³n espacial de eventos sobre el campo, limitada para mantener rendimiento estable durante la demo.",
    },
    "Datos brutos": {
        "title": "Datos brutos",
        "badge": "src/ui/raw_data_view.py Â· data/processed/*.parquet",
        "description": "InspecciÃ³n transparente del dataset cargado, rutas normalizadas, validaciÃ³n, tests y columnas principales.",
    },
    "GuÃ­a de uso": {
        "title": "GuÃ­a de uso",
        "badge": "Manual de navegaciÃ³n e interpretaciÃ³n",
        "description": "ExplicaciÃ³n de quÃ© hace cada pestaÃ±a, cÃ³mo se usan los filtros y cÃ³mo interpretar correctamente los resultados de la app.",
    },
}

LEGACY_VIEW_ALIASES = {
    "MÃ©tricas especÃ­ficas": "MÃ©tricas especÃ­ficas",
    "PÃ©rdidas": "PÃ©rdidas",
    "AnÃ¡lisis espacial": "Voronoi, Delaunay y sugerencia de pase",
    "An?lisis espacial": "Voronoi, Delaunay y sugerencia de pase",
}

TONE_ICON = {
    "blue": "bar-chart",
    "primary": "bar-chart",
    "green": "check",
    "success": "check",
    "red": "alert-triangle",
    "danger": "alert-triangle",
    "orange": "target",
    "warning": "target",
    "purple": "scale",
    "teal": "map",
    "neutral": "info",
    "slate": "info",
}


def canonical_view_name(view_name: object) -> str:
    """Normalize legacy view names into the current display labels."""
    display_name = display_text(view_name)
    return LEGACY_VIEW_ALIASES.get(str(view_name), display_name)


def resolve_tone_icon(tone: str) -> str:
    """Return the default icon for a semantic tone."""
    return TONE_ICON.get(tone_class(tone), "info")


def _page_meta(title: str, tone: str | None = None, icon: str | None = None) -> tuple[str, str]:
    """Resolve the default icon and tone for a page title."""
    default_icon, default_tone = PAGE_META.get(canonical_view_name(title), ("sparkles", "blue"))
    return icon or default_icon, tone_class(tone or default_tone)


def _hero_visual_html() -> str:
    """Return the decorative analysis visual container used in page heroes."""
    return '<div class="fea-hero-visual" aria-hidden="true"></div>'


def render_page_header(
    title: str,
    subtitle: str | None = None,
    badge: str | None = None,
    *,
    description: str | None = None,
    eyebrow: str | None = None,
    icon: str | None = None,
    tone: str | None = None,
) -> None:
    """Render one reusable hero-style page header block."""
    canonical_title = canonical_view_name(title)
    meta = VIEW_META.get(canonical_title, {})
    resolved_title = str(meta.get("title") or canonical_title)
    resolved_subtitle = subtitle if subtitle is not None else (description or meta.get("description") or "")
    resolved_badge = badge if badge is not None else (eyebrow or meta.get("badge"))
    _, resolved_tone = _page_meta(canonical_title, tone=tone, icon=icon)
    badge_html = f'<div class="fea-page-eyebrow">{html_text(resolved_badge)}</div>' if resolved_badge else ""
    subtitle_html = f"<p>{html_text(resolved_subtitle)}</p>" if resolved_subtitle else ""

    render_html_block(
        f"""
        <div class="fea-page-header section-card fea-tone-{resolved_tone}">
            <div class="fea-page-copy">
                {badge_html}
                <h2>{html_text(resolved_title)}</h2>
                {subtitle_html}
            </div>
            {_hero_visual_html()}
        </div>
        """
    )


def render_view_hero(
    view_name: str,
    title: str | None = None,
    badge: str | None = None,
    description: str | None = None,
) -> None:
    """Render the shared hero for a top-level app view."""
    render_page_header(title or view_name, subtitle=description, badge=badge)


def render_section_header(
    title: str,
    description: str | None = None,
    action: str | None = None,
    *,
    icon: str | None = None,
    tone: str = "neutral",
) -> None:
    """Render one compact section header."""
    resolved_tone = tone_class(tone)
    action_html = f'<div class="fea-section-action">{html_text(action)}</div>' if action else ""
    description_html = f"<p>{html_text(description)}</p>" if description else ""
    icon_html = f'<div class="fea-section-icon">{icon_svg(icon or resolve_tone_icon(resolved_tone))}</div>'

    render_html_block(
        f"""
        <div class="fea-section-header fea-tone-{resolved_tone}">
            <div class="fea-section-title-wrap">
                {icon_html}
                <div>
                    <h3>{html_text(title)}</h3>
                    {description_html}
                </div>
            </div>
            {action_html}
        </div>
        """
    )


def render_badge(label: str, tone: str = "neutral", variant: str | None = None) -> None:
    """Render one reusable badge."""
    resolved_tone = tone_class(variant or tone)
    render_html_block(
        f'<span class="fea-badge method-badge fea-badge-{resolved_tone}">'
        f'<span class="fea-badge-dot"></span>{html_text(label)}</span>'
    )


def render_badges(items: list[tuple[str, str]]) -> None:
    """Render multiple badges in a single safe HTML block."""
    if not items:
        return

    parts = [
        f'<span class="fea-badge method-badge fea-badge-{tone_class(tone)}">'
        f'<span class="fea-badge-dot"></span>{html_text(label)}</span>'
        for label, tone in items
    ]
    render_html_block(f'<div class="fea-badges-row">{"".join(parts)}</div>')


def render_context_bar(context: list[dict[str, object]] | dict[str, object]) -> None:
    """Render one compact contextual bar."""
    if not context:
        return

    items = (
        [{"label": key, "value": value} for key, value in context.items()]
        if isinstance(context, dict)
        else context
    )

    parts = []
    for item in items:
        label = item.get("label", "")
        value = item.get("value", "-")
        item_icon = item.get("icon")
        icon_html = icon_svg(str(item_icon), "fea-context-icon") if item_icon else ""
        parts.append(
            f'<div class="fea-context-item">{icon_html}<span>{html_text(label)}</span>'
            f'<strong>{html_text(value)}</strong></div>'
        )

    render_html_block(f'<div class="fea-context-bar context-bar">{"".join(parts)}</div>')


def render_page_intro(title: str, description: str) -> None:
    """Render a consistent page title and short description."""
    render_page_header(title, subtitle=description)


def navigate_to(view_name: str) -> None:
    """Request a top-level view change."""
    st.session_state["_requested_active_view"] = canonical_view_name(view_name)
    st.rerun()
