from __future__ import annotations

from datetime import datetime

import pandas as pd
import streamlit as st

from src.config.settings import DEFAULT_FREEZE_FRAME_PATH
from src.repositories.data_repository import load_match_labels
from src.core.metrics.basic import calculate_player_summary
from src.services.spatial_service import count_visible_spatial_events
from src.ui.components import (
    dataframe_preview,
    icon_svg,
    navigate_to,
    render_context_bar,
    render_empty_state,
    render_info_box,
    render_kpi_grid,
    render_page_header,
    render_plot_card,
    render_section_header,
)
from src.ui.components.html import render_html_block
from src.ui.components.visualizations import plot_event_heatmap, plot_events_on_pitch


def _safe_metric(metrics: dict[str, object], key: str, default: object = 0) -> object:
    """Safely get one metric from the metrics dictionary."""
    if not isinstance(metrics, dict):
        return default
    return metrics.get(key, default)


@st.cache_data(show_spinner=False)
def _get_freeze_frame_event_index(default_path: str) -> pd.DataFrame:
    """Load a minimal cached index of events that have associated 360 data."""
    try:
        freeze_frame_index = pd.read_parquet(default_path, columns=["event_id"])
    except Exception:
        return pd.DataFrame(columns=["event_id"])

    if "event_id" not in freeze_frame_index.columns:
        return pd.DataFrame(columns=["event_id"])

    freeze_frame_index = freeze_frame_index.dropna(subset=["event_id"]).copy()
    freeze_frame_index["event_id"] = freeze_frame_index["event_id"].astype(str)
    return freeze_frame_index.drop_duplicates(subset=["event_id"]).reset_index(drop=True)


def _count_events_with_360(events_df: pd.DataFrame, freeze_frames_df: pd.DataFrame | None = None) -> int:
    """Best-effort count of events with freeze-frame / 360 support."""
    if freeze_frames_df is not None and not freeze_frames_df.empty:
        if "event_id" in freeze_frames_df.columns and "event_id" in events_df.columns:
            return count_visible_spatial_events(events_df, freeze_frames_df)
        if "event_id" in freeze_frames_df.columns:
            return int(freeze_frames_df["event_id"].dropna().astype(str).nunique())

    if events_df is None or events_df.empty:
        return 0

    if "event_id" in events_df.columns:
        freeze_frame_index = _get_freeze_frame_event_index(DEFAULT_FREEZE_FRAME_PATH)
        if not freeze_frame_index.empty:
            visible_event_ids = set(events_df["event_id"].dropna().astype(str).tolist())
            if visible_event_ids:
                return int(freeze_frame_index["event_id"].isin(visible_event_ids).sum())

    candidate_columns = [
        "has_freeze_frame",
        "freeze_frame_available",
        "has_360",
        "has_three_sixty",
        "visible_area_available",
        "three_sixty_event_id",
    ]

    for column in candidate_columns:
        if column not in events_df.columns:
            continue
        if column == "three_sixty_event_id":
            return int(events_df[column].notna().sum())
        try:
            return int(events_df[column].fillna(False).astype(bool).sum())
        except Exception:
            continue

    return 0


def _resolve_scope_value(df: pd.DataFrame, column: str, fallback: str = "Todos") -> str:
    """Return one human-readable value when the filtered scope collapses to a single item."""
    if df.empty or column not in df.columns:
        return fallback

    unique_values = [
        str(value).strip()
        for value in df[column].dropna().astype(str).unique().tolist()
        if str(value).strip()
    ]
    if len(unique_values) == 1:
        return unique_values[0]
    return fallback


@st.cache_data(show_spinner=False)
def _get_match_labels() -> dict[str, str]:
    """Cache readable labels for match identifiers."""
    return load_match_labels()


def _format_match_label(match_id: object, match_labels: dict[str, str]) -> str:
    """Return a compact match label with teams and phase."""
    if match_id in {None, "", "Todos"}:
        return "Todos"

    raw_label = match_labels.get(str(match_id), f"Partido {match_id}")
    label_parts = [part.strip() for part in str(raw_label).split("|") if str(part).strip()]
    if len(label_parts) >= 3:
        return f"{label_parts[0]} | {label_parts[-1]}"
    return label_parts[0] if label_parts else str(raw_label)


def _render_feature_cards() -> None:
    """Render static feature cards."""
    cards = [
        (
            "bar-chart",
            "Resumen",
            "Consulta rápidamente el volumen de eventos, perfiles de jugador y mapas prioritarios del contexto filtrado.",
        ),
        (
            "scale",
            "Comparativa",
            "Compara jugadores, equipos y contextos mediante métricas, tablas y percentiles.",
        ),
        (
            "map",
            "Voronoi, Delaunay y sugerencia de pase",
            "Estudia freeze-frames, Voronoi, Delaunay y recomendaciones de pase de forma interpretable.",
        ),
    ]

    cards_html = [
        (
            f'<div class="fea-feature-card"><div class="fea-feature-icon">{icon_svg(icon_name)}</div>'
            f"<h4>{title}</h4><p>{body}</p></div>"
        )
        for icon_name, title, body in cards
    ]
    render_html_block(f'<div class="fea-card-grid fea-card-grid-4">{"".join(cards_html)}</div>')


def _render_flow_cards() -> None:
    """Render the recommended analysis flow."""
    flow = [
        ("1", "Filtra el contexto", "Selecciona partido, equipo, jugador y tramo temporal."),
        ("2", "Lee el resumen", "Empieza por KPIs, eventos clave y distribución general."),
        ("3", "Profundiza", "Usa Comparativa, Eventos y la sugerencia de pase para detectar patrones."),
        ("4", "Valida espacialmente", "Contrasta casos con freeze-frame, Voronoi y Delaunay."),
    ]

    cards_html = [
        (
            f'<div class="fea-step-card"><div class="fea-step-number">{number}</div>'
            f"<h4>{title}</h4><p>{body}</p></div>"
        )
        for number, title, body in flow
    ]
    render_html_block(f'<div class="fea-card-grid fea-card-grid-4">{"".join(cards_html)}</div>')


def _render_architecture_cards() -> None:
    """Render the real project pipeline as compact architecture cards."""
    steps = [
        ("Raw StatsBomb", "events, lineups, three_sixty y matches.json."),
        ("Scripts offline", "Normalización reproducible fuera del arranque de Streamlit."),
        ("Parquets normalizados", "events_normalized, lineups_normalized y three_sixty_normalized."),
        ("App Streamlit", "Orquestación, filtros globales, cache y navegación por vistas."),
        ("UI + módulos", "Métricas, comparativas, Voronoi, Delaunay, visualizaciones y depuración."),
    ]
    cards_html = []
    for index, (title, body) in enumerate(steps, start=1):
        cards_html.append(
            f'<div class="fea-step-card"><div class="fea-step-number">{index}</div>'
            f"<h4>{title}</h4><p>{body}</p></div>"
        )
    render_html_block(f'<div class="fea-card-grid fea-card-grid-4">{"".join(cards_html)}</div>')


def _render_demo_cards() -> None:
    """Render example demo cards."""
    cards = [
        (
            "alert-triangle",
            "Caso demo: pérdida en salida",
            "Ejemplo guiado para estudiar una pérdida y su contexto inmediato dentro de la posesión.",
        ),
        (
            "route",
            "Caso demo: progresión de jugador",
            "Vista pensada para explicar métricas, mapas y comparativa de rendimiento.",
        ),
        (
            "map",
            "Caso demo: Delaunay vs scoring",
            "Comparación entre conectividad espacial y recomendación heurística de pase.",
        ),
    ]

    cards_html = [
        (
            f'<div class="fea-demo-card"><div class="fea-demo-icon">{icon_svg(icon_name)}</div>'
            f"<h4>{title}</h4><p>{body}</p></div>"
        )
        for icon_name, title, body in cards
    ]
    render_html_block(f'<div class="fea-card-grid fea-card-grid-3">{"".join(cards_html)}</div>')


def _render_quick_actions() -> None:
    """Render quick navigation buttons."""
    row_1 = st.columns(2)
    with row_1[0]:
        if st.button("Ir a Resumen", key="home_go_summary", width="stretch", icon=":material/bar_chart:"):
            navigate_to("Resumen")
    with row_1[1]:
        if st.button("Ir a Comparativa", key="home_go_comparison", width="stretch", icon=":material/compare_arrows:"):
            navigate_to("Comparativa")

    if st.button(
        "Ir a Voronoi, Delaunay y sugerencia de pase",
        key="home_go_spatial",
        width="stretch",
        icon=":material/map:",
    ):
        navigate_to("Voronoi, Delaunay y sugerencia de pase")


def _render_terms_guide() -> None:
    """Render concise football and spatial-analysis definitions for non-experts."""
    terms = [
        (
            "Pérdida",
            "Acción en la que el equipo deja de conservar el balón: pase fallido, mal control, robo o error.",
        ),
        (
            "Presión",
            "Acción defensiva para dificultar que el rival controle, conduzca o pase con comodidad.",
        ),
        (
            "Freeze-frame / 360",
            "Instantánea de StatsBomb con jugadores visibles alrededor del evento en el momento de la acción.",
        ),
        (
            "Voronoi",
            "Modelo espacial que divide el campo según qué jugador está más cerca de cada zona.",
        ),
        (
            "Delaunay",
            "Red de vecindad entre jugadores usada para estudiar conexiones espaciales cercanas.",
        ),
        (
            "Secuencia",
            "Cadena temporal de eventos dentro de una misma posesión, antes o después de una acción clave.",
        ),
    ]
    cards_html = []
    for title, body in terms:
        cards_html.append(f'<div class="fea-term-card"><h4>{title}</h4><p>{body}</p></div>')
    st.markdown(f'<div class="fea-term-grid">{"".join(cards_html)}</div>', unsafe_allow_html=True)


def render_home_view(
    filtered_df: pd.DataFrame,
    events_df: pd.DataFrame,
    freeze_frames_df: pd.DataFrame | None,
    metrics: dict[str, object],
    selected_match: str = "Todos",
    selected_team: str = "Todos",
    selected_player: str = "Todos",
    max_plot_events: int = 600,
    spatial_events_count: int | None = None,
) -> None:
    """Render the landing view."""

    with st.container(key="home_intro_band"):
        match_labels = _get_match_labels()
        resolved_match_id = _resolve_scope_value(filtered_df, "match_id", selected_match)

        st.markdown(
            """
            <div class="fea-hero">
                <h2>TactiSpace</h2>
                <p>
                    Aplicación de TFG orientada al análisis visual, contextual y espacial de eventos de fútbol
                    con datos de StatsBomb Euro 2024. Integra eventos, lineups, freeze-frames y herramientas
                    interpretables como Voronoi, Delaunay y scoring heurístico para recomendaciones de pase.
                </p>
                <div class="fea-hero-badges">
                    <span class="fea-badge fea-badge-blue"><span class="fea-badge-dot"></span>Eventos StatsBomb</span>
                    <span class="fea-badge fea-badge-teal"><span class="fea-badge-dot"></span>Voronoi · Delaunay · sugerencia de pase</span>
                    <span class="fea-badge fea-badge-orange"><span class="fea-badge-dot"></span>Datos 360</span>
                    <span class="fea-badge fea-badge-purple"><span class="fea-badge-dot"></span>Comparativas</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        render_context_bar(
            [
                {"label": "Partido", "value": _format_match_label(resolved_match_id, match_labels)},
                {"label": "Equipo", "value": _resolve_scope_value(filtered_df, "team", selected_team)},
                {"label": "Jugador", "value": _resolve_scope_value(filtered_df, "player", selected_player)},
                {"label": "Eventos filtrados", "value": f"{len(filtered_df):,}"},
            ]
        )

        visible_matches = filtered_df["match_id"].nunique() if "match_id" in filtered_df.columns and not filtered_df.empty else 0
        filtered_players = filtered_df["player"].nunique() if "player" in filtered_df.columns and not filtered_df.empty else 0
        passes = int(_safe_metric(metrics, "total_passes", 0))
        fallback_spatial_events = _count_events_with_360(filtered_df, freeze_frames_df)
        spatial_events = (
            spatial_events_count
            if spatial_events_count not in {None, 0} or fallback_spatial_events == 0
            else fallback_spatial_events
        )

        render_kpi_grid(
            [
                {
                    "label": "Partidos",
                    "value": visible_matches,
                    "help": "Visibles en el contexto",
                    "tone": "blue",
                    "icon": "map-pin",
                },
                {
                    "label": "Eventos",
                    "value": f"{len(filtered_df):,}",
                    "help": "Contexto activo",
                    "tone": "green",
                    "icon": "list",
                },
                {
                    "label": "Jugadores",
                    "value": filtered_players,
                    "help": "Con eventos visibles",
                    "tone": "purple",
                    "icon": "users",
                },
                {
                    "label": "Eventos con 360",
                    "value": f"{spatial_events:,}",
                    "help": "Registros 360 asociados al contexto filtrado",
                    "tone": "orange",
                    "icon": "eye",
                },
            ]
        )

    render_section_header(
        "Arquitectura del proyecto",
        "Flujo real de datos y módulos de la aplicación, sin datos simulados.",
    )
    _render_architecture_cards()
    st.divider()

    render_section_header(
        "¿Qué puedes hacer en la app?",
        "Esta aplicación combina exploración descriptiva, análisis contextual y estudio espacial.",
    )
    _render_feature_cards()
    st.divider()

    render_section_header(
        "Flujo recomendado",
        "Ruta sugerida para recorrer la app durante la demo o la defensa del TFG.",
    )
    _render_flow_cards()
    st.divider()

    render_section_header(
        "Guía rápida de conceptos",
        "Definiciones breves para que la app sea comprensible sin conocimiento táctico avanzado.",
        icon="help-circle",
        tone="teal",
    )
    _render_terms_guide()
    st.divider()

    render_section_header(
        "Casos demo sugeridos",
        "Puntos de entrada útiles para enseñar rápidamente el valor de la herramienta.",
    )
    _render_demo_cards()
    st.divider()

    top_left, top_right = st.columns([1.4, 1.0], vertical_alignment="top")

    with top_left:
        render_section_header(
            "Mapa general de eventos",
            "Representación espacial básica del contexto filtrado.",
        )

        if filtered_df.empty:
            render_empty_state(
                "No hay eventos para visualizar en la página de inicio.",
                "Prueba a ampliar los filtros globales.",
            )
        else:
            plot_df = filtered_df.head(max_plot_events).copy()
            fig = plot_events_on_pitch(
                plot_df,
                title="Eventos del contexto activo",
                draw_movements=True,
                show_legend=True,
            )
            render_plot_card(
                "Eventos del contexto activo",
                fig,
                "Se muestran los primeros eventos del contexto filtrado para mantener rendimiento y legibilidad.",
            )

    with top_right:
        render_section_header(
            "Estado del contexto",
            "Resumen interpretativo rápido de lo que se está analizando.",
        )

        render_info_box(
            "Contexto actual",
            (
                f"Partido: {_format_match_label(resolved_match_id, match_labels)}. "
                f"Equipo: {_resolve_scope_value(filtered_df, 'team', selected_team)}. "
                f"Jugador: {_resolve_scope_value(filtered_df, 'player', selected_player)}. "
                f"Pases detectados: {passes:,}."
            ),
            tone="info",
        )
        st.divider()

        render_section_header(
            "Accesos rápidos",
            "Navega rápidamente hacia las vistas más importantes.",
        )
        _render_quick_actions()
        st.divider()

        render_info_box(
            "Lectura recomendada",
            (
                "Empieza por el resumen y la comparativa para detectar patrones. "
                "Después revisa pérdidas relevantes y utiliza el análisis espacial "
                "para contrastar el pase fallido con las alternativas sugeridas."
            ),
            tone="neutral",
        )

    st.divider()

    bottom_left, bottom_right = st.columns(2, vertical_alignment="top")

    with bottom_left:
        render_section_header(
            "Mapa de calor general",
            "Distribución espacial agregada de los eventos visibles.",
        )

        if filtered_df.empty:
            render_empty_state(
                "No hay eventos para construir el mapa de calor.",
                "Selecciona un contexto con eventos.",
            )
        else:
            fig = plot_event_heatmap(filtered_df.head(max_plot_events))
            render_plot_card(
                "Mapa de calor",
                fig,
                "Visión agregada de la concentración espacial de eventos en el contexto activo.",
            )

    with bottom_right:
        render_section_header(
            "Resumen por jugador",
            "Vista tabular del rendimiento agregado por jugador.",
        )

        summary_df = calculate_player_summary(filtered_df)
        if summary_df.empty:
            render_empty_state(
                "No hay datos suficientes para construir el resumen por jugador.",
                "Prueba a quitar el filtro de jugador o a ampliar el rango temporal.",
            )
        else:
            max_rows = len(summary_df) if selected_player != "Todos" else 12
            dataframe_preview(summary_df, "Resumen por jugador", max_rows=max_rows)

    st.divider()

    render_context_bar(
        [
            {"label": "Datos", "value": "StatsBomb Euro 2024"},
            {"label": "Partidos visibles", "value": filtered_df["match_id"].nunique() if "match_id" in filtered_df.columns and not filtered_df.empty else 0},
            {"label": "Equipos visibles", "value": filtered_df["team"].nunique() if "team" in filtered_df.columns and not filtered_df.empty else 0},
            {"label": "Jugadores visibles", "value": filtered_players},
            {"label": "Actualizado", "value": datetime.now().strftime("%d/%m/%Y %H:%M")},
        ]
    )
