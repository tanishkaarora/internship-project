import pandas as pd
import io
from src.analytics.data_ingester import DataIngester

def make_csv_file():
    csv_content = "Product Name,Sales Amount,Date\nWidget A,$1200,2024-01-01\nWidget B,$800,2024-02-01"
    return io.BytesIO(csv_content.encode()), "test.csv"

class MockFile:
    def __init__(self, content, name):
        self._content = content
        self.name = name
    def read(self, *args, **kwargs):
        return self._content.read(*args, **kwargs)
    def seek(self, pos):
        return self._content.seek(pos)

def test_ingester_loads_csv():
    content, name = make_csv_file()
    mock = MockFile(content, name)
    ingester = DataIngester()
    df, profile = ingester.ingest(mock)
    assert len(df) == 2
    assert "product_name" in df.columns  # lowercased

def test_ingester_converts_currency():
    content, name = make_csv_file()
    mock = MockFile(content, name)
    ingester = DataIngester()
    df, _ = ingester.ingest(mock)
    assert df["sales_amount"].dtype in ["float64", "int64"]

def test_profile_has_expected_keys():
    content, name = make_csv_file()
    mock = MockFile(content, name)
    ingester = DataIngester()
    _, profile = ingester.ingest(mock)
    assert "summary_text" in profile
    assert "numeric_cols" in profile

def test_ingester_rejects_empty_csv():
    """Empty CSV (headers only, no data rows) should raise ValueError."""
    csv_content = "Product Name,Sales Amount,Date\n"
    mock = MockFile(io.BytesIO(csv_content.encode()), "empty.csv")
    ingester = DataIngester()
    try:
        ingester.ingest(mock)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "no data rows" in str(e).lower()
        print("test_ingester_rejects_empty_csv passed!")

def test_ingester_warns_no_numeric_cols():
    """CSV with no numeric columns should return a warning, not crash."""
    csv_content = "Name,Category,Region\nAlice,Electronics,North\nBob,Clothing,South"
    mock = MockFile(io.BytesIO(csv_content.encode()), "text_only.csv")
    ingester = DataIngester()
    df, profile = ingester.ingest(mock)
    assert len(df) == 2
    assert any("numeric" in w.lower() for w in profile.get("warnings", []))
    print("test_ingester_warns_no_numeric_cols passed!")
