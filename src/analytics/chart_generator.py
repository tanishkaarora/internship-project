"""Auto-generate rich, annotated Plotly charts for retail business data"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import List, Tuple
import numpy as np

# ── Consistent color theme across all charts ────────────────────────────────
PALETTE = [
    "#6366f1", "#06b6d4", "#10b981", "#f59e0b",
    "#ef4444", "#8b5cf6", "#ec4899", "#14b8a6"
]
CHART_BG    = "rgba(0,0,0,0)"   # transparent — works on dark + light themes
GRID_COLOR  = "rgba(255,255,255,0.08)"
TEXT_COLOR  = "#e2e8f0"
FONT_FAMILY = "Inter, Outfit, sans-serif"

BASE_LAYOUT = dict(
    paper_bgcolor=CHART_BG,
    plot_bgcolor=CHART_BG,
    font=dict(family=FONT_FAMILY, color=TEXT_COLOR, size=12),
    margin=dict(t=60, b=40, l=40, r=20),
    colorway=PALETTE,
    hoverlabel=dict(
        bgcolor="#1e293b",
        bordercolor="#475569",
        font=dict(color="#f1f5f9", size=12)
    ),
    xaxis=dict(gridcolor=GRID_COLOR, linecolor=GRID_COLOR, zeroline=False),
    yaxis=dict(gridcolor=GRID_COLOR, linecolor=GRID_COLOR, zeroline=False),
)


def _apply_base(fig: go.Figure, title: str, subtitle: str = "") -> go.Figure:
    """Apply consistent theme and title to any figure."""
    full_title = (
        f"<b>{title}</b><br>"
        f"<span style='font-size:11px;color:#94a3b8'>{subtitle}</span>"
        if subtitle else f"<b>{title}</b>"
    )
    fig.update_layout(
        **BASE_LAYOUT,
        title=dict(
            text=full_title,
            x=0.02,
            xanchor="left",
            font=dict(size=15, color=TEXT_COLOR)
        )
    )
    return fig


def _insight_text(text: str) -> str:
    """Wrap insight text in styled HTML for display below chart."""
    return (
        f"<span style='font-size:12px;color:#94a3b8;"
        f"font-style:italic'>{text}</span>"
    )


# ── Individual chart builders ────────────────────────────────────────────────

def _bar_chart(df: pd.DataFrame, cat_col: str,
               num_col: str) -> Tuple[str, go.Figure, str]:
    """
    Ranked bar chart with value labels on each bar.
    Shows top 10 by default. Color-codes the #1 bar differently.
    """
    grouped = (
        df.groupby(cat_col)[num_col]
        .sum()
        .reset_index()
        .sort_values(num_col, ascending=False)
        .head(10)
    )
    if grouped.empty:
        raise ValueError("No data to plot")

    top_val   = grouped[num_col].iloc[0]
    top_label = grouped[cat_col].iloc[0]
    total     = grouped[num_col].sum()
    top_share = (top_val / total * 100) if total else 0

    colors = [PALETTE[0] if i == 0 else PALETTE[2]
              for i in range(len(grouped))]

    fig = go.Figure(go.Bar(
        x=grouped[cat_col],
        y=grouped[num_col],
        marker_color=colors,
        marker_line_width=0,
        text=[f"{v:,.0f}" for v in grouped[num_col]],
        textposition="outside",
        textfont=dict(size=10, color=TEXT_COLOR),
        hovertemplate=(
            f"<b>%{{x}}</b><br>"
            f"{num_col}: %{{y:,.2f}}<extra></extra>"
        ),
    ))

    label = num_col.replace("_", " ").title()
    cat   = cat_col.replace("_", " ").title()

    _apply_base(
        fig,
        title=f"{label} by {cat}",
        subtitle=f"Top 10 · Total: {total:,.0f}"
    )
    fig.update_layout(
        yaxis_title=label,
        xaxis_title=cat,
        showlegend=False,
    )

    insight = (
        f"📊 {top_label} leads with {top_val:,.0f} "
        f"({top_share:.1f}% of total shown)."
    )
    return (f"{label} by {cat}", fig, insight)


def _trend_chart(df: pd.DataFrame, date_col: str,
                 num_col: str) -> Tuple[str, go.Figure, str]:
    """
    Monthly trend line with:
    - Shaded area under the line
    - Annotated highest and lowest months
    - Growth rate in subtitle
    """
    df2 = df.copy()
    df2[date_col] = pd.to_datetime(df2[date_col])
    monthly = (
        df2.groupby(df2[date_col].dt.to_period("M"))[num_col]
        .sum()
        .reset_index()
    )
    monthly[date_col] = monthly[date_col].astype(str)

    if len(monthly) < 2:
        raise ValueError("Need at least 2 periods for trend")

    vals  = monthly[num_col].tolist()
    dates = monthly[date_col].tolist()

    growth = ((vals[-1] - vals[-2]) / vals[-2] * 100) if vals[-2] else 0
    growth_str = f"{'▲' if growth >= 0 else '▼'} {abs(growth):.1f}% vs last period"

    max_idx = int(np.argmax(vals))
    min_idx = int(np.argmin(vals))

    fig = go.Figure()

    # Shaded area
    fig.add_trace(go.Scatter(
        x=dates, y=vals,
        fill="tozeroy",
        fillcolor="rgba(99,102,241,0.12)",
        line=dict(color=PALETTE[0], width=0),
        showlegend=False, hoverinfo="skip"
    ))

    # Main line
    fig.add_trace(go.Scatter(
        x=dates, y=vals,
        mode="lines+markers",
        line=dict(color=PALETTE[0], width=2.5),
        marker=dict(size=6, color=PALETTE[0]),
        hovertemplate="<b>%{x}</b><br>Value: %{y:,.0f}<extra></extra>",
        showlegend=False,
        name=num_col.replace("_", " ").title(),
    ))

    # Peak annotation
    fig.add_annotation(
        x=dates[max_idx], y=vals[max_idx],
        text=f"Peak<br>{vals[max_idx]:,.0f}",
        showarrow=True, arrowhead=2,
        arrowcolor=PALETTE[2], font=dict(size=10, color=PALETTE[2]),
        bgcolor="rgba(16,185,129,0.15)", bordercolor=PALETTE[2],
        ay=-40
    )

    # Trough annotation (only if different from peak)
    if min_idx != max_idx:
        fig.add_annotation(
            x=dates[min_idx], y=vals[min_idx],
            text=f"Low<br>{vals[min_idx]:,.0f}",
            showarrow=True, arrowhead=2,
            arrowcolor=PALETTE[4], font=dict(size=10, color=PALETTE[4]),
            bgcolor="rgba(239,68,68,0.15)", bordercolor=PALETTE[4],
            ay=40
        )

    label = num_col.replace("_", " ").title()
    _apply_base(fig, title=f"{label} Over Time", subtitle=growth_str)
    fig.update_layout(yaxis_title=label, xaxis_title="Month")

    direction = "up" if growth >= 0 else "down"
    insight = (
        f"📈 {label} is trending {direction} {abs(growth):.1f}% "
        f"vs last period. Peak was {dates[max_idx]} "
        f"({vals[max_idx]:,.0f})."
    )
    return ("Trend Over Time", fig, insight)


def _category_pie(df: pd.DataFrame, cat_col: str,
                  num_col: str) -> Tuple[str, go.Figure, str]:
    """
    Donut chart showing share of each category.
    Better than a full pie — the hole gives space for a center label.
    """
    grouped = (
        df.groupby(cat_col)[num_col]
        .sum()
        .reset_index()
        .sort_values(num_col, ascending=False)
        .head(8)
    )
    if grouped.empty:
        raise ValueError("No data for pie")

    top_label = grouped[cat_col].iloc[0]
    top_val   = grouped[num_col].iloc[0]
    total     = grouped[num_col].sum()
    top_share = (top_val / total * 100) if total else 0

    fig = go.Figure(go.Pie(
        labels=grouped[cat_col],
        values=grouped[num_col],
        hole=0.55,
        marker=dict(
            colors=PALETTE[:len(grouped)],
            line=dict(color="#0f172a", width=2)
        ),
        textinfo="label+percent",
        textfont=dict(size=11),
        hovertemplate=(
            "<b>%{label}</b><br>"
            "Value: %{value:,.0f}<br>"
            "Share: %{percent}<extra></extra>"
        ),
    ))

    # Center annotation
    label = num_col.replace("_", " ").title()
    fig.add_annotation(
        text=f"<b>Total</b><br>{total:,.0f}",
        x=0.5, y=0.5, showarrow=False,
        font=dict(size=13, color=TEXT_COLOR)
    )

    cat = cat_col.replace("_", " ").title()
    _apply_base(
        fig,
        title=f"{label} Share by {cat}",
        subtitle=f"Top 8 categories · Total: {total:,.0f}"
    )
    fig.update_layout(showlegend=True, legend=dict(
        orientation="v", x=1.02, y=0.5
    ))

    insight = (
        f"🥧 {top_label} holds the largest share at "
        f"{top_share:.1f}% of total {label.lower()}."
    )
    return (f"{label} Share", fig, insight)


def _top_bottom_chart(df: pd.DataFrame, cat_col: str,
                      num_col: str) -> Tuple[str, go.Figure, str]:
    """
    Horizontal bar chart showing top N and bottom N side by side.
    Immediately shows best and worst performers at a glance.
    """
    grouped = (
        df.groupby(cat_col)[num_col]
        .sum()
        .reset_index()
        .sort_values(num_col, ascending=False)
    )
    if len(grouped) < 4:
        raise ValueError("Need at least 4 groups for top/bottom chart")

    n = min(5, len(grouped) // 2)
    top_df    = grouped.head(n)
    bottom_df = grouped.tail(n).sort_values(num_col, ascending=True)

    label = num_col.replace("_", " ").title()
    cat   = cat_col.replace("_", " ").title()

    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=[
            f"<b>Top {n}</b> by {label}",
            f"<b>Bottom {n}</b> by {label}"
        ],
        horizontal_spacing=0.12
    )

    fig.add_trace(go.Bar(
        y=top_df[cat_col], x=top_df[num_col],
        orientation="h",
        marker_color=PALETTE[2],
        marker_line_width=0,
        text=[f"{v:,.0f}" for v in top_df[num_col]],
        textposition="outside",
        textfont=dict(size=10, color=TEXT_COLOR),
        hovertemplate="<b>%{y}</b><br>Value: %{x:,.0f}<extra></extra>",
        showlegend=False,
    ), row=1, col=1)

    fig.add_trace(go.Bar(
        y=bottom_df[cat_col], x=bottom_df[num_col],
        orientation="h",
        marker_color=PALETTE[4],
        marker_line_width=0,
        text=[f"{v:,.0f}" for v in bottom_df[num_col]],
        textposition="outside",
        textfont=dict(size=10, color=TEXT_COLOR),
        hovertemplate="<b>%{y}</b><br>Value: %{x:,.0f}<extra></extra>",
        showlegend=False,
    ), row=1, col=2)

    fig.update_layout(
        **BASE_LAYOUT,
        title=dict(
            text=f"<b>Top vs Bottom Performers — {label} by {cat}</b>",
            x=0.02, font=dict(size=15, color=TEXT_COLOR)
        ),
        height=320,
    )
    fig.update_xaxes(gridcolor=GRID_COLOR, zeroline=False)
    fig.update_yaxes(gridcolor=GRID_COLOR)

    top_name    = top_df[cat_col].iloc[0]
    bottom_name = bottom_df[cat_col].iloc[0]
    gap = top_df[num_col].iloc[0] - bottom_df[num_col].iloc[0]

    insight = (
        f"🏆 {top_name} leads. "
        f"⚠️ {bottom_name} is the weakest performer. "
        f"Gap between best and worst: {gap:,.0f}."
    )
    return ("Top vs Bottom Performers", fig, insight)


def _histogram_chart(df: pd.DataFrame,
                     num_col: str) -> Tuple[str, go.Figure, str]:
    """
    Distribution histogram with:
    - Mean and median vertical lines
    - Annotations for both
    """
    col_data = df[num_col].dropna()
    if len(col_data) < 5:
        raise ValueError("Too few data points for histogram")

    mean_val   = col_data.mean()
    median_val = col_data.median()
    label      = num_col.replace("_", " ").title()

    fig = go.Figure(go.Histogram(
        x=col_data,
        marker_color=PALETTE[1],
        marker_line_color="#0f172a",
        marker_line_width=0.5,
        opacity=0.85,
        hovertemplate="Range: %{x}<br>Count: %{y}<extra></extra>",
        nbinsx=20,
    ))

    # Mean line
    fig.add_vline(
        x=mean_val, line_dash="dash",
        line_color=PALETTE[0], line_width=1.5,
        annotation_text=f"Mean: {mean_val:,.0f}",
        annotation_position="top right",
        annotation_font=dict(size=10, color=PALETTE[0])
    )

    # Median line
    fig.add_vline(
        x=median_val, line_dash="dot",
        line_color=PALETTE[3], line_width=1.5,
        annotation_text=f"Median: {median_val:,.0f}",
        annotation_position="top left",
        annotation_font=dict(size=10, color=PALETTE[3])
    )

    skew = "right-skewed" if mean_val > median_val else \
           "left-skewed"  if mean_val < median_val else "symmetric"

    _apply_base(
        fig,
        title=f"Distribution of {label}",
        subtitle=f"{len(col_data):,} values · {skew}"
    )
    fig.update_layout(
        xaxis_title=label,
        yaxis_title="Count",
        showlegend=False,
    )

    insight = (
        f"📉 {label} ranges from {col_data.min():,.0f} to "
        f"{col_data.max():,.0f}. Mean ({mean_val:,.0f}) vs "
        f"median ({median_val:,.0f}) — distribution is {skew}."
    )
    return (f"Distribution: {label}", fig, insight)


def _correlation_heatmap(df: pd.DataFrame,
                         numeric_cols: list) -> Tuple[str, go.Figure, str]:
    """
    Correlation heatmap with values shown in each cell.
    Only runs if there are 3+ numeric columns.
    """
    if len(numeric_cols) < 3:
        raise ValueError("Need 3+ numeric columns for correlation heatmap")

    corr = df[numeric_cols].corr().round(2)
    labels = [c.replace("_", " ").title() for c in numeric_cols]

    fig = go.Figure(go.Heatmap(
        z=corr.values,
        x=labels,
        y=labels,
        colorscale="RdBu",
        zmid=0,
        text=corr.values.round(2),
        texttemplate="%{text}",
        textfont=dict(size=11),
        hovertemplate=(
            "%{y} × %{x}<br>"
            "Correlation: %{z:.2f}<extra></extra>"
        ),
        colorbar=dict(
            title=dict(text="r", font=dict(color=TEXT_COLOR)),
            tickfont=dict(color=TEXT_COLOR)
        )
    ))

    _apply_base(
        fig,
        title="Correlation Between Numeric Columns",
        subtitle="Values near +1 = strong positive · near −1 = strong negative"
    )
    fig.update_layout(height=360)

    # Find strongest non-self correlation
    corr_no_diag = corr.copy()
    np.fill_diagonal(corr_no_diag.values, 0)
    max_idx = np.unravel_index(
        np.abs(corr_no_diag.values).argmax(),
        corr_no_diag.shape
    )
    r1 = labels[max_idx[0]]
    r2 = labels[max_idx[1]]
    rv = corr_no_diag.values[max_idx]
    direction = "positively" if rv > 0 else "negatively"

    insight = (
        f"🔗 Strongest relationship: {r1} and {r2} "
        f"are {direction} correlated (r={rv:.2f})."
    )
    return ("Correlations", fig, insight)


# ── Main entry point ─────────────────────────────────────────────────────────

def _best_grouping_col(
    df: pd.DataFrame,
    cat_cols: list,
    max_unique: int = 50,
) -> str | None:
    """
    Returns the best categorical column to use as a chart
    grouping dimension.

    Selection criteria (in priority order):
    1. Must not be an ID column (no _id suffix, not order_id etc.)
    2. Must have low cardinality (< max_unique unique values)
    3. Prefer columns with 3-20 unique values (ideal for charts)
    4. Among qualifying columns, prefer known business dimensions:
       category > sub_category > region > segment > product_name
       > city > state > brand > channel

    Returns None if no good grouping column exists.
    """
    # Columns that are bad for chart grouping
    BAD_SUFFIXES  = ("_id", "_key", "_number", "_no", "_ref")
    BAD_EXACT     = {"id", "index", "idx", "row", "key",
                     "uuid", "guid", "hash", "serial"}
    BAD_CONTAINS  = ["phone", "mobile", "fax", "email"]

    # Priority order for known good dimensions
    PRIORITY_KEYWORDS = [
        "category", "sub_category", "subcategory",
        "segment", "type", "class", "grade", "status",
        "region", "zone", "territory",
        "brand", "manufacturer",
        "channel", "source", "medium",
        "product", "item", "sku",
        "city", "state", "country",
        "department", "dept",
        "store", "branch", "outlet",
        "salesperson", "rep", "agent",
    ]

    def score(col: str, n_unique: int) -> int:
        """Lower score = better (will be sorted ascending)"""
        col_lower = col.lower()
        # Priority match
        for i, kw in enumerate(PRIORITY_KEYWORDS):
            if kw in col_lower:
                # Bonus for ideal cardinality (3-20 unique vals)
                cardinality_bonus = (
                    0 if 3 <= n_unique <= 20 else
                    5 if n_unique <= 50 else 20
                )
                return i + cardinality_bonus
        # Unknown column — deprioritise
        return len(PRIORITY_KEYWORDS) + n_unique

    def is_bad_col(col: str) -> bool:
        col_lower = col.lower()
        if col_lower in BAD_EXACT:
            return True
        if any(col_lower.endswith(s) for s in BAD_SUFFIXES):
            return True
        if any(kw in col_lower for kw in BAD_CONTAINS):
            return True
        return False

    # Build list of (col, n_unique, score) for valid candidates
    candidates = []
    for col in cat_cols:
        if is_bad_col(col):
            continue
        n_unique = df[col].nunique()
        if n_unique < 2:
            continue  # Only 1 value — useless for charts
        if n_unique > max_unique:
            continue  # Too many — chart becomes unreadable
        candidates.append((col, n_unique, score(col, n_unique)))

    if not candidates:
        return None

    # Sort by score (lower = better) and return best
    candidates.sort(key=lambda x: x[2])
    return candidates[0][0]


def _best_metric_col(
    df: pd.DataFrame,
    numeric_cols: list,
) -> str | None:
    METRIC_PRIORITY = [
        "revenue", "sales", "income", "gmv", "turnover",
        "profit", "margin", "earnings",
        "amount", "value", "total",
        "quantity", "units", "qty", "volume",
        "discount", "rate",
        "cost", "spend", "expense",
        "score", "rating", "nps",
        "actual", "predicted", "forecast",
        "error", "variance",
        "inventory", "stock",
    ]

    # Keywords that make a numeric column NOT a metric
    # even though it contains numbers
    NON_METRIC_KEYWORDS = [
        "postal", "zip", "pin", "postcode",
        "phone", "mobile", "fax", "tel",
        "lat", "lon", "latitude", "longitude",
        "year_of_birth", "birth_year", "dob",
        "id", "key", "index", "row",
        "code", "number", "no", "num", "ref",
        "serial", "seq", "hash", "uuid",
    ]

    def is_non_metric(col: str) -> bool:
        col_lower = col.lower()
        # Check each keyword as a standalone word in the name
        for kw in NON_METRIC_KEYWORDS:
            if (col_lower == kw
                    or col_lower.startswith(kw + "_")
                    or col_lower.endswith("_" + kw)
                    or col_lower == kw):
                return True
        # Also reject if all values are unique
        # (strong signal: ID or reference column)
        if df[col].nunique() == len(df):
            return True
        return False

    def metric_score(col: str) -> int:
        if is_non_metric(col):
            return 9999
        col_lower = col.lower()
        for i, kw in enumerate(METRIC_PRIORITY):
            if kw in col_lower:
                return i
        return len(METRIC_PRIORITY)

    valid = [c for c in numeric_cols if metric_score(c) < 9999]
    if not valid:
        return None
    return min(valid, key=metric_score)


def _decide_chart_type(
    df: pd.DataFrame,
    group_col: str,
    metric_col: str,
) -> str:
    """
    Decides the best chart type for a grouping × metric pair
    based on actual data characteristics.

    Returns one of:
      "ranked_bar"    — single bar chart, all categories ranked
      "top_bottom"    — top 5 vs bottom 5 side by side
      "top10_bar"     — bar chart of top 10 only
      "treemap"       — area proportional chart for many categories
    """
    n_unique = df[group_col].nunique()

    if n_unique <= 6:
        # Too few categories for top/bottom to be meaningful
        # Show all categories in a single ranked bar
        return "ranked_bar"
    elif n_unique <= 15:
        # Perfect range for top vs bottom comparison
        return "top_bottom"
    elif n_unique <= 50:
        # Too many for side-by-side — show top 10 bar
        return "top10_bar"
    else:
        # Very high cardinality — treemap shows proportions
        return "treemap"


def _ranked_bar_chart(
    df: pd.DataFrame,
    cat_col: str,
    num_col: str,
) -> tuple:
    """
    Single horizontal bar chart showing ALL categories
    ranked by metric. Used when there are 6 or fewer
    unique values — top/bottom would be redundant.

    Color codes bars by performance:
      Top bar: green
      Bottom bar: red
      Middle bars: indigo gradient
    """
    grouped = (
        df.groupby(cat_col)[num_col]
        .sum()
        .reset_index()
        .sort_values(num_col, ascending=True)  # ascending for horizontal
    )

    if grouped.empty:
        raise ValueError("No data to plot")

    n     = len(grouped)
    total = grouped[num_col].sum()

    # Color: top = green, bottom = red, rest = gradient of purples
    def bar_color(i: int, total_bars: int) -> str:
        if i == total_bars - 1:  # highest (last after ascending sort)
            return "#10b981"     # green
        elif i == 0:             # lowest
            return "#ef4444"     # red
        else:
            # Purple gradient for middle bars
            opacity = 0.4 + (i / total_bars) * 0.5
            return f"rgba(99,102,241,{opacity:.2f})"

    colors = [bar_color(i, n) for i in range(n)]

    fig = go.Figure(go.Bar(
        y=grouped[cat_col],
        x=grouped[num_col],
        orientation="h",
        marker_color=colors,
        marker_line_width=0,
        text=[f"{v:,.0f}" for v in grouped[num_col]],
        textposition="outside",
        textfont=dict(size=11, color=TEXT_COLOR),
        hovertemplate=(
            "<b>%{y}</b><br>"
            f"{num_col.replace('_',' ').title()}: %{{x:,.0f}}<br>"
            "Share: %{customdata:.1f}%<extra></extra>"
        ),
        customdata=[
            (v / total * 100) if total else 0
            for v in grouped[num_col]
        ],
    ))

    label  = num_col.replace("_", " ").title()
    cat    = cat_col.replace("_", " ").title()
    top_name   = grouped[cat_col].iloc[-1]
    top_val    = grouped[num_col].iloc[-1]
    bot_name   = grouped[cat_col].iloc[0]
    bot_val    = grouped[num_col].iloc[0]
    top_share  = (top_val / total * 100) if total else 0

    _apply_base(
        fig,
        title=f"{label} by {cat} — All {n} Categories Ranked",
        subtitle=f"Total: {total:,.0f} · Sorted by performance"
    )
    fig.update_layout(
        xaxis_title=label,
        yaxis_title="",
        showlegend=False,
        height=max(250, n * 52),  # Scale height with category count
    )

    insight = (
        f"🏆 {top_name} leads with {top_val:,.0f} "
        f"({top_share:.1f}% of total). "
        f"🔴 {bot_name} is lowest at {bot_val:,.0f}. "
        f"Gap: {top_val - bot_val:,.0f}."
    )
    return (f"{label} by {cat}", fig, insight)


def _profit_margin_chart(
    df: pd.DataFrame,
    cat_col: str,
    revenue_col: str,
    profit_col: str,
) -> tuple:
    """
    Profit margin % by category.
    Business question: which category is most efficient?
    Different from revenue chart — a category can have
    high revenue but terrible margin (e.g. 2%) vs
    low revenue but great margin (e.g. 40%).
    This is what analysts look at after seeing revenue.
    """
    grouped = df.groupby(cat_col).agg(
        revenue=(revenue_col, "sum"),
        profit=(profit_col, "sum")
    ).reset_index()

    grouped["margin_pct"] = (
        grouped["profit"] / grouped["revenue"] * 100
    ).round(1)
    grouped = grouped.sort_values("margin_pct", ascending=True)

    n      = len(grouped)
    avg_margin = grouped["margin_pct"].mean()

    # Color: above average = green, below = red, near = amber
    def margin_color(m: float) -> str:
        if m >= avg_margin * 1.1:
            return "#10b981"   # green — above avg
        elif m < avg_margin * 0.9:
            return "#ef4444"   # red — below avg
        else:
            return "#f59e0b"   # amber — near avg

    colors = [margin_color(m) for m in grouped["margin_pct"]]

    fig = go.Figure()

    # Margin bars
    fig.add_trace(go.Bar(
        y=grouped[cat_col],
        x=grouped["margin_pct"],
        orientation="h",
        marker_color=colors,
        marker_line_width=0,
        text=[f"{m:.1f}%" for m in grouped["margin_pct"]],
        textposition="outside",
        textfont=dict(size=11, color=TEXT_COLOR),
        name="Margin %",
        hovertemplate=(
            "<b>%{y}</b><br>"
            "Margin: %{x:.1f}%<br>"
            f"Revenue: %{{customdata[0]:,.0f}}<br>"
            f"Profit: %{{customdata[1]:,.0f}}"
            "<extra></extra>"
        ),
        customdata=list(zip(grouped["revenue"], grouped["profit"])),
    ))

    # Average line
    fig.add_vline(
        x=avg_margin,
        line_dash="dash",
        line_color="rgba(255,255,255,0.3)",
        line_width=1.5,
        annotation_text=f"Avg: {avg_margin:.1f}%",
        annotation_position="top",
        annotation_font=dict(size=10, color="#94a3b8"),
    )

    best_cat   = grouped[cat_col].iloc[-1]
    best_margin = grouped["margin_pct"].iloc[-1]
    worst_cat  = grouped[cat_col].iloc[0]
    worst_margin = grouped["margin_pct"].iloc[0]

    cat_label = cat_col.replace("_", " ").title()
    _apply_base(
        fig,
        title=f"Profit Margin % by {cat_label}",
        subtitle=f"Average margin: {avg_margin:.1f}% · Green = above avg"
    )
    fig.update_layout(
        xaxis_title="Profit Margin %",
        showlegend=False,
        height=max(250, n * 52),
    )

    insight = (
        f"💰 {best_cat} is most efficient at {best_margin:.1f}% margin. "
        f"⚠️ {worst_cat} has the lowest margin at {worst_margin:.1f}%. "
        f"{'Consider restructuring or pricing in ' + worst_cat + '.' if worst_margin < avg_margin * 0.7 else ''}"
    )
    return ("Profit Margin % by Category", fig, insight)


def _revenue_vs_profit_scatter(
    df: pd.DataFrame,
    cat_col: str,
    revenue_col: str,
    profit_col: str,
) -> tuple:
    """
    Revenue vs Profit scatter by category.
    Business question: which categories are high revenue
    but low profit (need pricing fix) vs low revenue but
    high profit (hidden gems to scale up)?

    Quadrant analysis:
    Top-right: Stars (high rev, high profit) — invest more
    Top-left:  Hidden gems (low rev, high profit) — scale up
    Bottom-right: Cash drains (high rev, low profit) — fix pricing
    Bottom-left: Laggards (low rev, low profit) — consider cutting
    """
    grouped = df.groupby(cat_col).agg(
        revenue=(revenue_col, "sum"),
        profit=(profit_col, "sum")
    ).reset_index()

    grouped["margin_pct"] = (
        grouped["profit"] / grouped["revenue"] * 100
    ).round(1)

    mid_rev    = grouped["revenue"].median()
    mid_profit = grouped["profit"].median()

    # Color by quadrant
    def quad_color(row) -> str:
        if row["revenue"] >= mid_rev and row["profit"] >= mid_profit:
            return "#10b981"   # Stars — green
        elif row["revenue"] < mid_rev and row["profit"] >= mid_profit:
            return "#6366f1"   # Hidden gems — purple
        elif row["revenue"] >= mid_rev and row["profit"] < mid_profit:
            return "#f59e0b"   # Cash drains — amber
        else:
            return "#ef4444"   # Laggards — red

    colors = [quad_color(row) for _, row in grouped.iterrows()]

    fig = go.Figure(go.Scatter(
        x=grouped["revenue"],
        y=grouped["profit"],
        mode="markers+text",
        marker=dict(
            color=colors,
            size=18,
            line=dict(color="rgba(255,255,255,0.2)", width=1)
        ),
        text=grouped[cat_col],
        textposition="top center",
        textfont=dict(size=10, color=TEXT_COLOR),
        hovertemplate=(
            "<b>%{text}</b><br>"
            f"Revenue: %{{x:,.0f}}<br>"
            f"Profit: %{{y:,.0f}}<br>"
            "Margin: %{customdata:.1f}%<extra></extra>"
        ),
        customdata=grouped["margin_pct"],
    ))

    # Quadrant lines
    fig.add_vline(
        x=mid_rev,
        line_dash="dot",
        line_color="rgba(255,255,255,0.12)",
        line_width=1,
    )
    fig.add_hline(
        y=mid_profit,
        line_dash="dot",
        line_color="rgba(255,255,255,0.12)",
        line_width=1,
    )

    # Quadrant labels
    x_range = grouped["revenue"].max() - grouped["revenue"].min()
    y_range = grouped["profit"].max() - grouped["profit"].min()

    for text, x_frac, y_frac, color in [
        ("⭐ Stars", 0.75, 0.9, "#10b981"),
        ("💎 Hidden Gems", 0.05, 0.9, "#6366f1"),
        ("⚠️ Fix Pricing", 0.75, 0.05, "#f59e0b"),
        ("🔴 Laggards", 0.05, 0.05, "#ef4444"),
    ]:
        fig.add_annotation(
            x=grouped["revenue"].min() + x_frac * x_range,
            y=grouped["profit"].min() + y_frac * y_range,
            text=text,
            showarrow=False,
            font=dict(size=10, color=color),
            opacity=0.5,
        )

    rev_label = revenue_col.replace("_", " ").title()
    prf_label = profit_col.replace("_", " ").title()
    cat_label = cat_col.replace("_", " ").title()

    _apply_base(
        fig,
        title=f"Revenue vs Profit by {cat_label}",
        subtitle=(
            "🟢 Stars · 💜 Hidden Gems · "
            "🟡 Fix Pricing · 🔴 Laggards"
        )
    )
    fig.update_layout(
        xaxis_title=rev_label,
        yaxis_title=prf_label,
        height=400,
        showlegend=False,
    )

    # Find cash drain (high rev, low profit)
    drains = grouped[
        (grouped["revenue"] >= mid_rev) &
        (grouped["profit"] < mid_profit)
    ]
    drain_text = (
        f"⚠️ {', '.join(drains[cat_col].tolist())} "
        f"{'has' if len(drains)==1 else 'have'} high revenue "
        f"but below-average profit — pricing opportunity. "
        if not drains.empty else ""
    )

    stars = grouped[
        (grouped["revenue"] >= mid_rev) &
        (grouped["profit"] >= mid_profit)
    ]
    star_text = (
        f"⭐ {', '.join(stars[cat_col].tolist())} "
        f"{'is' if len(stars)==1 else 'are'} Stars — invest more here."
        if not stars.empty else ""
    )

    insight = (drain_text + star_text).strip() or (
        "Scatter shows revenue vs profit positioning by category."
    )
    return ("Revenue vs Profit (Quadrant)", fig, insight)


def _mom_growth_chart(
    df: pd.DataFrame,
    date_col: str,
    metric_col: str,
) -> tuple:
    """
    Month-over-month growth rate % bar chart.
    Business question: are we accelerating or decelerating?
    More insightful than absolute trend — shows momentum.
    Green bars = growth months, Red bars = decline months.
    """
    df2 = df.copy()
    df2[date_col] = pd.to_datetime(df2[date_col])
    monthly = (
        df2.groupby(df2[date_col].dt.to_period("M"))[metric_col]
        .sum()
        .reset_index()
    )
    monthly[date_col] = monthly[date_col].astype(str)

    if len(monthly) < 3:
        raise ValueError("Need at least 3 months for growth chart")

    # Compute MoM growth %
    monthly["growth_pct"] = monthly[metric_col].pct_change() * 100
    monthly = monthly.dropna(subset=["growth_pct"])

    if monthly.empty:
        raise ValueError("Not enough data for growth chart")

    colors = [
        "#10b981" if g >= 0 else "#ef4444"
        for g in monthly["growth_pct"]
    ]

    positive_months = (monthly["growth_pct"] >= 0).sum()
    total_months    = len(monthly)
    avg_growth      = monthly["growth_pct"].mean()

    fig = go.Figure(go.Bar(
        x=monthly[date_col],
        y=monthly["growth_pct"],
        marker_color=colors,
        marker_line_width=0,
        text=[f"{g:+.1f}%" for g in monthly["growth_pct"]],
        textposition="outside",
        textfont=dict(size=9, color=TEXT_COLOR),
        hovertemplate=(
            "<b>%{x}</b><br>"
            "Growth: %{y:+.1f}%<extra></extra>"
        ),
    ))

    # Zero line
    fig.add_hline(
        y=0,
        line_color="rgba(255,255,255,0.2)",
        line_width=1,
    )

    # Average growth line
    fig.add_hline(
        y=avg_growth,
        line_dash="dash",
        line_color="#6366f1",
        line_width=1.5,
        annotation_text=f"Avg: {avg_growth:+.1f}%",
        annotation_position="right",
        annotation_font=dict(size=10, color="#a5b4fc"),
    )

    label = metric_col.replace("_", " ").title()
    _apply_base(
        fig,
        title=f"Month-over-Month {label} Growth %",
        subtitle=(
            f"{positive_months}/{total_months} growth months · "
            f"Avg: {avg_growth:+.1f}%"
        )
    )
    fig.update_layout(
        yaxis_title="Growth %",
        xaxis_title="Month",
        showlegend=False,
        xaxis_tickangle=-30,
    )

    trend = "accelerating" if monthly["growth_pct"].iloc[-1] > avg_growth else "decelerating"
    best_month = monthly.loc[monthly["growth_pct"].idxmax(), date_col]
    best_growth = monthly["growth_pct"].max()

    insight = (
        f"📈 {positive_months} of {total_months} months showed growth. "
        f"Best month: {best_month} (+{best_growth:.1f}%). "
        f"Recent momentum is {trend} vs average."
    )
    return (f"MoM {label} Growth %", fig, insight)


def _heatmap_category_time(
    df: pd.DataFrame,
    cat_col: str,
    date_col: str,
    metric_col: str,
) -> tuple:
    """
    Heatmap: categories as rows, months as columns.
    Cell colour = metric value.
    Business question: which category is growing in which
    time period? Where are the hidden seasonal patterns?
    """
    df2 = df.copy()
    df2[date_col] = pd.to_datetime(df2[date_col])
    df2["period"]  = df2[date_col].dt.to_period("M").astype(str)

    pivot = (
        df2.groupby([cat_col, "period"])[metric_col]
        .sum()
        .unstack(fill_value=0)
    )

    if pivot.empty or pivot.shape[1] < 2:
        raise ValueError("Not enough data for heatmap")

    # Limit to last 12 months and top 10 categories
    pivot = pivot.iloc[:, -12:]
    if len(pivot) > 10:
        row_sums = pivot.sum(axis=1)
        pivot = pivot.loc[row_sums.nlargest(10).index]

    label    = metric_col.replace("_", " ").title()
    cat_label = cat_col.replace("_", " ").title()

    fig = go.Figure(go.Heatmap(
        z=pivot.values,
        x=list(pivot.columns),
        y=list(pivot.index),
        colorscale=[
            [0.0, "#0d1220"],
            [0.3, "#1e1b4b"],
            [0.6, "#4338ca"],
            [0.8, "#6366f1"],
            [1.0, "#a5b4fc"],
        ],
        hovertemplate=(
            f"{cat_label}: %{{y}}<br>"
            f"Period: %{{x}}<br>"
            f"{label}: %{{z:,.0f}}<extra></extra>"
        ),
        colorbar=dict(
            title=dict(text=label, font=dict(color=TEXT_COLOR, size=11)),
            tickfont=dict(color=TEXT_COLOR, size=10),
        ),
        text=[[f"{v:,.0f}" for v in row] for row in pivot.values],
        texttemplate="%{text}",
        textfont=dict(size=8),
    ))

    _apply_base(
        fig,
        title=f"{label} by {cat_label} Over Time",
        subtitle="Darker = lower · Brighter = higher"
    )
    fig.update_layout(
        height=max(280, len(pivot) * 45 + 80),
        xaxis_tickangle=-30,
    )

    # Find the brightest cell
    max_val = pivot.values.max()
    max_pos = np.unravel_index(
        pivot.values.argmax(), pivot.values.shape
    )
    peak_cat    = pivot.index[max_pos[0]]
    peak_period = pivot.columns[max_pos[1]]

    insight = (
        f"🔥 {peak_cat} in {peak_period} was the peak "
        f"at {max_val:,.0f}. "
        f"Look for bright columns (peak periods) and "
        f"bright rows (top categories) to find opportunities."
    )
    return (f"{label} Heatmap by {cat_label}", fig, insight)


def _treemap_chart(
    df: pd.DataFrame,
    cat_col: str,
    num_col: str,
) -> tuple:
    """
    Treemap chart — area proportional to metric value.
    Best for 50+ unique categories where bar charts
    become unreadable. Shows relative share at a glance.
    """
    grouped = (
        df.groupby(cat_col)[num_col]
        .sum()
        .reset_index()
        .sort_values(num_col, ascending=False)
        .head(30)  # Top 30 for readability
    )

    if grouped.empty:
        raise ValueError("No data for treemap")

    label = num_col.replace("_", " ").title()
    cat   = cat_col.replace("_", " ").title()
    total = grouped[num_col].sum()

    fig = go.Figure(go.Treemap(
        labels=grouped[cat_col],
        values=grouped[num_col],
        parents=[""] * len(grouped),
        texttemplate=(
            "<b>%{label}</b><br>"
            "%{value:,.0f}<br>"
            "%{percentRoot:.1%}"
        ),
        hovertemplate=(
            "<b>%{label}</b><br>"
            f"{label}: %{{value:,.0f}}<br>"
            "Share: %{percentRoot:.1%}<extra></extra>"
        ),
        marker=dict(
            colorscale=[
                [0.0, "#1e1b4b"],
                [0.3, "#4338ca"],
                [0.6, "#6366f1"],
                [1.0, "#a5b4fc"],
            ],
            showscale=False,
            line=dict(width=1, color="#0a0f1e"),
        ),
        textfont=dict(size=12, color="white"),
    ))

    top_name  = grouped[cat_col].iloc[0]
    top_val   = grouped[num_col].iloc[0]
    top_share = (top_val / total * 100) if total else 0

    _apply_base(
        fig,
        title=f"{label} Share by {cat} (Top 30)",
        subtitle=f"Area = {label} · Total: {total:,.0f}"
    )
    fig.update_layout(height=420)

    insight = (
        f"🏆 {top_name} dominates with {top_val:,.0f} "
        f"({top_share:.1f}% of total {label.lower()})."
    )
    return (f"{label} Treemap", fig, insight)


def _top10_bar_chart(
    df: pd.DataFrame,
    cat_col: str,
    num_col: str,
    n: int = 10,
) -> tuple:
    """
    Vertical bar chart showing top N categories only.
    Used when 16-50 unique categories exist — top/bottom
    would be too crowded but ranked_bar would be too tall.
    """
    grouped = (
        df.groupby(cat_col)[num_col]
        .sum()
        .reset_index()
        .sort_values(num_col, ascending=False)
        .head(n)
    )

    if grouped.empty:
        raise ValueError("No data for top N bar")

    label = num_col.replace("_", " ").title()
    cat   = cat_col.replace("_", " ").title()
    total_all = df[num_col].sum()
    total_top = grouped[num_col].sum()
    coverage  = (total_top / total_all * 100) if total_all else 0

    # Color fade from bright to dim
    n_bars = len(grouped)
    colors = [
        f"rgba(99,102,241,{1.0 - (i/n_bars)*0.5:.2f})"
        for i in range(n_bars)
    ]
    colors[0] = "#10b981"   # Top bar always green

    fig = go.Figure(go.Bar(
        x=grouped[cat_col],
        y=grouped[num_col],
        marker_color=colors,
        marker_line_width=0,
        text=[f"{v:,.0f}" for v in grouped[num_col]],
        textposition="outside",
        textfont=dict(size=9, color=TEXT_COLOR),
        hovertemplate=(
            "<b>%{x}</b><br>"
            f"{label}: %{{y:,.0f}}<extra></extra>"
        ),
    ))

    top_name = grouped[cat_col].iloc[0]
    top_val  = grouped[num_col].iloc[0]

    _apply_base(
        fig,
        title=f"Top {n} {cat} by {label}",
        subtitle=f"Covers {coverage:.0f}% of total {label.lower()}"
    )
    fig.update_layout(
        yaxis_title=label,
        xaxis_title=cat,
        showlegend=False,
        xaxis_tickangle=-30 if n_bars > 6 else 0,
    )

    insight = (
        f"🏆 {top_name} leads with {top_val:,.0f}. "
        f"Top {n} {cat.lower()}s account for "
        f"{coverage:.0f}% of total {label.lower()}."
    )
    return (f"Top {n} {cat}", fig, insight)


def generate_charts(
    df: pd.DataFrame, profile: dict
) -> list:
    """
    Generates a set of charts that each answer a DIFFERENT
    business question — like a real analyst's dashboard.

    Story told across charts:
    1. What is the top line? (revenue by category)
    2. What is most EFFICIENT? (profit margin %)
    3. Where are the hidden opportunities? (rev vs profit scatter)
    4. Are we growing? (trend over time)
    5. Are we accelerating or decelerating? (MoM growth %)
    6. Which category × time period is the opportunity? (heatmap)
    7. How is revenue distributed? (histogram)

    Never shows the same data twice in different formats.
    """
    charts = []
    nums  = profile.get("numeric_cols", [])
    cats  = profile.get("cat_cols", [])
    dates = profile.get("date_cols", [])

    # Find best columns
    best_cat    = _best_grouping_col(df, cats, max_unique=200)
    best_metric = _best_metric_col(df, nums)

    if best_cat is None:
        best_cat = _best_grouping_col(df, cats, max_unique=500)

    # Find profit column specifically
    profit_col = None
    for col in nums:
        if "profit" in col.lower() or "margin" in col.lower():
            profit_col = col
            break

    # Find revenue/sales column specifically
    revenue_col = best_metric
    for col in nums:
        cl = col.lower()
        if any(w in cl for w in ["revenue", "sales", "amount"]):
            revenue_col = col
            break

    # ── Chart 1: Revenue by Category ───────────────────────
    # Business Q: Which category makes the most money?
    if best_cat and revenue_col:
        try:
            chart_type = _decide_chart_type(df, best_cat, revenue_col)
            if chart_type == "ranked_bar":
                charts.append(_ranked_bar_chart(df, best_cat, revenue_col))
            elif chart_type == "top_bottom":
                charts.append(_top_bottom_chart(df, best_cat, revenue_col))
            elif chart_type == "top10_bar":
                charts.append(_top10_bar_chart(df, best_cat, revenue_col))
            else:
                charts.append(_treemap_chart(df, best_cat, revenue_col))
        except Exception:
            pass

    # ── Chart 2: Profit Margin % by Category ───────────────
    # Business Q: Which category is most EFFICIENT?
    # Only if both revenue AND profit columns exist
    if best_cat and revenue_col and profit_col and revenue_col != profit_col:
        try:
            charts.append(
                _profit_margin_chart(df, best_cat, revenue_col, profit_col)
            )
        except Exception:
            pass

    # ── Chart 3: Revenue vs Profit Scatter ─────────────────
    # Business Q: Stars vs Cash Drains vs Hidden Gems?
    # Only if both revenue AND profit exist and 3+ categories
    if (best_cat and revenue_col and profit_col
            and revenue_col != profit_col
            and df[best_cat].nunique() >= 3):
        try:
            charts.append(
                _revenue_vs_profit_scatter(
                    df, best_cat, revenue_col, profit_col
                )
            )
        except Exception:
            pass

    # ── Chart 4: Revenue Trend Over Time ───────────────────
    # Business Q: Are we growing overall?
    if dates and revenue_col:
        try:
            charts.append(_trend_chart(df, dates[0], revenue_col))
        except Exception:
            pass

    # ── Chart 5: Month-over-Month Growth % ─────────────────
    # Business Q: Are we accelerating or decelerating?
    # Different from chart 4 — shows rate of change not absolute
    if dates and revenue_col:
        try:
            charts.append(_mom_growth_chart(df, dates[0], revenue_col))
        except Exception:
            pass

    # ── Chart 6: Category × Time Heatmap ───────────────────
    # Business Q: Which category in which period is the opportunity?
    if best_cat and dates and revenue_col:
        try:
            charts.append(
                _heatmap_category_time(
                    df, best_cat, dates[0], revenue_col
                )
            )
        except Exception:
            pass

    # ── Chart 7: Distribution histogram ────────────────────
    # Business Q: What does the spread of transactions look like?
    if revenue_col:
        try:
            charts.append(_histogram_chart(df, revenue_col))
        except Exception:
            pass

    return charts
