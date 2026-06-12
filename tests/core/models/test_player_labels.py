from __future__ import annotations

import pandas as pd

from src.core.models.player_labels import (
    apply_player_display_names,
    build_player_label_maps,
    get_player_display_name,
)


def test_build_player_label_maps_returns_empty_maps_for_empty_or_invalid_df():
    assert build_player_label_maps(pd.DataFrame()) == ({}, {})
    assert build_player_label_maps(pd.DataFrame([{"name": "Rodri"}])) == ({}, {})


def test_build_player_label_maps_prefers_nickname_and_disambiguates_duplicates():
    df = pd.DataFrame(
        [
            {"player": "Rodrigo Hernandez", "player_nickname": "Rodri"},
            {"player": "Rodri Sanchez", "player_nickname": "Rodri"},
            {"player": "Lamine Yamal", "player_nickname": "  "},
            {"player": "Pedri", "player_nickname": None},
        ]
    )

    full_to_display, display_to_full = build_player_label_maps(df)

    assert full_to_display["Rodrigo Hernandez"] == "Rodri (Rodrigo Hernandez)"
    assert full_to_display["Rodri Sanchez"] == "Rodri (Rodri Sanchez)"
    assert full_to_display["Lamine Yamal"] == "Lamine Yamal"
    assert full_to_display["Pedri"] == "Pedri"
    assert display_to_full["Rodri (Rodrigo Hernandez)"] == "Rodrigo Hernandez"


def test_apply_player_display_names_updates_default_columns_and_respects_nans():
    df = pd.DataFrame(
        [
            {
                "player": "Rodrigo Hernandez",
                "next_player": "Pedri",
                "origin_player": None,
                "passer": "Unknown Name",
                "Jugador": "Pedri",
            }
        ]
    )

    result = apply_player_display_names(
        df,
        {
            "Rodrigo Hernandez": "Rodri",
            "Pedri": "Pedri G.",
        },
    )

    assert result.loc[0, "player"] == "Rodri"
    assert result.loc[0, "next_player"] == "Pedri G."
    assert pd.isna(result.loc[0, "origin_player"])
    assert result.loc[0, "passer"] == "Unknown Name"
    assert result.loc[0, "Jugador"] == "Pedri G."


def test_apply_player_display_names_accepts_custom_columns():
    df = pd.DataFrame([{"captain": "Rodrigo Hernandez", "player": "Rodrigo Hernandez"}])

    result = apply_player_display_names(df, {"Rodrigo Hernandez": "Rodri"}, columns=["captain"])

    assert result.loc[0, "captain"] == "Rodri"
    assert result.loc[0, "player"] == "Rodrigo Hernandez"


def test_get_player_display_name_returns_fallback_name():
    assert get_player_display_name("Rodri", {"Pedri": "Pedro"}) == "Rodri"
