"""Runs analytics operations on the business DataFrame"""

from src.state.copilot_state import CopilotState
from src.analytics.analytics_engine import AnalyticsEngine
from src.analytics.column_detective import SmartColumnDetective
import streamlit as st

class AnalyticsNode:
    def __init__(self, llm):
        self.llm = llm
        self.engine = AnalyticsEngine()
        self.detective = SmartColumnDetective(llm)

    def run(self, state: CopilotState) -> CopilotState:
        """
        Determines what analytics to run based on question keywords,
        runs the computation, and stores result in state.
        """
        # Get the DataFrame from Streamlit session state
        # (passed externally because DataFrames can't be in LangGraph state)
        df = st.session_state.get("clean_df")
        profile = st.session_state.get("data_profile")

        if df is None or profile is None:
            analytics_result = "No data file has been uploaded. Please upload a CSV or Excel file first."
        else:
            analytics_result = self._run_analysis(state.question, df, profile)

        return CopilotState(**{**state.model_dump(), "analytics_result": analytics_result})

    def _run_analysis(self, question: str, df, profile: dict) -> str:
        """Select and run the right analytics based on question content"""
        q = question.lower()
        
        # Dynamically map query terms to columns
        mapped = self.detective.detect(question, profile)
        value_col = mapped.get("numeric_col")
        group_col = mapped.get("categorical_col")
        date_col = mapped.get("date_col")

        results = []

        # Summary / overview request — LLM writes a narrative
        summary_triggers = [
            "summarise", "summarize", "summary",
            "overview", "tell me about", "what does this data",
            "key insights", "analyse the data", "analyze the data",
            "what should i know", "what does this tell",
            "give me a", "overall",
        ]
        if any(w in q for w in summary_triggers):
            # Get full analytics summary and pass to LLM for narrative
            raw_summary = self.engine.full_summary(df, profile)
            llm_prompt = f"""You are a business analyst.
Write a clear, professional 3-paragraph narrative summary
of this retail dataset. Do NOT use bullet points.
Write in plain prose like an analyst presenting to a manager.

Dataset analysis:
{raw_summary}

Structure your narrative as:
Paragraph 1: What this dataset is and what it covers
(rows, columns, date range, key metrics)
Paragraph 2: The most important patterns and findings
(top performers, trends, notable numbers)
Paragraph 3: What needs attention and one recommendation

Maximum 180 words total. Be specific with numbers."""

            response = self.llm.invoke(llm_prompt)
            return response.content

        # Top/bottom performers
        if any(w in q for w in ["top", "best", "highest", "most"]):
            if group_col and value_col:
                results.append(self.engine.top_n_by_column(df, group_col, value_col, ascending=False))

        if any(w in q for w in ["bottom", "worst", "lowest", "underperform"]):
            if group_col and value_col:
                results.append(self.engine.top_n_by_column(df, group_col, value_col, ascending=True))

        # Trend
        if any(w in q for w in ["trend", "over time", "monthly", "growth", "decline", "drop"]):
            if date_col and value_col:
                results.append(self.engine.trend_over_time(df, date_col, value_col))

        # Anomalies
        if any(w in q for w in ["anomaly", "anomalies", "unusual", "spike", "outlier"]):
            if value_col:
                results.append(self.engine.detect_anomalies(df, value_col, group_col))

        # Default: full summary
        if len(results) == 1:  # Only metadata present
            results.append(self.engine.full_summary(df, profile))

        return "\n\n".join(results)

