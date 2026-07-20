"""Synthesises analytics results and RAG context into a final business answer"""

from src.state.copilot_state import CopilotState
from src.prompts.business_prompts import SYNTHESISER_PROMPT

class SynthesiserNode:
    def __init__(self, llm):
        self.llm = llm

    def synthesise(self, state: CopilotState) -> CopilotState:
        has_analytics = bool(state.analytics_result.strip())
        has_rag       = bool(state.rag_context.strip())

        # Build context sections
        analytics_section = ""
        if has_analytics:
            analytics_section = (
                f"=== STRUCTURED DATA ANALYSIS ===\n"
                f"{state.analytics_result}\n"
                f"=== END DATA ANALYSIS ==="
            )

        rag_section = ""
        if has_rag:
            rag_section = (
                f"=== DOCUMENT CONTENT (from uploaded PDF) ===\n"
                f"{state.rag_context}\n"
                f"=== END DOCUMENT CONTENT ==="
            )

        # Build context description for the prompt
        if has_analytics and has_rag:
            context_description = (
                "BOTH structured data analysis AND document excerpts. "
                "You MUST use both in your answer. "
                "First summarise what the data shows, "
                "then what the document adds or confirms."
            )
        elif has_analytics:
            context_description = "structured data analysis results"
        elif has_rag:
            context_description = "document excerpts from the uploaded PDF"
        else:
            context_description = "general business knowledge"

        # Chat history — last 2 exchanges, first sentence only
        history_text = "No prior conversation."
        if state.chat_history:
            recent = state.chat_history[-4:]
            parts = []
            for m in recent:
                role    = m["role"].upper()
                content = m["content"].split("\n")[0][:150]
                parts.append(f"{role}: {content}")
            history_text = "\n".join(parts)

        prompt = SYNTHESISER_PROMPT.format(
            context_description=context_description,
            analytics_section=analytics_section,
            rag_section=rag_section,
            question=state.question,
            chat_history=history_text,
        )

        response = self.llm.invoke(prompt)
        answer   = response.content

        # Collect sources from RAG
        sources = []
        if state.retrieved_docs:
            for doc in state.retrieved_docs[:3]:
                src  = doc.metadata.get("source", "document")
                page = doc.metadata.get("page", "")
                import os
                src_name = os.path.basename(str(src))
                sources.append(
                    src_name + (f" p.{page}" if page else "")
                )

        return CopilotState(
            **{**state.model_dump(),
               "answer": answer,
               "sources": list(dict.fromkeys(sources))}
        )
