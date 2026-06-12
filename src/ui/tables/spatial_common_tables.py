from __future__ import annotations

import pandas as pd

from src.ui.views.spatial_formatters import normalize_coordinate_key, normalize_merge_key


def merge_spatial_reference_ids(target_df: pd.DataFrame, freeze_frame_df: pd.DataFrame) -> pd.DataFrame:
    """Attach local spatial ids to one table when player identity is available."""
    if target_df.empty or freeze_frame_df.empty or "spatial_reference_id" not in freeze_frame_df.columns:
        return target_df.copy()

    reference_columns = [col for col in ["player_id", "player", "x", "y", "spatial_reference_id"] if col in freeze_frame_df.columns]
    reference_df = freeze_frame_df.loc[:, reference_columns].copy()
    reference_df = reference_df.dropna(subset=["spatial_reference_id"]).drop_duplicates()

    merged_df = target_df.copy()
    merged_df["spatial_reference_id"] = pd.Series(pd.NA, index=merged_df.index, dtype="object")
    if "player_id" in merged_df.columns and "player_id" in reference_df.columns:
        reference_by_id_df = reference_df[["player_id", "spatial_reference_id"]].copy()
        reference_by_id_df["_spatial_player_id_key"] = reference_by_id_df["player_id"].map(normalize_merge_key)
        reference_by_id_df = reference_by_id_df.dropna(subset=["_spatial_player_id_key"]).drop_duplicates(
            subset=["_spatial_player_id_key"],
            keep="first",
        )
        id_mapping = dict(zip(reference_by_id_df["_spatial_player_id_key"], reference_by_id_df["spatial_reference_id"], strict=False))
        merged_df["spatial_reference_id"] = merged_df["player_id"].map(normalize_merge_key).map(id_mapping).astype("object")
        if merged_df["spatial_reference_id"].notna().any():
            return merged_df

    if "player" in merged_df.columns and "player" in reference_df.columns:
        reference_by_player_df = reference_df[["player", "spatial_reference_id"]].copy()
        reference_by_player_df["_spatial_player_key"] = reference_by_player_df["player"].map(normalize_merge_key)
        reference_by_player_df = reference_by_player_df.dropna(subset=["_spatial_player_key"]).drop_duplicates(
            subset=["_spatial_player_key"],
            keep="first",
        )
        player_mapping = dict(zip(reference_by_player_df["_spatial_player_key"], reference_by_player_df["spatial_reference_id"], strict=False))
        missing_mask = merged_df["spatial_reference_id"].isna()
        merged_df.loc[missing_mask, "spatial_reference_id"] = (
            merged_df.loc[missing_mask, "player"].map(normalize_merge_key).map(player_mapping).astype("object")
        )
        if merged_df["spatial_reference_id"].notna().any():
            return merged_df

    if {"x", "y"}.issubset(merged_df.columns) and {"x", "y"}.issubset(reference_df.columns):
        reference_by_coords_df = reference_df[["x", "y", "spatial_reference_id"]].copy()
        reference_by_coords_df["_spatial_coords_key"] = reference_by_coords_df.apply(
            lambda row: normalize_coordinate_key(row.get("x"), row.get("y")),
            axis=1,
        )
        reference_by_coords_df = reference_by_coords_df.dropna(subset=["_spatial_coords_key"]).drop_duplicates(
            subset=["_spatial_coords_key"],
            keep="first",
        )
        coord_mapping = dict(zip(reference_by_coords_df["_spatial_coords_key"], reference_by_coords_df["spatial_reference_id"], strict=False))
        missing_mask = merged_df["spatial_reference_id"].isna()
        coords_series = merged_df.loc[missing_mask].apply(
            lambda row: coord_mapping.get(normalize_coordinate_key(row.get("x"), row.get("y"))),
            axis=1,
        )
        merged_df.loc[missing_mask, "spatial_reference_id"] = coords_series.astype("object")
    return merged_df


def lookup_spatial_reference_id(
    freeze_frame_df: pd.DataFrame,
    player_name: object,
    location: object = None,
) -> str | None:
    """Return the local plot/table id assigned to one freeze-frame player."""
    if freeze_frame_df.empty or "spatial_reference_id" not in freeze_frame_df.columns:
        return None

    if player_name not in {None, ""} and "player" in freeze_frame_df.columns:
        match_df = freeze_frame_df[freeze_frame_df["player"].astype(str) == str(player_name)]
        if not match_df.empty:
            reference_id = match_df.iloc[0].get("spatial_reference_id")
            if pd.notna(reference_id):
                return str(reference_id)

    if isinstance(location, (list, tuple)) and len(location) >= 2 and {"x", "y"}.issubset(freeze_frame_df.columns):
        x_value = pd.to_numeric(pd.Series([location[0]]), errors="coerce").iloc[0]
        y_value = pd.to_numeric(pd.Series([location[1]]), errors="coerce").iloc[0]
        if pd.notna(x_value) and pd.notna(y_value):
            coords_df = freeze_frame_df[["x", "y"]].apply(pd.to_numeric, errors="coerce")
            match_mask = coords_df["x"].sub(float(x_value)).abs().lt(1e-6) & coords_df["y"].sub(float(y_value)).abs().lt(1e-6)
            match_df = freeze_frame_df.loc[match_mask]
            if not match_df.empty:
                reference_id = match_df.iloc[0].get("spatial_reference_id")
                if pd.notna(reference_id):
                    return str(reference_id)
    return None


def rename_spatial_reference_column(table_df: pd.DataFrame) -> pd.DataFrame:
    """Expose the local player id using a short display label."""
    if "spatial_reference_id" not in table_df.columns:
        return table_df
    return table_df.rename(columns={"spatial_reference_id": "Id"})


def drop_empty_display_columns(table_df: pd.DataFrame) -> pd.DataFrame:
    """Hide columns that are completely empty after local enrichment."""
    if table_df.empty:
        return table_df
    keep_columns: list[str] = []
    for column in table_df.columns:
        series = table_df[column]
        non_empty = series.dropna()
        if non_empty.empty:
            continue
        if non_empty.astype(str).str.strip().eq("").all():
            continue
        if non_empty.astype(str).eq("None").all():
            continue
        keep_columns.append(column)
    return table_df.loc[:, keep_columns] if keep_columns else table_df
