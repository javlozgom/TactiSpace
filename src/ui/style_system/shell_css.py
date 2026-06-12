from __future__ import annotations

from src.ui.theme.tokens import css_token_vars


def build_shell_css() -> str:
    """Return the global shell and layout CSS foundations."""
    token_vars = css_token_vars()
    return f"""
        :root {{
            --blue: #0b63f6;
            --navy: #071338;
            --green: #16a34a;
            --red: #dc2626;
            --purple: #7c3aed;
            --teal: #0f766e;
            --orange: #ea580c;
            --fea-bg: #f8fbff;
            --fea-card: #ffffff;
            --fea-card-soft: #fbfdff;
            --fea-border: rgba(15, 23, 42, .10);
            --fea-border-strong: #cbd5e1;
            --fea-text: var(--navy);
            --fea-muted: #64748b;
            --fea-radius: 16px;
            --fea-radius-sm: 12px;
            --fea-shadow: 0 20px 46px rgba(15, 23, 42, .075);
            --fea-shadow-soft: 0 10px 28px rgba(15, 23, 42, .05);
            --fea-gap: 18px;
            --fea-gap-lg: 24px;
            --fea-gap-xl: 32px;
            --fea-sticky-top: 152px;
            --fea-sticky-bottom: 20px;
            --fea-title-size: clamp(1.52rem, 1.6vw, 1.76rem);
            --fea-subtitle-size: .99rem;
            --fea-section-size: 1.08rem;
            --fea-body-size: .95rem;
            --fea-card-padding: 17px;
            --fea-card-padding-lg: 20px;
            --fea-caption-size: .81rem;
            --fea-button-font-size: .92rem;
            --fea-button-height: 48px;
            --fea-button-height-lg: 54px;
            --fea-emoji-scale: 1.03;
            {token_vars}
        }}

        *,
        *::before,
        *::after {{
            box-sizing: border-box;
            letter-spacing: 0 !important;
        }}

        html,
        body,
        .stApp,
        [data-testid="stAppViewContainer"],
        [data-testid="stAppViewContainer"] > .main {{
            min-height: 100vh !important;
            overflow-x: hidden !important;
            color: var(--fea-text) !important;
            font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif !important;
            background:
                radial-gradient(circle at 8% 0%, rgba(37, 99, 235, .12), transparent 28%),
                radial-gradient(circle at 82% 12%, rgba(20, 184, 166, .10), transparent 30%),
                linear-gradient(180deg, #f8fbff 0%, #ffffff 45%, #f4f7fb 100%) !important;
        }}

        ::-webkit-scrollbar {{ width: 8px; height: 8px; }}
        ::-webkit-scrollbar-track {{ background: transparent; }}
        ::-webkit-scrollbar-thumb {{ background: #cbd5e1; border-radius: 999px; }}
        * {{ scrollbar-width: thin; scrollbar-color: #cbd5e1 transparent; }}

        header[data-testid="stHeader"],
        [data-testid="stToolbar"],
        [data-testid="stDecoration"],
        [data-testid="stStatusWidget"],
        [data-testid="stDeployButton"],
        .stDeployButton,
        #MainMenu,
        footer,
        section[data-testid="stSidebar"] {{
            display: none !important;
            visibility: hidden !important;
            height: 0 !important;
            min-height: 0 !important;
            max-height: 0 !important;
            opacity: 0 !important;
            pointer-events: none !important;
        }}

        .block-container {{
            width: 100% !important;
            max-width: 1840px !important;
            padding: 14px 20px 30px !important;
        }}

        [data-testid="stVerticalBlock"],
        [data-testid="stHorizontalBlock"],
        [data-testid="column"],
        [data-testid="stElementContainer"] {{
            min-width: 0 !important;
            max-width: 100% !important;
        }}

        [data-testid="stHorizontalBlock"] {{
            gap: var(--fea-gap) !important;
        }}

        [data-testid="stVerticalBlock"] > [data-testid="stElementContainer"] {{
            margin-bottom: 0.28rem !important;
        }}
    """
