from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from src.core.percentiles.calculations import (
    POSITION_OPTIONS,
    build_percentile_scatter_data,
    flatten_metric_options,
    flatten_percentile_presets,
    get_metric_label,
    get_metric_metadata,
    get_percentile_interpretation_text,
    get_percentile_metric_options,
    get_percentile_presets,
    is_efficiency_metric,
    is_risk_metric,
)
from src.ui.components import render_empty_state, render_section_header


def render_percentiles_section(filtered_df: pd.DataFrame, full_df: pd.DataFrame) -> None:
    """Render the percentile-based scatter comparison block."""
    with st.container():
        render_section_header("Percentiles y jugadores destacados", "Detecta perfiles destacados con dos métricas y una lectura relativa por percentiles.")
        st.caption(
            "Compara jugadores mediante dos métricas y resalta perfiles destacados según percentiles relativos."
        )

        metric_groups = get_percentile_metric_options()
        metric_display_names = flatten_metric_options(metric_groups)
        preset_groups = get_percentile_presets()
        presets = flatten_percentile_presets(preset_groups)
        group_names = list(metric_groups.keys())
        st.session_state.setdefault("percentiles_position_filter", POSITION_OPTIONS[0])
        st.session_state.setdefault("percentiles_min_events", 5)
        st.session_state.setdefault("percentiles_top_n", 10)

        with st.expander("Cómo interpretar este gráfico", expanded=False):
            st.markdown(
                "\n".join(
                    [
                        "- Cada punto representa un jugador.",
                        "- Un percentil alto significa posición relativa alta dentro del conjunto filtrado.",
                        "- El score combinado es la media de los percentiles interpretados de ambos ejes.",
                        "- En métricas de riesgo, un valor alto indica más riesgo o volumen negativo, no mejor rendimiento.",
                        "- En métricas de eficiencia, conviene exigir una muestra mínima antes de interpretar resultados.",
                    ]
                )
            )

        preset_group_names = list(preset_groups.keys())
        st.session_state.setdefault("percentiles_preset_group", preset_group_names[0] if preset_group_names else "")
        if st.session_state.get("percentiles_preset_group") not in preset_groups and preset_group_names:
            st.session_state["percentiles_preset_group"] = preset_group_names[0]
        current_preset_group = st.session_state.get("percentiles_preset_group", preset_group_names[0] if preset_group_names else "")
        current_group_presets = list(preset_groups.get(current_preset_group, {}).keys())
        st.session_state.setdefault("percentiles_preset_name", current_group_presets[0] if current_group_presets else "")
        if st.session_state.get("percentiles_preset_name") not in current_group_presets and current_group_presets:
            st.session_state["percentiles_preset_name"] = current_group_presets[0]

        preset_cols = st.columns([1.1, 1.4, 0.8], vertical_alignment="bottom")
        with preset_cols[0]:
            preset_group = st.selectbox(
                "Grupo de preset",
                preset_group_names,
                key="percentiles_preset_group",
            )
        with preset_cols[1]:
            preset_name = st.selectbox(
                "Preset",
                list(preset_groups.get(preset_group, {}).keys()),
                key="percentiles_preset_name",
                format_func=lambda name: _format_percentile_preset_label(str(name), presets),
            )
        with preset_cols[2]:
            if st.button("Aplicar preset", key="percentiles_apply_preset", width="stretch", icon=":material/tune:"):
                _apply_percentile_preset(preset_name, presets)
                st.rerun()
        if preset_name in presets:
            st.caption(presets[preset_name]["description"])

        _ensure_valid_axis_state(metric_groups, group_names)

        axis_cols = st.columns(2, vertical_alignment="top")
        with axis_cols[0]:
            st.markdown("**Eje X**")
            x_group = st.selectbox("Grupo métrica X", group_names, key="percentiles_x_group")
            x_metric_options = list(metric_groups[x_group].keys())
            if st.session_state.get("percentiles_x_metric") not in x_metric_options:
                st.session_state["percentiles_x_metric"] = x_metric_options[0]
            x_metric = st.selectbox(
                "Métrica X",
                x_metric_options,
                key="percentiles_x_metric",
                format_func=lambda metric_key: metric_display_names.get(metric_key, metric_key),
            )
        with axis_cols[1]:
            st.markdown("**Eje Y**")
            y_group = st.selectbox("Grupo métrica Y", group_names, key="percentiles_y_group")
            y_metric_options = list(metric_groups[y_group].keys())
            if st.session_state.get("percentiles_y_metric") not in y_metric_options:
                st.session_state["percentiles_y_metric"] = y_metric_options[0]
            y_metric = st.selectbox(
                "Métrica Y",
                y_metric_options,
                key="percentiles_y_metric",
                format_func=lambda metric_key: metric_display_names.get(metric_key, metric_key),
            )

        controls_row = st.columns(3, vertical_alignment="bottom")
        with controls_row[0]:
            position_filter = st.selectbox("Posición", POSITION_OPTIONS, key="percentiles_position_filter")
        with controls_row[1]:
            min_events = st.number_input(
                "Mínimo de eventos",
                min_value=1,
                step=1,
                key="percentiles_min_events",
                help=(
                    "Exige que un jugador tenga al menos ese número total de acciones en el contexto "
                    "seleccionado para entrar en la comparativa."
                ),
            )
        with controls_row[2]:
            top_n = st.slider("Destacados", min_value=5, max_value=20, step=1, key="percentiles_top_n")

        interpretation_text = get_percentile_interpretation_text(x_metric, y_metric)
        st.info(interpretation_text)
        st.caption(
            "`Mínimo de eventos` filtra jugadores con poca muestra total dentro del contexto seleccionado."
        )
        if x_metric == y_metric:
            st.warning("Has seleccionado la misma métrica en ambos ejes.")
        if is_risk_metric(x_metric) or is_risk_metric(y_metric):
            st.warning(
                "Has seleccionado una métrica de riesgo. Un percentil alto aquí indica más pérdidas o acciones negativas."
            )
        if is_efficiency_metric(x_metric) or is_efficiency_metric(y_metric):
            st.warning("Se recomienda usar un mínimo de eventos suficientemente alto para interpretar métricas de eficiencia.")

        draft_config = {
            "x_group": x_group,
            "x_metric": x_metric,
            "y_group": y_group,
            "y_metric": y_metric,
            "position_filter": position_filter,
            "min_events": int(min_events),
            "top_n": int(top_n),
        }
        st.session_state["percentiles_last_config"] = dict(draft_config)
        config = draft_config

        with st.container():
            _render_percentile_results(
                filtered_df=filtered_df,
                full_df=full_df,
                metric_display_names=metric_display_names,
                config=config,
            )


@st.cache_data(show_spinner=False)
def get_percentile_scatter_result(
    source_df: pd.DataFrame,
    x_metric: str,
    y_metric: str,
    position_filter: str,
    min_events: int,
    top_n: int,
    min_metric: str | None,
    min_metric_value: int | None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Cache the tabular percentile computation used by the scatter section."""
    clean_df = source_df.copy()
    if "player" in clean_df.columns:
        player_series = clean_df["player"].astype("string").fillna("").str.strip()
        clean_df = clean_df.loc[~player_series.str.lower().eq("unknown")].copy()

    return build_percentile_scatter_data(
        clean_df,
        x_metric=x_metric,
        y_metric=y_metric,
        position_filter=position_filter,
        min_events=min_events,
        top_n=top_n,
        min_metric=min_metric,
        min_metric_value=min_metric_value,
    )


def create_percentile_scatter_plot(
    scatter_df: pd.DataFrame,
    highlighted_df: pd.DataFrame,
    x_metric: str,
    y_metric: str,
    metric_display_names: dict[str, str],
):
    """Create the percentile scatter plot using Plotly when available."""
    try:
        import plotly.express as px
        import plotly.graph_objects as go
    except Exception:
        return _create_matplotlib_scatter_plot(
            scatter_df=scatter_df,
            highlighted_df=highlighted_df,
            x_metric=x_metric,
            y_metric=y_metric,
            metric_display_names=metric_display_names,
        )

    x_label = metric_display_names.get(x_metric, get_metric_label(x_metric))
    y_label = metric_display_names.get(y_metric, get_metric_label(y_metric))
    working_df = scatter_df.copy()
    if working_df.empty:
        fig = go.Figure()
        fig.update_layout(title="Percentiles y jugadores destacados", xaxis_title=x_label, yaxis_title=y_label)
        return fig

    color_arg = "team" if "team" in working_df.columns and working_df["team"].notna().any() else None
    fig = px.scatter(
        working_df,
        x=x_metric,
        y=y_metric,
        color=color_arg,
        hover_name="player",
        hover_data={
            "team": True if "team" in working_df.columns else False,
            "position": True if "position" in working_df.columns else False,
            "x_raw_percentile": True,
            "y_raw_percentile": True,
            "x_interpreted_percentile": True,
            "y_interpreted_percentile": True,
            "combined_percentile_score": True,
        },
        title=f"Percentiles: {x_label} vs {y_label}",
        labels={
            x_metric: x_label,
            y_metric: y_label,
            "x_raw_percentile": "Percentil bruto X",
            "y_raw_percentile": "Percentil bruto Y",
            "x_interpreted_percentile": "Percentil interpretado X",
            "y_interpreted_percentile": "Percentil interpretado Y",
            "combined_percentile_score": "Score combinado",
        },
    )
    fig.update_traces(marker=dict(size=6, opacity=0.55, line=dict(width=0)))

    if not highlighted_df.empty:
        fig.add_trace(
            go.Scatter(
                x=highlighted_df[x_metric],
                y=highlighted_df[y_metric],
                mode="markers+text",
                text=highlighted_df["player"],
                textposition="top center",
                name="Destacados",
                marker=dict(size=8, color="#17212b", line=dict(width=1.0, color="#ffffff")),
                textfont=dict(size=8),
                customdata=highlighted_df[
                    [
                        "team",
                        "position",
                        "x_raw_percentile",
                        "x_interpreted_percentile",
                        "y_raw_percentile",
                        "y_interpreted_percentile",
                        "combined_percentile_score",
                    ]
                ].fillna("-").to_numpy(),
                hovertemplate=(
                    "<b>%{text}</b><br>"
                    + "Equipo: %{customdata[0]}<br>"
                    + "Posición: %{customdata[1]}<br>"
                    + f"{x_label}: %{{x}}<br>"
                    + "Percentil bruto X: %{customdata[2]}<br>"
                    + "Percentil interpretado X: %{customdata[3]}<br>"
                    + f"{y_label}: %{{y}}<br>"
                    + "Percentil bruto Y: %{customdata[4]}<br>"
                    + "Percentil interpretado Y: %{customdata[5]}<br>"
                    + "Score combinado: %{customdata[6]}<extra></extra>"
                ),
            )
        )

    fig.update_layout(legend_title_text="Equipo", margin=dict(l=30, r=30, t=60, b=30))
    return fig


def _render_percentile_results(
    filtered_df: pd.DataFrame,
    full_df: pd.DataFrame,
    metric_display_names: dict[str, str],
    config: dict[str, object],
) -> None:
    """Render plot and table for one applied percentile configuration."""
    x_metric = str(config["x_metric"])
    y_metric = str(config["y_metric"])
    source_df = filtered_df
    if source_df.empty:
        render_empty_state(
            "No hay suficientes datos para generar el gráfico con los filtros actuales.",
            "Prueba a ampliar el contexto global o a relajar los filtros internos de esta sección.",
        )
        return

    full_dataset, highlighted_dataset = get_percentile_scatter_result(
        source_df,
        x_metric=x_metric,
        y_metric=y_metric,
        position_filter=str(config["position_filter"]),
        min_events=int(config["min_events"]),
        top_n=int(config["top_n"]),
        min_metric=str(config["min_metric"]) if config.get("min_metric") else None,
        min_metric_value=int(config["min_metric_value"]) if config.get("min_metric_value") else None,
    )
    if full_dataset.empty or len(full_dataset) < 2:
        render_empty_state(
            "No hay suficientes jugadores para generar el gráfico con los filtros actuales.",
            "Reduce el mínimo de eventos, cambia la posición o amplía el contexto.",
        )
        return

    fig = create_percentile_scatter_plot(
        scatter_df=full_dataset,
        highlighted_df=highlighted_dataset,
        x_metric=x_metric,
        y_metric=y_metric,
        metric_display_names=metric_display_names,
    )
    if hasattr(fig, "to_plotly_json"):
        st.plotly_chart(fig, width="stretch")
    else:
        st.pyplot(fig, width="stretch")
        plt.close(fig)

    if highlighted_dataset.empty:
        render_empty_state(
            "No se pudieron identificar jugadores destacados con la configuración actual.",
            "Prueba otras métricas o relaja el mínimo de eventos.",
        )
        return

    st.markdown("**Jugadores destacados**")
    highlighted_table = _build_highlighted_table(highlighted_dataset, x_metric, y_metric)
    st.dataframe(highlighted_table, width="stretch", hide_index=True)


def _get_metric_badges(metric_key: str) -> list[tuple[str, str]]:
    """Return lightweight badges describing one percentile metric."""
    metadata = get_metric_metadata(metric_key)
    badges = [(str(metadata.get("family", "Otras")).lower(), "slate")]
    direction = str(metadata.get("direction", "higher_is_better"))
    if direction == "efficiency":
        badges.append(("efficiency", "green"))
    elif direction == "higher_is_risk":
        badges.extend([("risk", "red"), ("lower_is_better", "orange")])
    else:
        badges.extend([("volume", "teal"), ("higher_is_better", "purple")])
    return badges


def _build_highlighted_table(highlighted_dataset: pd.DataFrame, x_metric: str, y_metric: str) -> pd.DataFrame:
    """Build the user-facing table of highlighted players."""
    x_label = get_metric_label(x_metric)
    y_label = get_metric_label(y_metric)
    x_column_label = f"{x_label} (X)" if x_metric == y_metric else x_label
    y_column_label = f"{y_label} (Y)" if x_metric == y_metric else y_label

    highlighted_df = highlighted_dataset.copy().rename(
        columns={
            "player": "Jugador",
            "team": "Equipo",
            "position": "Posición",
            x_metric: x_column_label,
            y_metric: y_column_label,
            "x_interpreted_percentile": "Percentil X",
            "y_interpreted_percentile": "Percentil Y",
            "combined_percentile_score": "Score combinado",
            "percentile_mode_label": "Tipo de interpretación",
        }
    )
    visible_columns = [
        "Jugador",
        "Equipo",
        "Posición",
        x_column_label,
        "Percentil X",
        y_column_label,
        "Percentil Y",
        "Score combinado",
        "Tipo de interpretación",
    ]
    visible_columns = [column for column in visible_columns if column in highlighted_df.columns]
    return highlighted_df.loc[:, visible_columns]


def _apply_percentile_preset(preset_name: str, presets: dict[str, dict[str, object]]) -> None:
    """Apply one preset to the editable percentile controls."""
    if preset_name == "Sin preset" or preset_name not in presets:
        return

    preset = presets[preset_name]
    x_metric = str(preset["x_metric"])
    y_metric = str(preset["y_metric"])
    st.session_state["percentiles_x_group"] = str(get_metric_metadata(x_metric)["family"])
    st.session_state["percentiles_x_metric"] = x_metric
    st.session_state["percentiles_y_group"] = str(get_metric_metadata(y_metric)["family"])
    st.session_state["percentiles_y_metric"] = y_metric
    st.session_state["percentiles_position_filter"] = str(preset.get("position", "Todas"))
    st.session_state["percentiles_min_events"] = int(preset.get("min_events", 5))


def _format_percentile_preset_label(preset_name: str, presets: dict[str, dict[str, object]]) -> str:
    """Return a compact visible label for one percentile preset selector entry."""
    preset = presets.get(preset_name)
    if not preset:
        return preset_name

    x_metric = str(preset.get("x_metric", "")).strip()
    y_metric = str(preset.get("y_metric", "")).strip()
    x_label = get_metric_label(x_metric) if x_metric else ""
    y_label = get_metric_label(y_metric) if y_metric else ""
    if x_label and y_label:
        return f"{x_label} / {y_label}"
    return preset_name


def _ensure_valid_axis_state(metric_groups: dict[str, dict[str, str]], group_names: list[str]) -> None:
    """Ensure session-state axis selections always point to valid group/metric pairs."""
    current_x_group = st.session_state.get("percentiles_x_group", group_names[0])
    if current_x_group not in metric_groups:
        current_x_group = group_names[0]
        st.session_state["percentiles_x_group"] = current_x_group
    valid_x_metrics = list(metric_groups[current_x_group].keys())
    if st.session_state.get("percentiles_x_metric") not in valid_x_metrics:
        st.session_state["percentiles_x_metric"] = valid_x_metrics[0]

    current_y_group = st.session_state.get("percentiles_y_group", group_names[0])
    if current_y_group not in metric_groups:
        current_y_group = group_names[0]
        st.session_state["percentiles_y_group"] = current_y_group
    valid_y_metrics = list(metric_groups[current_y_group].keys())
    if st.session_state.get("percentiles_y_metric") not in valid_y_metrics:
        st.session_state["percentiles_y_metric"] = valid_y_metrics[0]


def _create_matplotlib_scatter_plot(
    scatter_df: pd.DataFrame,
    highlighted_df: pd.DataFrame,
    x_metric: str,
    y_metric: str,
    metric_display_names: dict[str, str],
):
    """Fallback scatter plot when Plotly is not installed."""
    x_label = metric_display_names.get(x_metric, get_metric_label(x_metric))
    y_label = metric_display_names.get(y_metric, get_metric_label(y_metric))
    fig, ax = plt.subplots(figsize=(10, 6))
    if not scatter_df.empty:
        ax.scatter(scatter_df[x_metric], scatter_df[y_metric], s=28, alpha=0.55, color="#7db98c")
    if not highlighted_df.empty:
        ax.scatter(highlighted_df[x_metric], highlighted_df[y_metric], s=42, color="#17212b")
        for _, row in highlighted_df.iterrows():
            ax.annotate(
                str(row["player"]),
                (row[x_metric], row[y_metric]),
                xytext=(3, 3),
                textcoords="offset points",
                fontsize=7,
            )
    ax.set_title(f"Percentiles: {x_label} vs {y_label}")
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    ax.grid(alpha=0.2)
    return fig
