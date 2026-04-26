import streamlit as st

DARK_CSS = """
<style>
    /* Global dark background */
    .stApp {
        background-color: #0e1117 !important;
        color: #e0e0e0 !important;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #161b22 !important;
    }
    section[data-testid="stSidebar"] .stMarkdown, 
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] .stRadio > div {
        color: #c9d1d9 !important;
    }

    /* Main content area */
    .main .block-container {
        padding-top: 2rem;
        max-width: 1200px;
    }

    /* Metric cards */
    [data-testid="stMetricValue"] {
        font-size: 2rem !important;
        font-weight: 700 !important;
        color: #58a6ff !important;
    }
    [data-testid="stMetricLabel"] {
        color: #8b949e !important;
        font-size: 0.85rem !important;
    }
    [data-testid="stMetricDelta"] {
        font-size: 0.8rem !important;
    }

    /* Dataframe styling */
    .stDataFrame {
        border: 1px solid #30363d !important;
        border-radius: 8px !important;
    }

    /* Expander */
    .streamlit-expanderHeader {
        background-color: #161b22 !important;
        border: 1px solid #30363d !important;
        border-radius: 6px !important;
        color: #c9d1d9 !important;
    }
    .streamlit-expanderContent {
        background-color: #0d1117 !important;
        border: 1px solid #30363d !important;
        border-radius: 0 0 6px 6px !important;
    }

    /* Buttons */
    .stButton > button {
        border-radius: 6px !important;
        font-weight: 600 !important;
        transition: all 0.15s ease !important;
    }
    .stButton > button:hover {
        transform: translateY(-1px) !important;
    }

    /* Input fields */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > select {
        background-color: #161b22 !important;
        color: #e0e0e0 !important;
        border-color: #30363d !important;
    }

    /* Success / Error / Warning / Info boxes */
    .stSuccess { background-color: #0d2818 !important; border-left: 4px solid #3fb950 !important; color: #c9d1d9 !important; }
    .stError { background-color: #2d1117 !important; border-left: 4px solid #f85149 !important; color: #c9d1d9 !important; }
    .stWarning { background-color: #2d2000 !important; border-left: 4px solid #d29922 !important; color: #c9d1d9 !important; }
    .stInfo { background-color: #0d1d33 !important; border-left: 4px solid #58a6ff !important; color: #c9d1d9 !important; }

    /* Form styling */
    .stForm {
        background-color: #161b22 !important;
        border: 1px solid #30363d !important;
        border-radius: 8px !important;
        padding: 1.5rem !important;
    }

    /* Dividers */
    .stDivider {
        border-top-color: #30363d !important;
    }

    /* Page links */
    .stPageLink {
        color: #c9d1d9 !important;
    }

    /* Scrollbar */
    ::-webkit-scrollbar {
        width: 8px !important;
    }
    ::-webkit-scrollbar-track {
        background: #0e1117 !important;
    }
    ::-webkit-scrollbar-thumb {
        background: #30363d !important;
        border-radius: 4px !important;
    }

    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px !important;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 4px 4px 0 0 !important;
        padding: 8px 16px !important;
        color: #8b949e !important;
    }
    .stTabs [aria-selected="true"] {
        background-color: #161b22 !important;
        color: #58a6ff !important;
        border-bottom: 2px solid #58a6ff !important;
    }
</style>
"""

def apply_dark_theme():
    st.markdown(DARK_CSS, unsafe_allow_html=True)


STATUS_BADGES = {
    "scratch": ("⚠️", "#d29922"),
    "reviewed": ("✅", "#3fb950"),
    "canonical": ("👑", "#58a6ff"),
    "stale": ("⏳", "#8b949e"),
    "conflicted": ("⚡", "#f85149"),
    "archived": ("📦", "#6e7681"),
}

TYPE_ICONS = {
    "fact": "📌",
    "preference": "💛",
    "decision": "🎯",
    "workflow": "🔄",
    "project_note": "📒",
}

def status_badge(status: str) -> str:
    icon, color = STATUS_BADGES.get(status, ("•", "#8b949e"))
    return f'<span style="color:{color};font-weight:600;">{icon} {status}</span>'

def type_icon(t: str) -> str:
    icon = TYPE_ICONS.get(t, "📄")
    return f"{icon} {t}"