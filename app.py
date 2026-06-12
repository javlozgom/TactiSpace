from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st
import src.repositories  # noqa: F401

PROJECT_ROOT = Path(__file__).resolve().parent

project_root_path = str(PROJECT_ROOT)
if project_root_path not in sys.path:
    sys.path.insert(0, project_root_path)

from src.config.settings import (  # noqa: E402
    DATA_SCHEMA_VERSION,
    DEFAULT_DATA_PATH,
    DEFAULT_FREEZE_FRAME_PATH,
    DEFAULT_LINEUPS_PATH,
    NORMALIZED_DATA_PATH,
)
from src.services.context_service import build_view_contexts  # noqa: E402
from src.state.session import (  # noqa: E402
    clear_filter_reset_request,
    consume_filter_reset_request,
    get_active_view,
    has_minute_filter,
    initialize_session_state,
    mark_app_bootstrapped,
    mark_default_data_for_next_run,
    resolve_uploaded_file_bytes,
    set_active_view,
    store_last_filtered_df,
    store_visible_spatial_events,
)
from src.ui.cache import get_freeze_frames_cached, get_normalized_events_cached  # noqa: E402
from src.ui.components import render_app_header  # noqa: E402
from src.ui.layout import update_loading_overlay  # noqa: E402
from src.ui.navigation import render_active_view  # noqa: E402
from src.ui.navigation_config import EVENT_ANALYSIS_VIEW  # noqa: E402
from src.ui.sidebar import NAV_OPTIONS, _canonical_nav_view, render_navigation, render_sidebar, reset_filter_state  # noqa: E402
from src.ui.styles import apply_app_styles  # noqa: E402
from src.ui.views.event_analysis import event_analysis_requires_spatial_data  # noqa: E402


def main() -> None:
    """Run the Streamlit application."""
    st.set_page_config(page_title="TactiSpace", layout="wide")
    apply_app_styles()
    initialize_session_state(NAV_OPTIONS)

    overlay_placeholder = st.empty()
    header_placeholder = st.empty()
    nav_placeholder = st.empty()
    update_loading_overlay(overlay_placeholder, 5, "Inicializando la interfaz")

    update_loading_overlay(overlay_placeholder, 15, "Preparando fuente de datos")
    uploaded_file_bytes = resolve_uploaded_file_bytes()

    try:
        update_loading_overlay(overlay_placeholder, 35, "Cargando y normalizando eventos")
        events_df = get_normalized_events_cached(
            DEFAULT_DATA_PATH,
            NORMALIZED_DATA_PATH,
            DEFAULT_LINEUPS_PATH,
            uploaded_file_bytes,
            DATA_SCHEMA_VERSION,
        )
    except Exception as exc:  # pragma: no cover
        st.error(f"No se pudieron cargar los datos: {exc}")
        st.stop()

    if uploaded_file_bytes is None and not Path(NORMALIZED_DATA_PATH).exists():
        st.caption("Sugerencia: ejecuta `python scripts/build_all_normalized.py` para acelerar la carga inicial.")

    if consume_filter_reset_request():
        reset_filter_state(events_df)
        clear_filter_reset_request()

    if not has_minute_filter():
        reset_filter_state(events_df)

    active_view = _canonical_nav_view(get_active_view(NAV_OPTIONS[0]))
    if active_view not in NAV_OPTIONS:
        active_view = NAV_OPTIONS[0]
        set_active_view(active_view)

    filter_col, content_col = st.columns([0.22, 0.78], gap="large", vertical_alignment="top")

    update_loading_overlay(overlay_placeholder, 55, "Construyendo filtros")
    with filter_col:
        filter_state = render_sidebar(events_df)

    selected_match = filter_state["selected_match"]
    selected_team = filter_state["selected_team"]
    selected_player = filter_state["selected_player"]
    selected_minutes = filter_state["minute_range"]

    update_loading_overlay(overlay_placeholder, 72, "Aplicando filtros y calculando métricas")
    initial_filtered_df = pd.DataFrame()
    initial_spatial_match_ids = None
    context = build_view_contexts(
        events_df,
        selected_match=selected_match,
        selected_team=selected_team,
        selected_player=selected_player,
        selected_minutes=selected_minutes,
        freeze_frames_df=None,
    )
    filtered_df = context["filtered_df"]
    if isinstance(filtered_df, pd.DataFrame):
        initial_filtered_df = filtered_df
    initial_spatial_match_ids = context["spatial_match_ids"]

    freeze_frames_df = None
    if active_view == EVENT_ANALYSIS_VIEW and event_analysis_requires_spatial_data():
        try:
            freeze_frames_df = get_freeze_frames_cached(DEFAULT_FREEZE_FRAME_PATH, initial_spatial_match_ids)
        except Exception:  # pragma: no cover
            freeze_frames_df = pd.DataFrame()

    context = build_view_contexts(
        events_df,
        selected_match=selected_match,
        selected_team=selected_team,
        selected_player=selected_player,
        selected_minutes=selected_minutes,
        freeze_frames_df=freeze_frames_df,
    )
    filtered_df = context["filtered_df"]
    position_context_df = context["position_context_df"]
    comparative_context_df = context["comparative_context_df"]
    metrics = context["metrics"]
    spatial_match_ids = context["spatial_match_ids"]
    visible_spatial_events = int(context["visible_spatial_events"])
    store_last_filtered_df(filtered_df if isinstance(filtered_df, pd.DataFrame) else initial_filtered_df)
    store_visible_spatial_events(visible_spatial_events)

    with header_placeholder.container():
        with st.container(key="app_header_fixed"):
            _, use_default_data = render_app_header(filtered_df)
        if use_default_data:
            mark_default_data_for_next_run()
            st.rerun()

    with nav_placeholder.container():
        with st.container(key="app_nav_fixed"):
            active_view = render_navigation()

    try:
        update_loading_overlay(overlay_placeholder, 88, "Renderizando panel principal")
        with content_col:
            with st.container(key="main_content_panel"):
                render_active_view(
                    active_view,
                    filtered_df=filtered_df,
                    events_df=events_df,
                    freeze_frames_df=freeze_frames_df,
                    metrics=metrics,
                    selected_match=selected_match,
                    selected_team=selected_team,
                    selected_player=selected_player,
                    position_context_df=position_context_df,
                    comparative_context_df=comparative_context_df,
                    spatial_match_ids=spatial_match_ids,
                    visible_spatial_events=visible_spatial_events,
                )

        mark_app_bootstrapped()
        update_loading_overlay(overlay_placeholder, 100, "Listo")
    except Exception as exc:  # pragma: no cover
        st.error(f"Se produjo un error al renderizar la vista: {exc}")
        st.exception(exc)
    finally:
        overlay_placeholder.empty()


if __name__ == "__main__":
    main()
