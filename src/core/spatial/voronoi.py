from __future__ import annotations

import importlib
from typing import Any

import numpy as np
import pandas as pd


class _FallbackPitchPolygon:
    """Minimal polygon-like object for environments without shapely."""

    def __init__(self, coords: list[tuple[float, float]]):
        self._coords = coords
        self.is_valid = len(coords) >= 3
        self.area = _polygon_area(coords)


def get_pitch_polygon():
    """Return the StatsBomb pitch polygon."""
    polygon_class, error_message = _get_polygon_class()
    if polygon_class is None:
        return _FallbackPitchPolygon([(0, 0), (120, 0), (120, 80), (0, 80)])
    return polygon_class([(0, 0), (120, 0), (120, 80), (0, 80)])


def compute_voronoi(
    players_df: pd.DataFrame,
    x_col: str = "x",
    y_col: str = "y",
) -> dict[str, Any]:
    """Compute a scipy Voronoi structure from player points."""
    voronoi_class, error_message = _get_voronoi_class()
    if voronoi_class is None:
        return {"points": np.empty((0, 2)), "voronoi": None, "valid": False, "reason": error_message}
    if players_df.empty or not {x_col, y_col}.issubset(players_df.columns):
        return {"points": np.empty((0, 2)), "voronoi": None, "valid": False, "reason": "No hay puntos suficientes"}

    points_df = _prepare_voronoi_points(players_df, x_col=x_col, y_col=y_col)
    if len(points_df) < 3:
        return {
            "points": points_df.to_numpy(),
            "voronoi": None,
            "valid": False,
            "reason": "Se necesitan al menos 3 puntos distintos para Voronoi",
        }

    points = points_df.to_numpy(dtype=float)
    try:
        vor = voronoi_class(points, qhull_options="Qbb Qc Qz QJ")
    except Exception as exc:
        return {"points": points, "voronoi": None, "valid": False, "reason": str(exc)}
    return {"points": points, "voronoi": vor, "valid": True, "reason": ""}


def voronoi_finite_polygons_2d(vor, radius: float = 1000):
    """Reconstruct infinite Voronoi regions to finite regions."""
    if vor.points.shape[1] != 2:
        raise ValueError("Solo se soportan regiones 2D")

    new_regions = []
    new_vertices = vor.vertices.tolist()
    center = vor.points.mean(axis=0)
    radius = float(radius)

    all_ridges: dict[int, list[tuple[int, int, int]]] = {}
    for (point_1, point_2), (vertex_1, vertex_2) in zip(vor.ridge_points, vor.ridge_vertices):
        all_ridges.setdefault(point_1, []).append((point_2, vertex_1, vertex_2))
        all_ridges.setdefault(point_2, []).append((point_1, vertex_1, vertex_2))

    for point_index, region_index in enumerate(vor.point_region):
        vertices = vor.regions[region_index]
        if all(vertex >= 0 for vertex in vertices):
            new_regions.append(vertices)
            continue

        ridges = all_ridges.get(point_index, [])
        new_region = [vertex for vertex in vertices if vertex >= 0]

        for point_2, vertex_1, vertex_2 in ridges:
            if vertex_2 < 0:
                vertex_1, vertex_2 = vertex_2, vertex_1
            if vertex_1 >= 0:
                continue

            tangent = vor.points[point_2] - vor.points[point_index]
            tangent /= np.linalg.norm(tangent)
            normal = np.array([-tangent[1], tangent[0]])

            midpoint = vor.points[[point_index, point_2]].mean(axis=0)
            direction = np.sign(np.dot(midpoint - center, normal)) * normal
            far_point = vor.vertices[vertex_2] + direction * radius

            new_region.append(len(new_vertices))
            new_vertices.append(far_point.tolist())

        region_vertices = np.asarray([new_vertices[vertex] for vertex in new_region])
        centroid = region_vertices.mean(axis=0)
        angles = np.arctan2(region_vertices[:, 1] - centroid[1], region_vertices[:, 0] - centroid[0])
        new_regions.append(np.array(new_region)[np.argsort(angles)].tolist())

    return new_regions, np.asarray(new_vertices)


def build_voronoi_regions(
    players_df: pd.DataFrame,
    pitch_length: float = 120,
    pitch_width: float = 80,
) -> pd.DataFrame:
    """Build pitch-clipped Voronoi regions for one set of player points."""
    return build_voronoi_regions_with_diagnostics(
        players_df,
        pitch_length=pitch_length,
        pitch_width=pitch_width,
    )["regions_df"]


def build_voronoi_regions_with_diagnostics(
    players_df: pd.DataFrame,
    pitch_length: float = 120,
    pitch_width: float = 80,
) -> dict[str, Any]:
    """Build pitch-clipped Voronoi regions and include a human-readable failure reason."""
    expected_columns = ["player", "player_id", "team", "teammate", "x", "y", "polygon", "area"]
    polygon_class, polygon_error = _get_polygon_class()
    if players_df.empty:
        return {"regions_df": pd.DataFrame(columns=expected_columns), "reason": "No hay jugadores en el freeze-frame"}

    prepared_players_df = _prepare_players_for_voronoi(players_df)
    if len(prepared_players_df) < 3:
        return {
            "regions_df": pd.DataFrame(columns=expected_columns),
            "reason": "Se necesitan al menos 3 jugadores con coordenadas válidas para Voronoi",
        }

    shapely_rows, shapely_reason = _build_shapely_voronoi_rows(
        prepared_players_df,
        pitch_length=pitch_length,
        pitch_width=pitch_width,
    )
    if shapely_rows:
        return {"regions_df": pd.DataFrame(shapely_rows, columns=expected_columns), "reason": ""}

    voronoi_result = compute_voronoi(prepared_players_df)
    if not voronoi_result["valid"]:
        return {"regions_df": pd.DataFrame(columns=expected_columns), "reason": str(voronoi_result["reason"])}

    try:
        pitch_polygon = (
            polygon_class([(0, 0), (pitch_length, 0), (pitch_length, pitch_width), (0, pitch_width)])
            if polygon_class is not None
            else None
        )
        regions, vertices = voronoi_finite_polygons_2d(voronoi_result["voronoi"])
    except Exception as exc:
        return {"regions_df": pd.DataFrame(columns=expected_columns), "reason": str(exc)}

    points_df = prepared_players_df.reset_index(drop=True)
    if not len(points_df) or not len(regions):
        return {"regions_df": pd.DataFrame(columns=expected_columns), "reason": "No se pudieron reconstruir regiones finitas"}

    rows: list[dict[str, Any]] = []
    usable_len = min(len(points_df), len(regions))
    for row_index in range(usable_len):
        region = regions[row_index]
        try:
            if polygon_class is not None:
                pitch_polygon = polygon_class([(0, 0), (pitch_length, 0), (pitch_length, pitch_width), (0, pitch_width)])
                polygon = polygon_class(vertices[region]).buffer(0).intersection(pitch_polygon)
                polygon_area = float(getattr(polygon, "area", 0.0))
                polygon_payload = polygon
            else:
                clipped_coords = _clip_polygon_to_box(vertices[region], pitch_length=pitch_length, pitch_width=pitch_width)
                if len(clipped_coords) < 3:
                    continue
                polygon = clipped_coords
                polygon_area = _polygon_area(clipped_coords)
                polygon_payload = clipped_coords
        except Exception:
            continue
        if polygon_class is not None and polygon.is_empty:
            continue
        if polygon_area <= 0:
            continue

        player_row = points_df.iloc[row_index]
        rows.append(
            {
                "player": player_row.get("player"),
                "player_id": player_row.get("player_id"),
                "team": player_row.get("team"),
                "teammate": bool(player_row.get("teammate", False)),
                "x": float(player_row.get("x", 0)),
                "y": float(player_row.get("y", 0)),
                "polygon": polygon_payload,
                "area": polygon_area,
            }
        )

    if rows and polygon_class is not None:
        rows = _close_pitch_coverage_gaps(rows, pitch_length=pitch_length, pitch_width=pitch_width)

    if not rows:
        return {
            "regions_df": pd.DataFrame(columns=expected_columns),
            "reason": shapely_reason or polygon_error or "No se pudieron recortar regiones válidas dentro del campo",
        }
    return {"regions_df": pd.DataFrame(rows, columns=expected_columns), "reason": ""}


def _build_shapely_voronoi_rows(
    players_df: pd.DataFrame,
    pitch_length: float,
    pitch_width: float,
) -> tuple[list[dict[str, Any]], str]:
    """Build pitch-clipped Voronoi cells with Shapely's polygonal engine."""
    tools, error_message = _get_shapely_voronoi_tools()
    if tools is None:
        return [], error_message

    polygon_class = tools["Polygon"]
    point_class = tools["Point"]
    multi_point_class = tools["MultiPoint"]
    voronoi_diagram = tools["voronoi_diagram"]

    pitch_polygon = polygon_class([(0, 0), (pitch_length, 0), (pitch_length, pitch_width), (0, pitch_width)])
    points_df = players_df.reset_index(drop=True)
    coordinates = [(float(row.get("x")), float(row.get("y"))) for _, row in points_df.iterrows()]
    point_geometries = [point_class(x_value, y_value) for x_value, y_value in coordinates]

    try:
        diagram = voronoi_diagram(multi_point_class(point_geometries), envelope=pitch_polygon, edges=False)
    except Exception as exc:
        return [], str(exc)

    cells = _polygonal_parts(diagram)
    if not cells:
        return [], "No se pudieron generar celdas Voronoi poligonales"

    rows: list[dict[str, Any]] = []
    used_cell_indices: set[int] = set()
    for row_index, player_row in points_df.iterrows():
        cell_index = _find_cell_for_point(point_geometries[row_index], cells, used_cell_indices)
        if cell_index is None:
            continue

        used_cell_indices.add(cell_index)
        polygon = _clean_polygonal_geometry(cells[cell_index].intersection(pitch_polygon))
        polygon_area = float(getattr(polygon, "area", 0.0))
        if getattr(polygon, "is_empty", True) or polygon_area <= 0:
            continue

        rows.append(_build_region_row(player_row, polygon, polygon_area))

    rows = _close_pitch_coverage_gaps(rows, pitch_length=pitch_length, pitch_width=pitch_width)
    return rows, "" if rows else "No se pudieron asociar celdas Voronoi a los jugadores"


def _build_region_row(player_row: pd.Series, polygon: Any, polygon_area: float) -> dict[str, Any]:
    """Build one stable Voronoi region row."""
    return {
        "player": player_row.get("player"),
        "player_id": player_row.get("player_id"),
        "team": player_row.get("team"),
        "teammate": bool(player_row.get("teammate", False)),
        "x": float(player_row.get("x", 0)),
        "y": float(player_row.get("y", 0)),
        "polygon": polygon,
        "area": polygon_area,
    }


def _find_cell_for_point(point: Any, cells: list[Any], used_cell_indices: set[int]) -> int | None:
    """Return the Voronoi cell index generated by one input point."""
    for cell_index, cell in enumerate(cells):
        if cell_index in used_cell_indices:
            continue
        try:
            if cell.covers(point) or cell.buffer(1e-9).covers(point):
                return cell_index
        except Exception:
            continue

    best_index = None
    best_distance = float("inf")
    for cell_index, cell in enumerate(cells):
        if cell_index in used_cell_indices:
            continue
        try:
            distance = float(cell.distance(point))
        except Exception:
            continue
        if distance < best_distance:
            best_distance = distance
            best_index = cell_index
    return best_index


def _close_pitch_coverage_gaps(
    rows: list[dict[str, Any]],
    pitch_length: float,
    pitch_width: float,
    tolerance: float = 1e-6,
) -> list[dict[str, Any]]:
    """Assign tiny or missed pitch gaps to the nearest generated Voronoi cell."""
    if not rows:
        return rows

    tools, _ = _get_shapely_voronoi_tools()
    if tools is None:
        return rows

    polygon_class = tools["Polygon"]
    point_class = tools["Point"]
    unary_union = tools["unary_union"]
    pitch_polygon = polygon_class([(0, 0), (pitch_length, 0), (pitch_length, pitch_width), (0, pitch_width)])

    cleaned_rows: list[dict[str, Any]] = []
    for row in rows:
        polygon = _clean_polygonal_geometry(row.get("polygon"))
        if getattr(polygon, "is_empty", True):
            continue
        cleaned_row = dict(row)
        cleaned_row["polygon"] = polygon
        cleaned_row["area"] = float(polygon.area)
        cleaned_rows.append(cleaned_row)

    if not cleaned_rows:
        return rows

    try:
        covered_geometry = unary_union([row["polygon"] for row in cleaned_rows])
        gap_geometry = _clean_polygonal_geometry(pitch_polygon.difference(covered_geometry))
    except Exception:
        return cleaned_rows

    if getattr(gap_geometry, "is_empty", True) or float(getattr(gap_geometry, "area", 0.0)) <= tolerance:
        return cleaned_rows

    for gap_part in _polygonal_parts(gap_geometry):
        if float(getattr(gap_part, "area", 0.0)) <= tolerance:
            continue
        representative = gap_part.representative_point()
        nearest_index = _nearest_row_index(representative, cleaned_rows, point_class)
        if nearest_index is None:
            continue
        merged_polygon = _clean_polygonal_geometry(unary_union([cleaned_rows[nearest_index]["polygon"], gap_part]))
        if getattr(merged_polygon, "is_empty", True):
            continue
        cleaned_rows[nearest_index]["polygon"] = merged_polygon
        cleaned_rows[nearest_index]["area"] = float(merged_polygon.area)

    return cleaned_rows


def _nearest_row_index(point: Any, rows: list[dict[str, Any]], point_class: Any) -> int | None:
    """Return the row index whose generator point is nearest to one geometry point."""
    best_index = None
    best_distance = float("inf")
    for row_index, row in enumerate(rows):
        try:
            generator = point_class(float(row.get("x", 0)), float(row.get("y", 0)))
            distance = float(generator.distance(point))
        except Exception:
            continue
        if distance < best_distance:
            best_distance = distance
            best_index = row_index
    return best_index


def _clean_polygonal_geometry(geometry: Any) -> Any:
    """Return a valid polygonal geometry, preserving MultiPolygon when needed."""
    if geometry is None:
        return geometry
    try:
        if geometry.is_empty:
            return geometry
        if not geometry.is_valid:
            geometry = geometry.buffer(0)
    except Exception:
        return geometry

    geom_type = getattr(geometry, "geom_type", "")
    if geom_type in {"Polygon", "MultiPolygon"}:
        return geometry

    parts = _polygonal_parts(geometry)
    if not parts:
        return geometry

    tools, _ = _get_shapely_voronoi_tools()
    if tools is None:
        return geometry
    try:
        return tools["unary_union"](parts)
    except Exception:
        return geometry


def _polygonal_parts(geometry: Any) -> list[Any]:
    """Extract Polygon parts from Polygon, MultiPolygon or GeometryCollection."""
    if geometry is None or getattr(geometry, "is_empty", False):
        return []

    geom_type = getattr(geometry, "geom_type", "")
    if geom_type == "Polygon":
        return [geometry]
    if geom_type == "MultiPolygon":
        return list(geometry.geoms)
    if geom_type == "GeometryCollection":
        parts: list[Any] = []
        for sub_geometry in geometry.geoms:
            parts.extend(_polygonal_parts(sub_geometry))
        return parts
    return []


def calculate_space_metrics(
    players_df: pd.DataFrame,
    voronoi_regions_df: pd.DataFrame,
) -> pd.DataFrame:
    """Add simple space metrics to Voronoi regions."""
    if voronoi_regions_df.empty:
        return pd.DataFrame(columns=[*voronoi_regions_df.columns, "voronoi_area", "normalized_area", "nearest_opponent_distance"])

    metrics_df = voronoi_regions_df.copy()
    max_area = float(metrics_df["area"].max()) if "area" in metrics_df.columns and not metrics_df["area"].empty else 0.0
    metrics_df["voronoi_area"] = pd.to_numeric(metrics_df.get("area", 0), errors="coerce").fillna(0)
    metrics_df["normalized_area"] = metrics_df["voronoi_area"] / max_area if max_area > 0 else 0.0

    opponents_df = pd.DataFrame(columns=players_df.columns)
    if not players_df.empty and "teammate" in players_df.columns:
        opponents_df = players_df[~players_df["teammate"].fillna(False).astype(bool)].copy()

    metrics_df["nearest_opponent_distance"] = metrics_df.apply(
        lambda row: _nearest_opponent_distance(row.get("x"), row.get("y"), opponents_df),
        axis=1,
    )
    return metrics_df


def get_player_region(voronoi_regions_df: pd.DataFrame, player_id=None, player=None):
    """Return the Voronoi region row for one player when available."""
    if voronoi_regions_df.empty:
        return None
    if player_id is not None and "player_id" in voronoi_regions_df.columns:
        match_df = voronoi_regions_df[voronoi_regions_df["player_id"] == player_id]
        if not match_df.empty:
            return match_df.iloc[0]
    if player is not None and "player" in voronoi_regions_df.columns:
        match_df = voronoi_regions_df[voronoi_regions_df["player"].astype(str) == str(player)]
        if not match_df.empty:
            return match_df.iloc[0]
    return None


def _prepare_voronoi_points(
    players_df: pd.DataFrame,
    x_col: str = "x",
    y_col: str = "y",
) -> pd.DataFrame:
    """Return one safe point dataframe for Voronoi computation."""
    if players_df.empty or not {x_col, y_col}.issubset(players_df.columns):
        return pd.DataFrame(columns=[x_col, y_col])

    points_df = players_df[[x_col, y_col]].apply(pd.to_numeric, errors="coerce").dropna().copy()
    points_df[x_col] = points_df[x_col].clip(0, 120)
    points_df[y_col] = points_df[y_col].clip(0, 80)
    return points_df.drop_duplicates().reset_index(drop=True)


def _prepare_players_for_voronoi(players_df: pd.DataFrame) -> pd.DataFrame:
    """Return one player dataframe aligned with the sanitized Voronoi points."""
    if players_df.empty:
        return players_df.copy()

    prepared_df = players_df.copy()
    prepared_df[["x", "y"]] = prepared_df[["x", "y"]].apply(pd.to_numeric, errors="coerce")
    prepared_df = prepared_df.dropna(subset=["x", "y"]).copy()
    prepared_df["x"] = prepared_df["x"].clip(0, 120)
    prepared_df["y"] = prepared_df["y"].clip(0, 80)
    prepared_df = prepared_df.drop_duplicates(subset=["x", "y"]).reset_index(drop=True)
    return prepared_df


def _nearest_opponent_distance(x_value: object, y_value: object, opponents_df: pd.DataFrame) -> float:
    """Return one nearest-opponent distance safely."""
    if opponents_df.empty or pd.isna(x_value) or pd.isna(y_value):
        return 0.0

    opponent_coords = opponents_df[["x", "y"]].apply(pd.to_numeric, errors="coerce").dropna()
    if opponent_coords.empty:
        return 0.0

    deltas = opponent_coords.to_numpy(dtype=float) - np.array([float(x_value), float(y_value)])
    distances = np.sqrt((deltas ** 2).sum(axis=1))
    return float(distances.min()) if len(distances) else 0.0


def _get_voronoi_class() -> tuple[Any | None, str]:
    """Import scipy Voronoi lazily and return a readable error when it fails."""
    try:
        module = importlib.import_module("scipy.spatial")
        return getattr(module, "Voronoi"), ""
    except Exception as exc:  # pragma: no cover
        return None, f"scipy no está disponible: {exc}"


def _get_polygon_class() -> tuple[Any | None, str]:
    """Import shapely Polygon lazily and return a readable error when it fails."""
    try:
        module = importlib.import_module("shapely.geometry")
        return getattr(module, "Polygon"), ""
    except Exception as exc:  # pragma: no cover
        return None, f"shapely no está disponible: {exc}"


def _get_shapely_voronoi_tools() -> tuple[dict[str, Any] | None, str]:
    """Import Shapely geometry helpers used for robust Voronoi clipping."""
    try:
        geometry_module = importlib.import_module("shapely.geometry")
        ops_module = importlib.import_module("shapely.ops")
        return {
            "Point": getattr(geometry_module, "Point"),
            "MultiPoint": getattr(geometry_module, "MultiPoint"),
            "Polygon": getattr(geometry_module, "Polygon"),
            "voronoi_diagram": getattr(ops_module, "voronoi_diagram"),
            "unary_union": getattr(ops_module, "unary_union"),
        }, ""
    except Exception as exc:  # pragma: no cover
        return None, f"shapely no está disponible para Voronoi: {exc}"


def _clip_polygon_to_box(vertices: np.ndarray, pitch_length: float, pitch_width: float) -> list[tuple[float, float]]:
    """Clip one polygon to the pitch rectangle using Sutherland-Hodgman."""
    polygon = [(float(x), float(y)) for x, y in vertices]
    for edge_name in ["left", "right", "bottom", "top"]:
        polygon = _clip_polygon_edge(polygon, edge_name=edge_name, pitch_length=pitch_length, pitch_width=pitch_width)
        if not polygon:
            return []
    return polygon


def _clip_polygon_edge(
    polygon: list[tuple[float, float]],
    edge_name: str,
    pitch_length: float,
    pitch_width: float,
) -> list[tuple[float, float]]:
    """Clip one polygon against one rectangle edge."""
    if not polygon:
        return []

    clipped: list[tuple[float, float]] = []
    previous = polygon[-1]
    for current in polygon:
        previous_inside = _is_inside_edge(previous, edge_name, pitch_length, pitch_width)
        current_inside = _is_inside_edge(current, edge_name, pitch_length, pitch_width)
        if current_inside:
            if not previous_inside:
                clipped.append(_edge_intersection(previous, current, edge_name, pitch_length, pitch_width))
            clipped.append(current)
        elif previous_inside:
            clipped.append(_edge_intersection(previous, current, edge_name, pitch_length, pitch_width))
        previous = current
    return clipped


def _is_inside_edge(point: tuple[float, float], edge_name: str, pitch_length: float, pitch_width: float) -> bool:
    """Return whether one point stays inside one clipping edge."""
    x_value, y_value = point
    if edge_name == "left":
        return x_value >= 0
    if edge_name == "right":
        return x_value <= pitch_length
    if edge_name == "bottom":
        return y_value >= 0
    return y_value <= pitch_width


def _edge_intersection(
    start: tuple[float, float],
    end: tuple[float, float],
    edge_name: str,
    pitch_length: float,
    pitch_width: float,
) -> tuple[float, float]:
    """Return intersection point between one segment and one clipping edge."""
    x1, y1 = start
    x2, y2 = end
    dx = x2 - x1
    dy = y2 - y1

    if edge_name in {"left", "right"}:
        boundary = 0.0 if edge_name == "left" else float(pitch_length)
        if dx == 0:
            return boundary, y1
        t_value = (boundary - x1) / dx
        return boundary, y1 + (t_value * dy)

    boundary = 0.0 if edge_name == "bottom" else float(pitch_width)
    if dy == 0:
        return x1, boundary
    t_value = (boundary - y1) / dy
    return x1 + (t_value * dx), boundary


def _polygon_area(polygon: list[tuple[float, float]]) -> float:
    """Compute polygon area using the shoelace formula."""
    if len(polygon) < 3:
        return 0.0
    x_values = np.array([point[0] for point in polygon], dtype=float)
    y_values = np.array([point[1] for point in polygon], dtype=float)
    return float(abs(np.dot(x_values, np.roll(y_values, -1)) - np.dot(y_values, np.roll(x_values, -1))) * 0.5)
