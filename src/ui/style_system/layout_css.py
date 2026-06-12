from __future__ import annotations


def build_layout_css(header_background_image: str) -> str:
    """Return layout CSS for sticky panels, overlay, header and nav shell."""
    return f"""
        .st-key-app_header_fixed,
        .st-key-app_nav_fixed,
        .st-key-global_filters_panel,
        .st-key-main_content_panel {{
            width: 100% !important;
            min-width: 0 !important;
            max-width: 100% !important;
            overflow: visible !important;
        }}

        .st-key-main_content_panel,
        .st-key-global_filters_panel {{
            background: linear-gradient(180deg, #ffffff, #fbfdff) !important;
            border: 1px solid var(--fea-border) !important;
            border-radius: var(--fea-radius) !important;
            box-shadow: var(--fea-shadow-soft) !important;
        }}

        .st-key-main_content_panel {{ padding: 20px !important; }}

        .st-key-global_filters_panel {{
            padding: 21px 18px !important;
            background: rgba(255, 255, 255, .82) !important;
            backdrop-filter: blur(18px) !important;
            box-shadow: var(--fea-shadow) !important;
        }}

        @media (min-width: 901px) {{
            .st-key-global_filters_panel,
            .st-key-main_content_panel {{
                position: sticky !important;
                top: var(--fea-sticky-top) !important;
                align-self: flex-start !important;
                max-height: calc(100vh - var(--fea-sticky-top) - var(--fea-sticky-bottom)) !important;
                overflow-x: hidden !important;
                overflow-y: auto !important;
                overscroll-behavior: contain !important;
                scrollbar-gutter: stable !important;
            }}
        }}

        #fea-loading-overlay {{
            position: fixed !important;
            inset: 0 !important;
            z-index: 999999 !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            width: 100vw !important;
            height: 100vh !important;
            background: rgba(248, 251, 255, .84) !important;
            backdrop-filter: blur(14px) !important;
        }}

        .fea-loading-card {{
            width: min(430px, calc(100vw - 32px)) !important;
            padding: 24px !important;
            text-align: center !important;
            background: rgba(255, 255, 255, .92) !important;
            border: 1px solid var(--fea-border) !important;
            border-radius: var(--fea-radius) !important;
            box-shadow: var(--fea-shadow) !important;
        }}

        .fea-loading-title {{
            margin: 0 !important;
            color: var(--fea-muted) !important;
            font-size: .78rem !important;
            font-weight: 850 !important;
            text-transform: uppercase !important;
        }}

        .fea-loading-percent {{
            margin-top: 8px !important;
            color: var(--blue) !important;
            font-size: 2.35rem !important;
            font-weight: 900 !important;
            line-height: 1 !important;
        }}

        .fea-loading-progress {{
            width: 100% !important;
            height: 10px !important;
            margin-top: 14px !important;
            overflow: hidden !important;
            background: #e2e8f0 !important;
            border-radius: 999px !important;
        }}

        .fea-loading-progress-bar {{
            height: 100% !important;
            border-radius: 999px !important;
            background: var(--blue) !important;
        }}

        .fea-loading-text {{
            margin-top: 12px !important;
            color: var(--fea-muted) !important;
            font-size: .92rem !important;
        }}

        .st-key-app_header_fixed {{
            position: sticky !important;
            top: 0 !important;
            z-index: 40 !important;
            margin-bottom: 0 !important;
            padding: 28px 20px 24px !important;
            overflow: hidden !important;
            background:
                linear-gradient(90deg, rgba(255, 255, 255, .95) 0%, rgba(255, 255, 255, .86) 44%, rgba(255, 255, 255, .72) 100%),
                linear-gradient(180deg, rgba(248, 251, 255, .52), rgba(239, 246, 255, .66)),
                {header_background_image} !important;
            background-size: cover !important;
            background-position: center 50% !important;
            backdrop-filter: blur(18px) !important;
            border: 1px solid rgba(226, 232, 240, .96) !important;
            border-radius: var(--fea-radius) var(--fea-radius) 0 0 !important;
            box-shadow: 0 12px 30px rgba(15, 23, 42, .06) !important;
        }}

        .fea-topbar {{
            display: flex !important;
            align-items: center !important;
            gap: 16px !important;
            min-width: 0 !important;
            min-height: 104px !important;
        }}

        .fea-logo {{
            width: 52px !important;
            height: 52px !important;
            flex: 0 0 52px !important;
            display: grid !important;
            place-items: center !important;
        }}

        .fea-logo-icon {{ width: 36px !important; height: 36px !important; }}

        .fea-logo-image {{
            width: 52px !important;
            height: 52px !important;
            object-fit: contain !important;
            display: block !important;
        }}

        .fea-title {{
            min-width: 0 !important;
            display: flex !important;
            flex-direction: column !important;
            justify-content: center !important;
            min-height: 104px !important;
        }}

        .fea-title h1 {{
            margin: 0 !important;
            color: var(--navy) !important;
            font-size: clamp(1.35rem, 2vw, 1.82rem) !important;
            font-weight: 950 !important;
            line-height: 1.08 !important;
            text-shadow: 0 1px 2px rgba(255, 255, 255, .82) !important;
        }}

        .fea-title p {{
            margin: 4px 0 0 0 !important;
            color: #334155 !important;
            font-size: .92rem !important;
            line-height: 1.4 !important;
            text-shadow: 0 1px 2px rgba(255, 255, 255, .78) !important;
        }}

        .st-key-app_nav_fixed {{
            padding: 12px 12px 15px !important;
            margin-bottom: 18px !important;
            background: rgba(255, 255, 255, .92) !important;
            border: 1px solid rgba(226, 232, 240, .96) !important;
            border-top: none !important;
            border-radius: 0 0 var(--fea-radius) var(--fea-radius) !important;
            box-shadow: var(--fea-shadow-soft) !important;
        }}

        .fea-nav-row [data-testid="column"] {{
            padding: 0 !important;
        }}

        @media (max-width: 900px) {{
            .block-container {{
                padding: 12px !important;
            }}
            .st-key-main_content_panel,
            .st-key-global_filters_panel {{
                padding: 15px !important;
                position: static !important;
                max-height: none !important;
                overflow: visible !important;
            }}
        }}
    """
