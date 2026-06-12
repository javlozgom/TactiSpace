from __future__ import annotations

import base64
import hashlib
import io
from contextlib import nullcontext

import matplotlib.pyplot as plt
import streamlit as st

from src.ui.components.html import render_html_block
from src.ui.components.page_header import render_badges, render_section_header


def _figure_png_bytes(fig) -> bytes:
    """Return one matplotlib figure serialized as PNG without changing its size."""
    buffer = io.BytesIO()
    fig.savefig(
        buffer,
        format="png",
        dpi=260,
        bbox_inches="tight",
        pad_inches=0.02,
        facecolor=fig.get_facecolor(),
        edgecolor="none",
    )
    return buffer.getvalue()


def _render_png_bytes(image_bytes: bytes, width: int | str = "stretch") -> None:
    """Render figure bytes while preserving the current layout sizing rules."""
    if width == "stretch":
        st.image(image_bytes, width="stretch")
        return

    encoded_image = base64.b64encode(image_bytes).decode("ascii")
    pixel_width = int(width) if isinstance(width, (int, float)) else 900
    st.markdown(
        f"""
        <div style="display:flex; justify-content:center; width:100%;">
            <img
                src="data:image/png;base64,{encoded_image}"
                style="width:{pixel_width}px; max-width:100%; height:auto; display:block;"
            />
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_matplotlib_figure(fig, width: int | str = "stretch") -> bytes:
    """Render one matplotlib figure as a high-resolution PNG."""
    image_bytes = _figure_png_bytes(fig)
    _render_png_bytes(image_bytes, width=width)
    return image_bytes


def _plot_widget_key(prefix: str, title: str, description: str | None, image_bytes: bytes) -> str:
    """Build one stable widget key per rendered plot card."""
    digest = hashlib.sha1()
    digest.update(title.encode("utf-8", errors="ignore"))
    digest.update((description or "").encode("utf-8", errors="ignore"))
    digest.update(image_bytes[:128])
    return f"{prefix}_{digest.hexdigest()[:12]}"


def _render_plot_explorer(fig, image_bytes: bytes, *, title: str, description: str | None) -> None:
    """Render a compact explorer without changing the default plot size."""
    download_key = _plot_widget_key("plot_download", title, description, image_bytes)
    render_html_block(
        """
        <div class="fea-plot-toolbar">
            <div class="fea-plot-toolbar-copy">
                <strong>Exploración</strong> · abre un visor ampliado con toolbar de Streamlit y exportación PNG.
            </div>
        </div>
        """
    )
    with st.popover("🔎 Explorar plot", use_container_width=False):
        st.caption("Visor ampliado del gráfico. El tamaño por defecto del layout no cambia.")
        st.pyplot(fig, width="stretch", clear_figure=False)
        st.download_button(
            "Descargar PNG",
            data=image_bytes,
            file_name="tactispace_plot.png",
            mime="image/png",
            width="stretch",
            icon=":material/download:",
            key=download_key,
        )


def render_plot_card(
    title: str,
    fig=None,
    description: str | None = None,
    allow_expand: bool = True,
    badges: list[tuple[str, str]] | None = None,
    figure_width: int | str = "stretch",
    border: bool = True,
) -> None:
    """Render a plot inside a bounded card with stable spacing."""
    _ = allow_expand
    container = st.container(border=True) if border else nullcontext()
    with container:
        render_section_header(title, description)
        if badges:
            render_badges(badges)
        if fig is not None:
            image_bytes = _render_matplotlib_figure(fig, width=figure_width)
            _render_plot_explorer(fig, image_bytes, title=title, description=description)
            plt.close(fig)
        else:
            st.caption("No hay figura disponible para esta visualización.")


def plot_figure(fig) -> None:
    """Render and close one matplotlib figure."""
    _render_matplotlib_figure(fig)
    plt.close(fig)
