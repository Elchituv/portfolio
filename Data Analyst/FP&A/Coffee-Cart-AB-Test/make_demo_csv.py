"""
Generate SYNTHETIC demo data so coffee_sign_analysis.py can be run without the
original XP Lab dataset (which is not redistributed in this repo).

The numbers are made up. They only reproduce the table's shape:
28 days x 18 ten-minute slots = 504 rows, plain sign for 14 days, then the
cheerful sign for 14 days.

Run:  python make_demo_csv.py   ->  writes coffee_sales_DEMO.csv
"""

from pathlib import Path

import numpy as np
import pandas as pd

rng = np.random.default_rng(42)
HERE = Path(__file__).parent

rows = []
row_id = 1
for day in pd.date_range("2025-02-10", "2025-03-09", freq="D"):
    cheerful = day >= pd.Timestamp("2025-02-24")
    base_rate = 0.29 if cheerful else 0.19          # invented conversion rates
    for slot in range(18):                          # 07:00 .. 09:50
        ts = day + pd.Timedelta(hours=7, minutes=10 * slot)
        passers = int(rng.poisson(11))
        orders = int(rng.binomial(passers, base_rate))
        rows.append({
            "id": row_id,
            "ts_start": ts.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
            "date_of_sales": day.strftime("%Y-%m-%dT00:00:00.000Z"),
            "weekday": day.day_name(),
            "passers": passers,
            "orders": orders,
        })
        row_id += 1

out = HERE / "coffee_sales_DEMO.csv"
pd.DataFrame(rows).to_csv(out, index=False)
print(f"Wrote {len(rows)} synthetic rows to {out}")
