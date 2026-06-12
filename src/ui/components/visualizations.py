from __future__ import annotations

import matplotlib.pyplot as plt
from matplotlib import patches
from matplotlib.lines import Line2D
from matplotlib.legend_handler import HandlerBase
import pandas as pd
from mplsoccer import Pitch

from src.core.metrics.basic import SUCCESS_OUTCOMES, get_effective_outcome_series


PITCH_KWARGS = {
    "pitch_type": "statsbomb",
    "pitch_color": "#f7f7f2",
    "line_color": "#1f2937",
    "linewidth": 1.2,
}

EVENT_COLORS = {
    "Goal Keeper": "#0f5f48",
    "Pass": "#0f6a3c",
    "Ball Receipt*": "#1a7a45",
    "Clearance": "#2f855a",
    "Ball Recovery": "#3b9367",
    "Error": "#4c9f73",
    "Interception": "#5cab7f",
    "Block": "#6db78a",
    "Carry": "#2f855a",
    "Pressure": "#79bf93",
    "Shot": "#3f9b6b",
    "Dribble": "#68b684",
    "Duel": "#4f8f67",
    "Dispossessed": "#88c79c",
    "Miscontrol": "#9cd1ab",
    "Foul Won": "#acd8b8",
    "Own Goal For": "#c62828",
    "Own Goal Against": "#8b1e1e",
    "Offside": "#d97706",
}

EVENT_MARKERS = {
    "Goal Keeper": "P",
    "Pass": "o",
    "Ball Receipt*": "8",
    "Clearance": "s",
    "Ball Recovery": "H",
    "Error": "X",
    "Interception": "h",
    "Block": "D",
    "Carry": "^",
    "Pressure": "+",
    "Shot": "*",
    "Dribble": "p",
    "Duel": "d",
    "Dispossessed": "x",
    "Miscontrol": "v",
    "Foul Won": ">",
    "Own Goal For": "$F$",
    "Own Goal Against": "$C$",
    "Offside": "<",
}

SUCCESS_COLOR = "#198754"
FAILURE_COLOR = "#d64545"
UNKNOWN_COLOR = "#8aa190"
SHOT_OUTCOME_STYLES = {
    "Goal": {"color": "#198754", "marker": "*", "size": 130},
    "Saved": {"color": "#f0ad4e", "marker": "o", "size": 95},
    "Off Target": {"color": "#d64545", "marker": "X", "size": 105},
}


class _OffsideFlagLegendHandle:
    """Proxy handle used to render one custom offside-flag legend symbol."""

    def __init__(self, label: str = "Fuera de juego") -> None:
        self._label = label

    def get_label(self) -> str:
        return self._label


class _OffsideFlagLegendHandler(HandlerBase):
    """Draw the square offside flag inside matplotlib legends."""

    def create_artists(
        self,
        legend,
        orig_handle,
        xdescent,
        ydescent,
        width,
        height,
        fontsize,
        trans,
    ):
        aspect_ratio = 1.35 / 0.95
        max_width = width * 0.92
        max_height = height * 0.92
        flag_width = min(max_width, max_height * aspect_ratio)
        flag_height = flag_width / aspect_ratio
        flag_x = xdescent + (width - flag_width) / 2
        flag_y = ydescent + (height - flag_height) / 2
        half_width = flag_width / 2
        half_height = flag_height / 2

        squares = [
            patches.Rectangle(
                (flag_x, flag_y),
                half_width,
                half_height,
                facecolor="#facc15",
                edgecolor="#7c2d12",
                linewidth=0.45,
                transform=trans,
            ),
            patches.Rectangle(
                (flag_x + half_width, flag_y),
                half_width,
                half_height,
                facecolor="#dc2626",
                edgecolor="#7c2d12",
                linewidth=0.45,
                transform=trans,
            ),
            patches.Rectangle(
                (flag_x, flag_y + half_height),
                half_width,
                half_height,
                facecolor="#dc2626",
                edgecolor="#7c2d12",
                linewidth=0.45,
                transform=trans,
            ),
            patches.Rectangle(
                (flag_x + half_width, flag_y + half_height),
                half_width,
                half_height,
                facecolor="#facc15",
                edgecolor="#7c2d12",
                linewidth=0.45,
                transform=trans,
            ),
        ]
        return squares


def draw_offside_flag(ax, x: float, y: float, size: float = 2.0) -> None:
    """Draw a small square offside flag near one offside event."""
    if pd.isna(x) or pd.isna(y):
        return

    flag_width = size * 1.35
    flag_height = size * 0.95
    base_x = float(x) + size * 0.3
    base_y = float(y) + size * 0.55
    half_width = flag_width / 2
    half_height = flag_height / 2
    colors = [
        ("#facc15", base_x, base_y),
        ("#dc2626", base_x + half_width, base_y),
        ("#dc2626", base_x, base_y + half_height),
        ("#facc15", base_x + half_width, base_y + half_height),
    ]
    for color, rect_x, rect_y in colors:
        ax.add_patch(
            patches.Rectangle(
                (rect_x, rect_y),
                half_width,
                half_height,
                facecolor=color,
                edgecolor="#7c2d12",
                linewidth=0.35,
                zorder=6,
            )
        )


def _plot_offside_events(pitch: Pitch, ax, event_df: pd.DataFrame, marker_size: float = 86) -> None:
    """Render offside events using only the assistant-referee flag marker."""
    if event_df.empty:
        return
    for row in event_df.itertuples(index=False):
        draw_offside_flag(ax, getattr(row, "x", None), getattr(row, "y", None), size=1.6)


def _build_offside_legend_handle(label: str = "Fuera de juego") -> _OffsideFlagLegendHandle:
    """Return the custom legend proxy for one offside flag."""
    return _OffsideFlagLegendHandle(label=label)


def _style_figure(fig, ax):
    """Keep matplotlib output in a stable light theme inside Streamlit."""
    fig.patch.set_facecolor("#f5f7f4")
    ax.set_facecolor("#f7f7f2")
    ax.title.set_color("#17212b")
    return fig


def plot_events_on_pitch(
    df: pd.DataFrame,
    title: str = "Eventos",
    draw_movements: bool = True,
    show_legend: bool = True,
):
    """Plot events on a pitch with a separate legend band below the field."""
    figure_height = 7.4 if show_legend else 5.8
    fig = plt.figure(figsize=(10.2, figure_height))
    grid = fig.add_gridspec(
        nrows=2 if show_legend else 1,
        ncols=1,
        height_ratios=[5.2, 1.55] if show_legend else [1],
        hspace=0.12,
    )
    ax = fig.add_subplot(grid[0])
    pitch = Pitch(**PITCH_KWARGS)
    pitch.draw(ax=ax)
    _style_figure(fig, ax)

    if df.empty:
        ax.set_title(f"{title} - sin datos", fontsize=11, pad=10)
        return fig

    plot_df = df.copy()
    plot_df["_effective_outcome"] = get_effective_outcome_series(df).to_numpy()

    def outcome_color(outcome: str) -> str:
        if outcome in SUCCESS_OUTCOMES:
            return SUCCESS_COLOR
        if outcome in {"Unsuccessful", "Lost", "Off Target", "Saved"}:
            return FAILURE_COLOR
        return UNKNOWN_COLOR

    event_marker_size = 34
    shot_fallback_style = {"color": UNKNOWN_COLOR, "marker": "s", "size": 44}

    for event_type in plot_df["event_type"].dropna().unique():
        event_df = plot_df[plot_df["event_type"] == event_type]
        if event_df.empty:
            continue
        if event_type == "Offside":
            _plot_offside_events(pitch, ax, event_df, marker_size=42)
            continue
        if event_type == "Shot":
            for shot_outcome, shot_df in event_df.groupby("_effective_outcome", sort=False):
                style = SHOT_OUTCOME_STYLES.get(shot_outcome, shot_fallback_style)
                pitch.scatter(
                    shot_df["x"],
                    shot_df["y"],
                    ax=ax,
                    s=style["size"] * 0.42,
                    c=style["color"],
                    marker=style["marker"],
                    edgecolors="#1f2937",
                    linewidths=0.75,
                    alpha=0.96,
                    zorder=3,
                )
            continue

        if event_type in {"Own Goal For", "Own Goal Against"}:
            point_colors = EVENT_COLORS.get(event_type, UNKNOWN_COLOR)
        else:
            point_colors = event_df["_effective_outcome"].map(outcome_color)

        pitch.scatter(
            event_df["x"],
            event_df["y"],
            ax=ax,
            s=event_marker_size,
            c=point_colors,
            marker=EVENT_MARKERS.get(event_type, "o"),
            edgecolors="#1f2937",
            linewidths=0.75,
            alpha=0.94,
            zorder=3,
        )

    if draw_movements:
        movement_df = plot_df[plot_df["event_type"].isin(["Pass", "Carry"])].dropna(
            subset=["end_x", "end_y"]
        )
        pass_df = movement_df[movement_df["event_type"] == "Pass"].copy()
        carry_df = movement_df[movement_df["event_type"] == "Carry"].copy()

        if not pass_df.empty:
            successful_passes = pass_df[pass_df["_effective_outcome"].isin(SUCCESS_OUTCOMES)]
            failed_passes = pass_df[~pass_df["_effective_outcome"].isin(SUCCESS_OUTCOMES)]

            if not successful_passes.empty:
                pitch.arrows(
                    successful_passes["x"].to_numpy(),
                    successful_passes["y"].to_numpy(),
                    successful_passes["end_x"].to_numpy(),
                    successful_passes["end_y"].to_numpy(),
                    ax=ax,
                    width=1.15,
                    headwidth=3.3,
                    headlength=4.2,
                    color=SUCCESS_COLOR,
                    alpha=0.8,
                    zorder=2,
                )
            if not failed_passes.empty:
                pitch.arrows(
                    failed_passes["x"].to_numpy(),
                    failed_passes["y"].to_numpy(),
                    failed_passes["end_x"].to_numpy(),
                    failed_passes["end_y"].to_numpy(),
                    ax=ax,
                    width=1.15,
                    headwidth=3.3,
                    headlength=4.2,
                    color=FAILURE_COLOR,
                    alpha=0.8,
                    zorder=2,
                )

        if not carry_df.empty:
            successful_carries = carry_df[carry_df["_effective_outcome"].isin(SUCCESS_OUTCOMES)]
            failed_carries = carry_df[
                carry_df["_effective_outcome"].isin({"Unsuccessful", "Lost", "Off Target", "Saved"})
            ]
            unresolved_carries = carry_df[
                ~carry_df["_effective_outcome"].isin(
                    set(SUCCESS_OUTCOMES) | {"Unsuccessful", "Lost", "Off Target", "Saved"}
                )
            ]

            if not successful_carries.empty:
                pitch.arrows(
                    successful_carries["x"].to_numpy(),
                    successful_carries["y"].to_numpy(),
                    successful_carries["end_x"].to_numpy(),
                    successful_carries["end_y"].to_numpy(),
                    ax=ax,
                    width=1.05,
                    headwidth=3.1,
                    headlength=4.0,
                    color=SUCCESS_COLOR,
                    alpha=0.75,
                    zorder=2,
                )
            if not failed_carries.empty:
                pitch.arrows(
                    failed_carries["x"].to_numpy(),
                    failed_carries["y"].to_numpy(),
                    failed_carries["end_x"].to_numpy(),
                    failed_carries["end_y"].to_numpy(),
                    ax=ax,
                    width=1.05,
                    headwidth=3.1,
                    headlength=4.0,
                    color=FAILURE_COLOR,
                    alpha=0.75,
                    zorder=2,
                )
            if not unresolved_carries.empty:
                pitch.arrows(
                    unresolved_carries["x"].to_numpy(),
                    unresolved_carries["y"].to_numpy(),
                    unresolved_carries["end_x"].to_numpy(),
                    unresolved_carries["end_y"].to_numpy(),
                    ax=ax,
                    width=1.05,
                    headwidth=3.1,
                    headlength=4.0,
                    color=UNKNOWN_COLOR,
                    alpha=0.72,
                    zorder=2,
                )

    ax.set_title(title, fontsize=11, pad=10)

    present_event_types = set(plot_df["event_type"].dropna().unique())
    ordered_present_event_types = [
        event_type for event_type in EVENT_COLORS if event_type in present_event_types
    ]
    type_handles = [
        Line2D(
            [0],
            [0],
            marker=EVENT_MARKERS.get(event_type, "o"),
            color="w",
            label=event_type,
            markerfacecolor="#0f6a3c",
            markeredgecolor="#1f2937",
            markersize=6.0,
        )
        for event_type in ordered_present_event_types
        if event_type not in {"Shot", "Offside"}
    ]
    if "Offside" in present_event_types:
        type_handles.append(_build_offside_legend_handle())
    if {"Own Goal For", "Own Goal Against"} & present_event_types:
        type_handles.append(
            Line2D(
                [0],
                [0],
                marker=EVENT_MARKERS["Own Goal Against"],
                color="w",
                label="Gol en propia",
                markerfacecolor=EVENT_COLORS["Own Goal For"],
                markeredgecolor="#1f2937",
                markersize=6.0,
            )
        )
    result_handles = [
        Line2D(
            [0],
            [0],
            marker="o",
            color="w",
            label="Exito",
            markerfacecolor=SUCCESS_COLOR,
            markeredgecolor="#1f2937",
            markersize=5.8,
        ),
        Line2D(
            [0],
            [0],
            marker="o",
            color="w",
            label="Fracaso",
            markerfacecolor=FAILURE_COLOR,
            markeredgecolor="#1f2937",
            markersize=5.8,
        ),
        Line2D(
            [0],
            [0],
            marker="o",
            color="w",
            label="Sin resolver",
            markerfacecolor=UNKNOWN_COLOR,
            markeredgecolor="#1f2937",
            markersize=5.8,
        ),
        Line2D([0, 1], [0, 0], color=SUCCESS_COLOR, linewidth=1.7, label="Pass/Carry exitoso"),
        Line2D([0, 1], [0, 0], color=FAILURE_COLOR, linewidth=1.7, label="Pass/Carry fallido"),
        Line2D([0, 1], [0, 0], color=UNKNOWN_COLOR, linewidth=1.7, label="Pass/Carry sin resolver"),
    ]
    shot_handles: list[Line2D] = []
    if "Shot" in present_event_types:
        for label in ["Goal", "Saved", "Off Target"]:
            style = SHOT_OUTCOME_STYLES[label]
            shot_handles.append(
                Line2D(
                    [0],
                    [0],
                    marker=style["marker"],
                    color="w",
                    label=label,
                    markerfacecolor=style["color"],
                    markeredgecolor="#1f2937",
                    markersize=6.0,
                )
            )

    if show_legend:
        legend_grid = grid[1].subgridspec(
            1,
            3,
            width_ratios=[1.35, 1.6, 1.0],
            wspace=0.18,
        )
        type_ax = fig.add_subplot(legend_grid[0])
        result_ax = fig.add_subplot(legend_grid[1])
        shot_ax = fig.add_subplot(legend_grid[2])
        for legend_ax in [type_ax, result_ax, shot_ax]:
            legend_ax.set_facecolor("#f5f7f4")
            legend_ax.axis("off")

        legend_style = {
            "frameon": True,
            "facecolor": "white",
            "edgecolor": "#dbe6d8",
            "fontsize": 7.2,
            "title_fontsize": 7.4,
            "borderpad": 0.6,
            "labelspacing": 0.45,
            "columnspacing": 0.9,
            "handletextpad": 0.5,
        }

        if type_handles:
            type_legend = type_ax.legend(
                handles=type_handles,
                title="Tipos de evento",
                loc="center",
                bbox_to_anchor=(0.5, 0.5),
                ncol=min(2, len(type_handles)),
                handler_map={_OffsideFlagLegendHandle: _OffsideFlagLegendHandler()},
                **legend_style,
            )
            type_ax.add_artist(type_legend)

        result_legend = result_ax.legend(
            handles=result_handles,
            title="Pass y Carry con resultado",
            loc="center",
            bbox_to_anchor=(0.5, 0.5),
            ncol=2,
            **legend_style,
        )
        result_ax.add_artist(result_legend)

        if shot_handles:
            shot_legend = shot_ax.legend(
                handles=shot_handles,
                title="Tiros",
                loc="center",
                bbox_to_anchor=(0.5, 0.5),
                ncol=1,
                **legend_style,
            )
            shot_ax.add_artist(shot_legend)

    return fig


def plot_shot_map(df: pd.DataFrame, title: str = "Mapa de tiros"):
    """Plot shots on the pitch, separating goals from other outcomes."""
    pitch = Pitch(**PITCH_KWARGS)
    fig, ax = pitch.draw(figsize=(10, 7))
    _style_figure(fig, ax)

    shots_df = df[df["event_type"] == "Shot"].copy()
    if shots_df.empty:
        ax.set_title(f"{title} - sin tiros")
        return fig

    goals_df = shots_df[shots_df["outcome"] == "Goal"]
    other_shots_df = shots_df[shots_df["outcome"] != "Goal"]

    if not other_shots_df.empty:
        pitch.scatter(
            other_shots_df["x"],
            other_shots_df["y"],
            ax=ax,
            s=90,
            c="#dc2626",
            marker="o",
            edgecolors="#7f1d1d",
            alpha=0.75,
            label="Shot",
        )
    if not goals_df.empty:
        pitch.scatter(
            goals_df["x"],
            goals_df["y"],
            ax=ax,
            s=130,
            c="#16a34a",
            marker="*",
            edgecolors="#14532d",
            alpha=0.9,
            label="Goal",
        )

    ax.set_title(title)
    if not shots_df.empty:
        ax.legend(loc="upper left")
    return fig


def plot_event_heatmap(df: pd.DataFrame, title: str = "Mapa de calor de eventos"):
    """Plot a simple event heatmap using mplsoccer bin statistics."""
    pitch = Pitch(**PITCH_KWARGS)
    fig, ax = pitch.draw(figsize=(10, 7))
    _style_figure(fig, ax)

    if df.empty or len(df) < 2:
        ax.set_title(f"{title} - datos insuficientes")
        return fig

    bin_stats = pitch.bin_statistic(df["x"], df["y"], statistic="count", bins=(6, 4))
    pitch.heatmap(bin_stats, ax=ax, cmap="YlOrRd", edgecolors="#ffffff", alpha=0.8)
    ax.set_title(title)

    # TODO: permitir heatmaps por equipo o tipo de evento.
    return fig


def plot_single_event_map(
    df: pd.DataFrame,
    event_type: str,
    player_name: str | None = None,
    title: str | None = None,
    show_legend: bool = False,
):
    """Plot a single event-type map, optionally filtered to one player."""
    pitch = Pitch(**PITCH_KWARGS)
    fig, ax = pitch.draw(figsize=(9, 6))
    _style_figure(fig, ax)

    map_title = title or event_type
    if df.empty or "event_type" not in df.columns:
        ax.set_title(f"{map_title} - sin datos")
        return fig

    plot_df = df[df["event_type"] == event_type].copy()
    if player_name and player_name != "Todos" and "player" in plot_df.columns:
        plot_df = plot_df[plot_df["player"] == player_name].copy()

    plot_df = plot_df.dropna(subset=["x", "y"])
    if plot_df.empty:
        ax.set_title(f"{map_title} - sin eventos disponibles")
        return fig

    plot_df["_effective_outcome"] = get_effective_outcome_series(plot_df).to_numpy()
    legend_handles: list[Line2D] = []

    if event_type == "Shot":
        for shot_outcome, shot_df in plot_df.groupby("_effective_outcome", sort=False):
            style = SHOT_OUTCOME_STYLES.get(
                shot_outcome,
                {"color": UNKNOWN_COLOR, "marker": "s", "size": 100},
            )
            pitch.scatter(
                shot_df["x"],
                shot_df["y"],
                ax=ax,
                s=style["size"],
                c=style["color"],
                marker=style["marker"],
                edgecolors="#1f2937",
                linewidths=1.0,
                alpha=0.94,
            )
            if show_legend:
                legend_handles.append(
                    Line2D(
                        [0],
                        [0],
                        marker=style["marker"],
                        color="w",
                        label=shot_outcome,
                        markerfacecolor=style["color"],
                        markeredgecolor="#1f2937",
                        markersize=9,
                    )
                )
    elif event_type == "Offside":
        _plot_offside_events(pitch, ax, plot_df, marker_size=80)
        if show_legend:
            legend_handles.append(_build_offside_legend_handle())
    else:
        marker = EVENT_MARKERS.get(event_type, "o")
        marker_size = 100 if event_type in {"Own Goal For", "Own Goal Against"} else 95 if event_type == "Goal Keeper" else 78
        if event_type in {"Own Goal For", "Own Goal Against"}:
            colors = EVENT_COLORS.get(event_type, UNKNOWN_COLOR)
        else:
            colors = plot_df["_effective_outcome"].map(
                lambda outcome: (
                    SUCCESS_COLOR
                    if outcome in SUCCESS_OUTCOMES
                    else FAILURE_COLOR
                    if outcome in {"Unsuccessful", "Lost", "Off Target", "Saved"}
                    else UNKNOWN_COLOR
                )
            )

        pitch.scatter(
            plot_df["x"],
            plot_df["y"],
            ax=ax,
            s=marker_size,
            c=colors,
            marker=marker,
            edgecolors="#1f2937",
            linewidths=1.0,
            alpha=0.92,
        )

        if show_legend:
            legend_handles.extend(
                [
                    Line2D(
                        [0],
                        [0],
                        marker=marker,
                        color="w",
                        label="Exito",
                        markerfacecolor=SUCCESS_COLOR,
                        markeredgecolor="#1f2937",
                        markersize=8,
                    ),
                    Line2D(
                        [0],
                        [0],
                        marker=marker,
                        color="w",
                        label="Fracaso",
                        markerfacecolor=FAILURE_COLOR,
                        markeredgecolor="#1f2937",
                        markersize=8,
                    ),
                    Line2D(
                        [0],
                        [0],
                        marker=marker,
                        color="w",
                        label="Sin resolver",
                        markerfacecolor=UNKNOWN_COLOR,
                        markeredgecolor="#1f2937",
                        markersize=8,
                    ),
                ]
            )
            if event_type in {"Own Goal For", "Own Goal Against"}:
                legend_handles = [
                    Line2D(
                        [0],
                        [0],
                        marker=marker,
                        color="w",
                        label="Gol en propia",
                        markerfacecolor=EVENT_COLORS.get(event_type, UNKNOWN_COLOR),
                        markeredgecolor="#1f2937",
                        markersize=8,
                    )
                ]

    if event_type in {"Pass", "Carry"} and {"end_x", "end_y"}.issubset(plot_df.columns):
        movement_df = plot_df.dropna(subset=["end_x", "end_y"])
        if not movement_df.empty:
            if event_type == "Pass":
                movement_df = movement_df.copy()
                movement_df["_effective_outcome"] = get_effective_outcome_series(
                    movement_df
                ).to_numpy()
                successful_passes = movement_df[
                    movement_df["_effective_outcome"].isin(SUCCESS_OUTCOMES)
                ]
                failed_passes = movement_df[
                    ~movement_df["_effective_outcome"].isin(SUCCESS_OUTCOMES)
                ]

                if not successful_passes.empty:
                    pitch.arrows(
                        successful_passes["x"].to_numpy(),
                        successful_passes["y"].to_numpy(),
                        successful_passes["end_x"].to_numpy(),
                        successful_passes["end_y"].to_numpy(),
                        ax=ax,
                        width=1.6,
                        headwidth=4,
                        headlength=5,
                        color=SUCCESS_COLOR,
                        alpha=0.6,
                    )
                if not failed_passes.empty:
                    pitch.arrows(
                        failed_passes["x"].to_numpy(),
                        failed_passes["y"].to_numpy(),
                        failed_passes["end_x"].to_numpy(),
                        failed_passes["end_y"].to_numpy(),
                        ax=ax,
                        width=1.6,
                        headwidth=4,
                        headlength=5,
                        color=FAILURE_COLOR,
                        alpha=0.6,
                    )
            else:
                pitch.arrows(
                    movement_df["x"].to_numpy(),
                    movement_df["y"].to_numpy(),
                    movement_df["end_x"].to_numpy(),
                    movement_df["end_y"].to_numpy(),
                    ax=ax,
                    width=1.5,
                    headwidth=4,
                    headlength=5,
                    color="#f59e0b",
                    alpha=0.55,
                )

    ax.set_title(map_title)
    if show_legend and legend_handles:
        fig.subplots_adjust(bottom=0.18)
        ax.legend(
            handles=legend_handles,
            title="Interpretacion",
            loc="upper center",
            bbox_to_anchor=(0.5, -0.06),
            ncol=min(3, len(legend_handles)),
            frameon=True,
            facecolor="white",
            edgecolor="#dbe6d8",
            fontsize=8,
            title_fontsize=8,
            handler_map={_OffsideFlagLegendHandle: _OffsideFlagLegendHandler()},
        )
    return fig
