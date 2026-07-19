"""
New LangGraph workflow for Insight Copilot.
Replaces the old linear Retriever → Responder graph.
"""

from langgraph.graph import StateGraph, END
from src.state.copilot_state import CopilotState
from src.node.intent_router import IntentRouterNode
from src.node.analytics_node import AnalyticsNode
from src.node.synthesiser_node import SynthesiserNode
from src.vectorstore.vectorstore import VectorStore

def _infer_business_domain(col_text: str,
                            cols_lower: list) -> dict:
    """
    Infers what kind of business data has been uploaded
    based on column name keywords.
    Returns a dict with label, description, suggestion.
    """

    # Forecasting / demand planning
    if any(w in col_text for w in
           ["predicted", "forecast", "actual", "error_pct",
            "error", "accuracy"]):
        return {
            "label": "Demand Forecasting & Prediction Accuracy Data",
            "description": (
                "This data tracks forecast predictions against "
                "actual outcomes — typically used in retail or "
                "supply chain to measure how accurately demand "
                "was predicted for products or stores. "
                "The error_pct column shows how far off each "
                "prediction was from reality."
            ),
            "suggestion": (
                "Good questions to ask:\n"
                "- *'Which store has the highest forecast error?'*\n"
                "- *'Which item is hardest to predict accurately?'*\n"
                "- *'Show me the accuracy trend over time'*"
            ),
        }

    # Retail sales
    if any(w in col_text for w in
           ["sales", "revenue", "units_sold", "order",
            "product", "category", "sku"]):
        return {
            "label": "Retail Sales Data",
            "description": (
                "This is retail sales data tracking transactions "
                "across products, categories, or stores. "
                "It can be used to identify top performers, "
                "underperforming categories, seasonal trends, "
                "and revenue drivers."
            ),
            "suggestion": (
                "Good questions to ask:\n"
                "- *'Which product has the highest revenue?'*\n"
                "- *'Which category is underperforming?'*\n"
                "- *'Show me the sales trend over time'*"
            ),
        }

    # Inventory
    if any(w in col_text for w in
           ["inventory", "stock", "reorder", "warehouse",
            "quantity_on_hand", "stockout"]):
        return {
            "label": "Inventory Management Data",
            "description": (
                "This data tracks stock levels, inventory movement, "
                "and reorder points across products or warehouses. "
                "It helps identify items at risk of stockout and "
                "optimise reorder quantities."
            ),
            "suggestion": (
                "Good questions to ask:\n"
                "- *'Which items are low on stock?'*\n"
                "- *'Show inventory levels by category'*\n"
                "- *'Which products need immediate restocking?'*"
            ),
        }

    # Customer data
    if any(w in col_text for w in
           ["customer", "churn", "clv", "lifetime",
            "segment", "retention", "nps", "satisfaction"]):
        return {
            "label": "Customer Analytics Data",
            "description": (
                "This data tracks customer behaviour, segments, "
                "or satisfaction metrics. It can be used to "
                "identify high-value customers, churn risk, "
                "and retention opportunities."
            ),
            "suggestion": (
                "Good questions to ask:\n"
                "- *'Which customer segment is most valuable?'*\n"
                "- *'What is the churn rate by segment?'*\n"
                "- *'Who are the top customers by revenue?'*"
            ),
        }

    # Marketing / campaign
    if any(w in col_text for w in
           ["campaign", "clicks", "impressions", "ctr",
            "conversion", "spend", "roas", "channel"]):
        return {
            "label": "Marketing Performance Data",
            "description": (
                "This data tracks marketing campaign performance "
                "across channels. It can be used to identify "
                "the best-performing channels, optimise ad spend, "
                "and improve conversion rates."
            ),
            "suggestion": (
                "Good questions to ask:\n"
                "- *'Which channel has the highest ROAS?'*\n"
                "- *'Show me CTR trend over time'*\n"
                "- *'Which campaign has the lowest conversion?'*"
            ),
        }

    # Financial
    if any(w in col_text for w in
           ["profit", "margin", "cost", "expense",
            "budget", "ebitda", "gross"]):
        return {
            "label": "Financial Performance Data",
            "description": (
                "This data tracks financial metrics such as "
                "profit, margins, costs, or budget performance. "
                "It can be used to identify profitability drivers "
                "and areas where costs should be reduced."
            ),
            "suggestion": (
                "Good questions to ask:\n"
                "- *'Which product has the highest profit margin?'*\n"
                "- *'Show me cost trends over time'*\n"
                "- *'Which category is least profitable?'*"
            ),
        }

    # HR
    if any(w in col_text for w in
           ["employee", "salary", "department", "hire",
            "attrition", "headcount", "tenure"]):
        return {
            "label": "HR & People Analytics Data",
            "description": (
                "This data tracks workforce metrics such as "
                "headcount, salary, attrition, or department "
                "performance. It can be used to identify "
                "retention risks and optimise team structure."
            ),
            "suggestion": (
                "Good questions to ask:\n"
                "- *'Which department has the highest attrition?'*\n"
                "- *'Show me headcount trend over time'*\n"
                "- *'What is the average salary by department?'*"
            ),
        }

    # Generic fallback
    actual_cols = ", ".join(f"'{c}'" for c in cols_lower[:6])
    return {
        "label": "Business Dataset",
        "description": (
            f"This dataset contains business records with "
            f"columns: {actual_cols}. "
            "Based on the column names, the specific business "
            "domain could not be automatically detected — "
            "but I can still analyse the data for you."
        ),
        "suggestion": (
            "Good questions to ask:\n"
            "- *'Summarise the data'* — for a full overview\n"
            "- *'What are the key insights?'*\n"
            "- *'Are there any anomalies?'*"
        ),
    }


class CopilotGraphBuilder:

    def __init__(self, llm, vector_store: VectorStore):
        self.llm = llm
        self.vector_store = vector_store
        self.graph = None

        # Initialise nodes
        self.intent_router = IntentRouterNode(llm)
        self.analytics_node = AnalyticsNode(llm)
        self.synthesiser = SynthesiserNode(llm)

    def _rag_node(self, state: CopilotState) -> CopilotState:
        """
        RAG node: retrieves relevant chunks from FAISS, formats as context string.
        Extracted here to avoid a full class for a simple operation.
        """
        try:
            retriever = self.vector_store.get_retriever()
            docs = retriever.invoke(state.question)
            context = "\n\n".join(
                f"[Source: {d.metadata.get('source', 'doc')}, "
                f"Page: {d.metadata.get('page', '?')}]\n{d.page_content}"
                for d in docs[:5]
            )
        except ValueError:
            # Vector store not initialised — no PDF was uploaded
            docs = []
            context = "No documents have been indexed yet."

        return CopilotState(**{**state.model_dump(), "retrieved_docs": docs, "rag_context": context})

    def _general_node(self, state: CopilotState) -> CopilotState:
        """
        Handles greetings, dataset overview questions,
        and off-topic questions. Never runs analytics or
        FAISS — returns a clean, focused answer.
        """
        import streamlit as st
        question_lower = state.question.lower().strip()

        # Dataset overview questions
        overview_triggers = [
            "what is the data",
            "what does this data",
            "describe the dataset",
            "what information",
            "what does this file",
            "what can you tell me about this data",
            "about this data",
            "about the data",
        ]

        is_overview = any(t in question_lower for t in overview_triggers)

        # Business context questions — infer from data profile
        business_triggers = [
            "what is this business",
            "what business is this",
            "what kind of business",
            "what type of business",
            "what is this company",
            "what does this company",
            "what does this business",
            "what is this about",
            "tell me about this business",
            "what industry",
            "what sector",
            "describe this business",
            "what is being tracked",
            "what is this dataset tracking",
            "what does this data represent",
            "what is the purpose of this data",
        ]
        is_business_context = any(
            t in question_lower for t in business_triggers
        )

        if is_overview:
            profile = st.session_state.get("data_profile")
            if profile and profile.get("summary_text"):
                s = profile["summary_text"]
                nums = profile.get("numeric_cols", [])
                cats = profile.get("cat_cols", [])
                dates = profile.get("date_cols", [])

                num_str  = ", ".join(
                    c.replace("_"," ").title() for c in nums[:4]
                ) or "none detected"
                cat_str  = ", ".join(
                    c.replace("_"," ").title() for c in cats[:3]
                ) or "none detected"
                date_str = ", ".join(
                    c.replace("_"," ").title() for c in dates
                ) or "none detected"

                # Format numeric stats more readably
                num_details = []
                for col in nums[:3]:
                    col_data = st.session_state.get("clean_df")
                    if col_data is not None and col in col_data.columns:
                        total = col_data[col].sum()
                        mean  = col_data[col].mean()
                        label = col.replace("_", " ").title()
                        num_details.append(
                            f"**{label}**: total {total:,.0f}, "
                            f"avg {mean:,.1f} per row"
                        )

                num_detail_str = "\n".join(f"- {d}" for d in num_details) \
                    if num_details else f"Columns: {num_str}"

                row_count  = profile.get("row_count", "?")
                col_count  = profile.get("col_count", "?")
                date_range = ""
                if dates:
                    clean_df = st.session_state.get("clean_df")
                    if clean_df is not None and dates[0] in clean_df.columns:
                        try:
                            import pandas as pd
                            d_col = pd.to_datetime(clean_df[dates[0]])
                            date_range = (
                                f"\n\n**Date range**: "
                                f"{d_col.min().strftime('%d %b %Y')} → "
                                f"{d_col.max().strftime('%d %b %Y')} "
                                f"({(d_col.max()-d_col.min()).days} days)"
                            )
                        except Exception:
                            pass

                answer = (
                    f"**This dataset has {row_count:,} rows and "
                    f"{col_count} columns.**\n\n"
                    f"**Key metrics:**\n{num_detail_str}"
                    f"{date_range}\n\n"
                    f"**Groups/categories**: "
                    f"{cat_str if cat_str != 'none detected' else 'none found'}\n\n"
                    f"To explore further, try asking:\n"
                    f"- *'Summarise the data'* — for a full business narrative\n"
                    f"- *'Which {cats[0].replace('_',' ') if cats else 'category'} "
                    f"has the highest "
                    f"{nums[0].replace('_',' ') if nums else 'value'}?'* "
                    f"— for rankings\n"
                    f"- *'Show me the trend over time'* "
                    f"{'— for time analysis' if dates else '(no date column found)'}"
                )
            else:
                answer = (
                    "No data has been uploaded yet. "
                    "Please upload a CSV or Excel file in the sidebar "
                    "and click 🚀 Process Files."
                )

        elif is_business_context:
            profile = st.session_state.get("data_profile")
            clean_df = st.session_state.get("clean_df")

            if not profile or clean_df is None:
                answer = (
                    "No data has been uploaded yet. "
                    "Please upload a CSV file in the sidebar "
                    "and click 🚀 Process Files — then I can "
                    "tell you exactly what this business data "
                    "is about."
                )
            else:
                # Infer business type from column names
                cols_lower = [c.lower() for c in clean_df.columns]
                col_text   = " ".join(cols_lower)

                # Detect domain from column keywords
                domain = _infer_business_domain(col_text, cols_lower)

                nums  = profile.get("numeric_cols", [])
                cats  = profile.get("cat_cols", [])
                dates = profile.get("date_cols", [])

                row_count = profile.get("row_count", len(clean_df))
                col_count = profile.get("col_count", len(clean_df.columns))

                # Date range
                date_range_str = ""
                if dates:
                    try:
                        import pandas as pd
                        d_col = pd.to_datetime(clean_df[dates[0]])
                        date_range_str = (
                            f" covering "
                            f"{d_col.min().strftime('%d %b %Y')} to "
                            f"{d_col.max().strftime('%d %b %Y')}"
                        )
                    except Exception:
                        pass

                # Key metric summary
                metric_parts = []
                for col in nums[:3]:
                    if col in clean_df.columns:
                        total = clean_df[col].sum()
                        label = col.replace("_", " ").title()
                        metric_parts.append(
                            f"{label}: {total:,.0f} total"
                        )
                metric_str = " · ".join(metric_parts) \
                    if metric_parts else "No numeric metrics detected"

                # Category summary
                cat_summary = ""
                for col in cats[:2]:
                    if col in clean_df.columns:
                        n_unique = clean_df[col].nunique()
                        top_vals = clean_df[col].value_counts(
                        ).index[:3].tolist()
                        label = col.replace("_", " ").title()
                        top_str = ", ".join(str(v) for v in top_vals)
                        cat_summary += (
                            f"\n- **{label}**: "
                            f"{n_unique} unique values "
                            f"(e.g. {top_str})"
                        )

                answer = (
                    f"**{domain['label']}**\n\n"
                    f"{domain['description']}\n\n"
                    f"The uploaded dataset has **{row_count:,} records** "
                    f"and **{col_count} columns**{date_range_str}.\n\n"
                    f"**What is being tracked:**{cat_summary}\n\n"
                    f"**Key metrics:** {metric_str}\n\n"
                    f"{domain['suggestion']}"
                )

        # Greeting
        elif any(w in question_lower for w in
                 ["hi", "hello", "hey", "good morning",
                  "good evening", "namaste", "hii", "helo"]):
            answer = (
                "Hello! I am your AI Retail Decision Copilot.\n\n"
                "Upload your sales CSV and business documents "
                "in the sidebar, then ask me things like:\n\n"
                "- *Which product has the highest revenue?*\n"
                "- *Show me the sales trend*\n"
                "- *Which category is underperforming?*\n"
                "- *What does the strategy report say about Q3?*\n\n"
                "What would you like to know?"
            )

        # Capability question
        elif any(w in question_lower for w in
                 ["what can you do", "how do you work",
                  "help", "capabilities", "what do you do"]):
            answer = (
                "I can help with three types of questions:\n\n"
                "**📊 Analytics** — KPIs, trends, top/bottom "
                "performers, anomalies from your CSV data.\n\n"
                "**📄 Documents** — Search and retrieve from "
                "your uploaded PDF reports with page citations.\n\n"
                "**🔀 Combined** — Questions that need both data "
                "analysis and document context simultaneously.\n\n"
                "Upload your files in the sidebar to get started."
            )

        # Off-topic
        else:
            answer = (
                "I am specialised for retail business analysis. "
                "I work best with questions about your uploaded "
                "sales data or business documents.\n\n"
                "Try: *'Which product has the highest revenue?'* "
                "or *'What does the report say about strategy?'*"
            )

        return CopilotState(
            **{**state.model_dump(),
               "answer": answer,
               "sources": [],
               "analytics_result": "",
               "rag_context": ""}
        )

    def _route_edge(self, state: CopilotState) -> str:
        """Conditional edge function — determines which node runs after intent router"""
        return state.route  # "analytics", "rag", or "both"

    def _after_analytics(self, state: CopilotState) -> str:
        """If route is 'both', run RAG after analytics. Otherwise go to synthesiser."""
        if state.route == "both":
            return "rag_node"
        return "synthesiser"

    def build(self):
        builder = StateGraph(CopilotState)

        # Add all nodes
        builder.add_node("intent_router",  self.intent_router.route)
        builder.add_node("analytics_node", self.analytics_node.run)
        builder.add_node("rag_node",        self._rag_node)
        builder.add_node("synthesiser",    self.synthesiser.synthesise)
        builder.add_node("general_node",   self._general_node)

        # Entry point
        builder.set_entry_point("intent_router")

        # Conditional routing from intent_router
        builder.add_conditional_edges(
            "intent_router",
            self._route_edge,
            {
                "analytics": "analytics_node",
                "rag":       "rag_node",
                "both":      "analytics_node",
                "general":   "general_node",
                "unknown":   "general_node",
            }
        )

        # After analytics: if route==both, also run RAG; otherwise synthesise
        builder.add_conditional_edges(
            "analytics_node",
            self._after_analytics,
            {
                "rag_node":    "rag_node",
                "synthesiser": "synthesiser",
            }
        )

        # RAG always goes to synthesiser
        builder.add_edge("rag_node", "synthesiser")

        # Synthesiser → END
        builder.add_edge("synthesiser", END)
        builder.add_edge("general_node", END)

        self.graph = builder.compile()
        return self.graph

    def run(self, question: str, chat_history: list = None) -> dict:
        """Run the graph for a single question. Falls back to mock on LLM error."""
        if self.graph is None:
            self.build()

        initial = CopilotState(
            question=question,
            chat_history=chat_history or [],
            # Explicitly reset all result fields on every new question.
            # This prevents previous turn's analytics_result or rag_context
            # from bleeding into the new answer via state carry-over.
            analytics_result="",
            rag_context="",
            retrieved_docs=[],
            answer="",
            sources=[],
            route="unknown",
            kpi_summary="",
        )

        try:
            return self.graph.invoke(initial)
        except Exception as e:
            return self._fallback_with_mock(initial, e)

    def _fallback_with_mock(self, initial: CopilotState, error: Exception) -> dict:
        """
        Called when the real LLM raises an error (bad key, quota, network).
        Rebuilds the graph with MockChatModel and retries once.
        Saves the error to session state so the UI can show a warning banner.
        """
        import logging
        import streamlit as st
        from src.utils.mock_llm import MockChatModel
        from langchain_core.embeddings import Embeddings

        logger = logging.getLogger(__name__)
        logger.warning("LLM call failed (%s). Falling back to MockChatModel.", error)
        st.session_state["api_error_warning"] = str(error)

        # Swap embeddings to avoid re-triggering the API key error
        class _MockEmbeddings(Embeddings):
            def embed_documents(self, texts): return [[0.1] * 768 for _ in texts]
            def embed_query(self, text): return [0.1] * 768

        vs = st.session_state.get("vector_store", self.vector_store)
        if vs:
            vs.embeddings = _MockEmbeddings()
        st.session_state["vector_store"] = vs

        mock_builder = CopilotGraphBuilder(
            llm=MockChatModel(),
            vector_store=vs
        )
        mock_builder.build()
        st.session_state.graph = mock_builder

        return mock_builder.graph.invoke(initial)

