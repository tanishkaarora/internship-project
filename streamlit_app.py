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
        with st.spinner("Setting up Insight Copilot..."):
            # Initialise LLM (once)
            if st.session_state.llm is None:
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
            st.success("✅ Insight Copilot ready!")

    st.markdown("---")
    st.markdown("**Example questions:**")
    st.markdown("- Which product has the highest sales?")
    st.markdown("- Show me the revenue trend")
    st.markdown("- What anomalies exist in the data?")
    st.markdown("- Summarise the uploaded document")

# ── MAIN CONTENT TABS ────────────────────────────────────────────────────────
tab_overview, tab_charts, tab_chat = st.tabs(["📈 Overview", "📊 Charts", "💬 Ask"])

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

# Charts Tab
with tab_charts:
    if st.session_state.charts:
        for title, fig in st.session_state.charts:
            st.subheader(title)
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Upload data to see auto-generated charts.")

# Chat Tab
with tab_chat:
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
                st.caption(f"Route: {result.get('route', 'unknown').upper()} | Processing time: {elapsed:.1f}s")

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
