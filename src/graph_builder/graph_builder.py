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
        Handles greetings and off-topic questions.
        Returns a helpful fixed response without touching
        analytics or FAISS — saves API tokens and avoids
        confusing data-driven answers to casual questions.
        """
        question_lower = state.question.lower().strip()

        # Personalised greeting responses
        if any(w in question_lower for w in
               ["hi", "hello", "hey", "good morning",
                "good evening", "namaste"]):
            answer = (
                "Hello! I am your AI Retail Decision Copilot. "
                "Upload your sales CSV and business documents "
                "in the sidebar, then ask me things like:\n\n"
                "- *Which product has the highest revenue?*\n"
                "- *Show me the sales trend for the last 3 months*\n"
                "- *What does the strategy report say about Q3?*\n"
                "- *Which category is underperforming?*\n\n"
                "What would you like to know about your business?"
            )
        elif any(w in question_lower for w in
                 ["what can you do", "what do you do",
                  "how do you work", "help", "capabilities"]):
            answer = (
                "I can help you with three types of questions:\n\n"
                "**📊 Analytics** — I analyse your uploaded CSV data "
                "to find top/bottom performers, trends, anomalies, "
                "and KPIs.\n\n"
                "**📄 Documents** — I search your uploaded PDF reports "
                "and retrieve relevant excerpts with page citations.\n\n"
                "**🔀 Both** — For questions that need data analysis "
                "AND document context, I combine both sources.\n\n"
                "Upload your files in the sidebar to get started."
            )
        else:
            answer = (
                "I am specialised for retail business analysis. "
                "I work best with questions about your sales data "
                "or business documents. Try asking: "
                "*'Which product has the highest revenue?'* or "
                "*'What does the report say about our strategy?'*"
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
            chat_history=chat_history or []
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

