"""State definition for Insight Copilot LangGraph workflow"""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field
from langchain_core.documents import Document

class CopilotState(BaseModel):
    """
    State carried through the LangGraph workflow.
    Every node reads from and writes to this object.
    """

    # Input
    question: str

    # Routing — set by IntentRouter node
    route: Literal["analytics", "rag", "both", "general", "unknown"] = "unknown"

    # Analytics results — set by AnalyticsNode
    analytics_result: str = ""
    kpi_summary: str = ""

    # RAG results — set by RAGNode
    retrieved_docs: List[Document] = Field(default_factory=list)
    rag_context: str = ""

    # Final output — set by Synthesiser node
    answer: str = ""
    sources: List[str] = Field(default_factory=list)

    # Conversation memory — grows across turns
    chat_history: List[dict] = Field(default_factory=list)

    class Config:
        arbitrary_types_allowed = True
