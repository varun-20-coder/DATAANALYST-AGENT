"""
data_cleaning.py
-----------------
Handles file loading, automatic data cleaning, and exploratory
data analysis (EDA) helper functions for the AI Data Analyst Agent.
"""

import pandas as pd
import numpy as np
import io


def load_data(uploaded_file):
    """
    Load a CSV or Excel file (Streamlit UploadedFile object) into a DataFrame.
    """
    filename = uploaded_file.name.lower()

    if filename.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    elif filename.endswith((".xlsx", ".xls")):
        df = pd.read_excel(uploaded_file)
    else:
        raise ValueError("Unsupported file type. Please upload a CSV or Excel file.")

    return df


def auto_detect_date_columns(df):
    """
    Try to detect columns that look like dates and convert them to datetime.
    Returns the modified dataframe and a list of detected date columns.
    """
    date_cols = []
    for col in df.columns:
        if pd.api.types.is_object_dtype(df[col]) or pd.api.types.is_string_dtype(df[col]):
            sample = df[col].dropna().astype(str).head(20)
            if len(sample) == 0:
                continue
            try:
                import warnings
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    parsed = pd.to_datetime(sample, errors="coerce")
                success_rate = parsed.notna().mean()
                if success_rate > 0.8:
                    df[col] = pd.to_datetime(df[col], errors="coerce")
                    date_cols.append(col)
            except Exception:
                continue
    return df, date_cols


def clean_data(df):
    """
    Perform automatic data cleaning:
    - Strip whitespace from column names and string values
    - Drop fully empty rows/columns
    - Remove duplicate rows
    - Auto-detect and parse date columns
    - Report cleaning actions taken
    """
    report = []

    original_shape = df.shape

    # Clean column names
    df.columns = [str(c).strip() for c in df.columns]

    # Drop fully empty rows / columns
    df = df.dropna(axis=0, how="all")
    df = df.dropna(axis=1, how="all")

    # Strip whitespace in string/object columns
    obj_cols = df.select_dtypes(include=["object", "string"]).columns
    for col in obj_cols:
        df[col] = df[col].astype(str).str.strip().replace("nan", np.nan)

    # Remove duplicate rows
    dup_count = df.duplicated().sum()
    if dup_count > 0:
        df = df.drop_duplicates()
        report.append(f"Removed {dup_count} duplicate row(s).")

    # Auto-detect dates
    df, date_cols = auto_detect_date_columns(df)
    if date_cols:
        report.append(f"Auto-detected date column(s): {', '.join(date_cols)}")

    # Attempt numeric conversion on object columns that are mostly numeric
    for col in df.select_dtypes(include=["object", "string"]).columns:
        converted = pd.to_numeric(df[col], errors="coerce")
        if converted.notna().mean() > 0.9 and df[col].notna().sum() > 0:
            df[col] = converted
            report.append(f"Converted column '{col}' to numeric.")

    new_shape = df.shape
    report.insert(
        0,
        f"Original shape: {original_shape[0]} rows x {original_shape[1]} cols -> "
        f"Cleaned shape: {new_shape[0]} rows x {new_shape[1]} cols",
    )

    return df, report, date_cols


def get_summary_stats(df):
    """Return descriptive statistics for numeric and categorical columns."""
    numeric_df = df.select_dtypes(include=np.number)
    cat_df = df.select_dtypes(include=["object", "string"])

    numeric_summary = numeric_df.describe().transpose() if not numeric_df.empty else pd.DataFrame()
    cat_summary = cat_df.describe().transpose() if not cat_df.empty else pd.DataFrame()

    return numeric_summary, cat_summary


def detect_missing(df):
    """Return a DataFrame summarizing missing values per column."""
    missing = df.isna().sum()
    pct = (missing / len(df) * 100).round(2) if len(df) > 0 else missing
    result = pd.DataFrame({"missing_count": missing, "missing_pct": pct})
    result = result[result["missing_count"] > 0].sort_values("missing_count", ascending=False)
    return result


def detect_outliers_iqr(df):
    """
    Detect outliers in numeric columns using the IQR method.
    Returns a dict: {column_name: outlier_count}
    """
    outlier_report = {}
    numeric_df = df.select_dtypes(include=np.number)
    for col in numeric_df.columns:
        series = numeric_df[col].dropna()
        if len(series) < 4:
            continue
        q1, q3 = series.quantile(0.25), series.quantile(0.75)
        iqr = q3 - q1
        lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        count = ((series < lower) | (series > upper)).sum()
        if count > 0:
            outlier_report[col] = int(count)
    return outlier_report


def get_correlation(df):
    """Return the correlation matrix for numeric columns."""
    numeric_df = df.select_dtypes(include=np.number)
    if numeric_df.shape[1] < 2:
        return pd.DataFrame()
    return numeric_df.corr()


def guess_column_roles(df):
    """
    Heuristically guess which columns are likely date, categorical (region/product/etc.),
    and numeric measure columns (sales/revenue/units etc.). Useful to pre-fill chart pickers.
    """
    date_cols = list(df.select_dtypes(include="datetime64[ns]").columns)
    numeric_cols = list(df.select_dtypes(include=np.number).columns)
    categorical_cols = [c for c in df.columns if c not in date_cols and c not in numeric_cols]

    # Prioritize likely "measure" columns by common naming
    measure_keywords = ["sales", "revenue", "amount", "profit", "price", "total", "units", "qty", "quantity"]
    likely_measures = [c for c in numeric_cols if any(k in c.lower() for k in measure_keywords)]
    if not likely_measures:
        likely_measures = numeric_cols

    return {
        "date_cols": date_cols,
        "numeric_cols": numeric_cols,
        "categorical_cols": categorical_cols,
        "likely_measures": likely_measures,
    }


def dataframe_to_schema_string(df, max_sample_rows=5):
    """
    Build a compact textual schema description of the dataframe for use
    in LLM prompts (columns, dtypes, and a small sample of rows).
    """
    lines = []
    lines.append(f"Shape: {df.shape[0]} rows, {df.shape[1]} columns")
    lines.append("Columns and types:")
    for col in df.columns:
        lines.append(f"  - {col} ({df[col].dtype})")
    lines.append("\nSample rows:")
    lines.append(df.head(max_sample_rows).to_string())
    return "\n".join(lines)
