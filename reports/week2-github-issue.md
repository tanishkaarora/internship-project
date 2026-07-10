## Week 2 Submission — End-to-End MVP

### ✅ What I submitted this week

- End-to-end demo (screenshot + screen recording in demo/README.md)
- Updated README with architecture, usage guide, and what I learned
- First ADR (Architecture Decision Record) — docs/adr/ADR-001.md
- 15 commits on main branch
- "What surprised me" note
- Status one-pager

---

### 📸 Demo Evidence

Upload `data/sample_retail.csv` → click Process Files → go to Ask tab → ask:
- "Which product has the highest revenue?" → routes to analytics
- "What does the report say about Q3?" → routes to RAG
- "Why did electronics drop and what does the strategy doc say?" → routes to both

Screenshots and screen recording in `demo/README.md`.

---

### 📝 ADR-001 — Why I chose LangGraph over a simple chain

**Full doc:** `docs/adr/ADR-001.md`

**The problem I was solving:**

My first version sent every question through the same pipeline — whether someone asked "what are my top products?" (needs pandas) or "what does the report say?" (needs document search). This caused three problems:

1. Slow — document search ran even for simple number questions
2. Messy answers — the LLM got both chart data AND document text mixed together in one prompt
3. Expensive — wasted tokens on context that wasn't relevant

**What I decided:**

I rebuilt the pipeline as a LangGraph state machine with 4 separate nodes:

- `intent_router` — reads the question, decides: analytics / rag / both
- `analytics_node` — runs pandas calculations on the uploaded CSV
- `rag_node` — searches the FAISS index if a PDF was uploaded
- `synthesiser` — takes whatever ran and writes the final answer with citations

Now a question about sales numbers never touches the document index at all.

**What I gave up:**

One extra LLM call per question (the router). It adds ~100-300ms. Worth it for cleaner answers and lower overall token cost.

**What I rejected:**

- Simple if/else keyword routing — breaks on anything conversational
- Tool-calling agent — less predictable, harder to test and debug

---

### 💬 What Surprised Me

I expected the quality difference between the old and new version to be small. It wasn't. When I mixed the pandas analytics output and the PDF document text into one big prompt, the LLM got confused and gave generic answers that didn't really use either source well. Once I separated them and only merged at the synthesiser stage, the answers got dramatically more specific and accurate. The routing step wasn't just an optimisation — it was what made the answers actually useful.

---

### 📊 What I Built This Week

| Thing | Done? |
|-------|-------|
| LangGraph routing (analytics / rag / both) | ✅ |
| CSV cleaning and profiling (pandas) | ✅ |
| KPIs, trend analysis, anomaly detection | ✅ |
| Auto Plotly charts (bar, line, histogram, scatter) | ✅ |
| PDF parsing + FAISS vector indexing | ✅ |
| Streamlit UI — Overview, Charts, Ask tabs | ✅ |
| Unit tests + graph flow tests passing | ✅ |

---

### 🧱 Challenges I Hit and How I Fixed Them

**DataFrames in LangGraph state** — I tried putting the pandas DataFrame directly inside `CopilotState`. It caused serialization problems. Fixed it by keeping the DataFrame in `st.session_state` and only passing a lightweight text summary through the LangGraph state.

**Currency parsing** — CSVs with `$1,200` or `£800` were being read as strings. Wrote a regex in `data_ingester.py` to strip currency symbols before converting to numbers.

**Testing without Streamlit running** — Graph tests need `st.session_state` but there's no browser in a test. Fixed by mocking the session state dict directly in `test_graph_flow.py`.

---

### 🎯 Goals for Week 3

1. Polish the UI — better layout, loading states, error messages
2. Write ADR-002 (FAISS vs ChromaDB) and ADR-003 (Streamlit vs FastAPI+React)
3. Add the Smart Column Detective mini-extension
4. Start deployment prep

---

### 🙋 One thing I want mentor help on

How should I handle the case where neither a CSV nor a PDF has been uploaded and the user asks a question? Right now it returns a generic "no data uploaded" message — but should the copilot still try to answer from general knowledge, or always refuse?
