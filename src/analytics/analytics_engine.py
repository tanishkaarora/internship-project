"""Business analytics computations on pandas DataFrames"""

import pandas as pd
import numpy as np
from typing import Optional

class AnalyticsEngine:
    """Computes KPIs, trends, and anomalies from business DataFrames"""

    def compute_kpis(self, df: pd.DataFrame, profile: dict) -> dict:
        """Return a dict of KPI name → value for display as st.metric cards"""
        kpis = {"Total Rows": f"{len(df):,}"}
        for col in profile["numeric_cols"][:4]:
            label = col.replace("_", " ").title()
            kpis[f"Total {label}"] = f"{df[col].sum():,.2f}"
            kpis[f"Avg {label}"] = f"{df[col].mean():,.2f}"
        return kpis

    def top_n_by_column(self, df: pd.DataFrame, group_col: str,
                         value_col: str, n: int = 5, ascending: bool = False) -> str:
        """
        Returns a text table of top/bottom N entries.
        Used by the analytics node when question asks about best/worst performers.
        """
        # Guard: if group_col has only 1 unique value, ranking is meaningless
        if df[group_col].nunique() < 2:
            return (
                f"Only one unique value in '{group_col}' "
                f"({df[group_col].iloc[0]}) — no ranking possible."
            )

        # Guard: if value_col has no variance, all rankings are equal
        if df[value_col].nunique() < 2:
            return (
                f"All rows have the same value in '{value_col}' "
                f"({df[value_col].iloc[0]:,.2f}) — no ranking possible."
            )

        grouped = df.groupby(group_col)[value_col].sum().reset_index()
        grouped = grouped.sort_values(value_col, ascending=ascending).head(n)
        rows = [f"{rank}. {row[group_col]}: {row[value_col]:,.2f}"
                for rank, (_, row) in enumerate(grouped.iterrows(), 1)]
        direction = "Bottom" if ascending else "Top"
        return f"{direction} {n} {group_col} by {value_col}:\n" + "\n".join(rows)

    def trend_over_time(self, df: pd.DataFrame, date_col: str,
                        value_col: str) -> str:
        """Compute period-over-period trend and growth rate"""
        if date_col not in df.columns or value_col not in df.columns:
            return f"Columns {date_col} or {value_col} not found."
        df = df.copy()
        df[date_col] = pd.to_datetime(df[date_col])
        monthly = df.groupby(df[date_col].dt.to_period("M"))[value_col].sum()
        if len(monthly) < 2:
            return f"Not enough periods to compute trend for {value_col}."
        growth = ((monthly.iloc[-1] - monthly.iloc[-2]) / monthly.iloc[-2]) * 100
        direction = "up" if growth > 0 else "down"
        result = (
            f"{value_col} trend: {direction} {abs(growth):.1f}% "
            f"(latest period: {monthly.index[-1]}, value: {monthly.iloc[-1]:,.2f}). "
            f"Previous period: {monthly.index[-2]}, value: {monthly.iloc[-2]:,.2f}."
        )
        # Add last 6 periods
        recent = monthly.tail(6)
        result += "\nRecent monthly values:\n"
        result += "\n".join(f"  {p}: {v:,.2f}" for p, v in recent.items())
        return result

    def detect_anomalies(self, df: pd.DataFrame, value_col: str,
                          group_col: Optional[str] = None) -> str:
        """
        Simple Z-score anomaly detection.
        Flags values more than 2 standard deviations from mean.
        """
        if value_col not in df.columns:
            return f"Column {value_col} not found."
        col = df[value_col]
        mean, std = col.mean(), col.std()
        if std == 0:
            return f"No variance in {value_col} — cannot detect anomalies."
        z_scores = (col - mean) / std
        anomalies = df[abs(z_scores) > 2]
        if len(anomalies) == 0:
            return f"No anomalies detected in {value_col} (all values within 2 std of mean)."
        lines = [f"Found {len(anomalies)} anomalies in {value_col}:"]
        for _, row in anomalies.head(5).iterrows():
            if group_col and group_col in df.columns:
                lines.append(f"  {row[group_col]}: {row[value_col]:,.2f} (mean: {mean:,.2f})")
            else:
                lines.append(f"  {row[value_col]:,.2f} (mean: {mean:,.2f})")
        return "\n".join(lines)

    def full_summary(self, df: pd.DataFrame, profile: dict) -> str:
        """
        Generate a complete analytics summary for use in LLM prompts.
        This is what the Synthesiser node receives when route='both'.
        """
        parts = [f"=== Analytics Summary ===", profile["summary_text"]]

        # Top performers for each numeric × categorical combo
        for cat in profile["cat_cols"][:2]:
            for num in profile["numeric_cols"][:2]:
                try:
                    parts.append(self.top_n_by_column(df, cat, num, n=3))
                except Exception:
                    pass

        # Trend if date column exists
        if profile["date_cols"] and profile["numeric_cols"]:
            try:
                parts.append(self.trend_over_time(
                    df, profile["date_cols"][0], profile["numeric_cols"][0]
                ))
            except Exception:
                pass

        return "\n\n".join(parts)
