from __future__ import annotations

import pandas as pd
import streamlit as st

from src.ui.components.icons import header_logo_svg


def render_app_header(filtered_df: pd.DataFrame | None = None) -> tuple[bytes | None, bool]:
    """Render the top bar and return upload state."""
    _ = filtered_df
    st.markdown(
        f"""
        <div class="fea-topbar top-header">
            <div class="fea-logo">{header_logo_svg()}</div>
            <div class="fea-title">
                <h1>TactiSpace</h1>
                <p>TFG &middot; An&aacute;lisis visual, contextual y espacial de eventos de f&uacute;tbol &middot; StatsBomb Euro 2024</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    return None, False
