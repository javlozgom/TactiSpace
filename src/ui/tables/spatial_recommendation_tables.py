from __future__ import annotations

import pandas as pd

from src.core.spatial.pass_decision import DEFAULT_SCORING_PROFILE, resolve_scoring_profile
from src.ui.views.spatial_formatters import describe_scoring_profile_compact, format_location, format_score


def build_recommendation_comparison_df(
    delaunay_recommendation: dict,
    scoring_recommendation: dict,
) -> pd.DataFrame:
    """Build a comparison dataframe between Delaunay and scoring."""
    return pd.DataFrame(
        [
            {
                "Método": "Delaunay",
                "Id sugerido": delaunay_recommendation.get("spatial_reference_id") or "-",
                "Localización": format_location(delaunay_recommendation.get("recommended_location")),
                "Score": format_score(delaunay_recommendation.get("delaunay_score")),
                "Interpretación": "Conectividad espacial local mediante triangulación.",
            },
            {
                "Método": (
                    "Scoring espacial "
                    f"({resolve_scoring_profile(scoring_recommendation.get('scoring_profile', DEFAULT_SCORING_PROFILE))})"
                ),
                "Id sugerido": scoring_recommendation.get("spatial_reference_id") or "-",
                "Localización": format_location(scoring_recommendation.get("recommended_location")),
                "Score": format_score(scoring_recommendation.get("score")),
                "Interpretación": describe_scoring_profile_compact(
                    scoring_recommendation.get("scoring_profile", DEFAULT_SCORING_PROFILE)
                ),
            },
        ]
    )


def build_voronoi_scoring_comparison_df(
    voronoi_recommendation: dict,
    scoring_recommendation: dict,
) -> pd.DataFrame:
    """Build a comparison dataframe between Voronoi and scoring."""
    return pd.DataFrame(
        [
            {
                "Método": "Voronoi",
                "Id sugerido": voronoi_recommendation.get("spatial_reference_id") or "-",
                "Localización": format_location(voronoi_recommendation.get("recommended_location")),
                "Score": format_score(voronoi_recommendation.get("score")),
                "Interpretación": "Mayor área Voronoi con apoyo de espacio libre cercano.",
            },
            {
                "Método": (
                    "Scoring espacial "
                    f"({resolve_scoring_profile(scoring_recommendation.get('scoring_profile', DEFAULT_SCORING_PROFILE))})"
                ),
                "Id sugerido": scoring_recommendation.get("spatial_reference_id") or "-",
                "Localización": format_location(scoring_recommendation.get("recommended_location")),
                "Score": format_score(scoring_recommendation.get("score")),
                "Interpretación": describe_scoring_profile_compact(
                    scoring_recommendation.get("scoring_profile", DEFAULT_SCORING_PROFILE)
                ),
            },
        ]
    )
