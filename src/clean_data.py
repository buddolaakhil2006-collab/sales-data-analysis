from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "sales_raw.csv"
CLEAN = ROOT / "data" / "sales_clean.csv"
REPORT = ROOT / "reports" / "task2_data_quality_audit.md"
PROFILE = ROOT / "reports" / "before_after_profile.csv"
NUMERIC = ["units", "sales", "discount", "profit"]
RATES = ["discount"]
CATEGORICAL = ["region", "state", "customer_segment", "category", "subcategory", "product_id"]


def profile(df: pd.DataFrame, stage: str) -> pd.DataFrame:
    numeric = df.select_dtypes(include="number")
    return pd.DataFrame({
        "stage": [stage],
        "rows": [len(df)],
        "columns": [df.shape[1]],
        "missing_cells": [int(df.isna().sum().sum())],
        "duplicate_rows": [int(df.duplicated().sum())],
        "numeric_columns_with_nulls": [int(numeric.isna().any().sum())],
        "dtypes": ["; ".join(f"{c}={t}" for c, t in df.dtypes.astype(str).items())],
        "mean_sales": [float(numeric["sales"].mean()) if "sales" in numeric else np.nan],
        "median_sales": [float(numeric["sales"].median()) if "sales" in numeric else np.nan],
    })


def clean_sales_data(df: pd.DataFrame) -> tuple[pd.DataFrame, dict, pd.DataFrame]:
    original_rows = len(df)
    exact_duplicates = int(df.duplicated().sum())
    work = df.drop_duplicates().copy()
    before = profile(df, "before")
    date_parse_failures = int((work["order_date"].notna() & pd.to_datetime(work["order_date"], errors="coerce").isna()).sum())
    numeric_parse_failures = {col: int((work[col].notna() & pd.to_numeric(work[col], errors="coerce").isna()).sum()) for col in NUMERIC}
    work["order_date"] = pd.to_datetime(work["order_date"], errors="coerce")
    for col in NUMERIC:
        work[col] = pd.to_numeric(work[col], errors="coerce")
    # Impossible business values are treated as invalid observations, then imputed.
    invalid_units = int((work["units"] <= 0).sum())
    invalid_sales = int((work["sales"] < 0).sum())
    invalid_discount = int(((work["discount"] < 0) | (work["discount"] > 1)).sum())
    work.loc[work["units"] <= 0, "units"] = np.nan
    work.loc[work["sales"] < 0, "sales"] = np.nan
    work.loc[(work["discount"] < 0) | (work["discount"] > 1), "discount"] = np.nan
    # Date cannot be responsibly imputed because it determines time aggregation.
    invalid_or_missing_dates = int(work["order_date"].isna().sum())
    work = work.loc[work["order_date"].notna()].copy()
    numeric_imputations = {}
    for col in NUMERIC:
        missing = int(work[col].isna().sum())
        if missing:
            median = float(work[col].median())
            work[col] = work[col].fillna(median)
            numeric_imputations[col] = {"count": missing, "value": round(median, 4)}
    categorical_imputations = {}
    for col in CATEGORICAL:
        work[col] = work[col].astype("string").str.strip()
        work[col] = work[col].replace("", pd.NA)
        missing = int(work[col].isna().sum())
        if missing:
            mode = str(work[col].mode(dropna=True).iloc[0])
            work[col] = work[col].fillna(mode)
            categorical_imputations[col] = {"count": missing, "value": mode}
    work["units"] = work["units"].round().astype("int64")
    work["order_date"] = pd.to_datetime(work["order_date"])
    # IQR flags are diagnostic only. Keep high-value bulk orders: they are plausible,
    # and winsorizing financial totals would silently understate sales and profit.
    outlier_flags = {}
    for col in ["units", "sales", "profit"]:
        q1, q3 = work[col].quantile([.25, .75])
        iqr = q3 - q1
        lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        outlier_flags[col] = {"count": int(((work[col] < lo) | (work[col] > hi)).sum()), "lower": float(lo), "upper": float(hi)}
    after = profile(work, "after")
    profiles = pd.concat([before, after], ignore_index=True)
    details = {
        "input_rows": original_rows,
        "exact_duplicates_removed": exact_duplicates,
        "invalid_or_missing_dates_dropped": invalid_or_missing_dates,
        "date_parse_failures": date_parse_failures,
        "numeric_parse_failures": numeric_parse_failures,
        "invalid_units_set_missing": invalid_units,
        "invalid_sales_set_missing": invalid_sales,
        "invalid_discount_set_missing": invalid_discount,
        "numeric_imputations": numeric_imputations,
        "categorical_imputations": categorical_imputations,
        "iqr_outliers_retained": outlier_flags,
        "output_rows": len(work),
        "remaining_missing_cells": int(work.isna().sum().sum()),
        "remaining_duplicates": int(work.duplicated().sum()),
    }
    return work, details, profiles


def write_audit(details: dict, profiles: pd.DataFrame) -> None:
    p = profiles.set_index("stage")
    text = f'''# Task 2 — Data Cleaning Audit\n\n## Dataset and reproducibility\n\nThis report covers a deterministic, fictional retail line-item dataset generated by `src/generate_sales_data.py` (seed 42). It is synthetic, not company or customer data. The original `data/sales_raw.csv` is retained unchanged. Run `python src/generate_sales_data.py` to recreate it, then `python src/clean_data.py` to produce the clean output and this report.\n\n## Before and after\n\n| Measure | Before | After |\n|---|---:|---:|\n| Rows | {int(p.loc['before','rows']):,} | {int(p.loc['after','rows']):,} |\n| Columns | {int(p.loc['before','columns'])} | {int(p.loc['after','columns'])} |\n| Missing cells | {int(p.loc['before','missing_cells']):,} | {int(p.loc['after','missing_cells']):,} |\n| Exact duplicate rows | {int(p.loc['before','duplicate_rows']):,} | {int(p.loc['after','duplicate_rows']):,} |\n| Mean sales | ${p.loc['before','mean_sales']:,.2f} | ${p.loc['after','mean_sales']:,.2f} |\n| Median sales | ${p.loc['before','median_sales']:,.2f} | ${p.loc['after','median_sales']:,.2f} |\n\nDetailed machine-readable comparison: `reports/before_after_profile.csv`.\n\n## Transformations and rationale\n\n- Removed **{details['exact_duplicates_removed']} exact duplicate rows**. Exact duplicate records repeat the same line item and would double-count sales.\n- Parsed `order_date` as a date and numeric fields as numbers with coercion. Coercion detected **{details['date_parse_failures']} invalid non-empty date strings** and numeric parse issues `{details['numeric_parse_failures']}`; before/after dtype summaries are in `reports/before_after_profile.csv`. Invalid or missing dates (**{details['invalid_or_missing_dates_dropped']}**) were dropped because an invented date would misstate monthly trends.\n- Set impossible values to missing: non-positive units (**{details['invalid_units_set_missing']}**), negative sales (**{details['invalid_sales_set_missing']}**), and discounts outside 0–1 (**{details['invalid_discount_set_missing']}**).\n- Imputed missing numeric metrics with their post-deduplication median and missing categorical labels with the most common observed label. This retains most records while limiting the impact of skew. Imputation counts and values: `{details['numeric_imputations']}` and `{details['categorical_imputations']}`.\n- Used the 1.5×IQR rule to flag potential outliers in units, sales, and profit. Counts and cutoffs: `{details['iqr_outliers_retained']}`. Flagged high sales/profit values were retained because large orders are plausible and clipping would distort financial totals. Review flags with source context before excluding any record.\n\n## Quality result\n\nThe cleaned output has **{details['output_rows']:,} rows**, **{details['remaining_missing_cells']} missing cells**, and **{details['remaining_duplicates']} duplicate rows**.\n\n## Limitations\n\nThe data are simulated; quality improvements demonstrate a reproducible procedure, not a claim about real sales. Median and mode imputations reduce data loss but can shrink variability. In a production setting, invalid rows should be reconciled with source systems and domain owners, and financial outliers should be reviewed individually.\n'''
    REPORT.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    data = pd.read_csv(RAW)
    cleaned, details, profiles = clean_sales_data(data)
    CLEAN.parent.mkdir(parents=True, exist_ok=True)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    cleaned.to_csv(CLEAN, index=False, date_format="%Y-%m-%d")
    profiles.to_csv(PROFILE, index=False)
    write_audit(details, profiles)
    print(f"Cleaned {details['input_rows']} raw rows -> {details['output_rows']} rows")
    print(f"Missing cells: {details['remaining_missing_cells']}; duplicate rows: {details['remaining_duplicates']}")
