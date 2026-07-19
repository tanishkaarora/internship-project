import sys
sys.path.insert(0, ".")
from src.analytics.question_suggester import generate_suggestions


def make_profile(numeric=None, cat=None, dates=None):
    return {
        "numeric_cols": numeric or [],
        "cat_cols":     cat or [],
        "date_cols":    dates or [],
    }


def test_revenue_col_generates_revenue_questions():
    profile = make_profile(numeric=["revenue"], cat=["category"])
    suggestions = generate_suggestions(profile)
    questions = [s["question"] for s in suggestions]
    assert any("revenue" in q.lower() for q in questions), (
        "Expected revenue-related question"
    )
    print("test_revenue_col_generates_revenue_questions passed!")


def test_date_col_generates_trend_question():
    profile = make_profile(numeric=["sales"], dates=["order_date"])
    suggestions = generate_suggestions(profile)
    questions = [s["question"] for s in suggestions]
    assert any("trend" in q.lower() or "time" in q.lower() for q in questions), (
        "Expected a trend/time question"
    )
    print("test_date_col_generates_trend_question passed!")


def test_pdf_adds_document_questions():
    profile = make_profile(numeric=["revenue"])
    suggestions_no_pdf  = generate_suggestions(profile, has_pdf=False)
    suggestions_with_pdf = generate_suggestions(profile, has_pdf=True)
    routes_no_pdf   = [s["route"] for s in suggestions_no_pdf]
    routes_with_pdf = [s["route"] for s in suggestions_with_pdf]
    assert "rag" not in routes_no_pdf,   "No RAG questions without PDF"
    assert "rag" in routes_with_pdf,      "RAG questions added with PDF"
    print("test_pdf_adds_document_questions passed!")


def test_max_questions_respected():
    profile = make_profile(
        numeric=["revenue", "profit", "units"],
        cat=["category", "product", "region"],
        dates=["date"]
    )
    suggestions = generate_suggestions(profile, max_questions=4)
    assert len(suggestions) <= 4, f"Expected max 4, got {len(suggestions)}"
    print("test_max_questions_respected passed!")


def test_empty_profile_returns_fallback():
    profile = make_profile()
    suggestions = generate_suggestions(profile)
    assert len(suggestions) > 0, "Should return fallback questions"
    assert all(s["icon"] for s in suggestions), "All should have icons"
    print("test_empty_profile_returns_fallback passed!")


def test_no_duplicate_questions():
    profile = make_profile(
        numeric=["revenue", "revenue_ytd"],
        cat=["category"],
        dates=["order_date"]
    )
    suggestions = generate_suggestions(profile)
    questions = [s["question"] for s in suggestions]
    assert len(questions) == len(set(questions)), "Duplicate questions found"
    print("test_no_duplicate_questions passed!")


def test_all_suggestions_have_required_keys():
    profile = make_profile(numeric=["sales"], cat=["product"])
    suggestions = generate_suggestions(profile)
    for s in suggestions:
        assert "question" in s
        assert "icon" in s
        assert "route" in s
    print("test_all_suggestions_have_required_keys passed!")


if __name__ == "__main__":
    test_revenue_col_generates_revenue_questions()
    test_date_col_generates_trend_question()
    test_pdf_adds_document_questions()
    test_max_questions_respected()
    test_empty_profile_returns_fallback()
    test_no_duplicate_questions()
    test_all_suggestions_have_required_keys()
    print()
    print("All 7 question suggester tests passed!")
