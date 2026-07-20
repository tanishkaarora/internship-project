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

        # Filter out non-metric columns to populate _filtered_id_cols if not already set
        if not hasattr(self, "_filtered_id_cols"):
            all_numeric = df.select_dtypes(include="number").columns.tolist()
            def is_non_metric(col_name: str) -> bool:
                """
                Returns True only for columns that are pure technical
                identifiers with zero analytical value.

                EXCLUDED (true IDs — sequential numbers, no meaning):
                  row_id, order_id, customer_id, product_id,
                  transaction_id, record_id, index, row_number

                KEPT (location — useful for geographic analysis):
                  postal_code, zip_code, pin_code, city, state,
                  region, country, lat, lon

                KEPT (all other numerics):
                  sales, revenue, profit, quantity, price, discount,
                  rating, score, age, year, etc.
                """
                col_lower = col_name.lower()

                # --- Explicit KEEP list — never exclude these ---
                # Location columns are valuable for geo analysis
                ALWAYS_KEEP = [
                    "postal", "zip", "pin", "postcode",
                    "city", "state", "region", "country",
                    "district", "province", "territory",
                    "latitude", "longitude", "lat", "lon",
                    "location", "address", "area", "zone",
                    "store", "branch", "outlet", "warehouse",
                ]
                if any(kw in col_lower for kw in ALWAYS_KEEP):
                    return False  # Keep this column

                # --- True ID columns — exclude these ---
                # These are sequential row numbers or surrogate keys
                # with no analytical meaning
                TRUE_ID_PATTERNS = [
                    # Exact matches
                    "id", "index", "idx", "key",
                    "row_id", "row_number", "rowid",
                    "record_id", "record_number",
                    "serial", "seq", "sequence",
                    "uuid", "guid", "hash",
                    # Suffix patterns: order_id, customer_id, etc.
                ]

                # Check exact column name matches
                if col_lower in TRUE_ID_PATTERNS:
                    return True

                # Check if column name ENDS with _id or _key
                # This catches order_id, customer_id, product_id
                # but NOT city, state, region
                if col_lower.endswith("_id") or col_lower.endswith("_key"):
                    return True

                # Check if column name IS just "id" or starts with "id_"
                if col_lower == "id" or col_lower.startswith("id_"):
                    return True

                # Check for phone/fax numbers — numeric but not metrics
                CONTACT_PATTERNS = ["phone", "mobile", "fax", "tel",
                                    "contact", "whatsapp"]
                if any(kw in col_lower for kw in CONTACT_PATTERNS):
                    return True

                # Last resort: if EVERY value in the column is unique
                # AND the column name contains "number" or "no" or "num"
                # it is probably a reference number
                NUMBER_SUFFIXES = ["_number", "_no", "_num", "_ref",
                                   "_code" ]
                # But only if it also looks like a sequential ID
                # (all unique values that are integers)
                if any(col_lower.endswith(s) for s in NUMBER_SUFFIXES):
                    try:
                        # Check if values look like sequential integers
                        col_vals = df[col_name].dropna()
                        is_int_like = (col_vals == col_vals.astype(int)).all()
                        all_unique  = col_vals.nunique() == len(col_vals)
                        min_val     = col_vals.min()
                        max_val     = col_vals.max()
                        # Sequential: min is ~1 and max equals row count
                        looks_sequential = (
                            min_val <= 10 and
                            abs(max_val - len(df)) < len(df) * 0.1
                        )
                        if is_int_like and all_unique and looks_sequential:
                            return True
                    except Exception:
                        pass

                return False  # Keep everything else by default

            kept_numeric = [col for col in all_numeric if not is_non_metric(col)]
            if not kept_numeric and all_numeric:
                kept_numeric = all_numeric
            self._filtered_id_cols = [c for c in all_numeric if c not in kept_numeric]

        # Log filtered columns at debug level only —
        # users do not need to see this
        import logging
        filtered = getattr(self, "_filtered_id_cols", [])
        if filtered:
            logging.getLogger(__name__).debug(
                "Filtered non-metric columns: %s", filtered
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
        # Get all numeric columns
        all_numeric = df.select_dtypes(include="number").columns.tolist()

        # Filter out ID, code, and reference columns that are
        # numeric but not business metrics.
        # These columns contain identifiers, not measurable quantities.
        NON_METRIC_KEYWORDS = [
            "id", "code", "zip", "postal", "pin",
            "phone", "mobile", "fax", "index",
            "row", "number", "no", "num", "ref",
            "key", "hash", "lat", "lon", "latitude",
            "longitude", "year_of_birth", "dob",
        ]

        def is_non_metric(col_name: str) -> bool:
            """
            Returns True only for columns that are pure technical
            identifiers with zero analytical value.

            EXCLUDED (true IDs — sequential numbers, no meaning):
              row_id, order_id, customer_id, product_id,
              transaction_id, record_id, index, row_number

            KEPT (location — useful for geographic analysis):
              postal_code, zip_code, pin_code, city, state,
              region, country, lat, lon

            KEPT (all other numerics):
              sales, revenue, profit, quantity, price, discount,
              rating, score, age, year, etc.
            """
            col_lower = col_name.lower()

            # --- Explicit KEEP list — never exclude these ---
            # Location columns are valuable for geo analysis
            ALWAYS_KEEP = [
                "postal", "zip", "pin", "postcode",
                "city", "state", "region", "country",
                "district", "province", "territory",
                "latitude", "longitude", "lat", "lon",
                "location", "address", "area", "zone",
                "store", "branch", "outlet", "warehouse",
            ]
            if any(kw in col_lower for kw in ALWAYS_KEEP):
                return False  # Keep this column

            # --- True ID columns — exclude these ---
            # These are sequential row numbers or surrogate keys
            # with no analytical meaning
            TRUE_ID_PATTERNS = [
                # Exact matches
                "id", "index", "idx", "key",
                "row_id", "row_number", "rowid",
                "record_id", "record_number",
                "serial", "seq", "sequence",
                "uuid", "guid", "hash",
                # Suffix patterns: order_id, customer_id, etc.
            ]

            # Check exact column name matches
            if col_lower in TRUE_ID_PATTERNS:
                return True

            # Check if column name ENDS with _id or _key
            # This catches order_id, customer_id, product_id
            # but NOT city, state, region
            if col_lower.endswith("_id") or col_lower.endswith("_key"):
                return True

            # Check if column name IS just "id" or starts with "id_"
            if col_lower == "id" or col_lower.startswith("id_"):
                return True

            # Check for phone/fax numbers — numeric but not metrics
            CONTACT_PATTERNS = ["phone", "mobile", "fax", "tel",
                                "contact", "whatsapp"]
            if any(kw in col_lower for kw in CONTACT_PATTERNS):
                return True

            # Last resort: if EVERY value in the column is unique
            # AND the column name contains "number" or "no" or "num"
            # it is probably a reference number
            NUMBER_SUFFIXES = ["_number", "_no", "_num", "_ref",
                               "_code" ]
            # But only if it also looks like a sequential ID
            # (all unique values that are integers)
            if any(col_lower.endswith(s) for s in NUMBER_SUFFIXES):
                try:
                    # Check if values look like sequential integers
                    col_vals = df[col_name].dropna()
                    is_int_like = (col_vals == col_vals.astype(int)).all()
                    all_unique  = col_vals.nunique() == len(col_vals)
                    min_val     = col_vals.min()
                    max_val     = col_vals.max()
                    # Sequential: min is ~1 and max equals row count
                    looks_sequential = (
                        min_val <= 10 and
                        abs(max_val - len(df)) < len(df) * 0.1
                    )
                    if is_int_like and all_unique and looks_sequential:
                        return True
                except Exception:
                    pass

            return False  # Keep everything else by default

        numeric_cols = [
            col for col in all_numeric
            if not is_non_metric(col)
        ]

        # If filtering removed ALL numeric columns,
        # fall back to original list with a warning
        if not numeric_cols and all_numeric:
            numeric_cols = all_numeric
            # Will be caught by _validate() and shown to user

        filtered_out = [
            c for c in all_numeric if c not in numeric_cols
        ]
        # Store for profile warnings
        self._filtered_id_cols = filtered_out

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
            "filtered_id_cols": getattr(self, "_filtered_id_cols", []),
        }
