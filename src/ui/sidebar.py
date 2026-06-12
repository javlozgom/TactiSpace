from __future__ import annotations

from textwrap import dedent

import pandas as pd
import streamlit as st

from src.repositories.data_repository import load_match_labels
from src.services.filter_service import filter_events, get_filter_options
from src.core.models.player_labels import build_player_label_maps, get_player_display_name
from src.ui.components import icon_svg, render_pill_selector
from src.ui.navigation_config import NAV_OPTIONS, VIEW_ICONS, canonicalize_view_name, repair_view_text

def _is_selectable_player_name(player_name: object) -> bool:
    """Return whether a player name should appear in the global player selector."""
    if player_name is None or pd.isna(player_name):
        return False
    normalized = str(player_name).strip()
    return bool(normalized) and normalized.lower() != "unknown"


@st.cache_data(show_spinner=False)
def _get_cached_match_labels() -> dict[str, str]:
    """Cache readable match labels for sidebar filters."""
    return load_match_labels()


def _on_team_change() -> None:
    st.session_state["player_filter"] = "Todos"


def _on_match_change() -> None:
    return None


def _on_player_change() -> None:
    player_name = st.session_state.get("player_filter", "Todos")
    player_team_map = st.session_state.get("_player_team_map", {})
    if player_name != "Todos" and player_name in player_team_map:
        st.session_state["team_filter"] = player_team_map[player_name]


def reset_filter_state(events_df: pd.DataFrame) -> None:
    """Reset global filters to the dataset default state."""
    options = get_filter_options(events_df)
    st.session_state["match_filter"] = "Todos"
    st.session_state["team_filter"] = "Todos"
    st.session_state["player_filter"] = "Todos"
    st.session_state["minute_filter"] = (options["min_minute"], options["max_minute"])
    st.session_state["filters_applied"] = False


def request_filter_reset() -> None:
    """Mark the filter state to be reset on the next rerun."""
    st.session_state["_reset_filters_requested"] = True


def _format_nav_label(view_name: str) -> str:
    """Return a compact navigation label with the requested emoji."""
    icon = VIEW_ICONS.get(view_name, "\U0001f539")
    return view_name if view_name.startswith(icon) else f"{icon} {view_name}"


def _render_filter_label(icon_name: str, title: str, help_text: str) -> None:
    """Render a visual label while the native widget keeps its accessible label."""
    st.markdown(
        f"""
        <div class="fea-filter-label">
            <span class="fea-filter-label-icon">{icon_svg(icon_name, "fea-filter-icon")}</span>
            <span>{title}</span>
            <small>{help_text}</small>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_filter_summary(events_count: int, players_count: int, teams_count: int, matches_count: int) -> None:
    """Render the current filtered counts in the sidebar."""
    events_360_count = st.session_state.get("_visible_spatial_events")
    events_360_html = ""
    if isinstance(events_360_count, int):
        events_360_html = dedent(
            f"""
            <div class="fea-filter-summary-item">
                {icon_svg("eye", "fea-filter-summary-icon")}
                <span>Eventos 360</span>
                <strong>{events_360_count:,}</strong>
            </div>
            """
        ).strip()
    st.markdown(
        dedent(
            f"""
            <div class="fea-filter-summary">
                <h4>Contexto filtrado</h4>
                <div class="fea-filter-summary-item">
                    {icon_svg("list", "fea-filter-summary-icon")}
                    <span>Eventos filtrados</span>
                    <strong>{events_count:,}</strong>
                </div>
                <div class="fea-filter-summary-item">
                    {icon_svg("users", "fea-filter-summary-icon")}
                    <span>Jugadores</span>
                    <strong>{players_count:,}</strong>
                </div>
                <div class="fea-filter-summary-item">
                    {icon_svg("shield", "fea-filter-summary-icon")}
                    <span>Equipos</span>
                    <strong>{teams_count:,}</strong>
                </div>
                <div class="fea-filter-summary-item">
                    {icon_svg("map-pin", "fea-filter-summary-icon")}
                    <span>Partidos</span>
                    <strong>{matches_count:,}</strong>
                </div>
                {events_360_html}
            </div>
            """
        ).strip(),
        unsafe_allow_html=True,
    )


def _render_performance_badges() -> None:
    """Render stable performance constraints used by the app."""
    st.markdown(
        """
        <div class="fea-filter-performance">
            <h4>Rendimiento app</h4>
            <div class="fea-badges-row">
                <span class="fea-badge fea-badge-blue"><span class="fea-badge-dot"></span>st.cache_data</span>
                <span class="fea-badge fea-badge-green"><span class="fea-badge-dot"></span>MAX_PLOT_EVENTS = 600</span>
                <span class="fea-badge fea-badge-purple"><span class="fea-badge-dot"></span>Carga 360 lazy</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_navigation_legacy() -> str:
    """Render the top-level navigation."""
    if st.session_state.get("active_view") not in NAV_OPTIONS:
        st.session_state["active_view"] = NAV_OPTIONS[0]

    if hasattr(st, "segmented_control"):
        selected_view = st.segmented_control(
            "Navegación principal",
            NAV_OPTIONS,
            key="active_view",
            label_visibility="collapsed",
            selection_mode="single",
            format_func=_format_nav_label,
            width="stretch",
        )
        return selected_view or st.session_state["active_view"]

    st.radio(
        "Navegación principal",
        NAV_OPTIONS,
        key="active_view",
        horizontal=True,
        label_visibility="collapsed",
        format_func=_format_nav_label,
    )
    return st.session_state["active_view"]


def render_sidebar(df: pd.DataFrame) -> dict:
    """Render the global filter panel and return current values."""
    with st.container(key="global_filters_panel"):
        st.markdown(
            f"""
            <div class="fea-filter-title-block">
                <div class="fea-filter-title-icon">{icon_svg("filter", "fea-filter-title-svg")}</div>
                <div>
                    <h3>Filtros globales</h3>
                    <p>Define el partido, equipo, jugador y tramo temporal que se aplican a todas las vistas.</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        player_team_map = (
            df[df["player"].map(_is_selectable_player_name)][["player", "team"]]
            .dropna()
            .drop_duplicates(subset=["player"])
            .set_index("player")["team"]
            .to_dict()
        )
        st.session_state["_player_team_map"] = player_team_map

        full_to_display, _ = build_player_label_maps(df)
        match_labels = _get_cached_match_labels()

        current_match = st.session_state.get("match_filter", "Todos")
        current_team = st.session_state.get("team_filter", "Todos")
        current_player = st.session_state.get("player_filter", "Todos")
        inferred_player_team = player_team_map.get(current_player) if current_player != "Todos" else None
        effective_team_for_match = current_team if current_team != "Todos" else inferred_player_team

        match_source_df = df.copy()
        if effective_team_for_match:
            match_source_df = match_source_df[match_source_df["team"] == effective_team_for_match]

        match_options = ["Todos", *sorted(match_source_df["match_id"].dropna().astype(str).unique().tolist())]
        normalized_match = current_match if current_match in match_options else "Todos"
        if normalized_match != current_match:
            st.session_state["match_filter"] = normalized_match

        _render_filter_label(
            "map-pin",
            "Partido",
            "Selecciona un encuentro concreto o conserva toda la Euro 2024.",
        )
        selected_match = st.selectbox(
            "Partido",
            match_options,
            key="match_filter",
            on_change=_on_match_change,
            label_visibility="collapsed",
            help="Control global: todas las pestañas usarán este partido.",
            format_func=lambda match_id: (
                "Todos los partidos"
                if match_id == "Todos"
                else match_labels.get(str(match_id), f"Partido {match_id}")
            ),
        )

        team_source_df = df.copy()
        if selected_match != "Todos":
            team_source_df = team_source_df[team_source_df["match_id"].astype(str) == str(selected_match)]
        if inferred_player_team is not None:
            team_source_df = team_source_df[team_source_df["team"] == inferred_player_team]

        team_options = ["Todos", *sorted(team_source_df["team"].dropna().astype(str).unique().tolist())]
        normalized_team = st.session_state.get("team_filter", "Todos")
        if normalized_team not in team_options:
            normalized_team = "Todos"
            st.session_state["team_filter"] = normalized_team

        _render_filter_label(
            "shield",
            "Equipo",
            "Filtra eventos de una selección nacional concreta.",
        )
        selected_team = st.selectbox(
            "Equipo",
            team_options,
            key="team_filter",
            on_change=_on_team_change,
            label_visibility="collapsed",
            help="Al elegir un equipo, el selector de jugadores se ajusta a esa plantilla.",
        )

        player_source_df = df.copy()
        if selected_match != "Todos":
            player_source_df = player_source_df[player_source_df["match_id"].astype(str) == str(selected_match)]
        if selected_team != "Todos":
            player_source_df = player_source_df[player_source_df["team"] == selected_team]
        player_source_df = player_source_df[player_source_df["player"].map(_is_selectable_player_name)]

        current_player_value = st.session_state.get("player_filter", "Todos")
        player_values = sorted(player_source_df["player"].dropna().astype(str).unique().tolist())
        if current_player_value != "Todos" and current_player_value not in player_values:
            player_values = sorted({*player_values, current_player_value})

        player_options = ["Todos", *player_values]
        normalized_player = current_player_value if current_player_value in player_options else "Todos"
        if normalized_player != current_player_value:
            st.session_state["player_filter"] = normalized_player

        _render_filter_label(
            "users",
            "Jugador",
            "Aísla las acciones de un jugador; si eliges uno, el equipo se sincroniza.",
        )
        selected_player = st.selectbox(
            "Jugador",
            player_options,
            key="player_filter",
            on_change=_on_player_change,
            label_visibility="collapsed",
            help="Usa 'Todos' para mantener el contexto colectivo.",
            format_func=lambda player_name: (
                "Todos" if player_name == "Todos" else get_player_display_name(player_name, full_to_display)
            ),
        )

        minute_df = filter_events(
            df,
            match_id=selected_match,
            team=selected_team,
            player=selected_player,
        )
        minute_options = get_filter_options(minute_df)

        current_minute_filter = st.session_state.get("minute_filter")
        valid_minute_range = (minute_options["min_minute"], minute_options["max_minute"])
        if (
            current_minute_filter is None
            or len(current_minute_filter) != 2
            or current_minute_filter[0] < minute_options["min_minute"]
            or current_minute_filter[1] > minute_options["max_minute"]
            or current_minute_filter[0] > current_minute_filter[1]
        ):
            st.session_state["minute_filter"] = valid_minute_range

        _render_filter_label(
            "clock",
            "Minutos",
            "Acota el análisis a un intervalo del partido.",
        )
        minute_range = st.slider(
            "Minutos",
            min_value=minute_options["min_minute"],
            max_value=minute_options["max_minute"],
            key="minute_filter",
            label_visibility="collapsed",
            help="Rango temporal aplicado después de partido, equipo y jugador.",
        )

        context_df = filter_events(
            df,
            match_id=selected_match,
            team=selected_team,
            player=selected_player,
            minute_range=minute_range,
        )

        _render_filter_summary(
            events_count=len(context_df),
            players_count=context_df["player"].nunique() if "player" in context_df.columns else 0,
            teams_count=context_df["team"].nunique() if "team" in context_df.columns else 0,
            matches_count=context_df["match_id"].nunique() if "match_id" in context_df.columns else 0,
        )
        _render_performance_badges()

        with st.container(key="global_filters_actions"):
            if st.button("Reset filtros", width="stretch", icon=":material/refresh:"):
                request_filter_reset()
                st.rerun()

    return {
        "selected_match": selected_match,
        "selected_team": selected_team,
        "selected_player": selected_player,
        "minute_range": minute_range,
    }


def _canonical_nav_view(view_name: object) -> str:
    """Resolve current and legacy view names into the canonical navigation label."""
    repaired = repair_view_text(view_name)
    return canonicalize_view_name(repaired)


def _nav_slug(view_name: str) -> str:
    """Return a CSS/widget-safe slug for one navigation item."""
    slug = (
        view_name.lower()
        .replace("á", "a")
        .replace("é", "e")
        .replace("í", "i")
        .replace("ó", "o")
        .replace("ú", "u")
        .replace("ñ", "n")
        .replace(",", "")
        .replace("/", "_")
        .replace("️", "")
        .replace(" ", "_")
    )
    return "".join(char for char in slug if char.isalnum() or char == "_")


def _format_nav_label(view_name: str) -> str:
    """Return the requested visual label for one navigation item."""
    icon = VIEW_ICONS.get(view_name, "\U0001f539")
    return view_name if view_name.startswith(icon) else f"{icon} {view_name}"


def render_navigation() -> str:
    """Render a grid-style top-level navigation using Streamlit state."""
    st.session_state["active_view"] = _canonical_nav_view(st.session_state.get("active_view", NAV_OPTIONS[0]))
    formatted_options = [_format_nav_label(view_name) for view_name in NAV_OPTIONS]
    label_to_view = dict(zip(formatted_options, NAV_OPTIONS, strict=False))
    selected_label_state = st.session_state.get("active_view_nav_selector")
    selected_view_state = label_to_view.get(selected_label_state)
    if selected_view_state in NAV_OPTIONS:
        st.session_state["active_view"] = selected_view_state
    current_label = _format_nav_label(st.session_state["active_view"])
    if st.session_state.get("active_view_nav_selector") not in formatted_options:
        st.session_state["active_view_nav_selector"] = (
            current_label if current_label in formatted_options else formatted_options[0]
        )
    selected_label = render_pill_selector(
        "Navegación principal",
        formatted_options,
        key="active_view_nav_selector",
        columns_per_row=4,
    )
    st.session_state["active_view"] = label_to_view.get(selected_label, st.session_state["active_view"])
    return st.session_state["active_view"]
