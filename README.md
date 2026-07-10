# 🛍️ AI Retail Decision Copilot

An AI-powered business analytics assistant that helps retail businesses make smarter decisions — built with LangGraph, FAISS, pandas, and Streamlit.

Upload your sales CSV and business documents. Ask questions in plain English. Get answers like a business analyst.

---

## 💡 What Problem Does This Solve?

Retail businesses have two kinds of data:
- **Structured data** — sales CSVs, inventory sheets, customer records
- **Unstructured data** — annual reports, strategy PDFs, market research

Most tools handle one or the other. This copilot handles both simultaneously, routes your question to the right engine automatically, and gives you a single, cited answer.

---

## 🎥 Demo

> Loom walkthrough coming in Week 4

---

## ✨ What It Can Do

**Ask analytics questions about your CSV:**
- "Which product category drives the most profit?"
- "Show me the revenue trend over the last 3 months"
- "What are the anomalies in my sales data?"
- "Which products are underperforming?"

**Ask document questions about your PDF:**
- "What does the annual report say about Q3 performance?"
- "What risks were identified in the market research?"
- "Summarise the key recommendations from this report"

**Ask hybrid questions — it handles both:**
- "Why did electronics sales drop, and what does the strategy doc say about it?"

---

## 🏗️ How It Works

The core of this project is a **LangGraph conditional workflow** — not a simple chatbot chain. Every question gets classified first, then routed to the right processing path.

```
User Question
↓
IntentRouter — classifies: analytics / rag / both
↓                          ↓
AnalyticsNode              RAGNode
(runs pandas on CSV)  OR  (searches FAISS index)
↓                          ↓
Synthesiser
(writes business analyst answer with citations)
↓
Final Answer
```

The intent router uses the LLM to classify each question — so "which product sold most?" goes to the analytics engine, "what does the report say?" goes to FAISS retrieval, and questions that need both run both paths and synthesise the output.

---

## 🛠️ Tech Stack

| Layer | Technology | Why I chose it |
|-------|-----------|----------------|
| UI | Streamlit | Full app in Python, no frontend framework needed |
| Agent orchestration | LangGraph | Conditional routing between nodes — not possible with a simple chain |
| LLM | Google Gemini 1.5 Flash | Free tier, fast, good at structured output |
| Vector database | FAISS (local) | Zero infrastructure, runs in memory, sufficient for single-user |
| Data processing | pandas | Industry standard, handles messy retail CSVs well |
| Charts | Plotly Express | Interactive charts in 2–3 lines, native Streamlit support |
| Embeddings | Google Generative AI | Paired with Gemini, no extra API needed |

---

## 📂 Project Structure

```text
retail-decision-copilot/
│
├── src/
│   ├── analytics/
│   │   ├── data_ingester.py        # CSV/Excel loader, cleaner, profiler
│   │   ├── analytics_engine.py     # KPIs, trend, anomaly detection
│   │   └── chart_generator.py      # Auto Plotly charts
│   │
│   ├── config/
│   │   └── config.py               # API keys, model selection
│   │
│   ├── document_ingestion/
│   │   └── document_processor.py   # PDF parsing and chunking
│   │
│   ├── graph_builder/
│   │   └── graph_builder.py        # LangGraph StateGraph definition
│   │
│   ├── node/
│   │   ├── intent_router.py        # Classifies question intent
│   │   ├── analytics_node.py       # Runs pandas analytics
│   │   └── synthesiser_node.py     # Generates final business answer
│   │
│   ├── prompts/
│   │   └── business_prompts.py     # All LLM prompt templates
│   │
│   ├── state/
│   │   └── copilot_state.py        # Pydantic state schema for LangGraph
│   │
│   └── vectorstore/
│       └── vectorstore.py          # FAISS wrapper
│
├── tests/
│   ├── test_data_ingester.py       # Unit tests for data pipeline
│   └── test_graph_flow.py          # LangGraph routing tests
│
├── docs/
│   ├── design_doc.md
│   ├── architecture.png
│   └── adr/
│       ├── ADR-001.md              # Why LangGraph over simple chain
│       ├── ADR-002.md              # Why FAISS over ChromaDB
│       └── ADR-003.md              # Why Streamlit over FastAPI + React
│
├── data/
│   └── sample_retail.csv           # Sample dataset for testing
│
├── streamlit_app.py                # App entry point
├── run_tests.py                    # Test runner
├── requirements.txt
├── .env.example
└── README.md
```

---

## 🚀 Quickstart

### Prerequisites
- Python 3.11+
- A free Gemini API key — get one at [aistudio.google.com](https://aistudio.google.com)

### 1. Clone and install

```bash
git clone https://github.com/tanishkaarora/retailbrain.git
cd retailbrain
python -m venv .venv

# Windows
.venv\Scripts\Activate.ps1

# Mac/Linux
source .venv/bin/activate

pip install -r requirements.txt
```

### 2. Add your API key

Create a `.env` file in the root folder:
```env
GEMINI_API_KEY=your_key_here
USE_GEMINI=true
```

Or use **Groq** (also free, no credit card):
```env
GROQ_API_KEY=your_key_here
USE_GROQ=true
USE_GEMINI=false
```

### 3. Run

```bash
streamlit run streamlit_app.py
```

Open `http://localhost:8501` in your browser.

### 4. Try it

1. Upload `data/sample_retail.csv` in the sidebar
2. Click **🚀 Process Files**
3. Go to the **Ask** tab
4. Type: *"Which category has the highest revenue?"*

---

## 🧪 Tests

```bash
python run_tests.py
```

All tests should pass and print:
```text
test_ingester_loads_csv passed!
test_ingester_converts_currency passed!
test_profile_has_expected_keys passed!
All tests passed successfully!
```

---

## 📊 What's Built So Far

| Module | Status |
|--------|--------|
| CSV/Excel ingestion + cleaning | ✅ Done |
| KPI computation (revenue, trend, anomalies) | ✅ Done |
| Auto Plotly charts (bar, line, histogram, scatter) | ✅ Done |
| PDF parsing and FAISS indexing |⏳ Week 3 |
| LangGraph intent routing | ⏳ Week 3 |
| Streamlit UI (3 tabs: Overview, Charts, Ask) | ✅ Done |
| Unit tests |⏳ Week 3 |
| Deployment | ⏳ Week 4 |
| ADRs (3 required) | ⏳ Week 3 |

---

## 🧠 Key Things I Learned Building This

**LangGraph routing is not if/else** — the conditional edge works by returning a string key from a separate function, not by branching inside a node. I initially tried to put routing logic inside the IntentRouter node itself, which broke the graph. The right pattern is: node sets `state.route`, then a separate edge function reads it.

**Pydantic v2 breaking change** — `state.dict()` is deprecated. Every node was throwing `PydanticDeprecatedSince20` warnings on every call. The fix is `state.model_dump()` everywhere. Small change, but it was cluttering logs on every single query.

**DataFrames don't belong in LangGraph state** — putting a pandas DataFrame directly into the Pydantic state adds serialization overhead and causes issues. Better pattern: store the DataFrame in `st.session_state`, pass only the text summary (the `data_summary_text` string) through the LangGraph state.

**`has_csv` was always False** — I had `has_csv = bool(state.kpi_summary)` in the intent router, but `kpi_summary` is never populated in the graph. So the router was always telling the LLM "no CSV uploaded" even when one was. Fixed it to read from `st.session_state.get("clean_df") is not None`.

---

## ⚠️ Known Limitations (V1)

- Single file at a time — one CSV + one PDF
- In-memory only — data resets on page refresh
- No authentication — single user
- Answers are based on data summary, not raw rows (by design — for privacy and token efficiency)

---

## 👤 Author

**Tanishka Arora** — 2nd Year B.Tech CSE (AI & Data Engineering)  
Built during Summer Internship 2026 · Segment 3: Foundations of Applied ML

---

## 📄 License

MIT
