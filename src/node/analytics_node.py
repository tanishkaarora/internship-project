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

    def _run_analysis(
        self, question: str, df, profile: dict
    ) -> str:
        q       = question.lower()
        nums    = profile.get("numeric_cols", [])
        cats    = profile.get("cat_cols", [])
        dates   = profile.get("date_cols", [])

        # Filter to meaningful metrics only
        NON_METRIC = [
            "postal", "zip", "pin", "code",
            "id", "key", "index", "row", "number",
            "phone", "lat", "lon",
        ]
        def is_metric(col):
            cl = col.lower()
            return not any(
                cl == kw or cl.endswith("_" + kw)
                or cl.startswith(kw + "_")
                for kw in NON_METRIC
            )

        metric_cols = [c for c in nums if is_metric(c)]
        if not metric_cols and nums:
            metric_cols = nums[:2]

        # Good grouping columns only
        NON_GROUP = ["_id", "_key", "_number"]
        group_cols = [
            c for c in cats
            if not any(c.lower().endswith(s)
                       for s in NON_GROUP)
            and c.lower() not in ("id", "index", "row")
            and df[c].nunique() < 200
        ]

        primary_metric   = metric_cols[0] if metric_cols else None
        secondary_metric = metric_cols[1] if len(metric_cols) > 1 else None
        primary_group    = group_cols[0] if group_cols else None

        results = []

        # ── Summary / overview request ──────────────────────
        summary_triggers = [
            "summarise", "summarize", "summary",
            "overview", "tell me about", "what does this data",
            "key insights", "analyse", "analyze",
            "what should i know", "give me a",
            "overall", "tell about",
        ]
        if any(w in q for w in summary_triggers):
            results.append(
                self.engine.full_summary(df, profile)
            )
            # Add business framing
            if primary_group and primary_metric:
                results.append(
                    self.engine.top_n_by_column(
                        df, primary_group,
                        primary_metric, n=3
                    )
                )
            if dates and primary_metric:
                try:
                    results.append(
                        self.engine.trend_over_time(
                            df, dates[0], primary_metric
                        )
                    )
                except Exception:
                    pass
            return "\n\n".join(results)

        # ── Top performers ──────────────────────────────────
        if any(w in q for w in [
            "top", "best", "highest", "most",
            "leading", "drives", "which", "dominant"
        ]):
            if primary_group and primary_metric:
                # Detect if question specifies a different group
                chosen_group = primary_group
                for col in group_cols:
                    label = col.replace("_", " ").lower()
                    if label in q or col.lower() in q:
                        chosen_group = col
                        break

                chosen_metric = primary_metric
                for col in metric_cols:
                    label = col.replace("_", " ").lower()
                    if label in q or col.lower() in q:
                        chosen_metric = col
                        break

                results.append(
                    self.engine.top_n_by_column(
                        df, chosen_group,
                        chosen_metric, n=5,
                        ascending=False
                    )
                )
                # Add total context
                total = df[chosen_metric].sum()
                top5_total = (
                    df.groupby(chosen_group)[chosen_metric]
                    .sum()
                    .nlargest(5)
                    .sum()
                )
                share = (top5_total / total * 100
                         ) if total else 0
                results.append(
                    f"Total {chosen_metric.replace('_',' ').title()}: "
                    f"{total:,.2f}. "
                    f"Top 5 account for {share:.1f}% of total."
                )

        # ── Bottom / underperforming ────────────────────────
        if any(w in q for w in [
            "bottom", "worst", "lowest", "underperform",
            "weakest", "poor", "lagging", "dragging"
        ]):
            if primary_group and primary_metric:
                chosen_group  = primary_group
                chosen_metric = primary_metric
                for col in group_cols:
                    if col.replace("_"," ").lower() in q:
                        chosen_group = col
                        break
                for col in metric_cols:
                    if col.replace("_"," ").lower() in q:
                        chosen_metric = col
                        break

                results.append(
                    self.engine.top_n_by_column(
                        df, chosen_group,
                        chosen_metric, n=5,
                        ascending=True
                    )
                )

        # ── Trend ───────────────────────────────────────────
        if any(w in q for w in [
            "trend", "over time", "monthly", "growth",
            "decline", "drop", "growing", "falling",
            "improving", "worsening", "time"
        ]):
            if dates and metric_cols:
                chosen_metric = primary_metric
                for col in metric_cols:
                    if col.replace("_"," ").lower() in q:
                        chosen_metric = col
                        break
                try:
                    results.append(
                        self.engine.trend_over_time(
                            df, dates[0], chosen_metric
                        )
                    )
                except Exception as e:
                    results.append(
                        f"Could not compute trend: {e}"
                    )

        # ── Anomalies ────────────────────────────────────────
        if any(w in q for w in [
            "anomal", "unusual", "spike", "outlier",
            "weird", "unexpected", "strange"
        ]):
            if metric_cols:
                chosen_metric = primary_metric
                for col in metric_cols:
                    if col.replace("_"," ").lower() in q:
                        chosen_metric = col
                        break
                results.append(
                    self.engine.detect_anomalies(
                        df, chosen_metric,
                        group_col=primary_group
                    )
                )

        # ── Default: full summary if nothing matched ─────────
        if not results:
            if primary_group and primary_metric:
                results.append(
                    self.engine.top_n_by_column(
                        df, primary_group,
                        primary_metric, n=5
                    )
                )
                if dates:
                    try:
                        results.append(
                            self.engine.trend_over_time(
                                df, dates[0], primary_metric
                            )
                        )
                    except Exception:
                        pass
            else:
                results.append(
                    self.engine.full_summary(df, profile)
                )

        return "\n\n".join(results)

