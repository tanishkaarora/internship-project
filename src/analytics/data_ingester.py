"""CSV and Excel ingestion with cleaning for business data"""

import pandas as pd
from typing import Tuple

class DataIngester:
    """Loads, cleans, and profiles business CSV/Excel files"""

    def ingest(self, uploaded_file) -> Tuple[pd.DataFrame, dict]:
        """
        Main entry: takes Streamlit UploadedFile → returns (clean_df, profile)
        """
        raw_df = self._load(uploaded_file)
        clean_df = self._clean(raw_df)
        warnings = self._validate(clean_df)
        profile = self._profile(clean_df)
        profile["warnings"] = warnings
        return clean_df, profile

    def _load(self, uploaded_file) -> pd.DataFrame:
        name = uploaded_file.name.lower()
        if name.endswith(".csv"):
            for enc in ["utf-8", "latin-1", "cp1252"]:
                try:
                    return pd.read_csv(uploaded_file, encoding=enc)
                except UnicodeDecodeError:
                    uploaded_file.seek(0)
            raise ValueError("Cannot decode CSV. Try saving as UTF-8.")
        elif name.endswith((".xlsx", ".xls")):
            try:
                uploaded_file.seek(0)
                engine = "openpyxl" if name.endswith(".xlsx") else None
                return pd.read_excel(uploaded_file, engine=engine)
            except Exception as e:
                # Fallback 1: Install xlrd if missing for legacy .xls files
                if "xlrd" in str(e).lower() or "install xlrd" in str(e).lower():
                    try:
                        import subprocess
                        import sys
                        subprocess.check_call([sys.executable, "-m", "pip", "install", "xlrd"])
                        uploaded_file.seek(0)
                        return pd.read_excel(uploaded_file, engine="xlrd")
                    except Exception:
                        pass

                # Fallback 2: Read as comma-separated text
                try:
                    uploaded_file.seek(0)
                    return pd.read_csv(uploaded_file)
                except Exception:
                    pass

                # Fallback 3: Read as tab-separated text
                try:
                    uploaded_file.seek(0)
                    return pd.read_csv(uploaded_file, sep="\t")
                except Exception:
                    pass

                raise ValueError(f"Failed to read Excel file. If it is a legacy XLS file, please save it as XLSX or CSV. Detail: {e}")
        else:
            raise ValueError(f"Unsupported file type: {name}")

    def _clean(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        # Standardise column names
        df.columns = [c.lower().strip().replace(" ", "_").replace("-", "_")
                      for c in df.columns]
        # Strip whitespace from strings
        for col in df.select_dtypes(include="object").columns:
            df[col] = df[col].astype(str).str.strip()
        # Auto-convert date columns
        for col in df.columns:
            if any(k in col for k in ["date", "time", "month", "year"]):
                try:
                    df[col] = pd.to_datetime(df[col])
                except Exception:
                    pass
        # Convert currency strings to numeric
        for col in df.select_dtypes(include="object").columns:
            cleaned = df[col].str.replace(r"[$,£€%]", "", regex=True).str.strip()
            try:
                df[col] = pd.to_numeric(cleaned)
            except Exception:
                pass
        # Fill numeric nulls with median
        for col in df.select_dtypes(include="number").columns:
            df[col] = df[col].fillna(df[col].median())
        # Remove full duplicates
        df.drop_duplicates(inplace=True)
        return df

    def _validate(self, df: pd.DataFrame) -> list:
        """
        Validates the cleaned DataFrame is usable for analytics.
        Returns a list of warning strings (empty = all good).
        Raises ValueError for fatal problems that prevent any analysis.
        """
        warnings = []

        # Fatal: too few rows
        if len(df) == 0:
            raise ValueError(
                "The uploaded file has no data rows. "
                "Please check the file and try again."
            )

        if len(df) < 3:
            warnings.append(
                f"Very small dataset ({len(df)} rows). "
                "Trends and rankings may not be meaningful."
            )

        # Fatal: no columns at all
        if len(df.columns) == 0:
            raise ValueError(
                "No columns found after cleaning. "
                "Please check the file format."
            )

        # Warning: no numeric columns
        numeric_cols = df.select_dtypes(include="number").columns.tolist()
        if len(numeric_cols) == 0:
            warnings.append(
                "No numeric columns detected after cleaning. "
                "Analytics (KPIs, trends, rankings) will not be available. "
                "If your data has numbers, check that values do not contain "
                "unrecognised currency symbols or text."
            )

        # Warning: all numeric columns are constant (no variance)
        for col in numeric_cols:
            if df[col].nunique() == 1:
                warnings.append(
                    f"Column '{col}' has only one unique value "
                    f"({df[col].iloc[0]}) — rankings will not be meaningful."
                )

        # Warning: no categorical columns
        cat_cols = df.select_dtypes(include="object").columns.tolist()
        if len(cat_cols) == 0:
            warnings.append(
                "No categorical columns detected. "
                "Group-by analysis (by product, category, region) "
                "will not be available."
            )

        # Warning: very high null rate in numeric columns
        for col in numeric_cols:
            null_pct = df[col].isnull().sum() / len(df) * 100
            if null_pct > 30:
                warnings.append(
                    f"Column '{col}' has {null_pct:.0f}% missing values "
                    "after cleaning. Results may be unreliable."
                )

        return warnings

    def _profile(self, df: pd.DataFrame) -> dict:
        """Generate a text summary of the data for use in LLM prompts"""
        numeric_cols = df.select_dtypes(include="number").columns.tolist()
        cat_cols = df.select_dtypes(include="object").columns.tolist()
        date_cols = df.select_dtypes(include="datetime").columns.tolist()

        summary_parts = [
            f"Dataset: {len(df):,} rows, {len(df.columns)} columns.",
            f"Columns: {', '.join(df.columns.tolist())}.",
        ]
        for col in numeric_cols[:4]:
            summary_parts.append(
                f"{col}: min={df[col].min():.2f}, max={df[col].max():.2f}, "
                f"mean={df[col].mean():.2f}, sum={df[col].sum():.2f}."
            )
        for col in cat_cols[:3]:
            top = df[col].value_counts().index[:3].tolist()
            summary_parts.append(
                f"{col}: {df[col].nunique()} unique values. Top: {', '.join(str(v) for v in top)}."
            )
        if date_cols:
            col = date_cols[0]
            summary_parts.append(
                f"Date range ({col}): {df[col].min()} to {df[col].max()}."
            )

        return {
            "summary_text": " ".join(summary_parts),
            "numeric_cols": numeric_cols,
            "cat_cols": cat_cols,
            "date_cols": date_cols,
            "row_count": len(df),
            "col_count": len(df.columns),
        }
