from __future__ import annotations

import re
import unicodedata

import pandas as pd

from src.core.metrics.basic import get_effective_outcome_series


OWN_HALF_THRESHOLD = 60
FINAL_THIRD_THRESHOLD = 80
BOX_ENTRY_X_THRESHOLD = 102
BOX_ENTRY_Y_MIN = 18
BOX_ENTRY_Y_MAX = 62
PROGRESSIVE_DELTA_X = 10

SUCCESS_KEYWORDS = ("successful", "complete", "won", "success", "goal")
FAILURE_KEYWORDS = ("unsuccessful", "incomplete", "lost", "fail", "failed")

GENERIC_ZONE_EVENTS = {
    "Dispossessed",
    "Miscontrol",
    "Interception",
    "Clearance",
    "Block",
    "Goal Keeper",
    "Ball Receipt*",
}

THIRD_ZONE_OPTIONS = ["Todas", "1er tercio", "2o tercio", "3er tercio"]
CONTINUATION_OPTIONS = [
    "Todas",
    "Acaban en pase",
    "Acaban en conducción",
    "Acaban en tiro",
    "Acaban en regate",
    "Acaban en mal control",
    "Acaban en pérdida",
    "Acaban en falta recibida",
]


def get_focus_filter_options(event_type: str) -> dict[str, list[str]]:
    """Return grouped quick filters for the selected specific-metric event."""
    if event_type == "Pass":
        return {
            "Resultado": ["Todos", "Completados", "Fallidos"],
            "Progresión": ["Todos", "Progresivos", "Al área"],
            "Zona de origen": THIRD_ZONE_OPTIONS,
            "Zona de destino": THIRD_ZONE_OPTIONS,
            "Continuación": CONTINUATION_OPTIONS,
        }
    if event_type == "Carry":
        return {
            "Progresión": ["Todos", "Progresivos", "Al área"],
            "Zona de origen": THIRD_ZONE_OPTIONS,
            "Zona de destino": THIRD_ZONE_OPTIONS,
            "Continuación": CONTINUATION_OPTIONS,
        }
    if event_type == "Shot":
        return {
            "Resultado": ["Todos", "Goles", "Parados", "Fuera", "Bloqueados"],
        }
    if event_type == "Pressure":
        return {
            "Zona": THIRD_ZONE_OPTIONS,
        }
    if event_type == "Duel":
        return {
            "Resultado": ["Todos", "Ganados", "Perdidos"],
        }
    if event_type == "Dribble":
        return {
            "Resultado": ["Todos", "Exitosos", "Fallidos"],
            "Zona": THIRD_ZONE_OPTIONS,
        }
    if event_type == "Ball Recovery":
        return {
            "Zona": THIRD_ZONE_OPTIONS,
        }
    if event_type in GENERIC_ZONE_EVENTS:
        return {
            "Zona": THIRD_ZONE_OPTIONS,
        }
    return {}


def apply_specific_metric_focus_filters(
    df: pd.DataFrame,
    event_type: str,
    selected_filters: dict[str, str],
    context_df: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Filter a dataframe by event type and selected quick filters."""
    if df.empty or "event_type" not in df.columns:
        return pd.DataFrame(columns=df.columns)

    event_df = df[df["event_type"] == event_type].copy()
    if event_df.empty:
        return event_df

    working_context_df = context_df if context_df is not None else df
    for group_name, selected_option in selected_filters.items():
        event_df = _apply_group_filter(
            event_df,
            working_context_df,
            event_type,
            group_name,
            selected_option,
        )
        if event_df.empty:
            break
    return event_df


def _apply_group_filter(
    df: pd.DataFrame,
    context_df: pd.DataFrame,
    event_type: str,
    group_name: str,
    selected_option: str,
) -> pd.DataFrame:
    """Apply one grouped quick filter to a dataframe."""
    if selected_option in {"Todos", "Todas", "", None}:
        return df

    normalized_group_name = _normalize_label(group_name)
    if normalized_group_name == "resultado":
        return df[_result_mask(df, event_type, selected_option)].copy()
    if normalized_group_name == "progresion":
        return df[_progression_mask(df, selected_option)].copy()
    if normalized_group_name in {"zona", "zona de origen"}:
        return df[_zone_mask(df, selected_option, column="x")].copy()
    if normalized_group_name == "zona de destino":
        return df[_zone_mask(df, selected_option, column="end_x")].copy()
    if normalized_group_name == "continuacion":
        return df[_continuation_mask(df, context_df, event_type, selected_option)].copy()
    return df


def _result_mask(df: pd.DataFrame, event_type: str, selected_option: str) -> pd.Series:
    """Build a result-based mask for the selected option."""
    outcome_series = _normalized_outcome_series(df)
    normalized_option = _normalize_label(selected_option)
    if normalized_option in {"completados", "exitosos", "ganados"}:
        return _contains_keywords(outcome_series, SUCCESS_KEYWORDS)
    if normalized_option in {"fallidos", "perdidos"}:
        return _contains_keywords(outcome_series, FAILURE_KEYWORDS)
    if normalized_option == "goles":
        return outcome_series.str.contains("goal", case=False, na=False)
    if normalized_option == "parados":
        return outcome_series.str.contains("saved", case=False, na=False)
    if normalized_option == "fuera":
        return outcome_series.str.contains("off target", case=False, na=False)
    if normalized_option == "bloqueados":
        return outcome_series.str.contains(r"\bblocked?\b|\bblock\b", case=False, na=False, regex=True)
    return pd.Series(True, index=df.index)


def _progression_mask(df: pd.DataFrame, selected_option: str) -> pd.Series:
    """Build a progression-based mask for passes/carries."""
    normalized_option = _normalize_label(selected_option)
    if normalized_option == "progresivos":
        if not {"x", "end_x"}.issubset(df.columns):
            return pd.Series(False, index=df.index)
        coords = df.loc[:, ["x", "end_x"]].apply(pd.to_numeric, errors="coerce")
        return (coords["end_x"] - coords["x"] >= PROGRESSIVE_DELTA_X).fillna(False)

    if normalized_option == "al ultimo tercio":
        if "end_x" not in df.columns:
            return pd.Series(False, index=df.index)
        end_x = pd.to_numeric(df["end_x"], errors="coerce")
        return (end_x >= FINAL_THIRD_THRESHOLD).fillna(False)

    if normalized_option == "al area":
        if not {"end_x", "end_y"}.issubset(df.columns):
            return pd.Series(False, index=df.index)
        coords = df.loc[:, ["end_x", "end_y"]].apply(pd.to_numeric, errors="coerce")
        return (
            (coords["end_x"] >= BOX_ENTRY_X_THRESHOLD)
            & coords["end_y"].between(BOX_ENTRY_Y_MIN, BOX_ENTRY_Y_MAX)
        ).fillna(False)

    return pd.Series(True, index=df.index)


def _zone_mask(df: pd.DataFrame, selected_option: str, column: str = "x") -> pd.Series:
    """Build a zone mask for origin or destination coordinates."""
    if column not in df.columns:
        return pd.Series(False, index=df.index)

    normalized_option = _normalize_label(selected_option)
    x_series = pd.to_numeric(df[column], errors="coerce")
    if normalized_option == "1er tercio":
        return (x_series < 40).fillna(False)
    if normalized_option == "2o tercio":
        return ((x_series >= 40) & (x_series < 80)).fillna(False)
    if normalized_option == "3er tercio":
        return (x_series >= FINAL_THIRD_THRESHOLD).fillna(False)
    if normalized_option == "campo propio":
        return (x_series < OWN_HALF_THRESHOLD).fillna(False)
    if normalized_option == "campo rival":
        return (x_series >= OWN_HALF_THRESHOLD).fillna(False)
    if normalized_option == "ultimo tercio":
        return (x_series >= FINAL_THIRD_THRESHOLD).fillna(False)
    return pd.Series(True, index=df.index)


def _continuation_mask(
    event_df: pd.DataFrame,
    context_df: pd.DataFrame,
    event_type: str,
    selected_option: str,
) -> pd.Series:
    """Build a mask based on the next action of the same team in the same possession."""
    continuation_map = {
        "Acaban en pase": "Pass",
        "Acaban en conducción": "Carry",
        "Acaban en tiro": "Shot",
        "Acaban en regate": "Dribble",
        "Acaban en mal control": "Miscontrol",
        "Acaban en pérdida": "Dispossessed",
        "Acaban en falta recibida": "Foul Won",
    }
    normalized_map = {_normalize_label(key): value for key, value in continuation_map.items()}
    target_event = normalized_map.get(_normalize_label(selected_option))
    if not target_event:
        return pd.Series(True, index=event_df.index)

    required_columns = {"match_id", "possession_id", "timestamp", "team", "event_type"}
    if (
        event_df.empty
        or context_df.empty
        or not required_columns.issubset(event_df.columns)
        or not required_columns.issubset(context_df.columns)
    ):
        return pd.Series(False, index=event_df.index)

    ordered_df = context_df.sort_values(["match_id", "possession_id", "timestamp"]).copy()
    next_same_team_event = pd.Series(pd.NA, index=ordered_df.index, dtype="object")
    skipped_events = {"Ball Receipt*"} if event_type == "Pass" else set()

    for _, possession_df in ordered_df.groupby(["match_id", "possession_id"], sort=False):
        possession_df = possession_df.sort_values("timestamp")
        indices = possession_df.index.to_list()
        teams = possession_df["team"].tolist()
        event_types = possession_df["event_type"].tolist()

        for pos, current_index in enumerate(indices):
            current_team = teams[pos]
            next_event = None
            for next_pos in range(pos + 1, len(indices)):
                if teams[next_pos] == current_team:
                    candidate_event = event_types[next_pos]
                    if candidate_event in skipped_events:
                        continue
                    next_event = candidate_event
                    break
            next_same_team_event.at[current_index] = next_event

    return next_same_team_event.reindex(event_df.index).eq(target_event).fillna(False)


def _normalized_outcome_series(df: pd.DataFrame) -> pd.Series:
    """Return a lower-case outcome series safe for partial matching."""
    if df.empty or not {"outcome", "inferred_outcome"}.intersection(df.columns):
        return pd.Series("", index=df.index, dtype="object")
    return get_effective_outcome_series(df).fillna("").astype(str).str.strip().str.lower()


def _contains_keywords(series: pd.Series, keywords: tuple[str, ...]) -> pd.Series:
    """Return whether each row contains any of the provided keywords."""
    if series.empty:
        return pd.Series(False, index=series.index)
    patterns = [re.compile(rf"\b{re.escape(keyword)}\b", flags=re.IGNORECASE) for keyword in keywords]
    return series.apply(lambda value: any(pattern.search(value) for pattern in patterns))


def _normalize_label(value: object) -> str:
    """Normalize visible labels to a stable ascii key."""
    text = "" if value is None else str(value)
    text = unicodedata.normalize("NFKD", text)
    text = "".join(char for char in text if not unicodedata.combining(char))
    return text.strip().lower()
