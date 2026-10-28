from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = ROOT / "data" / "sales_raw.csv"
SEED = 42
N_ORDERS = 1800


def generate_sales_data(n_orders: int = N_ORDERS, seed: int = SEED) -> pd.DataFrame:
    """Create deterministic, fictional retail line items with known data issues."""
    rng = np.random.default_rng(seed)
    dates = pd.Timestamp("2023-01-01") + pd.to_timedelta(
        rng.integers(0, 1096, size=n_orders), unit="D"
    )
    regions = np.array(["West", "East", "Central", "South"])
    categories = np.array(["Technology", "Furniture", "Office Supplies"])
    subcategories = {
        "Technology": ["Phones", "Computers", "Accessories"],
        "Furniture": ["Chairs", "Tables", "Bookcases"],
        "Office Supplies": ["Binders", "Paper", "Storage"],
    }
    category = rng.choice(categories, size=n_orders, p=[0.28, 0.24, 0.48])
    region = rng.choice(regions, size=n_orders, p=[0.31, 0.24, 0.27, 0.18])
    month = pd.DatetimeIndex(dates).month.to_numpy()
    seasonal = 1 + 0.16 * np.sin(2 * np.pi * (month - 1) / 12) + 0.28 * np.isin(month, [11, 12])
    base_price = np.select(
        [category == "Technology", category == "Furniture"],
        [rng.lognormal(4.25, 0.65, n_orders), rng.lognormal(4.0, 0.55, n_orders)],
        default=rng.lognormal(2.8, 0.50, n_orders),
    )
    quantity = rng.integers(1, 9, size=n_orders)
    discount = np.clip(rng.beta(1.5, 8, size=n_orders), 0, 0.65)
    sales = base_price * quantity * (1 - discount) * seasonal
    margin = np.select(
        [category == "Technology", category == "Furniture"],
        [rng.normal(0.17, 0.09, n_orders), rng.normal(0.11, 0.12, n_orders)],
        default=rng.normal(0.22, 0.08, n_orders),
    )
    profit = sales * margin
    # Two large, plausible bulk orders create high-end statistical outliers.
    for idx, multiplier in [(17, 16), (951, 20)]:
        if idx < n_orders:
            sales[idx] *= multiplier
            profit[idx] *= multiplier
            quantity[idx] *= 8
    rows = pd.DataFrame({
        "order_id": [f"ORD-{i+1:05d}" for i in range(n_orders)],
        "order_date": pd.to_datetime(dates).strftime("%Y-%m-%d"),
        "region": region,
        "state": rng.choice(["CA", "NY", "TX", "IL", "FL", "WA", "MA", "GA"], n_orders),
        "customer_segment": rng.choice(["Consumer", "Corporate", "Home Office"], n_orders, p=[0.52, 0.30, 0.18]),
        "category": category,
        "subcategory": [rng.choice(subcategories[c]) for c in category],
        "product_id": [f"SKU-{x:04d}" for x in rng.integers(1, 251, size=n_orders)],
        "units": quantity,
        "sales": np.round(sales, 2),
        "discount": np.round(discount, 3),
        "profit": np.round(profit, 2),
    })
    # Deliberately introduce documented quality defects in the raw source.
    dupes = rows.sample(frac=0.015, random_state=seed)
    rows = pd.concat([rows, dupes], ignore_index=True)
    for col, frac in [("order_date", .012), ("region", .008), ("category", .008), ("sales", .015), ("profit", .012), ("units", .01)]:
        ids = rng.choice(rows.index, size=max(1, int(len(rows) * frac)), replace=False)
        rows.loc[ids, col] = np.nan
    bad_dates = rng.choice(rows.index, 9, replace=False)
    rows.loc[bad_dates, "order_date"] = "not-a-date"
    bad_units = rng.choice(rows.index.difference(bad_dates), 8, replace=False)
    rows["units"] = rows["units"].astype(object)
    rows.loc[bad_units, "units"] = "unknown"
    invalid_sales = rng.choice(rows.index.difference(bad_units), 6, replace=False)
    rows.loc[invalid_sales, "sales"] = -abs(pd.to_numeric(rows.loc[invalid_sales, "sales"], errors="coerce"))
    return rows


if __name__ == "__main__":
    RAW_PATH.parent.mkdir(parents=True, exist_ok=True)
    generate_sales_data().to_csv(RAW_PATH, index=False)
    print(f"Wrote {RAW_PATH}")


