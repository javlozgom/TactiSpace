from __future__ import annotations

import pandas as pd


REQUIRED_COLUMNS = [
    "match_id",
    "team",
    "player",
    "minute",
    "second",
    "event_type",
    "outcome",
    "x",
    "y",
    "end_x",
    "end_y",
    "possession_id",
]

REQUIRED_VALUE_COLUMNS = [
    "match_id",
    "minute",
    "second",
    "event_type",
]

NUMERIC_COLUMNS = ["minute", "second", "x", "y", "end_x", "end_y"]
SUCCESS_TOKENS = ("successful", "complete", "won", "goal", "saved", "success")
FAILURE_TOKENS = ("unsuccessful", "incomplete", "lost", "fail", "failed")
SPECIAL_DESCRIPTIVE_EVENTS = {"Own Goal For", "Own Goal Against", "Offside"}


def add_derived_event_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Add reusable derived event columns used across multiple views."""
    if df.empty:
        return df.copy()

    derived_df = df.copy()
    outcome_series = (
        derived_df["outcome"].astype("string").fillna("").str.lower()
        if "outcome" in derived_df.columns
        else pd.Series("", index=derived_df.index, dtype="object")
    )
    event_type_series = (
        derived_df["event_type"].astype("string").fillna("")
        if "event_type" in derived_df.columns
        else pd.Series("", index=derived_df.index, dtype="object")
    )

    derived_df["is_successful"] = outcome_series.apply(lambda value: any(token in value for token in SUCCESS_TOKENS))
    derived_df["is_failed"] = outcome_series.apply(lambda value: any(token in value for token in FAILURE_TOKENS))
    derived_df["is_pass"] = event_type_series.eq("Pass")
    derived_df["is_carry"] = event_type_series.eq("Carry")
    derived_df["is_shot"] = event_type_series.eq("Shot")

    descriptive_mask = event_type_series.isin(SPECIAL_DESCRIPTIVE_EVENTS)
    if descriptive_mask.any():
        derived_df.loc[descriptive_mask, "is_successful"] = False
        derived_df.loc[descriptive_mask, "is_failed"] = False

    if {"x", "y", "end_x", "end_y"}.issubset(derived_df.columns):
        coords_df = derived_df[["x", "y", "end_x", "end_y"]].apply(pd.to_numeric, errors="coerce")
        derived_df["action_length"] = (
            ((coords_df["end_x"] - coords_df["x"]) ** 2 + (coords_df["end_y"] - coords_df["y"]) ** 2) ** 0.5
        ).fillna(0.0)
        derived_df["is_progressive"] = (coords_df["end_x"] - coords_df["x"] >= 10).fillna(False)
        derived_df["to_final_third"] = (coords_df["end_x"] >= 80).fillna(False)
        derived_df["box_entry"] = (
            (coords_df["end_x"] >= 102) & coords_df["end_y"].between(18, 62, inclusive="both")
        ).fillna(False)
    else:
        derived_df["action_length"] = 0.0
        derived_df["is_progressive"] = False
        derived_df["to_final_third"] = False
        derived_df["box_entry"] = False

    if "x" in derived_df.columns:
        x_series = pd.to_numeric(derived_df["x"], errors="coerce")
        derived_df["field_zone"] = pd.Series("Tercio medio", index=derived_df.index, dtype="object")
        derived_df.loc[x_series < 40, "field_zone"] = "Tercio defensivo"
        derived_df.loc[x_series >= 80, "field_zone"] = "Tercio ofensivo"
    else:
        derived_df["field_zone"] = "Tercio medio"

    derived_df["loss_type"] = None
    derived_df.loc[event_type_series.eq("Dispossessed"), "loss_type"] = "Dispossessed"
    derived_df.loc[event_type_series.eq("Miscontrol"), "loss_type"] = "Miscontrol"
    derived_df.loc[event_type_series.eq("Error"), "loss_type"] = "Error"
    derived_df.loc[derived_df["is_pass"] & derived_df["is_failed"], "loss_type"] = "Failed Pass"
    derived_df.loc[event_type_series.eq("Dribble") & derived_df["is_failed"], "loss_type"] = "Failed Dribble"

    return derived_df


def infer_duel_outcomes(df: pd.DataFrame) -> pd.DataFrame:
    """Infer duel outcomes from the next event in the same match."""
    if df.empty:
        result_df = df.copy()
        result_df["inferred_outcome"] = pd.Series(dtype="object")
        return result_df

    inferred_df = df.copy()
    inferred_df["inferred_outcome"] = inferred_df["outcome"]

    ordered_df = inferred_df.sort_values(
        by=["match_id", "timestamp", "possession_id"],
        ascending=True,
    ).reset_index()

    ordered_df["next_team"] = ordered_df.groupby("match_id")["team"].shift(-1)
    duel_mask = ordered_df["event_type"] == "Duel"
    same_team_mask = ordered_df["next_team"] == ordered_df["team"]
    other_team_mask = ordered_df["next_team"].notna() & ~same_team_mask

    ordered_df.loc[duel_mask & same_team_mask, "inferred_outcome"] = "Won"
    ordered_df.loc[duel_mask & other_team_mask, "inferred_outcome"] = "Lost"
    ordered_df.loc[duel_mask & ordered_df["next_team"].isna(), "inferred_outcome"] = "Unknown"

    restored_df = (
        ordered_df.sort_values("index")
        .drop(columns=["index", "next_team"])
        .reset_index(drop=True)
    )
    return restored_df


def normalize_events(df: pd.DataFrame) -> pd.DataFrame:
    """Validate and normalize the football events DataFrame."""
    missing_columns = [column for column in REQUIRED_COLUMNS if column not in df.columns]
    if missing_columns:
        raise ValueError(f"Faltan columnas obligatorias: {', '.join(missing_columns)}")

    clean_df = df.copy()

    for column in NUMERIC_COLUMNS:
        clean_df[column] = pd.to_numeric(clean_df[column], errors="coerce")

    clean_df["possession_id"] = pd.to_numeric(clean_df["possession_id"], errors="coerce")

    for column in ["team", "player", "event_type", "outcome"]:
        clean_df[column] = clean_df[column].astype("string").fillna("Unknown")

    clean_df["end_x"] = clean_df["end_x"].fillna(clean_df["x"])
    clean_df["end_y"] = clean_df["end_y"].fillna(clean_df["y"])

    clean_df = clean_df.dropna(subset=REQUIRED_VALUE_COLUMNS).copy()
    clean_df["minute"] = clean_df["minute"].astype(int)
    clean_df["second"] = clean_df["second"].astype(int)
    clean_df["possession_id"] = clean_df["possession_id"].fillna(0).astype(int)
    clean_df["timestamp"] = clean_df["minute"] * 60 + clean_df["second"]

    clean_df = clean_df.sort_values(
        by=["match_id", "possession_id", "timestamp"],
        ascending=True,
    ).reset_index(drop=True)
    clean_df = infer_duel_outcomes(clean_df)
    clean_df = add_derived_event_columns(clean_df)

    # TODO: ampliar con reglas especificas por proveedor de datos.
    return clean_df
