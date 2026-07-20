"""Routes user questions to the right processing path"""

from src.state.copilot_state import CopilotState
from src.prompts.business_prompts import INTENT_ROUTER_PROMPT

class IntentRouterNode:
    def __init__(self, llm):
        self.llm = llm

    def route(self, state: CopilotState) -> CopilotState:
        import streamlit as st

        # Check what data sources are available
        has_csv = st.session_state.get("clean_df") is not None
        vs = st.session_state.get("vector_store")
        has_pdf = (
            vs is not None
            and getattr(vs, "db", None) is not None
        )

        prompt = INTENT_ROUTER_PROMPT.format(
            has_csv=str(has_csv),
            has_pdf=str(has_pdf),
            question=state.question
        )

        response = self.llm.invoke(prompt)
        route_text = response.content.strip().lower()

        # Extract just the route word — LLM sometimes
        # adds punctuation or extra words
        route = "analytics"  # safe default
        for word in ["both", "rag", "general", "analytics"]:
            if word in route_text:
                route = word
                break

        # Override: if question mentions both data and document
        # and PDF is available, force "both"
        q_lower = state.question.lower()
        both_triggers = [
            "and the document", "and the report", "and the pdf",
            "data and document", "document and data",
            "summarise document and data",
            "summarise the data and",
            "document and the data",
            "tell about", "both", "too",
        ]
        has_both_trigger = any(t in q_lower for t in both_triggers)

        if has_both_trigger and has_pdf and has_csv:
            route = "both"

        return CopilotState(
            **{**state.model_dump(), "route": route}
        )
