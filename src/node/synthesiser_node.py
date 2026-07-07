"""Synthesises analytics results and RAG context into a final business answer"""

from src.state.copilot_state import CopilotState
from src.prompts.business_prompts import SYNTHESISER_PROMPT

class SynthesiserNode:
    def __init__(self, llm):
        self.llm = llm

    def synthesise(self, state: CopilotState) -> CopilotState:
        # Build context description
        context_parts = []
        if state.analytics_result:
            context_parts.append("structured data analytics results")
        if state.rag_context:
            context_parts.append("relevant document excerpts")
        context_desc = " and ".join(context_parts) if context_parts else "general knowledge"

        analytics_section = (
            f"Analytics Results:\n{state.analytics_result}"
            if state.analytics_result else ""
        )
        rag_section = (
            f"Document Context:\n{state.rag_context}"
            if state.rag_context else ""
        )

        # Format recent chat history
        history_text = ""
        if state.chat_history:
            recent = state.chat_history[-4:]  # last 2 exchanges
            history_text = "\n".join(
                f"{m['role'].upper()}: {m['content'][:200]}" for m in recent
            )

        prompt = SYNTHESISER_PROMPT.format(
            context_description=context_desc,
            analytics_section=analytics_section,
            rag_section=rag_section,
            question=state.question,
            chat_history=history_text or "No prior conversation."
        )

        # Workaround: remove double curly braces/strip brackets if prompt formatting complaints occur,
        # but here we just use python format which should be clean.
        response = self.llm.invoke(prompt)
        answer = response.content

        # Collect sources
        sources = []
        if state.retrieved_docs:
            for doc in state.retrieved_docs[:3]:
                src = doc.metadata.get("source", "document")
                page = doc.metadata.get("page", "")
                sources.append(f"{src}" + (f" p.{page}" if page else ""))

        return CopilotState(**{
            **state.model_dump(),
            "answer": answer,
            "sources": sources
        })
