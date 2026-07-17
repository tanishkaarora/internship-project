import pytest
from src.analytics.column_detective import SmartColumnDetective

class MockLLMResponse:
    def __init__(self, content: str):
        self.content = content

class MockLLM:
    def __init__(self, response_json_str: str):
        self.response_json_str = response_json_str
        self.calls = []

    def invoke(self, prompt: str):
        self.calls.append(prompt)
        return MockLLMResponse(self.response_json_str)

def test_detective_rule_based_exact_match():
    # Setup simple profile
    profile = {
        "numeric_cols": ["sales_amount", "profit_margin"],
        "cat_cols": ["product_name", "store_region"],
        "date_cols": ["transaction_date"]
    }
    
    # We do NOT pass an LLM, testing only the rule-based fast path
    detective = SmartColumnDetective(llm=None)
    
    # Test case 1: Query clearly mentions "sales_amount" and "product_name"
    res1 = detective.detect("Show sales_amount for product_name", profile)
    assert res1["numeric_col"] == "sales_amount"
    assert res1["categorical_col"] == "product_name"
    assert res1["date_col"] == "transaction_date"  # fallback

    # Test case 2: Query mentions synonym "profit" and "region"
    res2 = detective.detect("Is there profit in each region?", profile)
    assert res2["numeric_col"] == "profit_margin"
    assert res2["categorical_col"] == "store_region"

def test_detective_llm_based_match():
    # Setup simple profile
    profile = {
        "numeric_cols": ["sales_amount", "profit_margin"],
        "cat_cols": ["product_name", "store_region"],
        "date_cols": ["transaction_date"]
    }
    
    # Mock LLM to return a JSON string
    mock_response = '{"numeric_col": "profit_margin", "categorical_col": "store_region", "date_col": "transaction_date"}'
    llm = MockLLM(mock_response)
    
    detective = SmartColumnDetective(llm=llm)
    res = detective.detect("Give me regional margins", profile)
    
    assert res["numeric_col"] == "profit_margin"
    assert res["categorical_col"] == "store_region"
    assert res["date_col"] == "transaction_date"
    assert len(llm.calls) == 1

def test_detective_llm_fallback_on_invalid_column():
    # Setup simple profile
    profile = {
        "numeric_cols": ["sales_amount"],
        "cat_cols": ["product_name"],
        "date_cols": ["transaction_date"]
    }
    
    # Mock LLM returns a column that does not exist in schema
    mock_response = '{"numeric_col": "invalid_column_name", "categorical_col": "product_name", "date_col": ""}'
    llm = MockLLM(mock_response)
    
    detective = SmartColumnDetective(llm=llm)
    res = detective.detect("Get sales_amount", profile)
    
    # Should fall back to the default numeric column since LLM returned an invalid one
    assert res["numeric_col"] == "sales_amount"
    assert res["categorical_col"] == "product_name"
