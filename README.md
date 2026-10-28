# Sales Data Analysis — CodeNova Data Science Task 1

A reproducible exploratory analysis of fictional retail sales, including core financial metrics, monthly/quarterly/seasonal trends, product category and regional breakdowns, reconciliation checks, and stakeholder recommendations.

> **Synthetic data:** the assignment brief supplied no sales dataset. All records are deterministic fictional data generated locally with seed 42. Results are examples only, not real business findings.

## Deliverables

- `notebooks/sales_data_analysis.ipynb` — completed notebook with executed outputs and written interpretation.
- `figures/` — five scalable, high-resolution SVG exports.
- `data/sales_raw.csv` and `data/sales_clean.csv` — synthetic source and analysis-ready data.
- `src/` — reproducible data generation, cleaning, and chart-export scripts.

## Executive summary

Cleaned records total **$351,401.19 sales**, **$56,986.38 profit**, **16.2% weighted profit margin**, **$198.20 average line-item value**, and **8,113 units**. Technology contributes **$179,569.90 (51.1%)** of revenue. Office Supplies has the highest category margin (**22.4%**), while Furniture has the lowest (**11.2%**). West leads regional sales at **$115,081.67 (32.7%)**. Category, region, and monthly revenue totals each reconcile to overall revenue.

### Recommendations

1. Protect Technology availability and review product-level contribution because it drives about half of simulated revenue.
2. Test whether Office Supplies can scale while preserving its higher margin.
3. Compare regional product mix and discounting before changing inventory allocation.
4. Treat seasonal patterns as illustrative; the generator intentionally adds seasonal variation. Validate on complete real history before planning.

## Run locally

From the repository root, with Python 3.10+:

```bash
python -m pip install -r requirements.txt
python src/generate_sales_data.py
python src/clean_data.py
python src/make_charts.py
jupyter notebook notebooks/sales_data_analysis.ipynb
```

The notebook expects the repository root as the working directory. `data/sales_raw.csv` is never modified by the cleaning script.

## Limitations

This is simulated data, not a description of a real retailer. The analysis is descriptive and does not establish causes. Some cleaning choices, particularly median/mode imputation, reduce variability; see the separate **Data Cleaning** repository for the full audit and empirical before/after profile.
