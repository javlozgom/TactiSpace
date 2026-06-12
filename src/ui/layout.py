from __future__ import annotations


def update_loading_overlay(placeholder, percent: int, message: str) -> None:
    """Render a centered loading overlay with numeric progress."""
    placeholder.markdown(
        f"""
        <div id="fea-loading-overlay">
            <div class="fea-loading-card">
                <div class="fea-loading-title">Procesando datos</div>
                <div class="fea-loading-percent">{percent}%</div>
                <div class="fea-loading-progress">
                    <div class="fea-loading-progress-bar" style="width: {percent}%;"></div>
                </div>
                <div class="fea-loading-text">{message}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
