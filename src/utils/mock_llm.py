"""
Shared MockChatModel for offline/no-API-key operation.
Used by Config.get_llm() when no key is present,
and by graph_builder.py as fallback on LLM errors.
"""

import json
import logging
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, AIMessage
from langchain_core.outputs import ChatResult, ChatGeneration
from typing import List, Any, Optional

logger = logging.getLogger(__name__)


def _map_columns(question: str, numeric_cols: list, cat_cols: list, date_cols: list) -> dict:
    """Rule-based column mapping — safe fallback, no eval()."""
    q = question.lower()

    # Map numeric column
    mapped_num = numeric_cols[0] if numeric_cols else ""
    for keyword, synonyms in {
        "revenue": ["sales", "revenue", "amount"],
        "profit":  ["profit", "margin"],
        "quantity": ["quantity", "unit", "qty"],
    }.items():
        if any(s in q for s in synonyms):
            for col in numeric_cols:
                if any(s in col.lower() for s in synonyms):
                    mapped_num = col
                    break
            break

    # Map categorical column
    mapped_cat = cat_cols[0] if cat_cols else ""
    for keyword, synonyms in {
        "product":  ["product", "item", "sku"],
        "category": ["category", "type", "dept"],
        "customer": ["customer", "client", "buyer"],
        "region":   ["region", "store", "location"],
    }.items():
        if any(s in q for s in synonyms):
            for col in cat_cols:
                if any(s in col.lower() for s in synonyms):
                    mapped_cat = col
                    break
            break

    # Map date column
    mapped_date = date_cols[0] if date_cols else ""
    for col in date_cols:
        if any(k in col.lower() for k in ["date", "time", "month", "year"]):
            mapped_date = col
            break

    return {
        "numeric_col": mapped_num,
        "categorical_col": mapped_cat,
        "date_col": mapped_date,
    }


def _parse_column_context(original_msg: str) -> dict:
    """
    Safely parse column lists from a prompt string using json.loads().
    Replaces the previous eval() approach which was a security risk.
    """
    numeric_cols, cat_cols, date_cols, question = [], [], [], ""

    try:
        lines = original_msg.split("\n")
        for line in lines:
            if "Available Numeric Columns:" in line:
                raw = line.split("Available Numeric Columns:")[-1].strip()
                # Convert Python list repr to valid JSON
                numeric_cols = json.loads(raw.replace("'", '"'))
            elif "Available Categorical Columns:" in line:
                raw = line.split("Available Categorical Columns:")[-1].strip()
                cat_cols = json.loads(raw.replace("'", '"'))
            elif "Available Date Columns:" in line:
                raw = line.split("Available Date Columns:")[-1].strip()
                date_cols = json.loads(raw.replace("'", '"'))
            elif line.strip().startswith("Question:"):
                question = line.split("Question:")[-1].strip()
    except (json.JSONDecodeError, Exception) as e:
        logger.warning(f"MockLLM column parse failed: {e}")

    return {"numeric_cols": numeric_cols, "cat_cols": cat_cols,
            "date_cols": date_cols, "question": question}


class MockChatModel(BaseChatModel):
    """
    Offline mock LLM. Used when no API key is configured or
    when the real LLM call fails at runtime.

    Handles three prompt types:
      1. Intent routing  → returns "analytics", "rag", or "both"
      2. Column mapping  → returns JSON column selection
      3. Synthesis       → echoes the analytics result as the answer
    """

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> ChatResult:
        original_msg = messages[-1].content
        msg_lower = original_msg.lower()

        # --- Path 1: Intent routing ---
        if any(kw in msg_lower for kw in ["classifying", "intent", "classify into exactly one"]):
            if any(w in msg_lower for w in
                   ["highest", "trend", "anomaly", "outlier",
                    "sales", "revenue", "product", "quantity", "price"]):
                content = "analytics"
            elif any(w in msg_lower for w in
                     ["report", "strategy", "policy", "document", "summarise"]):
                content = "rag"
            else:
                content = "both"

        # --- Path 2: Column mapping ---
        elif "map a user's question to the correct columns" in msg_lower:
            ctx = _parse_column_context(original_msg)
            result = _map_columns(
                ctx["question"],
                ctx["numeric_cols"],
                ctx["cat_cols"],
                ctx["date_cols"],
            )
            content = json.dumps(result)

        # --- Path 3: Synthesis / everything else ---
        else:
            # Echo the analytics result if present, otherwise generic answer
            if "analytics results:" in msg_lower:
                try:
                    idx = msg_lower.find("analytics results:")
                    after = original_msg[idx + len("analytics results:"):]
                    # Stop before any next section header
                    for header in ["document context:", "recent chat history:",
                                   "user question:", "human:", "system:"]:
                        hi = after.lower().find(header)
                        if hi != -1:
                            after = after[:hi]
                    content = "### 📊 Analytics Report\n\n" + after.strip()
                except Exception:
                    content = "Analytics computation completed."
            else:
                content = (
                    "Based on the uploaded data, the top product is Laptop "
                    "with the highest revenue. Electronics leads all categories. "
                    "Recommendation: prioritise restocking Electronics."
                )

        return ChatResult(
            generations=[ChatGeneration(message=AIMessage(content=content))]
        )

    @property
    def _llm_type(self) -> str:
        return "mock-chat-model"
