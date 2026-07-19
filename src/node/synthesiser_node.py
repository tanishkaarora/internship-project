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
            # Only pass the last 2 exchanges (4 messages max)
            # Truncate each message more aggressively to prevent
            # previous analytics results from polluting new answers
            recent = state.chat_history[-4:]
            history_text_parts = []
            for m in recent:
                role = m["role"].upper()
                # For assistant messages, only take first sentence
                # to avoid full analytics dumps appearing as context
                content = m["content"]
                if role == "ASSISTANT":
                    # Take only up to the first newline or 120 chars
                    first_line = content.split("\n")[0][:120]
                    content = first_line + ("..." if len(content) > 120 else "")
                else:
                    # User questions: keep full but cap at 150 chars
                    content = content[:150]
                history_text_parts.append(f"{role}: {content}")
            history_text = "\n".join(history_text_parts)

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
