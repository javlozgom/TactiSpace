from __future__ import annotations

from src.ui.views.spatial_debug import render_delaunay_debug_section


def render_delaunay_debug(*, context: dict[str, object]) -> None:
    """Render raw Delaunay data, diagnostics and downloads."""
    render_delaunay_debug_section(context)
