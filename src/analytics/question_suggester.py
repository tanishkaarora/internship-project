"""
Generates contextual suggested questions from a data profile.
Only generates questions that are logically meaningful —
never asks about IDs, codes, or nonsensical column combos.
"""

from typing import List, Optional


# ── Column classification helpers ────────────────────────────────────────────

# Columns that should NEVER be used as a grouping dimension
# in suggested questions (they are IDs or reference numbers)
NON_GROUPING_KEYWORDS = [
    "id", "key", "uuid", "guid", "hash",
    "index", "idx", "row", "serial", "seq",
    "number", "ref", "code", "num", "no",
    "phone", "mobile", "fax", "email",
    "order_id", "customer_id", "product_id",
    "transaction_id", "record_id",
    "customer_name", "customer name", "client_name", "client name",
    "postal_code", "postal", "zip", "zip_code", "postcode", "pincode",
]

# Columns that ARE good grouping dimensions
GOOD_GROUPING_KEYWORDS = [
    "category", "sub_category", "subcategory",
    "product", "item", "sku", "brand",
    "region", "state", "city", "country", "zone",
    "postal", "zip", "postcode", "district",
    "store", "branch", "outlet", "channel",
    "segment", "customer_type", "customer_segment",
    "department", "dept",
    "salesperson", "rep", "agent", "manager",
    "month", "quarter", "year", "week",
    "status", "type", "class", "grade",
]

# Columns that ARE good numeric metrics
GOOD_METRIC_KEYWORDS = [
    "sales", "revenue", "profit", "amount", "income",
    "quantity", "units", "qty", "orders", "count",
    "discount", "margin", "cost", "price", "rate",
    "spend", "budget", "gmv", "aov", "clv",
    "score", "rating", "nps", "satisfaction",
    "actual", "predicted", "forecast", "target",
    "error", "accuracy", "variance",
    "inventory", "stock", "reorder",
    "visits", "clicks", "impressions", "conversions",
]

# Location columns — get geographic question templates
LOCATION_KEYWORDS = [
    "postal", "zip", "postcode", "pincode",
    "city", "state", "region", "country",
    "district", "province", "territory", "zone",
    "area", "location",
]


def _is_good_grouping(col: str) -> bool:
    """
    Returns True if this column is a meaningful grouping
    dimension for analytics questions.
    Rejects ID columns, reference numbers, pure codes.
    """
    col_lower = col.lower()

    # Explicit reject: ends with _id or _key
    if col_lower.endswith("_id") or col_lower.endswith("_key"):
        return False

    # Explicit reject: is exactly "id" or "index"
    if col_lower in ("id", "index", "idx", "key", "row", "no"):
        return False

    # Explicit reject: ends with name (except product/item name)
    if col_lower == "name" or col_lower.endswith("_name") or col_lower.endswith(" name"):
        if "product" not in col_lower and "item" not in col_lower:
            return False

    # Explicit reject: contains non-grouping keywords
    for kw in NON_GROUPING_KEYWORDS:
        if col_lower == kw:
            return False

    # Explicit accept: matches known good grouping column
    for kw in GOOD_GROUPING_KEYWORDS:
        if kw in col_lower:
            return True

    # Explicit accept: location columns
    for kw in LOCATION_KEYWORDS:
        if kw in col_lower:
            return True

    # Default: allow — better to include than exclude
    return True


def _is_good_metric(col: str) -> bool:
    """
    Returns True if this column is a meaningful numeric metric.
    """
    col_lower = col.lower()

    # Reject IDs even if numeric
    if col_lower.endswith("_id") or col_lower == "id":
        return False

    # Accept known metric keywords
    for kw in GOOD_METRIC_KEYWORDS:
        if kw in col_lower:
            return True

    # Default: allow (unknown columns may still be metrics)
    return True


def _is_location(col: str) -> bool:
    col_lower = col.lower()
    return any(kw in col_lower for kw in LOCATION_KEYWORDS)


def _col_label(col: str) -> str:
    """Human-readable column label."""
    return col.replace("_", " ").title()


# ── Question templates ───────────────────────────────────────────────────────

def _questions_for_grouping_x_metric(
    group_col: str,
    metric_col: str,
    is_location_col: bool = False,
) -> list:
    g = _col_label(group_col)
    m = _col_label(metric_col)

    if is_location_col:
        return [
            f"Which {g} drives the most {m}?",
            f"Which {g} is underperforming — where should we focus?",
        ]

    # Business-analyst style questions per metric type
    m_lower = metric_col.lower()

    if any(w in m_lower for w in ["profit", "margin"]):
        return [
            f"Which {g} is most profitable?",
            f"Which {g} has the lowest profit — should we cut it?",
        ]
    elif any(w in m_lower for w in ["sales", "revenue", "amount", "income"]):
        return [
            f"Which {g} drives the most revenue?",
            f"Which {g} is underperforming in sales?",
        ]
    elif any(w in m_lower for w in ["quantity", "units", "qty", "volume"]):
        return [
            f"Which {g} sells the most units?",
            f"Which {g} has the lowest volume?",
        ]
    elif any(w in m_lower for w in ["discount"]):
        return [
            f"Which {g} gets the highest discounts?",
            f"Is discounting hurting profit in any {g}?",
        ]
    elif any(w in m_lower for w in ["cost", "spend", "expense"]):
        return [
            f"Which {g} has the highest cost?",
            f"Where can we reduce costs?",
        ]
    elif any(w in m_lower for w in ["error", "variance", "accuracy"]):
        return [
            f"Which {g} has the highest forecast error?",
            f"Which {g} is hardest to predict?",
        ]
    else:
        return [
            f"Which {g} has the highest {m}?",
            f"Which {g} is underperforming?",
        ]


def _trend_question(metric_col: str) -> str:
    m = _col_label(metric_col)
    return f"Show me {m} trend over time"


def _anomaly_question(metric_col: str) -> str:
    m = _col_label(metric_col)
    return f"Are there any anomalies in {m}?"


def _summary_question() -> str:
    return "Summarise the data"


def _overview_question() -> str:
    return "What are the key insights?"


# ── Main entry point ─────────────────────────────────────────────────────────

def generate_suggestions(
    profile: dict,
    has_pdf: bool = False,
    max_questions: int = 6,
) -> List[dict]:
    """
    Generate contextual suggested questions from a data profile.

    Rules:
    - Only use columns that are good grouping dimensions
    - Only use columns that are meaningful metrics
    - Never suggest "which order_id has highest sales"
    - Location columns get geographic question phrasing
    - Prioritise the most business-relevant column pairs
    - No duplicate questions
    """
    suggestions = []
    seen = set()

    def add(question: str, icon: str, route: str):
        if question not in seen and len(suggestions) < max_questions:
            seen.add(question)
            suggestions.append({
                "question": question,
                "icon": icon,
                "route": route,
            })

    all_numeric = profile.get("numeric_cols", [])
    all_cat     = profile.get("cat_cols", [])
    date_cols   = profile.get("date_cols", [])

    # Filter numeric cols to only genuine business metrics
    # Remove location codes, IDs, reference numbers
    NON_METRIC_KW = [
        "postal", "zip", "pin", "postcode",
        "phone", "mobile", "fax", "lat", "lon",
        "latitude", "longitude", "id", "key",
        "index", "row", "code", "number",
        "no", "num", "ref", "serial",
    ]

    def _col_is_metric(col: str) -> bool:
        col_lower = col.lower()
        for kw in NON_METRIC_KW:
            if (col_lower == kw
                    or col_lower.endswith("_" + kw)
                    or col_lower.startswith(kw + "_")):
                return False
        return True

    # Only use genuine metrics for question generation
    good_metrics_all = [
        c for c in all_numeric if _col_is_metric(c)
    ]

    # Filter to only meaningful columns
    good_metrics  = good_metrics_all
    good_grouping = [c for c in all_cat if _is_good_grouping(c)]

    # Separate location columns from non-location categoricals
    location_cols    = [c for c in good_grouping if _is_location(c)]
    non_location_cols = [
        c for c in good_grouping if not _is_location(c)
    ]

    # ── Priority 1: non-location grouping × primary metric ──
    # e.g. "Which category has highest sales?"
    if not good_metrics:
        # Fallback to first numeric if all were filtered
        good_metrics = all_numeric[:1]
    primary_metric = good_metrics[0] if good_metrics else None

    for cat in non_location_cols[:2]:
        if primary_metric:
            qs = _questions_for_grouping_x_metric(
                cat, primary_metric, is_location_col=False
            )
            for q in qs[:1]:  # 1 per categorical column
                add(q, "📊", "analytics")

    # ── Priority 2: second metric with first grouping ──
    # e.g. "Which category has highest profit?"
    if len(good_metrics) >= 2 and non_location_cols:
        secondary_metric = good_metrics[1]
        best_cat = non_location_cols[0]
        q = f"Which {_col_label(best_cat)} has the highest {_col_label(secondary_metric)}?"
        add(q, "📊", "analytics")

    # ── Priority 3: location questions ──
    # e.g. "Which region has highest sales?"
    for loc in location_cols[:2]:
        if primary_metric:
            q = f"Which {_col_label(loc)} has the highest {_col_label(primary_metric)}?"
            add(q, "🗺️", "analytics")

    # ── Priority 4: trend question ──
    if date_cols and primary_metric:
        m_lower = primary_metric.lower()
        if any(w in m_lower for w in ["sales", "revenue"]):
            add("How has revenue trended — growing or declining?",
                "📈", "analytics")
        elif "profit" in m_lower:
            add("Is profitability improving over time?",
                "📈", "analytics")
        elif "quantity" in m_lower or "units" in m_lower:
            add("Are we selling more or fewer units over time?",
                "📈", "analytics")
        else:
            m = _col_label(primary_metric)
            add(f"Show me {m} trend over time", "📈", "analytics")

    # ── Priority 5: underperforming ──
    if non_location_cols and primary_metric:
        best_cat = non_location_cols[0]
        m_lower = primary_metric.lower()
        if any(w in m_lower for w in
               ["sales", "revenue", "amount"]):
            q = "Which category is dragging down overall revenue?"
        elif "profit" in m_lower:
            q = "Which category should we consider cutting or restructuring?"
        elif "quantity" in m_lower or "units" in m_lower:
            q = "Which products are not moving — slow sellers?"
        else:
            g = _col_label(best_cat)
            m = _col_label(primary_metric)
            q = f"Which {g} needs immediate attention?"
        add(q, "⚠️", "analytics")

    # ── Priority 6: anomaly ──
    if primary_metric:
        m_lower = primary_metric.lower()
        if any(w in m_lower for w in ["sales", "revenue"]):
            add("Are there any unusual sales spikes or drops?",
                "🔍", "analytics")
        elif "profit" in m_lower:
            add("Are there products losing money unexpectedly?",
                "🔍", "analytics")
        else:
            m = _col_label(primary_metric)
            add(f"Are there any anomalies in {m}?",
                "🔍", "analytics")

    # ── Priority 7: document question if PDF uploaded ──
    if has_pdf:
        add("Summarise the uploaded document", "📄", "rag")
        add("What are the key findings in the report?", "📄", "rag")

    # ── Fill remaining slots with general questions ──
    FALLBACK = [
        ("What is the single biggest opportunity in this data?",
         "💡", "analytics"),
        ("Where should I focus to improve profitability?",
         "💡", "analytics"),
        ("What does this data tell me about my business?",
         "💡", "analytics"),
    ]
    for q, icon, route in FALLBACK:
        add(q, icon, route)

    return suggestions[:max_questions]
