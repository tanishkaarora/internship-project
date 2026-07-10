# Week 2 Submission – End-to-End MVP

## ✅ Deliverables

- [x] **End-to-end demo.** Screenshot or 3-min screen recording of the full product working on a small slice (refer to the [demo/README.md](file:///c:/Users/HP/OneDrive/Desktop/ai%20copilot/demo/README.md) walkthrough).
- [x] **Updated README** (the "What I learned" section has grown).
- [x] **First ADR (Architecture Decision Record).**
- [x] **At least 10 GitHub commits** total on main.
- [x] **A "What surprised me" note** (2-3 sentences). Real learning, not fluff.
- [x] **Status one-pager** (same format as Week 1).

---

## Updated README

The repository's [README.md](file:///c:/Users/HP/OneDrive/Desktop/ai%20copilot/README.md) has been updated with:
* An **Architecture Overview** containing a Mermaid schema of our LangGraph StateGraph pipeline.
* A step-by-step **Usage Guide** explaining file upload, dashboards, and chat questions.
* Explicit **Testing Guidelines** for running local unit tests and graph tests.
* A **"What I Learned"** section detailing 8 genuine engineering takeaways on dynamic routing, pandas currency normalization, state decoupling, and FAISS vector indices.

---

## ADR-001

Reference:

[docs/adr/ADR-001.md](file:///c:/Users/HP/OneDrive/Desktop/ai%20copilot/docs/adr/ADR-001.md)

### ADR-001: Adopting LangGraph StateGraph for Context-Aware Routing and Orchestration

#### Context
The AI Retail Decision Copilot was initially designed as a sequential execution chain where all user requests passed through the same linear pipeline. Requests for quantitative calculations (e.g., top products, monthly sales trends) and qualitative document searches (e.g., return policies, store SOPs) went through identical processing blocks.

This linear pipeline approach suffered from inefficient latency, context pollution (merging unrelated document snippets with quantitative table analysis), and API cost inefficiency (high-token document context ran through the LLM for every single interaction).

#### Decision
We chose to migrate from a sequential pipeline to a state-machine based directed graph architecture using **LangGraph StateGraph**.

The implemented design organizes the application flow into discrete execution nodes:
1. **`intent_router`:** Classifies user query intent into `analytics`, `rag`, or `both`.
2. **`analytics_node`:** Invokes pandas-based analytical logic on dataframes.
3. **`rag_node`:** Ingests document questions, retrieves relevant chunks from FAISS.
4. **`synthesiser`:** Evaluates outputs, reconciles calculations with qualitative text, and outputs the final cited response.

State is defined globally using a Pydantic-based `CopilotState` schema.

#### Consequences
* **Positive:**
  * Quantitative queries skip vector searches completely (faster, lower cost).
  * Decoupled nodes make the codebase highly modular.
  * Context isolation prevents LLM prompt dilution.
* **Negative:**
  * Increased system complexity and learning curve.
  * Minor routing latency overhead (approx. 100–300ms) for the initial LLM intent routing call.
* **Trade-offs:** We accepted the initial classification call latency in exchange for cleaner context, higher reasoning accuracy, and reduced downstream token usage.

#### Alternatives Considered
* **Single LLM Prompt with Tool Calling:** Rejected because tool-calling agents are less deterministic and harder to test.
* **Rule/Regex-Based Router:** Rejected because conversational queries are highly expressive, and semantic routing is far more robust.

---

## Commits

The current commit count in the repository is **13 commits** on the main branch.

---

## What Surprised Me

During implementation, I was surprised by how much prompt pollution degraded synthesis quality when quantitative table findings were mixed with unstructured document text. Transitioning to a semantic StateGraph router using LangGraph not only resolved this by separating analytical and retrieval contexts but also drastically optimized API costs by avoiding redundant vector queries.

---

## Status Report

Reference:

[reports/status-week2.md](file:///c:/Users/HP/OneDrive/Desktop/ai%20copilot/reports/status-week2.md)

### Week 2 Status

#### Objectives
* Implement dynamic query routing.
* Build automated business analytics helpers.
* Develop local PDF document parsing, text chunking, and local FAISS vector indexing.
* Unify frontend dashboard features and conversational chat widget.

#### Work Completed
* **LangGraph Orchestration:** Replaced linear pipeline with `StateGraph` workflow.
* **Robust Ingestion Pipeline:** Implemented clean pandas ingestion.
* **Analytical Analytics Engine:** Designed calculations for top-N ranking, monthly trends, and outlier detection.
* **Plotly Chart Builder:** Created automated visualization code.
* **Local RAG Integration:** Implemented PDF text extraction, chunking, and local FAISS.
* **Streamlit UI Layout:** Sidebar drawers, KPI metrics, charts, and chat are live.

#### Challenges & Solutions
* **State vs. Streamlit Coupling:** Kept DataFrame in Streamlit session state and passed only lightweight metadata in `CopilotState`.
* **Currency Parsing:** Wrote cleaning regexes in `data_ingester.py` to scrub currency symbols before numeric conversion.
* **Streamlit Script Context in Tests:** Mocked Streamlit session variables inside graph tests to run assertions headlessly.

#### Current Progress
The end-to-end MVP is fully functional. Ingestion, charts, KPIs, RAG, and StateGraph routing work together. All unit and graph tests pass.

#### Next Week Goals
* Split the monolithic layout into a dedicated backend API (FastAPI) and modern frontend space (React/TypeScript).
* Upgrade FAISS to pgvector on PostgreSQL.
* Add predictive ML models (Prophet/XGBoost).
