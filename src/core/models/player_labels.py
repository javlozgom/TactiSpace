from __future__ import annotations

import pandas as pd


def build_player_label_maps(df: pd.DataFrame) -> tuple[dict[str, str], dict[str, str]]:
    """Build mappings between full player names and display labels."""
    if df.empty or "player" not in df.columns:
        return {}, {}

    players_df = df.loc[:, [column for column in ["player", "player_nickname"] if column in df.columns]].copy()
    players_df = players_df.dropna(subset=["player"]).copy()

    if "player_nickname" in players_df.columns:
        players_df["player_nickname"] = players_df["player_nickname"].astype("string").fillna("").str.strip()
        players_df = (
            players_df.sort_values(by="player_nickname", key=lambda s: s.eq(""))
            .drop_duplicates(subset=["player"], keep="first")
        )
    else:
        players_df = players_df.drop_duplicates(subset=["player"])

    full_to_display: dict[str, str] = {}
    for _, row in players_df.iterrows():
        player_name = str(row["player"])
        nickname = str(row["player_nickname"]).strip() if "player_nickname" in row and pd.notna(row["player_nickname"]) else ""
        full_to_display[player_name] = nickname or player_name

    display_counts: dict[str, int] = {}
    for label in full_to_display.values():
        display_counts[label] = display_counts.get(label, 0) + 1

    for player_name, label in list(full_to_display.items()):
        if display_counts.get(label, 0) > 1:
            full_to_display[player_name] = f"{label} ({player_name})"

    display_to_full = {display: full for full, display in full_to_display.items()}
    return full_to_display, display_to_full


def apply_player_display_names(
    df: pd.DataFrame,
    full_to_display: dict[str, str],
    columns: list[str] | None = None,
) -> pd.DataFrame:
    """Replace visible player-name columns with display labels."""
    if df.empty or not full_to_display:
        return df.copy()

    display_df = df.copy()
    target_columns = columns or [
        column
        for column in display_df.columns
        if column in {"player", "next_player", "origin_player", "passer", "Jugador"}
    ]
    for column in target_columns:
        if column in display_df.columns:
            display_df[column] = display_df[column].map(
                lambda value: full_to_display.get(str(value), value) if pd.notna(value) else value
            )
    return display_df


def get_player_display_name(player_name: str, full_to_display: dict[str, str]) -> str:
    """Return a visible label for a player."""
    return full_to_display.get(player_name, player_name)
