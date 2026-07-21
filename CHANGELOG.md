# Changelog

All notable changes to this project will be documented in this file.

## [v1.0-m1] - 2026-07-22

### Initial Alpha Release

#### Highlights
- **Live Deployment**: Deployed on Streamlit Community Cloud at [retail-brain.streamlit.app](https://retail-brain.streamlit.app/) with caching optimizations.
- **LangGraph Workflow**: Dynamic conditional stategraph routing utilizing Intent Router, Analytics Node, RAG Node, and Synthesiser Node.
- **Hybrid Analytics + RAG**: Simultaneously handles structured CSV data queries and unstructured PDF RAG document contexts.
- **Business Analytics**: Automated calculations for Category Rankings, Trends, and Anomaly Detection.
- **Document Ingestion**: PDF parsing, chunking, and local vector indexing using FAISS and CPU-based embeddings.
- **Question Suggestions**: Dynamic suggest questions tailored to the data profile and PDF metadata.
- **Architecture Documentation**: High-level designs, modular boundaries, and a 3rd-year decoupled scaling path.
- **ADRs**: Architectural Decision Records documenting core module migrations and choices.
- **Testing**: Complete testing coverage including unit tests and graph flow validation.
