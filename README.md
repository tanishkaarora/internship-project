# 🛍️ AI Retail Decision Copilot

[![Python Version](https://img.shields.io/badge/python-3.9%20%7C%203.10%20%7C%203.11-blue.svg)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/framework-Streamlit-FF4B4B.svg)](https://streamlit.io/)
[![Orchestration](https://img.shields.io/badge/orchestration-LangGraph-0052FF.svg)](https://github.com/langchain-ai/langgraph)
[![Vector Database](https://img.shields.io/badge/vector%20db-FAISS-green.svg)](https://github.com/facebookresearch/faiss)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Build Status](https://img.shields.io/badge/tests-passing-brightgreen.svg)](run_tests.py)

> **An AI-powered decision support platform that combines Business Analytics, Retrieval-Augmented Generation (RAG), Machine Learning, and Large Language Models (LLMs) to help retail businesses make intelligent, data-driven decisions.**

---

## 📌 Project Overview

Retail businesses generate large volumes of structured data (sales, inventory, customer records) and unstructured data (reports, manuals, market research). Extracting meaningful insights from this information often requires multiple tools and technical expertise.

**AI Retail Decision Copilot** simplifies this process by combining business analytics, Retrieval-Augmented Generation (RAG), machine learning, and AI-powered conversational interfaces into a single intelligent platform.

Users can upload retail datasets and business documents, ask natural language questions, explore dashboards, retrieve information from documents, and receive actionable business recommendations.

This project is being developed as the foundation for a larger enterprise AI platform that will continue evolving throughout my third year.

---

## 🎯 Project Objectives

* **Analyze Retail Data:** Ingest and profile retail sales, inventory, and customer datasets.
* **Dynamic Conversational QA:** Answer business questions using natural language.
* **Context-Driven Routing:** Dynamically route queries to structured analytics, unstructured RAG, or both using LangGraph.
* **Document Intelligence:** Parse and retrieve information from uploaded business reports (PDF) using RAG and local FAISS vector search.
* **Intelligent Recommendations:** Synthesize statistical insights and policy text into logical business recommendations with proper source citation.
* **Visual Dashboards:** Generate interactive Plotly charts corresponding to natural language analytics queries.

---

## 📄 Project Documentation

Explore the detailed documentation for the design and system architecture:

| Document | Description |
| :--- | :--- |
| 📘 **[Design Document](docs/design_doc.md)** | Product overview, functional & non-functional requirements, technology stack, target users, and future scope. |
| 🏗️ **[Architecture Document](docs/architecture.md)** | Detailed system layout, Mermaid data flow diagrams, module responsibilities, and 3rd-year system evolution. |

---

## ✨ Key Features

### 📊 Business Analytics
* Category & product performance analysis (top/bottom performers).
* Monthly & quarterly sales trend analysis.
* Automated statistical anomaly detection with dynamic scatter charts.
* Interactive Plotly visualizations rendered dynamically.

### 📚 Document Intelligence (RAG)
* Text extraction and chunking of uploaded PDF documents.
* In-memory FAISS semantic index configuration.
* Automated citation injection referencing the source name and page number.

### 🤖 AI Conversational Copilot
* LangGraph state machine orchestrating stateless node transitions.
* Intent Router classifying queries dynamically.
* Multi-model provider integration (supporting OpenAI, Google Gemini, and Groq).
* Complete conversational history awareness.

---

## 🏗️ Tech Stack

| Layer | Component | Technology |
| :--- | :--- | :--- |
| **Frontend** | User Interface | Streamlit |
| **Backend** | Python Framework | LangGraph & LangChain |
| **Data Processing** | Numeric & Table Wrangling | Pandas, NumPy |
| **Visualization** | Interactive Plotting | Plotly |
| **Vector Database** | Semantic Retrieval Index | FAISS (Local) |
| **LLM Engine** | Large Language Models | OpenAI / Gemini / Groq |

---

## 📂 Repository Structure

The actual project structure is structured as a unified modular application:

```text
ai-retail-copilot/
│
├── docs/                           # Project documentation
│   ├── design_doc.md               # Software design specifications
│   ├── architecture.md             # Detailed high-level system architecture
│   └── images/                     # System architecture diagrams
│       └── .gitkeep
│
├── src/                            # Main application package
│   ├── analytics/                  # Data cleaning, profiling, and analytics logic
│   │   ├── analytics_engine.py     # Algorithms for top-n, trends, and anomalies
│   │   ├── chart_generator.py      # Plotly visualization builders
│   │   └── data_ingester.py        # CSV/Excel parsing and metadata profiling
│   │
│   ├── config/                     # Configuration and model initialization
│   │   └── config.py               # Key lookups and LLM loaders
│   │
│   ├── document_ingestion/         # Unstructured parsing
│   │   └── document_processor.py   # PDF text extraction and chunking
│   │
│   ├── graph_builder/              # LangGraph pipeline definition
│   │   └── graph_builder.py        # StateGraph nodes and conditional edges
│   │
│   ├── node/                       # Individual LangGraph nodes
│   │   ├── analytics_node.py       # Data analytics execution node
│   │   ├── intent_router.py        # Intent classification node
│   │   └── synthesiser_node.py     # Response generation & citation node
│   │
│   ├── prompts/                    # Prompts for LLM nodes
│   │   └── business_prompts.py     # Prompt templates for routing and synthesis
│   │
│   ├── state/                      # LangGraph state configuration
│   │   └── copilot_state.py        # Pydantic-based CopilotState schema
│   │
│   └── vectorstore/                # Vector store integrations
│       └── vectorstore.py          # FAISS manager & retriever client
│
├── tests/                          # Automated unit tests
│   ├── test_data_ingester.py       # Data cleaner & profiler tests
│   └── test_graph_flow.py          # LangGraph state transitions tests
│
├── requirements.txt                # Project python packages dependencies
├── run_tests.py                    # Unit test suite execution script
├── streamlit_app.py                # Main Streamlit user interface entrypoint
├── .env                            # Environment variables (local credentials)
└── README.md                       # Project landing documentation
```

---

## ⚙️ Installation & Local Setup

### Prerequisites
* Python 3.9, 3.10, or 3.11 installed.
* An API Key for OpenAI, Google Gemini, or Groq.

### 1. Clone the Repository
```bash
git clone https://github.com/tanishkaarora/retailbrain.git
cd retailbrain
```

### 2. Configure Virtual Environment
```bash
python -m venv .venv
# On Windows (PowerShell)
.venv\Scripts\Activate.ps1
# On Linux/macOS
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Set Up Environment Keys
Create a `.env` file in the root directory:
```env
OPENAI_API_KEY="your-openai-api-key"
# Optional:
GEMINI_API_KEY="your-gemini-api-key"
GROQ_API_KEY="your-groq-api-key"
USE_GEMINI="false"
USE_GROQ="false"
```

### 5. Run the Application
```bash
streamlit run streamlit_app.py
```

### 6. Run the Unit Test Suite
```bash
python run_tests.py
```

---

## 📊 Current Project Status

| Module | Status | Details |
| :--- | :--- | :--- |
| **Repository Setup** | ✅ Completed | Repository structure, requirements, and test suites are initialized. |
| **Design & Architecture** | ✅ Completed | Created design doc and architecture diagrams. |
| **Data Ingestion** | ✅ Completed | Implemented Pandas cleaning and metadata profiling. |
| **Analytics Engine** | ✅ Completed | Built calculations for trends, categories, anomalies, and Plotly visualization. |
| **RAG Pipeline** | ⏳ in progess | Setup PDF text chunker and local FAISS vector database. |
| **Graph Orchestration** | ⏳ in progess | Designed LangGraph StateGraph pipeline with routing. |
| **User Interface** | ⏳ in progess | Streamlit chat widget, file upload drawers, and dashboards are live. |
| **Deployment** | ⏳ Planned | Preparation for production cloud hosting. |

---

## 📅 Weekly Progress (Week 0 & 1)

### ✅ Week 0 — Foundation & Architecture
* [x] Initialized Git repository and set up standard `.gitignore`.
* [x] Drafted system architecture, decoupled responsibilities, and designed data paths.
* [x] Drafted professional software design documentation.
* [x] Designed the interactive, unified Streamlit dashboard and chat user interface.

### ✅ Week 1 — Core Engine & LangGraph Integration
* [x] Built the Python Data Ingestion Pipeline to parse, clean, and profile spreadsheets.
* [x] Developed the business analytics algorithms (Top/Bottom, Trend, Anomaly Detection).
* [x] Implemented PDF chunking and embedded indexing in local FAISS.
* [x] Structured the LangGraph StateGraph to route user requests based on data context.
* [x] Fixed key bugs, resolved Pydantic 2.x deprecation warnings, and verified test suites.

---

## 🛣️ Long-Term Roadmap (3rd Year)

This project will continue to evolve into a production-grade enterprise platform throughout my third year:

* **SaaS Split Architecture:** Separate frontend (React/TypeScript) and backend (FastAPI, Redis) execution spaces.
* **Persistent Knowledge DB:** Transition from local FAISS to a cloud-based pgvector/PostgreSQL setup.
* **Machine Learning Analytics:** Train and integrate ML models (XGBoost/Prophet) for future inventory and sales forecasting.
* **Collaborative AI Agent Framework:** Build specialized sub-agents coordinating autonomously to write briefs or replenish stocks.
* **Enterprise Security:** Support multi-tenant OAuth2 user login and dataset permission rules.

---

## 🤝 Acknowledgements

Developed as part of my Summer Internship 2026. This project serves as the foundation for a long-term AI engineering project continuing through my third academic year.

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.
