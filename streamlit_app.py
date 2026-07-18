"""Insight Copilot — AI Business Analytics Assistant"""

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
from src.graph_builder.graph_builder import CopilotGraphBuilder

# ── PAGE CONFIG ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Insight Copilot",
    page_icon="📊",
    layout="wide"
)

# ── CUSTOM CSS FOR PREMIUM AESTHETICS ────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Outfit', sans-serif;
}

.gradient-text {
    background: linear-gradient(135deg, #6366f1 0%, #06b6d4 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-weight: 800;
    font-size: 2.8rem;
    margin-bottom: 0rem;
}

div[data-testid="stMetricValue"] {
    font-size: 2.0rem;
    font-weight: 800;
    background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

div[data-testid="metric-container"] {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 16px;
    padding: 20px;
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05);
    backdrop-filter: blur(12px);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

div[data-testid="metric-container"]:hover {
    transform: translateY(-4px);
    border-color: rgba(99, 102, 241, 0.3);
    box-shadow: 0 20px 25px -5px rgba(99, 102, 241, 0.1);
}

section[data-testid="stSidebar"] {
    background-color: #0b0f19 !important;
    border-right: 1px solid rgba(255, 255, 255, 0.05);
}

/* Tab indicator line color */
button[data-baseweb="tab"] {
    font-size: 1.1rem;
    font-weight: 600;
}
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="gradient-text">📊 Insight Copilot</h1>', unsafe_allow_html=True)
st.caption("AI Business Analytics Assistant — structured CSV datasets & text documents in unison.")

# ── SESSION STATE INIT ───────────────────────────────────────────────────────
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
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

def reset_for_new_upload():
    """
    Called every time Process Files is clicked.
    Clears all derived state so the new file gets a fresh
    graph, fresh LLM, and fresh chat history.

    Why this matters: if a user uploads File A, asks questions,
    then uploads File B without refreshing, the graph was built
    on File A's data profile. Column Detective maps to File A's
    columns. All analytics answers are wrong for File B.
    This reset prevents that silent bug.
    """
    keys_to_reset = [
        "graph",
        "llm",
        "clean_df",
        "data_profile",
        "kpis",
        "charts",
        "chat_history",
        "vector_store",
        "api_error_warning",
    ]
    for key in keys_to_reset:
        if key in st.session_state:
            del st.session_state[key]

    # Re-initialise with defaults
    init_state()

# ── SIDEBAR — FILE UPLOADS ───────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📁 Upload Datasets")

    csv_file = st.file_uploader(
        "Business Data (CSV or Excel)",
        type=["csv", "xlsx", "xls"],
        help="Sales, customer, transaction, or product data"
    )
    pdf_file = st.file_uploader(
        "Business Document (PDF — optional)",
        type=["pdf"],
        help="Reports, SOPs, strategy documents"
    )

    if st.button("🚀 Process Files", type="primary", use_container_width=True):
        # Always reset — ensures a new upload never uses
        # graph or profile from a previous upload
        reset_for_new_upload()
        with st.spinner("Setting up Insight Copilot..."):
            st.session_state.llm = Config.get_llm()

            # Process CSV
            if csv_file:
                ingester = DataIngester()
                try:
                    df, profile = ingester.ingest(csv_file)
                    st.session_state.clean_df = df
                    st.session_state.data_profile = profile
                    engine = AnalyticsEngine()
                    st.session_state.kpis = engine.compute_kpis(df, profile)
                    st.session_state.charts = generate_charts(df, profile)
                    st.success(f"✅ Data loaded: {len(df):,} rows")
                    # Show any data quality warnings from validation
                    for warning in profile.get("warnings", []):
                        st.warning(f"⚠️ {warning}")
                    if len(df) > st.session_state.get("MAX_ROWS", 100_000):
                        st.warning(
                            f"⚠️ Large dataset ({len(df):,} rows). "
                            "Analytics may be slow. Consider uploading a sample."
                        )
                    if len(df) < 10:
                        st.warning(
                            "⚠️ Very small dataset (fewer than 10 rows). "
                            "Insights and trends may not be meaningful."
                        )
                except ValueError as e:
                    st.error(str(e))

            # Process PDF
            vs = VectorStore()
            if pdf_file:
                import tempfile, os
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                    tmp.write(pdf_file.read())
                    tmp_path = tmp.name
                try:
                    processor = DocumentProcessor(
                        chunk_size=Config.CHUNK_SIZE,
                        chunk_overlap=Config.CHUNK_OVERLAP
                    )
                    docs = processor.load_from_pdf(tmp_path)
                    chunks = processor.split_documents(docs)
                    vs.create_vectorstore(chunks)
                    st.success(f"✅ Document indexed: {len(chunks)} chunks")
                finally:
                    os.unlink(tmp_path)

            st.session_state.vector_store = vs

            # Build graph
            st.session_state.graph = CopilotGraphBuilder(
                llm=st.session_state.llm,
                vector_store=vs
            )
            st.session_state.graph.build()
            st.success("✅ Insight Copilot ready! Previous session cleared.")

    st.markdown("---")
    st.markdown("### 💡 Demo Mode")
    if st.button("📦 Load Sample Datasets", use_container_width=True):
        with st.spinner("Loading sample dataset and document..."):
            import os
            if st.session_state.llm is None:
                st.session_state.llm = Config.get_llm()

            # Load CSV
            sample_csv_path = "data/sample_sales.csv"
            if os.path.exists(sample_csv_path):
                class MockUploadedFile:
                    def __init__(self, path):
                        self.path = path
                        self.name = os.path.basename(path)
                        self._file = open(path, "rb")
                    def read(self, *args, **kwargs):
                        return self._file.read(*args, **kwargs)
                    def seek(self, pos):
                        return self._file.seek(pos)

                ingester = DataIngester()
                csv_mock = MockUploadedFile(sample_csv_path)
                try:
                    df, profile = ingester.ingest(csv_mock)
                    st.session_state.clean_df = df
                    st.session_state.data_profile = profile
                    engine = AnalyticsEngine()
                    st.session_state.kpis = engine.compute_kpis(df, profile)
                    st.session_state.charts = generate_charts(df, profile)
                    st.sidebar.success("✅ Sample CSV loaded: 11 rows")
                except Exception as e:
                    st.sidebar.error(f"Error loading CSV: {e}")

            # Load PDF
            sample_pdf_path = "data/sample_document.pdf"
            vs = VectorStore()
            if os.path.exists(sample_pdf_path):
                try:
                    processor = DocumentProcessor(
                        chunk_size=Config.CHUNK_SIZE,
                        chunk_overlap=Config.CHUNK_OVERLAP
                    )
                    docs = processor.load_from_pdf(sample_pdf_path)
                    chunks = processor.split_documents(docs)
                    vs.create_vectorstore(chunks)
                    st.sidebar.success(f"✅ Sample PDF indexed: {len(chunks)} chunks")
                except Exception as e:
                    st.sidebar.error(f"Error loading PDF: {e}")

            st.session_state.vector_store = vs
            st.session_state.graph = CopilotGraphBuilder(
                llm=st.session_state.llm,
                vector_store=vs
            )
            st.session_state.graph.build()
            st.sidebar.success("✅ Insight Copilot ready with sample data!")
            st.rerun()

    st.markdown("---")
    st.markdown("**Example questions:**")
    st.markdown("- Which product has the highest sales?")
    st.markdown("- Show me the revenue trend")
    st.markdown("- What anomalies exist in the data?")
    st.markdown("- Summarise the uploaded document")

# ── MAIN CONTENT TABS ────────────────────────────────────────────────────────
tab_overview, tab_charts, tab_chat = st.tabs(["📈 Overview", "📊 Charts", "💬 Ask"])

# Show API error warning if LLM fell back to mock
if st.session_state.get("api_error_warning"):
    st.warning(
        f"⚠️ LLM API error: {st.session_state['api_error_warning']}. "
        "Running in offline mode with mock responses. "
        "Add a valid API key in the sidebar to enable real AI answers.",
        icon="⚠️"
    )
    if st.button("Dismiss warning", key="dismiss_api_warn"):
        del st.session_state["api_error_warning"]
        st.rerun()

# Overview Tab
with tab_overview:
    if st.session_state.kpis:
        st.subheader("Key Metrics")
        cols = st.columns(min(len(st.session_state.kpis), 4))
        for i, (name, value) in enumerate(st.session_state.kpis.items()):
            cols[i % 4].metric(label=name, value=value)
    else:
        st.info("Upload a data file and click 'Process Files' to see metrics.")

    if st.session_state.data_profile:
        st.markdown("---")
        st.markdown("### 📋 Data Profile Summary")
        st.code(st.session_state.data_profile["summary_text"], language="text")
        with st.expander("🔍 Preview raw data (first 10 rows)"):
            st.dataframe(
                st.session_state.clean_df.head(10),
                use_container_width=True
            )

# Charts Tab
with tab_charts:
    if st.session_state.charts:
        for item in st.session_state.charts:
            # Support both old (title, fig) and new (title, fig, insight)
            if len(item) == 3:
                title, fig, insight = item
            else:
                title, fig = item
                insight = ""
            st.subheader(title)
            st.plotly_chart(fig, use_container_width=True)
            if insight:
                st.markdown(
                    f"<p style='font-size:13px;color:#94a3b8;"
                    f"margin-top:-8px;margin-bottom:16px;"
                    f"font-style:italic'>{insight}</p>",
                    unsafe_allow_html=True
                )
    else:
        st.info("Upload data to see auto-generated charts.")

# Chat Tab
with tab_chat:
    if "api_error_warning" in st.session_state:
        st.warning(f"⚠️ Model API Error: {st.session_state['api_error_warning']}. Running in local Mock Mode.")

    # Display chat history
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
            if msg.get("sources"):
                with st.expander("Sources"):
                    for src in msg["sources"]:
                        st.caption(f"• {src}")

    # Chat input
    if question := st.chat_input("Ask about your data or documents..."):
        if st.session_state.graph is None:
            st.error("Please upload files and click 'Process Files' first.")
        else:
            # Show user message
            st.session_state.chat_history.append({"role": "user", "content": question})
            with st.chat_message("user"):
                st.write(question)

            # Get answer
            with st.chat_message("assistant"):
                with st.spinner("Analysing..."):
                    start = time.time()
                    result = st.session_state.graph.run(
                        question=question,
                        chat_history=st.session_state.chat_history[:-1]
                    )
                    elapsed = time.time() - start

                st.write(result.get("answer", "Sorry, I could not generate an answer. Please try again."))
                route = result.get('route', 'unknown')
                route_emoji = {
                    "analytics": "📊 Analytics",
                    "rag":       "📄 Document",
                    "both":      "🔀 Combined",
                    "unknown":   "❓ Unknown"
                }.get(route, route)
                st.caption(f"{route_emoji} · {elapsed:.1f}s")

                # Show Smart Column Detective mapping
                analytics_res = result.get("analytics_result", "")
                if analytics_res and "Analysis Metadata:" in analytics_res:
                    import re
                    match = re.search(r"\*\(Analysis Metadata: (.*?)\)\*", analytics_res)
                    if match:
                        st.info(f"🕵️ {match.group(1)}")

                if result.get("sources"):
                    with st.expander("Sources"):
                        for src in result["sources"]:
                            st.caption(f"• {src}")

            # Save to history
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": result.get("answer", ""),
                "sources": result.get("sources", [])
            })
