"""AI Retail Decision Copilot — Professional SaaS UI"""

import streamlit as st
import time
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent))

from src.config.config import Config
from src.document_ingestion.document_processor import DocumentProcessor
from src.vectorstore.vectorstore import VectorStore
from src.analytics.data_ingester import DataIngester
from src.analytics.analytics_engine import AnalyticsEngine
from src.analytics.chart_generator import generate_charts
from src.analytics.question_suggester import generate_suggestions
from src.graph_builder.graph_builder import CopilotGraphBuilder

# ── Page config — must be first ─────────────────────────────────────────────
st.set_page_config(
    page_title="Retail Copilot",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": None,
        "Report a bug": None,
        "About": "AI Retail Decision Copilot — Built by Tanishka Arora",
    }
)

# ── All CSS in one place ─────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* ── Reset & base ── */
*, *::before, *::after { box-sizing: border-box; }

html, body, [class*="css"], .stApp {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    background-color: #0a0f1e;
    color: #e2e8f0;
}

/* ── Hide default Streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display: none; }
.viewerBadge_container__r5tak { display: none; }

/* ── Main container padding ── */
.block-container {
    padding: 1.5rem 2rem 2rem;
    max-width: 1200px;
}

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background: #0d1220 !important;
    border-right: 1px solid rgba(99,102,241,0.15) !important;
    width: 300px !important;
}

section[data-testid="stSidebar"] .block-container {
    padding: 1.5rem 1rem;
}

/* ── Sidebar logo area ── */
.sidebar-logo {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 0 0 1.2rem;
    border-bottom: 1px solid rgba(255,255,255,0.06);
    margin-bottom: 1.2rem;
}

.sidebar-logo-icon {
    width: 36px;
    height: 36px;
    background: linear-gradient(135deg, #6366f1, #06b6d4);
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 18px;
    flex-shrink: 0;
}

.sidebar-logo-text {
    font-size: 15px;
    font-weight: 600;
    color: #f1f5f9;
    line-height: 1.2;
}

.sidebar-logo-sub {
    font-size: 11px;
    color: #64748b;
    font-weight: 400;
}

/* ── Sidebar section labels ── */
.sidebar-section-label {
    font-size: 10px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #475569;
    margin: 1rem 0 0.5rem;
}

/* ── File uploader ── */
[data-testid="stFileUploader"] {
    background: rgba(255,255,255,0.02) !important;
    border: 1.5px dashed rgba(99,102,241,0.3) !important;
    border-radius: 10px !important;
    padding: 0.5rem !important;
    transition: border-color 0.2s;
}

[data-testid="stFileUploader"]:hover {
    border-color: rgba(99,102,241,0.6) !important;
}

/* ── Process button ── */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%) !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    font-size: 13px !important;
    letter-spacing: 0.02em !important;
    padding: 0.6rem 1.2rem !important;
    color: white !important;
    width: 100% !important;
    transition: all 0.2s !important;
    box-shadow: 0 4px 12px rgba(99,102,241,0.3) !important;
}

.stButton > button[kind="primary"]:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 20px rgba(99,102,241,0.45) !important;
}

/* ── Secondary buttons (pills) ── */
.stButton > button[kind="secondary"],
.stButton > button:not([kind]) {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 20px !important;
    color: #94a3b8 !important;
    font-size: 12px !important;
    font-weight: 400 !important;
    padding: 0.3rem 0.8rem !important;
    transition: all 0.15s !important;
}

.stButton > button[kind="secondary"]:hover,
.stButton > button:not([kind]):hover {
    background: rgba(99,102,241,0.12) !important;
    border-color: rgba(99,102,241,0.4) !important;
    color: #a5b4fc !important;
}

/* ── Header area ── */
.app-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 0 1.5rem;
    border-bottom: 1px solid rgba(255,255,255,0.06);
    margin-bottom: 1.5rem;
}

.app-title {
    font-size: 22px;
    font-weight: 700;
    background: linear-gradient(135deg, #e2e8f0 0%, #94a3b8 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 0;
    line-height: 1.2;
}

.app-subtitle {
    font-size: 13px;
    color: #475569;
    margin: 3px 0 0;
    font-weight: 400;
}

.status-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-size: 12px;
    font-weight: 500;
    padding: 5px 12px;
    border-radius: 20px;
    background: rgba(16,185,129,0.1);
    border: 1px solid rgba(16,185,129,0.25);
    color: #34d399;
}

.status-badge-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: #10b981;
    animation: pulse 2s infinite;
}

.status-badge-offline {
    background: rgba(100,116,139,0.1);
    border-color: rgba(100,116,139,0.25);
    color: #64748b;
}

.status-badge-offline .status-badge-dot {
    background: #475569;
    animation: none;
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.4; }
}

/* ── Tabs ── */
[data-testid="stTabs"] [role="tablist"] {
    background: rgba(255,255,255,0.02);
    border-radius: 12px;
    padding: 4px;
    border: 1px solid rgba(255,255,255,0.06);
    gap: 2px;
}

[data-testid="stTabs"] button[role="tab"] {
    border-radius: 8px !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    color: #64748b !important;
    padding: 6px 16px !important;
    transition: all 0.15s !important;
    border: none !important;
}

[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
    background: rgba(99,102,241,0.15) !important;
    color: #a5b4fc !important;
    border: 1px solid rgba(99,102,241,0.25) !important;
}

[data-testid="stTabs"] button[role="tab"]:hover {
    color: #94a3b8 !important;
    background: rgba(255,255,255,0.04) !important;
}

/* ── KPI metric cards ── */
[data-testid="metric-container"] {
    background: rgba(255,255,255,0.03) !important;
    border: 1px solid rgba(255,255,255,0.07) !important;
    border-radius: 14px !important;
    padding: 1.1rem 1.25rem !important;
    transition: all 0.2s !important;
    position: relative;
    overflow: hidden;
}

[data-testid="metric-container"]::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, #6366f1, #06b6d4);
    opacity: 0;
    transition: opacity 0.2s;
}

[data-testid="metric-container"]:hover {
    border-color: rgba(99,102,241,0.25) !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 24px rgba(0,0,0,0.2) !important;
}

[data-testid="metric-container"]:hover::before {
    opacity: 1;
}

[data-testid="stMetricLabel"] {
    font-size: 11px !important;
    font-weight: 500 !important;
    color: #64748b !important;
    text-transform: uppercase !important;
    letter-spacing: 0.06em !important;
}

[data-testid="stMetricValue"] {
    font-size: 1.6rem !important;
    font-weight: 700 !important;
    color: #e2e8f0 !important;
    letter-spacing: -0.02em !important;
}

/* ── Info / success / warning boxes ── */
[data-testid="stAlert"] {
    border-radius: 10px !important;
    border-left-width: 3px !important;
    font-size: 13px !important;
}

/* ── Chat messages ── */
[data-testid="stChatMessage"] {
    background: rgba(255,255,255,0.02) !important;
    border: 1px solid rgba(255,255,255,0.05) !important;
    border-radius: 14px !important;
    padding: 1rem 1.25rem !important;
    margin-bottom: 0.75rem !important;
}

[data-testid="stChatMessage"][data-testid*="user"] {
    background: rgba(99,102,241,0.06) !important;
    border-color: rgba(99,102,241,0.15) !important;
}

/* ── Chat input ── */
[data-testid="stChatInput"] {
    border-radius: 14px !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    background: rgba(255,255,255,0.03) !important;
    font-size: 14px !important;
    transition: border-color 0.2s !important;
}

[data-testid="stChatInput"]:focus-within {
    border-color: rgba(99,102,241,0.5) !important;
    box-shadow: 0 0 0 3px rgba(99,102,241,0.1) !important;
}

/* ── Expanders ── */
[data-testid="stExpander"] {
    border: 1px solid rgba(255,255,255,0.06) !important;
    border-radius: 10px !important;
    background: rgba(255,255,255,0.02) !important;
    overflow: hidden !important;
}

[data-testid="stExpander"] summary {
    font-size: 12px !important;
    color: #64748b !important;
    font-weight: 500 !important;
    padding: 0.6rem 0.75rem !important;
}

/* ── Section divider ── */
.section-divider {
    border: none;
    border-top: 1px solid rgba(255,255,255,0.06);
    margin: 1.25rem 0;
}

/* ── Empty state ── */
.empty-state {
    text-align: center;
    padding: 3rem 1rem;
    color: #334155;
}

.empty-state-icon {
    font-size: 2.5rem;
    margin-bottom: 0.75rem;
    display: block;
}

.empty-state-title {
    font-size: 15px;
    font-weight: 500;
    color: #475569;
    margin-bottom: 0.4rem;
}

.empty-state-sub {
    font-size: 13px;
    color: #334155;
}

/* ── Data quality badge ── */
.quality-badge {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    font-size: 11px;
    font-weight: 500;
    padding: 3px 10px;
    border-radius: 20px;
    margin-left: 8px;
}

.quality-high {
    background: rgba(16,185,129,0.1);
    border: 1px solid rgba(16,185,129,0.25);
    color: #34d399;
}

.quality-mid {
    background: rgba(245,158,11,0.1);
    border: 1px solid rgba(245,158,11,0.25);
    color: #fbbf24;
}

.quality-low {
    background: rgba(239,68,68,0.1);
    border: 1px solid rgba(239,68,68,0.25);
    color: #f87171;
}

/* ── Route badge in chat ── */
.route-badge {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    font-size: 11px;
    font-weight: 500;
    padding: 2px 9px;
    border-radius: 20px;
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.08);
    color: #64748b;
    margin-right: 6px;
}

/* ── Suggested question pills ── */
.pill-row {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin: 0.75rem 0;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb {
    background: rgba(255,255,255,0.08);
    border-radius: 3px;
}
::-webkit-scrollbar-thumb:hover {
    background: rgba(255,255,255,0.15);
}

/* ── Plotly chart background fix ── */
.js-plotly-plot .plotly,
.js-plotly-plot .plotly .main-svg {
    background: transparent !important;
}

/* ── Code blocks ── */
code {
    background: rgba(99,102,241,0.1) !important;
    border: 1px solid rgba(99,102,241,0.2) !important;
    border-radius: 5px !important;
    padding: 1px 5px !important;
    font-size: 12px !important;
    color: #a5b4fc !important;
}

/* ── Spinner ── */
[data-testid="stSpinner"] {
    color: #6366f1 !important;
}

/* ── Progress bar ── */
[data-testid="stProgressBar"] > div {
    background: linear-gradient(90deg, #6366f1, #06b6d4) !important;
    border-radius: 4px !important;
}

/* ── Sidebar upload helper text ── */
.upload-helper {
    font-size: 11px;
    color: #475569;
    margin-top: 4px;
    line-height: 1.5;
}

/* ── Sidebar status chips ── */
.sidebar-status {
    display: flex;
    align-items: center;
    gap: 7px;
    font-size: 12px;
    color: #64748b;
    padding: 6px 0;
    border-bottom: 1px solid rgba(255,255,255,0.04);
}

.sidebar-status-dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    flex-shrink: 0;
}

.dot-ready { background: #10b981; }
.dot-empty { background: #334155; }
.dot-warn  { background: #f59e0b; }

/* ── Insight text below charts ── */
.chart-insight {
    font-size: 12px;
    color: #64748b;
    font-style: italic;
    margin: -8px 0 20px;
    padding-left: 4px;
    border-left: 2px solid rgba(99,102,241,0.3);
    line-height: 1.5;
}

/* ── Section headers inside tabs ── */
.section-header {
    font-size: 13px;
    font-weight: 600;
    color: #94a3b8;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin: 1.2rem 0 0.75rem;
}
</style>
""", unsafe_allow_html=True)


# ── Session state init ───────────────────────────────────────────────────────
def init_state():
    defaults = {
        "chat_history": [],
        "clean_df": None,
        "data_profile": None,
        "vector_store": None,
        "graph": None,
        "llm": None,
        "kpis": {},
        "charts": [],
        "suggested_questions": [],
        "prefill_question": None,
        "gemini_api_key": "",
        "groq_api_key": "",
        "use_groq_toggle": False,
        "csv_filename": None,
        "pdf_filename": None,
        "api_error_warning": None,
        "data_ready": False,
        "show_settings": False,
        "show_ready_toast": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()


def reset_for_new_upload():
    keys = [
        "graph", "llm", "clean_df", "data_profile",
        "kpis", "charts", "chat_history", "vector_store",
        "api_error_warning", "suggested_questions",
        "csv_filename", "pdf_filename", "data_ready",
    ]
    for k in keys:
        if k in st.session_state:
            del st.session_state[k]
    init_state()


# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:

    # Logo
    st.markdown("""
    <div class="sidebar-logo">
        <div class="sidebar-logo-icon">🛍️</div>
        <div>
            <div class="sidebar-logo-text">Retail Copilot</div>
            <div class="sidebar-logo-sub">AI Decision Platform</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # File uploads
    st.markdown(
        '<div class="sidebar-section-label">Data Sources</div>',
        unsafe_allow_html=True
    )

    csv_file = st.file_uploader(
        "Business Data",
        type=["csv", "xlsx", "xls"],
        help="Sales, inventory, customer, or any business CSV",
        label_visibility="collapsed",
    )
    st.markdown(
        '<div class="upload-helper">CSV or Excel · '
        'Sales, inventory, forecasts, customers</div>',
        unsafe_allow_html=True
    )

    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

    pdf_file = st.file_uploader(
        "Business Document (optional)",
        type=["pdf"],
        help="Reports, SOPs, strategy documents",
        label_visibility="collapsed",
    )
    st.markdown(
        '<div class="upload-helper">PDF optional · '
        'Reports, strategy docs, SOPs</div>',
        unsafe_allow_html=True
    )

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    # Process button
    if st.button("⚡ Analyse Data", type="primary", use_container_width=True):
        reset_for_new_upload()

        with st.spinner("Processing..."):
            import os

            # API key setup
            if st.session_state.get("use_groq_toggle") and st.session_state.get("groq_api_key"):
                os.environ["USE_GROQ"]   = "true"
                os.environ["USE_GEMINI"] = "false"
                os.environ["GROQ_API_KEY"] = st.session_state["groq_api_key"]
            elif st.session_state.get("gemini_api_key"):
                os.environ["USE_GEMINI"]    = "true"
                os.environ["GEMINI_API_KEY"] = st.session_state["gemini_api_key"]
                os.environ["GOOGLE_API_KEY"] = st.session_state["gemini_api_key"]

            import importlib
            import src.config.config as cfg_mod
            importlib.reload(cfg_mod)
            from src.config.config import Config as Cfg
            st.session_state.llm = Cfg.get_llm()

            # Process CSV
            if csv_file:
                try:
                    ingester = DataIngester()
                    df, profile = ingester.ingest(csv_file)
                    st.session_state.clean_df       = df
                    st.session_state.data_profile   = profile
                    st.session_state.csv_filename   = csv_file.name
                    engine = AnalyticsEngine()
                    st.session_state.kpis   = engine.compute_kpis(df, profile)
                    st.session_state.charts = generate_charts(df, profile)
                except ValueError as e:
                    st.error(str(e))

            # Process PDF
            vs = VectorStore()
            if pdf_file:
                import tempfile
                with tempfile.NamedTemporaryFile(
                    delete=False, suffix=".pdf"
                ) as tmp:
                    tmp.write(pdf_file.read())
                    tmp_path = tmp.name
                try:
                    processor = DocumentProcessor(
                        chunk_size=Cfg.CHUNK_SIZE,
                        chunk_overlap=Cfg.CHUNK_OVERLAP
                    )
                    docs   = processor.load_from_pdf(tmp_path)
                    chunks = processor.split_documents(docs)
                    vs.create_vectorstore(chunks)
                    st.session_state.pdf_filename = pdf_file.name
                finally:
                    os.unlink(tmp_path)

            st.session_state.vector_store = vs

            # Build graph
            st.session_state.graph = CopilotGraphBuilder(
                llm=st.session_state.llm,
                vector_store=vs,
            )
            st.session_state.graph.build()

            # Suggested questions
            if st.session_state.data_profile:
                has_pdf = pdf_file is not None
                st.session_state.suggested_questions = generate_suggestions(
                    profile=st.session_state.data_profile,
                    has_pdf=has_pdf,
                    max_questions=6,
                )

            st.session_state.data_ready = True
            st.session_state.show_ready_toast = True

    # Status panel
    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    st.markdown(
        '<div class="sidebar-section-label">Status</div>',
        unsafe_allow_html=True
    )

    csv_name = st.session_state.get("csv_filename")
    pdf_name = st.session_state.get("pdf_filename")
    has_graph = st.session_state.get("graph") is not None

    csv_dot   = "dot-ready" if csv_name  else "dot-empty"
    pdf_dot   = "dot-ready" if pdf_name  else "dot-empty"
    graph_dot = "dot-ready" if has_graph else "dot-empty"
    csv_lbl   = csv_name  or "No file uploaded"
    pdf_lbl   = pdf_name  or "No document uploaded"
    graph_lbl = "Graph ready" if has_graph else "Not initialised"

    st.markdown(f"""
    <div class="sidebar-status">
        <div class="sidebar-status-dot {csv_dot}"></div>
        <span>{csv_lbl}</span>
    </div>
    <div class="sidebar-status">
        <div class="sidebar-status-dot {pdf_dot}"></div>
        <span>{pdf_lbl}</span>
    </div>
    <div class="sidebar-status">
        <div class="sidebar-status-dot {graph_dot}"></div>
        <span>{graph_lbl}</span>
    </div>
    """, unsafe_allow_html=True)

    # Auto-dismiss ready toast
    if st.session_state.get("show_ready_toast"):
        ready_placeholder = st.empty()
        ready_placeholder.success("✅ Ready! Data loaded successfully.")
        import time as _time
        _time.sleep(1.5)
        ready_placeholder.empty()
        st.session_state["show_ready_toast"] = False

    if st.button(
        "⚙️ Settings",
        key="open_settings",
        use_container_width=True,
    ):
        st.session_state["show_settings"] = not st.session_state.get(
            "show_settings", False
        )

    # Version
    st.markdown(
        "<div style='margin-top:2rem;font-size:11px;"
        "color:#1e293b;text-align:center'>"
        "Retail Copilot v1.0 · Built by Tanishka Arora"
        "</div>",
        unsafe_allow_html=True
    )


# ── Header ───────────────────────────────────────────────────────────────────
data_ready = st.session_state.get("data_ready", False)
is_online  = bool(
    st.session_state.get("gemini_api_key") or
    st.session_state.get("groq_api_key")
)

if is_online and data_ready:
    status_html = (
        '<span class="status-badge">'
        '<span class="status-badge-dot"></span>Ready</span>'
    )
elif data_ready:
    status_html = (
        '<span class="status-badge">'
        '<span class="status-badge-dot"></span>Offline mode</span>'
    )
else:
    status_html = (
        '<span class="status-badge status-badge-offline">'
        '<span class="status-badge-dot"></span>Awaiting data</span>'
    )

st.markdown(f"""
<div class="app-header">
    <div>
        <div class="app-title">AI Retail Decision Copilot</div>
        <div class="app-subtitle">
            Upload your data · Ask in plain English · Get business insights
        </div>
    </div>
    {status_html}
</div>
""", unsafe_allow_html=True)

# API error banner
if st.session_state.get("api_error_warning"):
    col_warn, col_dismiss = st.columns([8, 1])
    with col_warn:
        st.warning(
            f"⚠️ LLM error: {st.session_state['api_error_warning']}. "
            "Running in offline mode."
        )
    with col_dismiss:
        if st.button("✕", key="dismiss_warn"):
            del st.session_state["api_error_warning"]
            st.rerun()


if st.session_state.get("show_settings", False):
    with st.expander("⚙️ Settings — API Keys", expanded=True):
        col_a, col_b = st.columns(2)
        with col_a:
            gemini_key = st.text_input(
                "Gemini API Key",
                type="password",
                value=st.session_state.get("gemini_api_key", ""),
                placeholder="AIza...",
                help="Free at aistudio.google.com"
            )
            if gemini_key:
                st.session_state["gemini_api_key"] = gemini_key
        with col_b:
            groq_key = st.text_input(
                "Groq API Key (alternative, free)",
                type="password",
                value=st.session_state.get("groq_api_key", ""),
                placeholder="gsk_...",
                help="Free at console.groq.com"
            )
            if groq_key:
                st.session_state["groq_api_key"] = groq_key

        use_groq = st.toggle(
            "Use Groq instead of Gemini",
            value=st.session_state.get("use_groq_toggle", False)
        )
        st.session_state["use_groq_toggle"] = use_groq

        if not st.session_state.get("gemini_api_key") and \
           not st.session_state.get("groq_api_key"):
            st.warning(
                "No API key set. App runs in offline mode "
                "with mock responses. Add a key and click "
                "⚡ Analyse Data to enable real AI answers."
            )
        else:
            st.success(
                "✅ API key saved. Click ⚡ Analyse Data "
                "to apply."
            )

        st.markdown(
            "<div style='font-size:11px;color:#475569;"
            "margin-top:8px'>"
            "Keys are stored in session memory only — "
            "never saved to disk or sent anywhere except "
            "the LLM provider you choose."
            "</div>",
            unsafe_allow_html=True
        )

# ── Main tabs ────────────────────────────────────────────────────────────────
tab_overview, tab_charts, tab_chat = st.tabs(
    ["  📈  Overview  ", "  📊  Charts  ", "  💬  Ask Copilot  "]
)


# ── Tab 1: Overview ──────────────────────────────────────────────────────────
with tab_overview:
    if not st.session_state.kpis:
        st.markdown("""
        <div class="empty-state">
            <span class="empty-state-icon">📂</span>
            <div class="empty-state-title">No data loaded yet</div>
            <div class="empty-state-sub">
                Upload a CSV or Excel file in the sidebar<br>
                and click ⚡ Analyse Data to get started
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # KPI cards
        st.markdown(
            '<div class="section-header">Key Metrics</div>',
            unsafe_allow_html=True
        )
        kpi_items = list(st.session_state.kpis.items())
        cols = st.columns(min(len(kpi_items), 4))
        for i, (name, value) in enumerate(kpi_items):
            cols[i % 4].metric(label=name, value=value)

        st.markdown(
            '<hr class="section-divider">',
            unsafe_allow_html=True
        )

        # Data profile
        if st.session_state.data_profile:
            st.markdown(
                '<div class="section-header">Dataset Profile</div>',
                unsafe_allow_html=True
            )
            profile = st.session_state.data_profile
            p_cols  = st.columns(3)

            with p_cols[0]:
                st.metric(
                    "Rows",
                    f"{profile.get('row_count', 0):,}"
                )
            with p_cols[1]:
                st.metric(
                    "Columns",
                    profile.get("col_count", 0)
                )
            with p_cols[2]:
                num_count = len(profile.get("numeric_cols", []))
                st.metric("Numeric Columns", num_count)

            with st.expander("📋 Column details", expanded=False):
                nums  = profile.get("numeric_cols", [])
                cats  = profile.get("cat_cols", [])
                dates = profile.get("date_cols", [])
                if nums:
                    st.caption(
                        "**Numeric:** " +
                        ", ".join(
                            f"`{c}`" for c in nums
                        )
                    )
                if cats:
                    st.caption(
                        "**Categorical:** " +
                        ", ".join(
                            f"`{c}`" for c in cats
                        )
                    )
                if dates:
                    st.caption(
                        "**Date:** " +
                        ", ".join(
                            f"`{c}`" for c in dates
                        )
                    )

            with st.expander("🔍 Preview data", expanded=False):
                st.dataframe(
                    st.session_state.clean_df.head(10),
                    use_container_width=True,
                    hide_index=True,
                )

            profile = st.session_state.data_profile
            warnings = profile.get("warnings", [])
            filtered_ids = profile.get("filtered_id_cols", [])

            # Show filtered ID columns as a subtle caption,
            # not a loud warning
            if filtered_ids:
                filtered_labels = ", ".join(
                    f"`{c}`" for c in filtered_ids
                )
                st.caption(
                    f"ℹ️ {filtered_labels} "
                    f"{'was' if len(filtered_ids) == 1 else 'were'} "
                    f"detected as ID/code columns and excluded from "
                    f"analytics. Only business metrics are used."
                )

            # Show other warnings (low row count, no numeric cols)
            # as small info boxes, not yellow warnings
            for w in warnings:
                # Skip the filtered_id warning — handled above
                if "excluded from analytics" not in w:
                    st.info(f"ℹ️ {w}", icon=None)


# ── Tab 2: Charts ────────────────────────────────────────────────────────────
with tab_charts:
    if not st.session_state.charts:
        st.markdown("""
        <div class="empty-state">
            <span class="empty-state-icon">📊</span>
            <div class="empty-state-title">No charts yet</div>
            <div class="empty-state-sub">
                Charts are auto-generated after you upload data
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        for item in st.session_state.charts:
            if len(item) == 3:
                title, fig, insight = item
            else:
                title, fig = item
                insight = ""

            st.plotly_chart(fig, use_container_width=True)
            if insight:
                st.markdown(
                    f'<div class="chart-insight">{insight}</div>',
                    unsafe_allow_html=True
                )


# ── Tab 3: Ask Copilot ───────────────────────────────────────────────────────
with tab_chat:

    # Suggested questions
    suggestions = st.session_state.get("suggested_questions", [])
    chat_history = st.session_state.get("chat_history", [])

    if suggestions and len(chat_history) == 0:
        st.markdown(
            '<div style="font-size:12px;color:#475569;'
            'margin-bottom:8px;font-weight:500">'
            '✦ Suggested questions</div>',
            unsafe_allow_html=True
        )
        pairs = [
            suggestions[i:i+2]
            for i in range(0, len(suggestions), 2)
        ]
        for pair_idx, pair in enumerate(pairs):
            cols = st.columns(len(pair))
            for col_idx, (col, sug) in enumerate(zip(cols, pair)):
                global_idx = pair_idx * 2 + col_idx
                with col:
                    if st.button(
                        f"{sug['icon']} {sug['question']}",
                        key=f"sug_{global_idx}",
                        use_container_width=True,
                    ):
                        st.session_state.prefill_question = (
                            sug["question"]
                        )
                        st.rerun()

        st.markdown(
            '<hr class="section-divider">',
            unsafe_allow_html=True
        )

    elif suggestions and len(chat_history) > 0:
        with st.expander("✦ More questions to try", expanded=False):
            pairs = [
                suggestions[i:i+2]
                for i in range(0, len(suggestions), 2)
            ]
            for pair_idx, pair in enumerate(pairs):
                cols = st.columns(len(pair))
                for col_idx, (col, sug) in enumerate(zip(cols, pair)):
                    global_idx = pair_idx * 2 + col_idx
                    with col:
                        if st.button(
                            f"{sug['icon']} {sug['question']}",
                            key=f"sug2_{global_idx}",
                            use_container_width=True,
                        ):
                            st.session_state.prefill_question = (
                                sug["question"]
                            )
                            st.rerun()

    # Chat messages
    for msg in chat_history:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
            if msg.get("sources"):
                with st.expander(
                    f"📎 {len(msg['sources'])} source(s)", expanded=False
                ):
                    for src in msg["sources"]:
                        st.caption(f"• {src}")
            if msg.get("route") and msg["role"] == "assistant":
                route_labels = {
                    "analytics": "📊 Analytics",
                    "rag":       "📄 Document",
                    "both":      "🔀 Combined",
                    "general":   "💬 General",
                    "unknown":   "❓ Unknown",
                }
                route_lbl = route_labels.get(
                    msg["route"], msg["route"]
                )
                elapsed = msg.get("elapsed", 0)
                st.caption(f"{route_lbl} · {elapsed:.1f}s")

    # Input
    prefill = st.session_state.pop("prefill_question", None)

    if question := st.chat_input(
        "Ask anything about your data or documents...",
        key="main_chat_input",
    ):
        active_q = question
    elif prefill:
        active_q = prefill
    else:
        active_q = None

    if active_q:
        if not st.session_state.get("graph"):
            st.error(
                "Upload data and click ⚡ Analyse Data first."
            )
        else:
            st.session_state.chat_history.append(
                {"role": "user", "content": active_q}
            )
            with st.chat_message("user"):
                st.write(active_q)

            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    t0 = time.time()
                    result = st.session_state.graph.run(
                        question=active_q,
                        chat_history=(
                            st.session_state.chat_history[:-1]
                        ),
                    )
                    elapsed = time.time() - t0

                answer = result.get(
                    "answer",
                    "Sorry, I could not generate an answer."
                )
                st.write(answer)

                route = result.get("route", "unknown")
                route_labels = {
                    "analytics": "📊 Analytics",
                    "rag":       "📄 Document",
                    "both":      "🔀 Combined",
                    "general":   "💬 General",
                    "unknown":   "❓ Unknown",
                }
                st.caption(
                    f"{route_labels.get(route, route)} · {elapsed:.1f}s"
                )

                if result.get("sources"):
                    with st.expander(
                        f"📎 {len(result['sources'])} source(s)",
                        expanded=False
                    ):
                        for src in result["sources"]:
                            st.caption(f"• {src}")

            st.session_state.chat_history.append({
                "role":    "assistant",
                "content": answer,
                "sources": result.get("sources", []),
                "route":   route,
                "elapsed": elapsed,
            })
            st.rerun()
