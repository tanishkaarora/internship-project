import sys
import os

# Add current folder to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from tests.test_data_ingester import (
        test_ingester_loads_csv,
        test_ingester_converts_currency,
        test_profile_has_expected_keys
    )
    from tests.test_column_detective import (
        test_detective_rule_based_exact_match,
        test_detective_llm_based_match,
        test_detective_llm_fallback_on_invalid_column
    )
    from tests.test_question_suggester import (
        test_revenue_col_generates_revenue_questions,
        test_date_col_generates_trend_question,
        test_pdf_adds_document_questions,
        test_max_questions_respected,
        test_empty_profile_returns_fallback,
        test_no_duplicate_questions,
        test_all_suggestions_have_required_keys,
    )
    
    print("Running test_ingester_loads_csv...")
    test_ingester_loads_csv()
    print("test_ingester_loads_csv passed!")

    print("Running test_ingester_converts_currency...")
    test_ingester_converts_currency()
    print("test_ingester_converts_currency passed!")

    print("Running test_profile_has_expected_keys...")
    test_profile_has_expected_keys()
    print("test_profile_has_expected_keys passed!")

    print("Running test_detective_rule_based_exact_match...")
    test_detective_rule_based_exact_match()
    print("test_detective_rule_based_exact_match passed!")

    print("Running test_detective_llm_based_match...")
    test_detective_llm_based_match()
    print("test_detective_llm_based_match passed!")

    print("Running test_detective_llm_fallback_on_invalid_column...")
    test_detective_llm_fallback_on_invalid_column()
    print("test_detective_llm_fallback_on_invalid_column passed!")
    
    print("\nRunning question suggester tests...")
    test_revenue_col_generates_revenue_questions()
    test_date_col_generates_trend_question()
    test_pdf_adds_document_questions()
    test_max_questions_respected()
    test_empty_profile_returns_fallback()
    test_no_duplicate_questions()
    test_all_suggestions_have_required_keys()
    print("All question suggester tests passed!")
    
    print("\nAll tests passed successfully!")
except Exception as e:
    import traceback
    print(f"Test failed with error: {e}")
    traceback.print_exc()
    sys.exit(1)

