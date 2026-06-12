from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from src.core.spatial.pass_decision import DEFAULT_SCORING_PROFILE, resolve_scoring_profile
from src.repositories.data_repository import load_match_labels
from src.state import spatial as spatial_state
from src.ui.components import render_info_box
from src.ui.config.spatial_labels import DEFAULT_SPATIAL_PLOTS, SCORING_PROFILE_OPTIONS
from src.ui.views.spatial_formatters import safe_display, safe_int_like
from src.ui.views.spatial_utils import coalesce_event_value, extract_event_id

SPATIAL_DEMO_CASES_PATH = Path("data/processed/spatial_demo_cases.csv")


@st.cache_data(show_spinner=False)
def _get_match_labels() -> dict[str, str]:
    """Cache readable labels for match identifiers."""
    return load_match_labels()


def build_match_labels() -> dict[str, str]:
    """Expose cached match labels to external wrappers."""
    return _get_match_labels()


def render_spatial_view_controls() -> dict[str, object]:
    """Render high-level controls for the spatial view."""
    with st.container(border=True):
        scoring_profile = st.selectbox(
            "Perfil de scoring heurístico",
            options=SCORING_PROFILE_OPTIONS,
            index=SCORING_PROFILE_OPTIONS.index(DEFAULT_SCORING_PROFILE),
            key=spatial_state.SCORING_PROFILE,
        )
    return {
        "scoring_profile": resolve_scoring_profile(scoring_profile),
        "selected_plots": list(DEFAULT_SPATIAL_PLOTS),
    }


def render_scoring_profile_info_box(scoring_profile: str) -> None:
    """Render one concise orange info box describing the active scoring profile."""
    resolved_profile = resolve_scoring_profile(scoring_profile)
    body_by_profile = {
        "Conservador": (
            "Scoring heurístico conservador activo: se priorizan opciones más seguras, "
            "cercanas y con menor presión rival."
        ),
        "Intermedio": (
            "Scoring heurístico intermedio activo: se equilibran progresión, espacio disponible, "
            "presión rival y distancia de pase."
        ),
        "Arriesgado": (
            "Scoring heurístico arriesgado activo: se priorizan opciones más progresivas y con mayor "
            "ganancia espacial, aceptando mayor coste de pase."
        ),
    }
    render_info_box(
        f"Perfil activo: {resolved_profile}",
        body_by_profile[resolved_profile],
        tone="warning",
        icon="target",
    )


def filter_failed_passes_with_freeze_frame(
    failed_passes_df: pd.DataFrame,
    freeze_frames_df: pd.DataFrame,
) -> pd.DataFrame:
    """Keep only failed passes that have a corresponding freeze-frame event."""
    if failed_passes_df.empty or freeze_frames_df.empty:
        return pd.DataFrame(columns=failed_passes_df.columns)
    if "event_id" not in freeze_frames_df.columns:
        return pd.DataFrame(columns=failed_passes_df.columns)

    event_ids = set(freeze_frames_df["event_id"].dropna().astype(str).unique().tolist())
    event_id_col = next((candidate for candidate in ["event_id", "id"] if candidate in failed_passes_df.columns), None)
    if event_id_col is None:
        return pd.DataFrame(columns=failed_passes_df.columns)

    mask = failed_passes_df[event_id_col].astype(str).isin(event_ids)
    result = failed_passes_df[mask].copy()
    if "has_freeze_frame" not in result.columns:
        result["has_freeze_frame"] = True
    return result


def format_match_label(match_id: object, match_labels: dict[str, str]) -> str:
    """Return the full readable match label used in the global filters."""
    if match_id in {None, "", "Todos"}:
        return "Todos"
    return str(match_labels.get(str(match_id), f"Partido {match_id}"))


def format_failed_pass_label(event_row: pd.Series, match_labels: dict[str, str] | None = None) -> str:
    """Build a readable label for the failed-pass selector."""
    match_id = coalesce_event_value(event_row, ["match_id", "partido"])
    match_label = format_match_label(match_id, match_labels or _get_match_labels())
    team = safe_display(coalesce_event_value(event_row, ["possession_team", "team"]))
    minute = safe_int_like(event_row.get("minute"))
    second = safe_int_like(event_row.get("second"))
    player = event_row.get("player", "Jugador desconocido")

    def _normalize_selector_part(value: object) -> str:
        text = str(value)
        return text.replace("Ã‚Â·", "-").replace("Â·", "-").replace("  ", " ").strip()

    return (
        f"{_normalize_selector_part(match_label)} | {_normalize_selector_part(team)} | "
        f"{minute}:{second:02d} | {_normalize_selector_part(player)}"
    )


def render_failed_pass_selector(
    failed_passes_df: pd.DataFrame,
    preselected_event_id: str | None = None,
) -> int | None:
    """Render selection controls for one failed pass."""
    options = list(range(len(failed_passes_df)))
    if not options:
        return None

    default_index = resolve_default_selector_index(failed_passes_df, preselected_event_id)
    selected_index = st.selectbox(
        "Pase fallido a analizar",
        options,
        index=default_index,
        key=spatial_state.FAILED_PASS_INDEX,
        format_func=lambda idx: format_failed_pass_label(failed_passes_df.iloc[int(idx)]),
    )
    return int(selected_index)


def show_spatial_case_picker() -> None:
    """Show the case selection controls again."""
    st.session_state[spatial_state.CASE_PICKER_VISIBLE] = True


def is_spatial_case_picker_visible() -> bool:
    """Resolve whether the case selector should currently be rendered."""
    value = st.session_state.get(spatial_state.CASE_PICKER_VISIBLE)
    if value is None:
        return True
    return bool(value)


def ensure_spatial_case_picker_state(selector_df: pd.DataFrame) -> None:
    """Initialize stable state for the spatial case selector."""
    current_index = st.session_state.get(spatial_state.FAILED_PASS_INDEX, 0)
    if not isinstance(current_index, int) or not 0 <= current_index < len(selector_df):
        current_index = 0
        st.session_state[spatial_state.FAILED_PASS_INDEX] = current_index
    if spatial_state.LAST_COMMITTED_FAILED_PASS_INDEX not in st.session_state:
        st.session_state[spatial_state.LAST_COMMITTED_FAILED_PASS_INDEX] = current_index


def resolve_spatial_controls_state() -> dict[str, object]:
    """Resolve spatial control values from session state when the controls are hidden."""
    return {
        "scoring_profile": resolve_scoring_profile(
            st.session_state.get(spatial_state.SCORING_PROFILE, DEFAULT_SCORING_PROFILE)
        ),
        "selected_plots": list(DEFAULT_SPATIAL_PLOTS),
        "demo_event_id": None,
    }


def resolve_preselected_event_id(selected_demo_event_id: str | None) -> str | None:
    """Resolve the preferred event id from demo mode or cross-view session state."""
    if selected_demo_event_id:
        return selected_demo_event_id

    selected_event_id = st.session_state.get(spatial_state.SELECTED_EVENT_ID)
    if selected_event_id is None:
        return None
    return str(selected_event_id)


def resolve_default_selector_index(
    failed_passes_df: pd.DataFrame,
    preselected_event_id: str | None,
) -> int:
    """Resolve the selector index honoring an externally selected event when possible."""
    if preselected_event_id and "event_id" in failed_passes_df.columns:
        matches = failed_passes_df.index[failed_passes_df["event_id"].astype(str) == str(preselected_event_id)].tolist()
        if matches:
            first_match = matches[0]
            if failed_passes_df.index.is_monotonic_increasing:
                return int(failed_passes_df.index.get_loc(first_match))

    current_index = st.session_state.get(spatial_state.FAILED_PASS_INDEX, 0)
    if isinstance(current_index, int) and 0 <= current_index < len(failed_passes_df):
        return current_index
    return 0


def store_selected_spatial_event_id(event_row: pd.Series) -> None:
    """Persist the current spatial event selection for cross-view navigation."""
    event_id = extract_event_id(event_row)
    if event_id is not None:
        st.session_state[spatial_state.SELECTED_EVENT_ID] = event_id
