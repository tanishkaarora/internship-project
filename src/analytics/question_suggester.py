"""
Generates contextual suggested questions based on what
columns were detected in the uploaded dataset and whether
a PDF document was indexed.

No LLM needed — pure rule-based logic.
Runs instantly after every file upload.
"""

from typing import List


# Maps column name keywords → suggested question templates
# {col} gets replaced with the actual column name found
NUMERIC_TEMPLATES = {
    # Revenue / Sales
    "revenue":  [
        "Which product has the highest revenue?",
        "Show me the revenue trend over time",
        "Which category contributes most to total revenue?",
        "Are there any anomalies in revenue?",
        "What is the revenue breakdown by category?",
    ],
    "sales": [
        "Which product has the highest sales?",
        "Show me the sales trend over time",
        "Which category is underperforming in sales?",
        "What are the top 5 products by sales?",
        "Are there any anomalies in sales data?",
    ],
    "profit": [
        "Which product is most profitable?",
        "Show me the profit trend over time",
        "Which category has the lowest profit margin?",
        "What are the bottom 5 products by profit?",
        "Are there unusual spikes or drops in profit?",
    ],
    "units": [
        "Which product sells the most units?",
        "Show me the units sold trend",
        "Which category moves the highest volume?",
        "What products have the lowest units sold?",
        "Are there anomalies in units sold?",
    ],
    "quantity": [
        "Which product has the highest quantity sold?",
        "Show me quantity sold over time",
        "Which items have critically low quantities?",
        "What is the quantity distribution?",
    ],
    "price": [
        "What is the average price across products?",
        "Which product has the highest price?",
        "Show me the price distribution",
        "Are there any pricing anomalies?",
    ],
    "cost": [
        "Which product has the highest cost?",
        "Show me cost trends over time",
        "Which category has the highest cost?",
        "Are there anomalies in costs?",
    ],
    "inventory": [
        "Which products are low on inventory?",
        "Show me inventory levels by category",
        "Which items need immediate restocking?",
        "Are there any inventory anomalies?",
    ],
    "discount": [
        "Which products have the highest discount?",
        "What is the average discount across categories?",
        "Show me discount trends over time",
    ],
    "orders": [
        "How many orders per category?",
        "Show me order trends over time",
        "Which product has the most orders?",
    ],
}

CATEGORICAL_TEMPLATES = {
    "category": [
        "Which category is performing best?",
        "Which category is underperforming?",
        "Compare revenue across all categories",
    ],
    "product": [
        "What are the top 5 products?",
        "What are the bottom 5 products?",
        "Which product should we prioritise?",
    ],
    "region": [
        "Which region has the highest sales?",
        "Which region is underperforming?",
        "Compare performance across regions",
    ],
    "store": [
        "Which store has the highest revenue?",
        "Which store needs attention?",
        "Compare performance across stores",
    ],
    "customer": [
        "Who are the top customers by revenue?",
        "Which customer segment is most valuable?",
        "Show customer distribution by category",
    ],
    "segment": [
        "Which customer segment drives most revenue?",
        "Compare segments by profitability",
    ],
    "channel": [
        "Which sales channel performs best?",
        "Compare online vs offline channels",
    ],
    "brand": [
        "Which brand has the highest sales?",
        "Compare brand performance",
    ],
}

DATE_TEMPLATES = [
    "Show me the trend over time",
    "What month had the highest sales?",
    "Is there a seasonal pattern in the data?",
    "Show month-over-month growth rate",
    "What was the best performing period?",
]

DOCUMENT_TEMPLATES = [
    "Summarise the uploaded document",
    "What are the key findings in the report?",
    "What risks are mentioned in the document?",
    "What recommendations does the report make?",
    "What does the document say about strategy?",
]

GENERAL_FALLBACK = [
    "Give me an overview of this dataset",
    "What are the most important insights?",
    "What should I focus on first?",
    "Are there any problems I should know about?",
    "What does this data tell me about my business?",
]


def _match_col(col_name: str, templates: dict) -> List[str]:
    """
    Check if any keyword from templates matches the column name.
    Returns list of matched question strings, or empty list.
    """
    col_lower = col_name.lower()
    for keyword, questions in templates.items():
        if keyword in col_lower:
            return questions
    return []


def generate_suggestions(
    profile: dict,
    has_pdf: bool = False,
    max_questions: int = 6,
) -> List[dict]:
    """
    Generate contextual suggested questions from a data profile.

    Args:
        profile:       Output of DataIngester._profile() — contains
                       numeric_cols, cat_cols, date_cols lists.
        has_pdf:       Whether a PDF document has been indexed.
        max_questions: Maximum number of suggestions to return.

    Returns:
        List of dicts: {
            "question": str,   — the question text
            "icon":     str,   — emoji prefix
            "route":    str,   — expected route (for display hint)
        }
    """
    suggestions = []
    seen = set()  # prevent duplicates

    def add(question: str, icon: str, route: str):
        if question not in seen and len(suggestions) < max_questions:
            seen.add(question)
            suggestions.append({
                "question": question,
                "icon": icon,
                "route": route,
            })

    numeric_cols = profile.get("numeric_cols", [])
    cat_cols     = profile.get("cat_cols", [])
    date_cols    = profile.get("date_cols", [])

    # Priority 1: numeric column questions (most useful for retail)
    for col in numeric_cols[:2]:
        matched = _match_col(col, NUMERIC_TEMPLATES)
        if matched:
            # Add top 2 from matched templates
            for q in matched[:2]:
                add(q, "📊", "analytics")
        else:
            # Generic numeric question using actual column name
            label = col.replace("_", " ").title()
            add(f"Which product has the highest {label}?", "📊", "analytics")
            add(f"Show me {label} trends over time", "📈", "analytics")

    # Priority 2: categorical questions
    for col in cat_cols[:1]:
        matched = _match_col(col, CATEGORICAL_TEMPLATES)
        if matched:
            add(matched[0], "🏆", "analytics")
        else:
            label = col.replace("_", " ").title()
            add(f"Which {label} is performing best?", "🏆", "analytics")
            add(f"Which {label} is underperforming?", "⚠️", "analytics")

    # Priority 3: time trend question (if date column exists)
    if date_cols:
        add(DATE_TEMPLATES[0], "📈", "analytics")
        if len(suggestions) < max_questions:
            add(DATE_TEMPLATES[3], "📅", "analytics")

    # Priority 4: anomaly question (always useful)
    if numeric_cols:
        label = numeric_cols[0].replace("_", " ").title()
        add(f"Are there any anomalies in {label}?", "⚠️", "analytics")

    # Priority 5: document question (if PDF uploaded)
    if has_pdf:
        add(DOCUMENT_TEMPLATES[0], "📄", "rag")
        add(DOCUMENT_TEMPLATES[2], "📄", "rag")

    # Fill remaining slots with general fallbacks
    for q in GENERAL_FALLBACK:
        if len(suggestions) >= max_questions:
            break
        add(q, "💡", "analytics")

    return suggestions[:max_questions]
