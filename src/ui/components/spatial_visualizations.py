from __future__ import annotations

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from mplsoccer import Pitch


PITCH_KWARGS = {
    "pitch_type": "statsbomb",
    "pitch_color": "#f7f7f2",
    "line_color": "#1f2937",
    "linewidth": 1.2,
}

DEFAULT_SPATIAL_POINT_SIZE = 115
DEFAULT_SPATIAL_HIGHLIGHT_POINT_SIZE = int(DEFAULT_SPATIAL_POINT_SIZE * 1.4)
DEFAULT_VORONOI_FILL_ALPHA = 0.30
DEFAULT_SPATIAL_FIGURE_SIZE = (10, 6)
TEAMMATE_BLUE = "#0b63f6"
TEAMMATE_BLUE_DARK = "#1d4ed8"
TEAMMATE_BLUE_SOFT = "#60a5fa"
TEAMMATE_BLUE_TEXT = "#1e3a8a"


def plot_freeze_frame(
    event_row: pd.Series,
    freeze_frame_df: pd.DataFrame,
    title: str = "Freeze-frame",
):
    """Plot one freeze-frame on a StatsBomb pitch."""
    fig, ax = _build_pitch_figure(title)
    if freeze_frame_df.empty:
        ax.text(60, 40, "Sin freeze-frame disponible", ha="center", va="center", fontsize=11, color="#475569")
        return fig

    teammates_df = freeze_frame_df[freeze_frame_df.get("teammate", False).fillna(False).astype(bool)].copy()
    opponents_df = freeze_frame_df[~freeze_frame_df.get("teammate", False).fillna(False).astype(bool)].copy()
    _plot_players(ax, teammates_df, TEAMMATE_BLUE_DARK, "Compañeros")
    _plot_players(ax, opponents_df, "#c05621", "Rivales")
    _plot_actor(ax, freeze_frame_df)
    _plot_event(ax, event_row, failed_color="#d64545")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.03), ncol=3, frameon=False)
    return fig


def plot_voronoi_freeze_frame(
    event_row: pd.Series,
    freeze_frame_df: pd.DataFrame,
    voronoi_regions_df: pd.DataFrame,
    title: str = "Voronoi espacial",
):
    """Plot freeze-frame plus Voronoi regions."""
    fig, ax = _build_pitch_figure(title)
    if freeze_frame_df.empty:
        ax.text(60, 40, "Sin freeze-frame disponible", ha="center", va="center", fontsize=11, color="#475569")
        return fig

    _plot_voronoi_regions(ax, voronoi_regions_df)

    teammates_df = freeze_frame_df[freeze_frame_df.get("teammate", False).fillna(False).astype(bool)].copy()
    opponents_df = freeze_frame_df[~freeze_frame_df.get("teammate", False).fillna(False).astype(bool)].copy()
    _plot_players(ax, teammates_df, TEAMMATE_BLUE_DARK, "Compañeros")
    _plot_players(ax, opponents_df, "#b45309", "Rivales")
    _plot_actor(ax, freeze_frame_df)
    _plot_event(ax, event_row, failed_color="#d64545")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.03), ncol=3, frameon=False)
    return fig


def plot_delaunay_freeze_frame(
    event_row: pd.Series,
    freeze_frame_df: pd.DataFrame,
    delaunay_edges_df: pd.DataFrame,
    title: str = "Conectividad por Delaunay",
):
    """Plot freeze-frame plus Delaunay edges."""
    fig, ax = _build_pitch_figure(title)
    if freeze_frame_df.empty:
        ax.text(60, 40, "Sin freeze-frame disponible", ha="center", va="center", fontsize=11, color="#475569")
        return fig

    _plot_delaunay_edges(ax, delaunay_edges_df)
    teammates_df = freeze_frame_df[freeze_frame_df.get("teammate", False).fillna(False).astype(bool)].copy()
    opponents_df = freeze_frame_df[~freeze_frame_df.get("teammate", False).fillna(False).astype(bool)].copy()
    _plot_players(ax, teammates_df, TEAMMATE_BLUE_DARK, "Compañeros")
    _plot_players(ax, opponents_df, "#b45309", "Rivales")
    _plot_actor(ax, freeze_frame_df)
    _plot_event(ax, event_row, failed_color="#d64545")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.03), ncol=3, frameon=False)
    return fig


def plot_voronoi_delaunay_freeze_frame(
    event_row: pd.Series,
    freeze_frame_df: pd.DataFrame,
    voronoi_regions_df: pd.DataFrame,
    delaunay_edges_df: pd.DataFrame,
    title: str = "Voronoi + Delaunay",
):
    """Plot freeze-frame with Voronoi regions and Delaunay edges."""
    fig, ax = _build_pitch_figure(title)
    if freeze_frame_df.empty:
        ax.text(60, 40, "Sin freeze-frame disponible", ha="center", va="center", fontsize=11, color="#475569")
        return fig

    _plot_voronoi_regions(ax, voronoi_regions_df)

    _plot_delaunay_edges(ax, delaunay_edges_df)
    teammates_df = freeze_frame_df[freeze_frame_df.get("teammate", False).fillna(False).astype(bool)].copy()
    opponents_df = freeze_frame_df[~freeze_frame_df.get("teammate", False).fillna(False).astype(bool)].copy()
    _plot_players(ax, teammates_df, TEAMMATE_BLUE_DARK, "Compañeros")
    _plot_players(ax, opponents_df, "#b45309", "Rivales")
    _plot_actor(ax, freeze_frame_df)
    _plot_event(ax, event_row, failed_color="#d64545")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.03), ncol=3, frameon=False)
    return fig


def plot_pass_recommendation(
    event_row: pd.Series,
    freeze_frame_df: pd.DataFrame,
    voronoi_regions_df: pd.DataFrame,
    recommendation: dict,
    title: str = "Pase fallido vs alternativa sugerida",
):
    """Plot failed pass versus one suggested alternative."""
    fig, ax = _build_pitch_figure(title)
    if freeze_frame_df.empty:
        ax.text(60, 40, "Sin freeze-frame disponible", ha="center", va="center", fontsize=11, color="#475569")
        return fig

    _plot_voronoi_regions(ax, voronoi_regions_df)

    teammates_df = freeze_frame_df[freeze_frame_df.get("teammate", False).fillna(False).astype(bool)].copy()
    opponents_df = freeze_frame_df[~freeze_frame_df.get("teammate", False).fillna(False).astype(bool)].copy()
    _plot_players(ax, teammates_df, TEAMMATE_BLUE_DARK, "Compañeros")
    _plot_players(ax, opponents_df, "#b45309", "Rivales")
    _plot_actor(ax, freeze_frame_df)
    _plot_event(ax, event_row, failed_color="#d64545")

    recommended_location = recommendation.get("recommended_location")
    if isinstance(recommended_location, tuple) and len(recommended_location) == 2:
        start_x = _to_float(event_row.get("x"), 0.0)
        start_y = _to_float(event_row.get("y"), 0.0)
        end_x = _to_float(recommended_location[0], None)
        end_y = _to_float(recommended_location[1], None)
        if end_x is not None and end_y is not None:
            ax.annotate(
                "",
                xy=(end_x, end_y),
                xytext=(start_x, start_y),
                arrowprops=dict(arrowstyle="->", color=TEAMMATE_BLUE, lw=2.2),
            )

    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.03), ncol=3, frameon=False)
    return fig


def plot_delaunay_recommendation(
    event_row: pd.Series,
    freeze_frame_df: pd.DataFrame,
    delaunay_edges_df: pd.DataFrame,
    recommendation: dict,
    title: str = "Alternativa sugerida mediante Delaunay",
):
    """Plot failed pass and one Delaunay-based recommendation."""
    fig, ax = _build_pitch_figure(title)
    if freeze_frame_df.empty:
        ax.text(60, 40, "Sin freeze-frame disponible", ha="center", va="center", fontsize=11, color="#475569")
        return fig

    _plot_delaunay_edges(ax, delaunay_edges_df)
    teammates_df = freeze_frame_df[freeze_frame_df.get("teammate", False).fillna(False).astype(bool)].copy()
    opponents_df = freeze_frame_df[~freeze_frame_df.get("teammate", False).fillna(False).astype(bool)].copy()
    _plot_players(ax, teammates_df, TEAMMATE_BLUE_DARK, "Compañeros")
    _plot_players(ax, opponents_df, "#b45309", "Rivales")
    _plot_actor(ax, freeze_frame_df)
    _plot_event(ax, event_row, failed_color="#d64545")

    recommended_location = recommendation.get("recommended_location")
    if isinstance(recommended_location, tuple) and len(recommended_location) == 2:
        start_x = _to_float(event_row.get("x"), 0.0)
        start_y = _to_float(event_row.get("y"), 0.0)
        end_x = _to_float(recommended_location[0], None)
        end_y = _to_float(recommended_location[1], None)
        if end_x is not None and end_y is not None:
            ax.annotate(
                "",
                xy=(end_x, end_y),
                xytext=(start_x, start_y),
                arrowprops=dict(arrowstyle="->", color="#7e22ce", lw=2.2),
                zorder=8,
            )

    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.03), ncol=3, frameon=False)
    return fig


def _build_pitch_figure(title: str):
    """Build one standard pitch figure."""
    fig, ax = plt.subplots(figsize=DEFAULT_SPATIAL_FIGURE_SIZE)
    pitch = Pitch(**PITCH_KWARGS)
    pitch.draw(ax=ax)
    fig.patch.set_facecolor("#f5f7f4")
    ax.set_facecolor("#f7f7f2")
    ax.set_title(title, fontsize=11, pad=10, color="#17212b")
    return fig, ax


def _plot_players(ax, players_df: pd.DataFrame, color: str, label: str) -> None:
    """Plot one player group."""
    if players_df.empty or not {"x", "y"}.issubset(players_df.columns):
        return
    working_df = players_df.copy()
    working_df[["x", "y"]] = working_df[["x", "y"]].apply(pd.to_numeric, errors="coerce")
    working_df = working_df.dropna(subset=["x", "y"])
    if "visible" in working_df.columns:
        working_df = working_df[working_df["visible"].fillna(True).astype(bool)].copy()
    if working_df.empty:
        return
    ax.scatter(
        working_df["x"],
        working_df["y"],
        s=DEFAULT_SPATIAL_POINT_SIZE,
        c=color,
        edgecolors="#17212b",
        linewidths=0.8,
        alpha=0.92,
        label=label,
        zorder=3,
    )
    if "spatial_reference_id" not in working_df.columns:
        return
    for _, player_row in working_df.iterrows():
        reference_id = player_row.get("spatial_reference_id")
        if reference_id is None or pd.isna(reference_id):
            continue
        ax.text(
            float(player_row["x"]),
            float(player_row["y"]),
            str(reference_id),
            ha="center",
            va="center",
            fontsize=6.8,
            color="#ffffff",
            weight="bold",
            zorder=4,
        )


def _plot_actor(ax, freeze_frame_df: pd.DataFrame) -> None:
    """Highlight the actor when available."""
    if freeze_frame_df.empty or "actor" not in freeze_frame_df.columns:
        return
    actor_df = freeze_frame_df[freeze_frame_df["actor"].fillna(False).astype(bool)].copy()
    if actor_df.empty:
        return
    actor_df[["x", "y"]] = actor_df[["x", "y"]].apply(pd.to_numeric, errors="coerce")
    actor_df = actor_df.dropna(subset=["x", "y"])
    if actor_df.empty:
        return
    ax.scatter(
        actor_df["x"],
        actor_df["y"],
        s=DEFAULT_SPATIAL_HIGHLIGHT_POINT_SIZE,
        facecolors="none",
        edgecolors="#17212b",
        linewidths=1.8,
        zorder=6,
    )


def _plot_event(ax, event_row: pd.Series, failed_color: str) -> None:
    """Plot the event location and movement when coordinates exist."""
    start_x = _to_float(event_row.get("x"), None)
    start_y = _to_float(event_row.get("y"), None)
    if start_x is None or start_y is None:
        return

    ax.scatter([start_x], [start_y], s=60, c="#111827", marker="o", edgecolors="#ffffff", linewidths=0.9, zorder=7)
    end_x = _to_float(event_row.get("end_x"), None)
    end_y = _to_float(event_row.get("end_y"), None)
    if end_x is None or end_y is None:
        return
    ax.annotate(
        "",
        xy=(end_x, end_y),
        xytext=(start_x, start_y),
        arrowprops=dict(arrowstyle="->", color=failed_color, lw=2.2),
        zorder=8,
    )


def _plot_delaunay_edges(ax, delaunay_edges_df: pd.DataFrame) -> None:
    """Plot Delaunay edges softly so players and arrows remain visible."""
    if delaunay_edges_df is None or delaunay_edges_df.empty:
        ax.text(60, 6, "Sin aristas Delaunay disponibles", ha="center", va="center", fontsize=9, color="#64748b")
        return

    for _, edge in delaunay_edges_df.iterrows():
        a_x = _to_float(edge.get("a_x"), None)
        a_y = _to_float(edge.get("a_y"), None)
        b_x = _to_float(edge.get("b_x"), None)
        b_y = _to_float(edge.get("b_y"), None)
        if None in {a_x, a_y, b_x, b_y}:
            continue

        if bool(edge.get("a_teammate", False)) and bool(edge.get("b_teammate", False)):
            color = TEAMMATE_BLUE_SOFT
        elif not bool(edge.get("a_teammate", False)) and not bool(edge.get("b_teammate", False)):
            color = "#f59e0b"
        else:
            color = "#94a3b8"

        ax.plot([a_x, b_x], [a_y, b_y], color=color, linewidth=1.0, alpha=0.35, zorder=2)


def _fill_polygon(ax, polygon, color: str) -> None:
    """Fill one polygon or multipolygon on the current axes."""
    if polygon is None:
        return

    if isinstance(polygon, (list, tuple)):
        if len(polygon) < 3:
            return
        try:
            x_coords = [float(point[0]) for point in polygon]
            y_coords = [float(point[1]) for point in polygon]
        except Exception:
            return
        ax.fill(
            x_coords,
            y_coords,
            facecolor=color,
            edgecolor="none",
            alpha=0.16,
            zorder=1,
            linewidth=0,
            antialiased=False,
        )
        return

    if getattr(polygon, "is_empty", False):
        return

    geom_type = getattr(polygon, "geom_type", "")
    if geom_type == "Polygon":
        shapes = [polygon]
    elif geom_type == "MultiPolygon":
        shapes = list(getattr(polygon, "geoms", []))
    elif geom_type == "GeometryCollection":
        shapes = [
            geom
            for geom in getattr(polygon, "geoms", [])
            if getattr(geom, "geom_type", "") == "Polygon" and not getattr(geom, "is_empty", False)
        ]
    else:
        return

    for shape in shapes:
        if getattr(shape, "is_empty", False) or not hasattr(shape, "exterior"):
            continue
        x_coords, y_coords = shape.exterior.xy
        ax.fill(
            x_coords,
            y_coords,
            facecolor=color,
            edgecolor="none",
            alpha=0.16,
            zorder=1,
            linewidth=0,
            antialiased=False,
        )


def _plot_voronoi_regions(ax, voronoi_regions_df: pd.DataFrame) -> None:
    """Fill Voronoi regions and draw their borders in a separate pass."""
    if voronoi_regions_df.empty:
        return

    region_entries: list[tuple[float, float, object, str]] = []
    for _, row in voronoi_regions_df.iterrows():
        polygon = row.get("polygon")
        if polygon is None or getattr(polygon, "is_empty", False):
            continue
        x_value = _to_float(row.get("x"), None)
        y_value = _to_float(row.get("y"), None)
        if x_value is None or y_value is None:
            continue
        color = TEAMMATE_BLUE_DARK if bool(row.get("teammate", False)) else "#c05621"
        region_entries.append((x_value, y_value, polygon, color))

    if region_entries:
        _draw_voronoi_fill_raster(ax, region_entries)


def _plot_polygon_outline(ax, polygon, color: str) -> None:
    """Draw polygon borders on top of Voronoi fills."""
    if polygon is None or getattr(polygon, "is_empty", False):
        return

    geom_type = getattr(polygon, "geom_type", "")
    if geom_type == "Polygon":
        shapes = [polygon]
    elif geom_type == "MultiPolygon":
        shapes = list(getattr(polygon, "geoms", []))
    elif geom_type == "GeometryCollection":
        shapes = [
            geom
            for geom in getattr(polygon, "geoms", [])
            if getattr(geom, "geom_type", "") == "Polygon" and not getattr(geom, "is_empty", False)
        ]
    elif isinstance(polygon, (list, tuple)):
        shapes = [polygon]
    else:
        return

    for shape in shapes:
        if isinstance(shape, (list, tuple)):
            if len(shape) < 3:
                continue
            try:
                x_coords = [float(point[0]) for point in shape]
                y_coords = [float(point[1]) for point in shape]
            except Exception:
                continue
            x_coords = [*x_coords, x_coords[0]]
            y_coords = [*y_coords, y_coords[0]]
            ax.plot(x_coords, y_coords, color=color, alpha=0.55, linewidth=0.8, zorder=1.4, solid_joinstyle="round")
            continue

        if getattr(shape, "is_empty", False) or not hasattr(shape, "exterior"):
            continue
        x_coords, y_coords = shape.exterior.xy
        ax.plot(
            x_coords,
            y_coords,
            color=color,
            alpha=0.55,
            linewidth=0.8,
            zorder=1.4,
            solid_joinstyle="round",
            solid_capstyle="round",
        )


def _draw_voronoi_fill_raster(ax, region_entries: list[tuple[float, float, object, str]]) -> None:
    """Rasterize Voronoi by nearest generator on a dense grid to avoid seam artifacts."""
    if not region_entries:
        return

    pitch_length, pitch_width = 120.0, 80.0
    x_points = 1800
    y_points = 1200
    x_coords = np.linspace(0.0, pitch_length, x_points, endpoint=False) + (pitch_length / x_points) * 0.5
    y_coords = np.linspace(0.0, pitch_width, y_points, endpoint=False) + (pitch_width / y_points) * 0.5
    grid_x, grid_y = np.meshgrid(x_coords, y_coords)
    sample_points = np.column_stack([grid_x.ravel(), grid_y.ravel()])

    generators = np.array([(x_value, y_value) for x_value, y_value, _, _ in region_entries], dtype=float)
    if generators.size == 0:
        return
    color_map = {
        TEAMMATE_BLUE_DARK: np.array([96 / 255.0, 165 / 255.0, 250 / 255.0, DEFAULT_VORONOI_FILL_ALPHA], dtype=float),
        "#c05621": np.array([236 / 255.0, 164 / 255.0, 120 / 255.0, DEFAULT_VORONOI_FILL_ALPHA], dtype=float),
    }
    generator_colors = np.array(
        [
            color_map.get(color, np.array([0.0, 0.0, 0.0, DEFAULT_VORONOI_FILL_ALPHA], dtype=float))
            for _, _, _, color in region_entries
        ],
        dtype=float,
    )

    nearest_indices = np.empty(len(sample_points), dtype=int)
    chunk_size = 100000
    for start_index in range(0, len(sample_points), chunk_size):
        end_index = min(start_index + chunk_size, len(sample_points))
        chunk = sample_points[start_index:end_index]
        deltas = chunk[:, None, :] - generators[None, :, :]
        nearest_indices[start_index:end_index] = np.argmin(np.sum(deltas * deltas, axis=2), axis=1)

    rgba = generator_colors[nearest_indices].reshape(y_points, x_points, 4)
    labels = nearest_indices.reshape(y_points, x_points)

    ax.imshow(
        rgba,
        extent=(0.0, pitch_length, 0.0, pitch_width),
        origin="lower",
        interpolation="nearest",
        zorder=1,
    )
    _draw_voronoi_boundary_contours(ax, x_coords, y_coords, labels, generator_colors)


def _draw_voronoi_boundary_contours(
    ax,
    x_coords: np.ndarray,
    y_coords: np.ndarray,
    labels: np.ndarray,
    generator_colors: np.ndarray,
) -> None:
    """Overlay smooth Voronoi boundaries derived from the same raster labels."""
    if labels.size == 0:
        return

    unique_labels = np.unique(labels)
    if unique_labels.size == 0:
        return

    for label_index in unique_labels:
        region_mask = (labels == label_index).astype(float)
        if not region_mask.any():
            continue

        color = generator_colors[int(label_index)]
        ax.contour(
            x_coords,
            y_coords,
            region_mask,
            levels=[0.5],
            colors=[color[:3]],
            linewidths=0.95,
            alpha=0.9,
            zorder=1.25,
            antialiased=True,
        )


def _to_float(value: object, default: float | None) -> float | None:
    """Convert one scalar to float."""
    if value is None or pd.isna(value):
        return default
    try:
        return float(value)
    except Exception:
        return default


