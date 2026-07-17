"""Smart Column Detective to map user queries to dataframe columns"""

import json
import logging

logger = logging.getLogger(__name__)

class SmartColumnDetective:
    """Detects target columns for analysis based on user queries and data schema"""

    def __init__(self, llm):
        self.llm = llm

    def detect(self, question: str, profile: dict) -> dict:
        """
        Maps a question to the most relevant numeric, categorical, and date columns.
        Returns a dict: {"numeric_col": str, "categorical_col": str, "date_col": str}
        """
        numeric_cols = profile.get("numeric_cols", [])
        cat_cols = profile.get("cat_cols", [])
        date_cols = profile.get("date_cols", [])

        q_lower = question.lower()

        # 1. Rule-based keyword matching (Fast Path)
        detected_num = self._find_best_match(q_lower, numeric_cols, {
            "sales": ["sales", "revenue", "amount", "sold"],
            "profit": ["profit", "margin", "gain"],
            "cost": ["cost", "price", "expense"],
            "quantity": ["quantity", "units", "qty", "count"]
        })

        detected_cat = self._find_best_match(q_lower, cat_cols, {
            "product": ["product", "item", "sku"],
            "category": ["category", "dept", "department", "type"],
            "brand": ["brand", "manufacturer", "supplier"],
            "customer": ["customer", "client", "user", "buyer"],
            "region": ["region", "store", "location", "city", "country"]
        })

        detected_date = self._find_best_match(q_lower, date_cols, {
            "date": ["date", "time", "timestamp", "day", "month", "year"]
        })

        # Default fallbacks if no keyword matching worked
        default_num = detected_num or (numeric_cols[0] if numeric_cols else None)
        default_cat = detected_cat or (cat_cols[0] if cat_cols else None)
        default_date = detected_date or (date_cols[0] if date_cols else None)

        # 2. LLM-based matching (Semantic Path)
        if not self.llm:
            return {
                "numeric_col": default_num,
                "categorical_col": default_cat,
                "date_col": default_date
            }

        try:
            from src.prompts.business_prompts import COLUMN_DETECTIVE_PROMPT
            prompt = COLUMN_DETECTIVE_PROMPT.format(
                numeric_cols=str(numeric_cols),
                categorical_cols=str(cat_cols),
                date_cols=str(date_cols),
                question=question
            )
            response = self.llm.invoke(prompt)
            content = response.content.strip()

            # Clean JSON out of markdown blocks
            if content.startswith("```"):
                lines = content.split("\n")
                if lines[0].startswith("```json") or lines[0].startswith("```"):
                    content = "\n".join(lines[1:-1]).strip()

            res_dict = json.loads(content)

            final_num = res_dict.get("numeric_col")
            final_cat = res_dict.get("categorical_col")
            final_date = res_dict.get("date_col")

            # Validate that LLM-selected columns actually exist in the schema
            if final_num not in numeric_cols:
                final_num = default_num
            if final_cat not in cat_cols:
                final_cat = default_cat
            if final_date not in date_cols:
                final_date = default_date

            return {
                "numeric_col": final_num or default_num,
                "categorical_col": final_cat or default_cat,
                "date_col": final_date or default_date
            }

        except Exception as e:
            logger.warning(f"SmartColumnDetective LLM call failed, falling back to heuristics: {e}")
            return {
                "numeric_col": default_num,
                "categorical_col": default_cat,
                "date_col": default_date
            }

    def _find_best_match(self, question: str, columns: list, synonym_map: dict) -> str:
        """Finds if a column name or its synonyms are mentioned in the question"""
        # First check for exact/partial column name matches in the question
        for col in columns:
            col_clean = col.lower().replace("_", " ")
            if col in question or col_clean in question:
                return col

        # Next check for synonym mapping matches
        for concept, synonyms in synonym_map.items():
            if any(syn in question for syn in synonyms):
                # Find a column that matches the concept or synonyms
                for col in columns:
                    col_lower = col.lower()
                    if concept in col_lower or any(syn in col_lower for syn in synonyms):
                        return col

        return None
