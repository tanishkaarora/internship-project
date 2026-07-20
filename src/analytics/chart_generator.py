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
    Horizontal bar chart showing top 5 and bottom 5 side by side.
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

    top5    = grouped.head(5)
    bottom5 = grouped.tail(5).sort_values(num_col, ascending=True)

    label = num_col.replace("_", " ").title()
    cat   = cat_col.replace("_", " ").title()

    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=[
            f"<b>Top 5</b> by {label}",
            f"<b>Bottom 5</b> by {label}"
        ],
        horizontal_spacing=0.12
    )

    fig.add_trace(go.Bar(
        y=top5[cat_col], x=top5[num_col],
        orientation="h",
        marker_color=PALETTE[2],
        marker_line_width=0,
        text=[f"{v:,.0f}" for v in top5[num_col]],
        textposition="outside",
        textfont=dict(size=10),
        hovertemplate="<b>%{y}</b><br>Value: %{x:,.0f}<extra></extra>",
        showlegend=False,
    ), row=1, col=1)

    fig.add_trace(go.Bar(
        y=bottom5[cat_col], x=bottom5[num_col],
        orientation="h",
        marker_color=PALETTE[4],
        marker_line_width=0,
        text=[f"{v:,.0f}" for v in bottom5[num_col]],
        textposition="outside",
        textfont=dict(size=10),
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

    top_name    = top5[cat_col].iloc[0]
    bottom_name = bottom5[cat_col].iloc[0]
    gap = top5[num_col].iloc[0] - bottom5[num_col].iloc[0]

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
            title="r",
            tickfont=dict(color=TEXT_COLOR),
            titlefont=dict(color=TEXT_COLOR)
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


def generate_charts(
    df: pd.DataFrame, profile: dict
) -> list:
    """
    Returns list of (title, plotly_figure, insight_text).
    Each chart uses meaningful grouping dimensions only.
    One failed chart never kills the rest.
    """
    charts = []
    nums  = profile.get("numeric_cols", [])
    cats  = profile.get("cat_cols", [])
    dates = profile.get("date_cols", [])

    # Find the best grouping column and best metric column
    # These are used across multiple charts for consistency
    best_cat    = _best_grouping_col(df, cats, max_unique=50)
    best_metric = _best_metric_col(df, nums)

    # Fallback: if no good grouping col with max 50,
    # try up to 100 unique values
    if best_cat is None:
        best_cat = _best_grouping_col(df, cats, max_unique=100)

    # Find second-best grouping col (different from best_cat)
    remaining_cats = [c for c in cats if c != best_cat]
    second_cat = _best_grouping_col(
        df, remaining_cats, max_unique=50
    )

    # Find second metric
    remaining_nums = [c for c in nums if c != best_metric]
    second_metric = _best_metric_col(df, remaining_nums)

    # ── Chart 1: Top vs Bottom Performers ──────────────────
    # Uses best_cat × best_metric
    if best_cat and best_metric:
        try:
            charts.append(
                _top_bottom_chart(df, best_cat, best_metric)
            )
        except Exception:
            try:
                charts.append(
                    _bar_chart(df, best_cat, best_metric)
                )
            except Exception:
                pass

    # ── Chart 2: Trend over time ────────────────────────────
    if dates and best_metric:
        try:
            charts.append(
                _trend_chart(df, dates[0], best_metric)
            )
        except Exception:
            pass

    # ── Chart 3: Donut / share chart ───────────────────────
    if best_cat and best_metric:
        try:
            charts.append(
                _category_pie(df, best_cat, best_metric)
            )
        except Exception:
            pass

    # ── Chart 4: Second metric bar chart ───────────────────
    # e.g. profit by category (after sales by category)
    if best_cat and second_metric:
        try:
            charts.append(
                _bar_chart(df, best_cat, second_metric)
            )
        except Exception:
            pass

    # ── Chart 5: Distribution histogram ────────────────────
    if best_metric:
        try:
            charts.append(_histogram_chart(df, best_metric))
        except Exception:
            pass

    # ── Chart 6: Second grouping dimension chart ────────────
    # e.g. sales by region (after sales by category)
    if second_cat and best_metric:
        try:
            charts.append(
                _bar_chart(df, second_cat, best_metric)
            )
        except Exception:
            pass

    # ── Chart 7: Correlation heatmap ───────────────────────
    if len(nums) >= 3:
        try:
            charts.append(
                _correlation_heatmap(df, nums[:6])
            )
        except Exception:
            pass

    return charts
