"""Auto-generate Plotly charts from business DataFrames"""

import pandas as pd
import plotly.express as px
from typing import List, Tuple

def generate_charts(df: pd.DataFrame, profile: dict) -> List[Tuple[str, object]]:
    """
    Returns list of (title, plotly_figure) tuples.
    Called from streamlit_app.py and rendered with st.plotly_chart().
    """
    charts = []
    nums = profile["numeric_cols"]
    cats = profile["cat_cols"]
    dates = profile["date_cols"]

    # Bar: first categorical vs first numeric
    if cats and nums:
        grouped = df.groupby(cats[0])[nums[0]].sum().reset_index()
        grouped = grouped.sort_values(nums[0], ascending=False).head(10)
        fig = px.bar(grouped, x=cats[0], y=nums[0],
                     title=f"{nums[0].replace('_',' ').title()} by {cats[0].replace('_',' ').title()}")
        charts.append((f"By {cats[0]}", fig))

    # Line: trend over time
    if dates and nums:
        df2 = df.copy()
        df2[dates[0]] = pd.to_datetime(df2[dates[0]])
        monthly = df2.groupby(df2[dates[0]].dt.to_period("M"))[nums[0]].sum().reset_index()
        monthly[dates[0]] = monthly[dates[0]].astype(str)
        fig = px.line(monthly, x=dates[0], y=nums[0], title="Trend Over Time", markers=True)
        charts.append(("Trend", fig))

    # Histogram: distribution of first numeric
    if nums:
        fig = px.histogram(df, x=nums[0],
                           title=f"Distribution: {nums[0].replace('_',' ').title()}")
        charts.append(("Distribution", fig))

    # Scatter: if 2+ numerics
    if len(nums) >= 2:
        scatter_df = df.copy()
        if cats and scatter_df[cats[0]].nunique() > 15:
            color_col = None
        else:
            color_col = cats[0] if cats else None
        fig = px.scatter(scatter_df, x=nums[0], y=nums[1],
                         color=color_col,
                         title=f"{nums[0]} vs {nums[1]}")
        charts.append((f"{nums[0]} vs {nums[1]}", fig))

    return charts
