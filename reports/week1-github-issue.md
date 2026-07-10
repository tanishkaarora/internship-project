## Week 1 Submission — Foundation & Architecture

### ✅ Deliverables

- [x] **Repo created and public.** Link: https://github.com/tanishkaarora/retailbrain
- [x] **README.md** with: project name, one-line description, problem-statement code, segment name, your name, "what I learned this week" section.
- [x] **Initial Design Doc (1 page)** — Linked at [docs/design_doc.md](file:///c:/Users/HP/OneDrive/Desktop/ai%20copilot/docs/design_doc.md).
- [x] **Tech stack table.** Choice and rationale included.
- [x] **Data layer working.** Terminal output of unit tests demonstrating successful CSV ingestion, cleaning, and profiling.
- [x] **At least 5 GitHub commits** on the main branch.
- [x] **A "What I learned" note** (3-5 bullet points).
- [x] **One-pager status** at the end of the issue.

---

### 📂 Repository & Project Metadata

* **Repository Link:** https://github.com/tanishkaarora/retailbrain
* **Project Name:** AI Retailbrain
* **One-Line Description:** An AI-powered business analytics assistant that helps retail businesses make smarter decisions by combining structured data analysis with unstructured document retrieval.
* **Author:** Tanishka Arora — 2nd Year B.Tech CSE (AI & Data Engineering)
* **Internship Segment:** Segment 3: Foundations of Applied ML

---

### 📝 Initial Design Doc

The initial project design document has been created and peer-reviewed.
* **Document Location:** [docs/design_doc.md](file:///c:/Users/HP/OneDrive/Desktop/ai%20copilot/docs/design_doc.md)
* **Summary:** The document defines functional requirements for multi-file tabular ingestion, RAG document indexing, anomaly detection, dynamic routing via LangGraph, and user dashboard layouts, alongside scalability and security constraints.

---

### 🛠️ Tech Stack Table

| Component | Choice | Why (one line) |
| :--- | :--- | :--- |
| **UI** | Streamlit | Rapid prototyping of highly interactive dashboard layout in pure Python. |
| **Orchestration** | LangGraph | State-machine framework allowing custom loops, condition branches, and strict state controls. |
| **LLM Engine** | Google Gemini 1.5 Flash | Highly performant model with a generous free API tier. |
| **Vector DB** | FAISS (local) | High-speed, zero-infrastructure, local in-memory semantic indexing. |
| **Data Ingestion** | Pandas | Industry-standard data science library for loading, cleaning, and profiling tabular logs. |
| **Visualizations** | Plotly Express | Hover-responsive, interactive charts built natively with Streamlit compatibility. |

---

### ⚙️ Data Layer Working (Verification Evidence)

The ingestion pipeline (`src/analytics/data_ingester.py`) cleans raw columns, converts dirty currency strings to numbers, imputes null values, and profiles data.

Terminal output from running the unit tests verifies the data layer works:
```text
Running test_ingester_loads_csv...
test_ingester_loads_csv passed!
Running test_ingester_converts_currency...
test_ingester_converts_currency passed!
Running test_profile_has_expected_keys...
test_profile_has_expected_keys passed!

All tests passed successfully!
```

---



### 💡 What I Learned (Bullet Points)

* **Pandas Currency Cleaning:** Real-world retail data has symbols like `$`, `€`, `£`, `%` or commas which crash numeric parsing. Writing regex cleaning routines to coerce strings to floats pre-profile is key.
* **Decoupling Application State:** Storing large Pandas DataFrames inside a serializable state machine like LangGraph creates major bottlenecks. Instead, dataframes should be held in UI session memory, and only metadata summaries passed in the orchestrator state.
* **Streamlit Widget Constraints:** Interactive inputs (like file upload hooks) trigger script refreshes from top-to-bottom. We must structure session variable loaders defensively to prevent resetting cached results.

---

### 📊 One-Pager Status (Week 1)

* **What's done:**
  * Drafted system architecture and [Design Document](file:///c:/Users/HP/OneDrive/Desktop/ai%20copilot/docs/design_doc.md).
  * Built the data cleaning and profiling pipeline inside `DataIngester`.
  * Configured unit tests verifying cleaning conversions.
  * Designed the Streamlit app structure.
* **What's stuck:**
  * None.
* **3 goals for next week:**
  * Set up PDF chunking and local FAISS vector stores.
  * Build the LangGraph StateGraph pipeline with intent classification routing.
  * Complete integrated mock-based graph flow routing tests.
* **One thing I'd like help from my mentor on:**
  *confused about the frontend part,should i switch to react or stick with streamlit only.
