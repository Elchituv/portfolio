# Coffee Cart Conversion — Did a Cheerful Sign Sell More Coffee?

> A before/after experiment on a campus coffee cart: measure whether a friendlier sign converted more passers-by into buyers, and what that is worth in dollars.

![Python](https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white)
![pandas](https://img.shields.io/badge/pandas-150458?logo=pandas&logoColor=white)
![statsmodels](https://img.shields.io/badge/statsmodels-4051B5)
![Source](https://img.shields.io/badge/XP%20Lab-challenge%20%C2%B7%20Easy-6A1B9A)

---

## The business question

Rita runs a coffee cart on South Quad every morning, 07:00–10:00. Every 10 minutes two numbers are logged: how many people walked past, and how many of them ordered.

For two weeks the cart had a plain sign. For the next two weeks it had a cheerful one ("Cheerful Sign +Smile").

**Question:** did the new sign make a larger share of passers-by buy coffee — and is it worth keeping?

**Why not just compare sales?** If more people simply walked by in weeks 3–4, sales would rise regardless of the sign. So the core metric is the **conversion rate**:

```
conversion rate = orders ÷ passers-by
```

## Answer in one line

**Keep the cheerful sign.** Conversion rose from **19.3% to 29.7%** (+10.5 percentage points, +54% relative, p < 0.001), worth roughly **21 extra cups and ~$42 a day**.

---

## Data

**Grain: one row = one morning × one 10-minute slot.** 18 slots a day × 28 days = **504 rows**.

| Period | Sign | From | To | Days |
|---|---|---|---|---|
| A | Plain Sign | 2025-02-10 | 2025-02-23 | 14 |
| B | Cheerful Sign (+Smile) | 2025-02-24 | 2025-03-09 | 14 |

| Column | Description |
|---|---|
| `id` | Row ID |
| `date_of_sales` | Date of the morning |
| `ts_start` | Start of the 10-minute slot (stored as text) |
| `weekday` | Day of week |
| `passers` | People who walked past in that slot |
| `orders` | People who ordered |

Derived columns: `slot` (time of day, e.g. `07:10`), `hour` (7/8/9), `sign` (assigned from the date).

---

## Solution process

### 1. Parse types first
Timestamps arrived as **text** (`"2025-02-10T07:00:00.000Z"`). Text compares alphabetically, not chronologically, so everything is converted to real datetimes before any other step.

### 2. De-duplicate on the true grain — *the bug I fixed*
A reading is unique by **day + slot**. My first submission de-duplicated on the time column alone. Because `07:10` appears once per day (28 times), pandas treated 27 of them as duplicates and **silently collapsed 504 rows to 18** — no error, just a one-day analysis.

| | De-duplication key | Result |
|---|---|---|
| v1 (wrong) | `ts_start` only | 504 → 18 rows |
| v2 (correct) | `date_of_sales` + `slot` | all 504 rows kept |

v2 also adds a **guard-rail**: if a "cleaning" step removes more than 10% of the data, the script stops — that is almost always a bug, not dirty data.

### 3. Prove the periods are comparable
Seven pass/fail checks run before any comparison: no missing values, `orders ≤ passers` in every row, 18 readings per day, equal days per period, identical weekday mix, no missing calendar days, and footfall within 20% between periods.

### 4. Conversion rate and significance
- Conversion is computed on **totals** (Σ orders ÷ Σ passers), not as an average of 504 small rates — otherwise a slot with 2 passers-by would weigh as much as one with 32.
- **Two-proportion z-test:** *if the sign had no effect, how often would chance alone create a gap this big?*
- **95% confidence interval:** the p-value says *whether* there is an effect; the interval says *how big*, which is what a decision needs.

### 5. Translate to money and operations
- Absolute lift in **percentage points** vs. relative lift in **percent**.
- Extra cups/day = average daily footfall × absolute lift; extra revenue = cups × $2. The confidence interval is carried through, so revenue is a **range**, not false precision.
- Operational check: can one person handle the extra demand? (≈ 1 extra cup per 10-minute slot.)

### 6. Is the lift consistent through the morning?
An overall average can hide an uneven effect. v2 compares every 10-minute slot across the two periods, and formally tests the **three opening hours** (~900 passers-by each) with a **Bonferroni correction** (5% ÷ 3) instead of running 18 thin, noisy tests.

### 7. Day-level robustness
Daily conversion rates for each period are compared with a one-sided **Mann-Whitney U test** (no normality assumption, suitable for 14 values per group), to confirm the whole distribution of days shifted — not one unusual day.

### 8. Visuals
Daily conversion over time (with the switch date marked), conversion by time of day, lift per slot (negative slots in red), and the spread of daily rates.

---

## Results

| Metric | Plain sign | Cheerful sign |
|---|---|---|
| Conversion rate | **19.25%** | **29.74%** |
| Orders / passers-by | 521 / 2,706 | 850 / 2,858 |

| Impact | Value |
|---|---|
| Absolute lift | **+10.5 percentage points** |
| Relative lift | **+54%** |
| 95% CI on the lift | +8.2 to +12.7 pp |
| z-statistic / p-value | 9.07 / ≈ 1.2 × 10⁻¹⁹ |
| Extra cups per day | ≈ 21 |
| Extra revenue per day | ≈ $42 (95% CI $33–$51) |
| Extra revenue per 30 trading days | ≈ $1,250 |

**Decision:** keep the cheerful sign. Footfall was similar in both periods (2,706 vs. 2,858), so the gain comes from conversion, not from a bigger crowd.

---

## Limitations

- **Before/after, not randomised.** Anything else that changed in those weeks (weather, campus events) could contribute. The comparability checks reduce this risk but can't remove it.
- **Two weeks per period.** It can't tell whether the effect lasts or is a novelty effect that fades once the sign becomes familiar.

## Feedback & iteration

The challenge was reviewed after submission. The review confirmed the conclusion and praised the ratio-of-sums method and the business translation, and flagged three things — all addressed in v2 (`coffee_sign_analysis.py`):

| Review point | v2 change |
|---|---|
| De-duplication key wiped most of the data | Key changed to day + slot, plus a 10% guard-rail |
| No check that the lift holds across the morning | Per-slot comparison + per-hour tests with Bonferroni |
| No explicit validation that periods are comparable | Seven automated pass/fail checks |

---

## How to run

```bash
pip install pandas numpy matplotlib seaborn scipy statsmodels
```

The original dataset belongs to XP Lab and is not included. Either:

- **Real data:** export it once from the XP Lab notebook with `df_coffee_sales.to_csv("coffee_sales.csv", index=False)` and place it next to the script, or
- **Demo data:** run `python make_demo_csv.py` to create clearly-labelled synthetic data.

```bash
python coffee_sign_analysis.py
```

The script prints every table and saves the four charts to `coffee_sign_charts.png`. Each `# %%` block can also be pasted into a notebook cell.

## Files

| File | Description |
|---|---|
| `coffee_sign_analysis.py` | Full corrected analysis (v2) |
| `make_demo_csv.py` | Generates synthetic data to test-run the script |

**Tools:** Python · pandas · NumPy · SciPy · statsmodels · matplotlib · seaborn

**Challenge:** [XP Lab](https://www.xp-lab.com) — "Coffee Cart Conversion"

[← Back to Data Analyst](../README.md) · [Portfolio home](../../README.md)
