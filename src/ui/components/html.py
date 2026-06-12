from __future__ import annotations

import re
from html import escape
from textwrap import dedent

import streamlit as st


def display_text(value: object) -> str:
    """Return readable text, repairing common UTF-8-as-Latin-1 mojibake."""
    text = str(value)
    if any(marker in text for marker in ("Ãƒ", "Ã‚", "Ã¢")):
        try:
            repaired = text.encode("latin1").decode("utf-8")
        except Exception:
            return text
        if repaired:
            return repaired
    return text


def html_text(value: object) -> str:
    """Escape dynamic text before injecting it into HTML UI blocks."""
    return escape(display_text(value), quote=True)


def render_html_block(markup: str) -> None:
    """Render a complete HTML fragment without Markdown code-block side effects."""
    clean_markup = dedent(markup).strip()
    clean_markup = re.sub(r">\s+<", "><", clean_markup)
    clean_markup = re.sub(r"\s*\n\s*", " ", clean_markup)
    st.markdown(clean_markup, unsafe_allow_html=True)


def tone_class(value: object, fallback: str = "neutral") -> str:
    """Return a conservative CSS class suffix for visual tone names."""
    raw_value = str(value or fallback).strip().lower()
    cleaned_value = re.sub(r"[^a-z0-9_-]+", "-", raw_value).strip("-")
    return cleaned_value or fallback
