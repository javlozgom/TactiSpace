from __future__ import annotations

from src.ui.views.spatial_debug import render_voronoi_debug_section


def render_voronoi_debug(*, context: dict[str, object]) -> None:
    """Render debug and technical data related to the Voronoi branch."""
    render_voronoi_debug_section(context)
