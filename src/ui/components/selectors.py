from __future__ import annotations

import streamlit as st


def render_pill_selector(
    label: str,
    options: list[str],
    key: str,
    *,
    columns_per_row: int = 4,
) -> str:
    """Render a stable button-based single selector with a persistent active state."""
    _ = label
    if not options:
        return ""

    resolved_options = [str(option) for option in options]
    current_value = str(st.session_state.get(key, resolved_options[0]))
    if current_value not in resolved_options:
        current_value = resolved_options[0]
        st.session_state[key] = current_value

    max_option_length = max(len(option) for option in resolved_options)
    if max_option_length >= 26:
        effective_columns = min(columns_per_row, 2)
    elif max_option_length >= 18:
        effective_columns = min(columns_per_row, 3)
    else:
        effective_columns = columns_per_row

    per_row = max(1, min(effective_columns, len(resolved_options)))
    for row_index in range(0, len(resolved_options), per_row):
        row_options = resolved_options[row_index : row_index + per_row]
        columns = st.columns(per_row, gap="small", vertical_alignment="center")
        for option_index, option in enumerate(row_options):
            with columns[option_index]:
                if st.button(
                    option,
                    key=f"{key}__pill_{row_index}_{option_index}",
                    type="primary" if option == current_value else "secondary",
                    width="stretch",
                ):
                    if option != current_value:
                        st.session_state[key] = option
                        st.rerun()
                    current_value = option

    return str(current_value)
