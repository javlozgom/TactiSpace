from __future__ import annotations


def build_widgets_css() -> str:
    """Return CSS for Streamlit widgets and repeated interactive controls."""
    return """
        .stButton > button,
        [data-testid="stDownloadButton"] > button {
            min-height: var(--fea-button-height-lg) !important;
            height: var(--fea-button-height-lg) !important;
            padding: 8px 16px !important;
            border-radius: 999px !important;
            border: 1px solid var(--fea-border-strong) !important;
            background: #ffffff !important;
            color: var(--navy) !important;
            font-weight: 850 !important;
            font-size: var(--fea-button-font-size) !important;
            box-shadow: none !important;
            white-space: normal !important;
            word-break: normal !important;
            overflow-wrap: normal !important;
            hyphens: none !important;
            text-align: center !important;
            line-height: 1.12 !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            transition:
                background-color .18s ease,
                border-color .18s ease,
                color .18s ease,
                box-shadow .18s ease,
                transform .18s ease !important;
        }

        .stButton > button:hover,
        [data-testid="stDownloadButton"] > button:hover {
            border-color: #bfdbfe !important;
            background: #eff6ff !important;
            color: var(--blue) !important;
            box-shadow: 0 9px 22px rgba(37, 99, 235, .13) !important;
            transform: translateY(-1px) !important;
        }

        .stButton > button[kind="primary"],
        .stButton > button[data-testid="stBaseButton-primary"] {
            border-color: #bfdbfe !important;
            background: #eff6ff !important;
            color: var(--blue) !important;
            box-shadow: 0 11px 26px rgba(37, 99, 235, .15) !important;
        }

        .stButton > button[kind="primary"]:hover,
        .stButton > button[data-testid="stBaseButton-primary"]:hover {
            border-color: #93c5fd !important;
            background: #dbeafe !important;
            color: #1d4ed8 !important;
            box-shadow: 0 13px 28px rgba(37, 99, 235, .18) !important;
        }

        .stButton > button p,
        [data-testid="stDownloadButton"] > button p,
        [data-baseweb="button-group"] button p {
            margin: 0 !important;
            font-size: inherit !important;
            line-height: inherit !important;
        }

        .stButton > button [data-testid="stMarkdownContainer"],
        [data-testid="stDownloadButton"] > button [data-testid="stMarkdownContainer"],
        [data-baseweb="button-group"] button [data-testid="stMarkdownContainer"] {
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
            gap: 0.46rem !important;
        }

        [class*="st-key-nav_cell_"] .stButton > button,
        .fea-nav-cell .stButton > button {
            position: relative !important;
            width: 100% !important;
            min-height: var(--fea-button-height-lg) !important;
            height: var(--fea-button-height-lg) !important;
            padding: 8px 14px !important;
            border-radius: 12px !important;
            border: 1px solid transparent !important;
            background: transparent !important;
            color: #374151 !important;
            font-size: .89rem !important;
            font-weight: 750 !important;
            white-space: normal !important;
            word-break: normal !important;
            overflow-wrap: normal !important;
            hyphens: none !important;
            line-height: 1.12 !important;
            box-shadow: none !important;
        }

        [class*="st-key-nav_cell_"] .stButton > button:hover,
        .fea-nav-cell .stButton > button:hover {
            background: #f8fafc !important;
            border-color: #e2e8f0 !important;
            color: var(--navy) !important;
            box-shadow: 0 9px 22px rgba(15, 23, 42, .09) !important;
        }

        [class*="st-key-nav_cell_"][class*="_active"] .stButton > button,
        [class*="st-key-nav_cell_"][class*="_active"] .stButton > button:hover,
        .fea-nav-active .stButton > button,
        .fea-nav-active .stButton > button:hover {
            color: var(--blue) !important;
            font-weight: 900 !important;
            background: #eff6ff !important;
            border-color: #bfdbfe !important;
            box-shadow: 0 11px 26px rgba(37, 99, 235, .15) !important;
        }

        [class*="st-key-nav_cell_"][class*="_active"] .stButton > button::after,
        .fea-nav-active .stButton > button::after {
            content: "";
            position: absolute;
            left: 16px;
            right: 16px;
            bottom: -8px;
            height: 3px;
            border-radius: 999px;
            background: var(--blue);
        }

        .fea-filter-title-block {
            display: grid;
            grid-template-columns: 44px minmax(0, 1fr);
            gap: 6px 12px;
            align-items: start;
            padding-bottom: 16px;
            margin-bottom: 18px;
            border-bottom: 1px solid #e2e8f0;
        }

        .fea-filter-title-icon {
            grid-row: 1 / span 2;
            width: 44px;
            height: 44px;
            border-radius: 12px;
        }

        .fea-filter-title-block h3 {
            margin: 0 !important;
            color: var(--navy);
            font-size: 1.28rem !important;
            font-weight: 950;
        }

        .fea-filter-title-block p {
            margin: 2px 0 0 !important;
            color: var(--fea-muted);
            font-size: .81rem;
            line-height: 1.42;
        }

        .fea-filter-label {
            display: grid;
            grid-template-columns: 30px minmax(0, 1fr);
            gap: 2px 9px;
            align-items: start;
            margin: 0 0 9px !important;
        }

        .fea-filter-label-icon {
            grid-row: 1 / span 2;
            width: 30px;
            height: 30px;
            color: var(--teal);
            background: #f0fdfa;
            border-color: #99f6e4;
            border-radius: 9px;
        }

        .fea-filter-label span:not(.fea-filter-label-icon) {
            color: var(--navy);
            font-size: .88rem;
            font-weight: 900;
        }

        .fea-filter-label small {
            color: var(--fea-muted);
            font-size: .78rem;
        }

        .st-key-global_filters_panel [data-testid="stSelectbox"],
        .st-key-global_filters_panel [data-testid="stSlider"] {
            margin-bottom: 18px !important;
        }

        div[data-baseweb="select"] > div,
        div[data-baseweb="base-input"] input,
        textarea {
            min-height: 42px !important;
            border-radius: 10px !important;
            border-color: #cbd5e1 !important;
            background: #ffffff !important;
        }

        .fea-filter-summary,
        .fea-filter-performance {
            display: grid;
            gap: 10px;
            padding: 14px;
            margin: 15px 0;
            background: linear-gradient(180deg, #ffffff, #fbfdff);
            border: 1px solid var(--fea-border);
            border-radius: var(--fea-radius);
            box-shadow: var(--fea-shadow-soft);
        }

        .fea-filter-summary h4,
        .fea-filter-performance h4 {
            margin: 0 0 4px !important;
            color: var(--navy);
            font-size: .98rem;
            font-weight: 950;
        }

        .fea-filter-summary-item {
            display: grid;
            grid-template-columns: 24px minmax(0, 1fr) auto;
            align-items: center;
            gap: 9px;
            min-height: 28px;
            color: var(--fea-muted);
            font-size: .86rem;
        }

        .fea-filter-summary-item strong {
            color: var(--blue);
            font-weight: 950;
            font-variant-numeric: tabular-nums;
        }

        [data-testid="stDataFrame"],
        .stDataFrame {
            width: 100% !important;
            max-width: 100% !important;
            overflow: hidden !important;
            border-radius: var(--fea-radius) !important;
            border: 1px solid var(--fea-border) !important;
            box-shadow: var(--fea-shadow-soft) !important;
            background: #ffffff !important;
        }

        [data-testid="stDataFrame"] > div,
        .stDataFrame > div {
            max-width: 100% !important;
        }

        [data-testid="stDataFrame"] [role="columnheader"] {
            background: #f8fafc !important;
            color: #475569 !important;
            font-size: .78rem !important;
            font-weight: 900 !important;
            text-transform: uppercase !important;
        }

        [data-testid="stPyplot"],
        [data-testid="stPlotlyChart"],
        img,
        figure,
        canvas,
        iframe {
            max-width: 100% !important;
            border-radius: var(--fea-radius-sm) !important;
        }

        [data-testid="stPyplot"],
        [data-testid="stPlotlyChart"] {
            margin: 8px 0 4px !important;
        }

        [data-testid="stExpander"] {
            border: 1px solid var(--fea-border) !important;
            border-radius: var(--fea-radius) !important;
            background: rgba(255, 255, 255, .86) !important;
            box-shadow: var(--fea-shadow-soft) !important;
            margin: 12px 0 0 !important;
        }

        [data-testid="stExpander"] summary {
            font-weight: 900 !important;
            color: var(--navy) !important;
        }

        .stTabs [data-baseweb="tab-list"] {
            gap: 9px !important;
        }

        .stTabs [data-baseweb="tab"] {
            min-height: 42px !important;
            height: 42px !important;
            padding: 0 16px !important;
            border: 1px solid #e2e8f0 !important;
            border-radius: 999px !important;
            background: #ffffff !important;
            color: #475569 !important;
            font-weight: 850 !important;
            font-size: .89rem !important;
        }

        .stTabs [aria-selected="true"] {
            background: #eff6ff !important;
            color: var(--blue) !important;
            border-color: #bfdbfe !important;
            box-shadow: 0 11px 26px rgba(37, 99, 235, .15) !important;
        }

        .fea-step-number {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 34px;
            height: 34px;
            color: var(--blue);
            background: #eff6ff;
            border: 1px solid #bfdbfe;
            border-radius: 999px;
            font-weight: 950;
        }

        .fea-icon,
        .fea-context-icon,
        .fea-filter-icon,
        .fea-filter-title-svg,
        .fea-filter-summary-icon {
            width: 18px;
            height: 18px;
        }

        [data-testid="stVerticalBlockBorderWrapper"] {
            margin: 12px 0 16px !important;
            overflow: hidden !important;
        }

        [data-testid="stVerticalBlockBorderWrapper"] > div {
            padding: 15px 16px !important;
        }

        [data-testid="stAlert"] {
            border-radius: var(--fea-radius) !important;
            border: 1px solid var(--fea-border) !important;
            box-shadow: var(--fea-shadow-soft) !important;
            margin: 12px 0 16px !important;
        }

        .stCaptionContainer,
        [data-testid="stCaptionContainer"] {
            margin-top: 3px !important;
            margin-bottom: 5px !important;
        }

        .stCaptionContainer p,
        [data-testid="stCaptionContainer"] p,
        .stCaption {
            color: #64748b !important;
            font-size: var(--fea-caption-size) !important;
            line-height: 1.48 !important;
        }

        .stMarkdown p,
        .stMarkdown li {
            font-size: var(--fea-body-size) !important;
            line-height: 1.64 !important;
        }

        .stMarkdown ul,
        .stMarkdown ol {
            margin-top: 9px !important;
            margin-bottom: 9px !important;
            padding-left: 1.15rem !important;
        }

        .stMarkdown li + li {
            margin-top: 5px !important;
        }

        hr {
            margin: 15px 0 17px !important;
            border-top: 1px solid rgba(148, 163, 184, .22) !important;
        }

        .fea-inline-note {
            margin: 2px 0 0 !important;
            color: #64748b !important;
            font-size: .84rem !important;
            line-height: 1.48 !important;
        }

        .fea-block-note {
            margin: 6px 0 2px !important;
            color: #475569 !important;
            font-size: .87rem !important;
            line-height: 1.52 !important;
        }

        [data-baseweb="button-group"] {
            display: flex !important;
            flex-wrap: wrap !important;
            gap: 9px !important;
            margin: 5px 0 3px !important;
        }

        [data-baseweb="button-group"] button,
        [data-testid="stRadio"] [role="radiogroup"] label {
            min-height: 42px !important;
            padding: 0 14px !important;
            border-radius: 999px !important;
            border: 1px solid #dbe4f0 !important;
            background: #ffffff !important;
            color: #475569 !important;
            font-weight: 800 !important;
            box-shadow: none !important;
            transition:
                background-color .18s ease,
                border-color .18s ease,
                color .18s ease,
                box-shadow .18s ease,
                transform .18s ease !important;
        }

        [data-baseweb="button-group"] button:hover,
        [data-testid="stRadio"] [role="radiogroup"] label:hover {
            border-color: #bfdbfe !important;
            background: #f8fbff !important;
            color: var(--navy) !important;
            box-shadow: 0 9px 22px rgba(15, 23, 42, .09) !important;
            transform: translateY(-1px) !important;
        }

        [data-baseweb="button-group"] button[aria-pressed="true"],
        [data-baseweb="button-group"] button[aria-selected="true"],
        [data-testid="stRadio"] [role="radiogroup"] label:has(input:checked) {
            background: #eff6ff !important;
            color: var(--blue) !important;
            border-color: #bfdbfe !important;
            box-shadow: 0 11px 26px rgba(37, 99, 235, .15) !important;
        }

        [data-testid="stRadio"] [role="radiogroup"] {
            display: flex !important;
            flex-wrap: wrap !important;
            gap: 9px !important;
        }

        [data-testid="stPopover"] button {
            min-height: 38px !important;
            height: 38px !important;
            padding: 0 12px !important;
            border-radius: 999px !important;
            border: 1px solid rgba(148, 163, 184, .26) !important;
            background: rgba(255, 255, 255, .92) !important;
            color: var(--navy) !important;
            font-size: .84rem !important;
            font-weight: 800 !important;
            box-shadow: none !important;
        }

        [data-testid="stPopover"] button:hover {
            background: #f8fbff !important;
            border-color: #bfdbfe !important;
            color: var(--blue) !important;
        }

        [data-testid="stPopoverContent"] {
            border-radius: 16px !important;
            border: 1px solid var(--fea-border) !important;
            box-shadow: var(--fea-shadow) !important;
        }

        @media (max-width: 900px) {
            .fea-nav-active .stButton > button::after {
                display: none;
            }
        }
    """
