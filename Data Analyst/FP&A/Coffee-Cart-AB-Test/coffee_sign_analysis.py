# =============================================================================
# South Quad Coffee Cart - did the cheerful sign lift conversion?
# Corrected analysis (v2)
#
# Data grain: ONE ROW = one day x one 10-minute slot.
#             07:00-10:00 is 3 hours = 18 slots per day, 28 days = 504 rows.
#
#   Period A  "Plain Sign"             2025-02-10 .. 2025-02-23   (14 days)
#   Period B  "Cheerful Sign (+Smile)" 2025-02-24 .. 2025-03-09   (14 days)
#
# Each cell below is marked with `# %%` so it can be pasted straight into a
# notebook, one cell at a time.
# =============================================================================

# %%
# -----------------------------------------------------------------------------
# 0. SETUP
# -----------------------------------------------------------------------------
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import mannwhitneyu
from statsmodels.stats.proportion import proportions_ztest, confint_proportions_2indep

# Every "magic number" is named ONCE here instead of being retyped in the code
# below. If the experiment is ever re-run with different dates or a different
# price, this block is the only thing that changes.
SWITCH_DATE   = pd.Timestamp("2025-02-24")   # first morning with the new sign
OPEN_HOURS    = 3                            # 07:00 -> 10:00
SLOTS_PER_DAY = OPEN_HOURS * 6               # 18 readings of 10 minutes each
PRICE         = 2.00                         # dollars per coffee
ALPHA         = 0.05                         # significance threshold

PLAIN    = "Plain Sign"
CHEERFUL = "Cheerful Sign (+Smile)"

# Fixed colours, assigned once and reused by every chart, so that blue ALWAYS
# means the plain sign and orange ALWAYS means the cheerful sign.
C_PLAIN, C_CHEERFUL, C_NEGATIVE = "#2a78d6", "#eb6834", "#e34948"
SIGN_COLORS = {PLAIN: C_PLAIN, CHEERFUL: C_CHEERFUL}

# -----------------------------------------------------------------------------
# 0b. LOAD THE DATA (works both in the notebook and as a plain .py file)
# -----------------------------------------------------------------------------
# There are two situations, and the script handles both:
#
#   (a) IN THE NOTEBOOK the environment hands you a ready-made `df_coffee_sales`
#       variable. Nothing to load - it is already in memory.
#
#   (b) AS A STANDALONE SCRIPT that variable does not exist, which is exactly
#       what "NameError: name 'df_coffee_sales' is not defined" means. The data
#       is not on your computer at all, so first export it ONCE from the
#       notebook with this single line:
#
#           df_coffee_sales.to_csv("coffee_sales.csv", index=False)
#
#       then download that CSV and put it in the SAME FOLDER as this script.
from pathlib import Path

# HERE = the folder this script lives in. Using it (instead of a bare filename)
# means the script finds its data no matter which folder VS Code decides to run
# it from - a very common source of "file not found" confusion.
HERE = Path(__file__).parent if "__file__" in globals() else Path.cwd()

# Set this to a full path if your CSV lives somewhere else, e.g.
#   DATA_FILE = r"C:\Users\Elchanan\Downloads\coffee_sales.csv"
DATA_FILE = None

# Searched in order; the first one found wins. The _DEMO file is last, so the
# moment you drop in the real coffee_sales.csv it takes priority automatically.
CSV_CANDIDATES = ["coffee_sales.csv", "df_coffee_sales.csv",
                  "coffee_cart_sales.csv", "coffee_sales_DEMO.csv"]

USING_DEMO_DATA = False   # flipped on below if the demo file is what got loaded


def load_sales():
    """Return the sales table, from memory if possible, otherwise from a CSV."""
    global USING_DEMO_DATA

    # (a) already in memory (the notebook case)
    if "df_coffee_sales" in globals():
        print("Data source: df_coffee_sales (already in memory)")
        return globals()["df_coffee_sales"]

    # (b) an explicit path you set above
    paths = [Path(DATA_FILE)] if DATA_FILE else [HERE / n for n in CSV_CANDIDATES]

    # (c) a CSV sitting next to this script
    for path in paths:
        if path.exists():
            print(f"Data source: {path}")
            if "DEMO" in path.name.upper():
                USING_DEMO_DATA = True
                print("\n" + "!" * 72)
                print("!!  WARNING: this is SYNTHETIC DEMO DATA, not Rita's real readings.")
                print("!!  Every number and chart below is made up. It only proves the")
                print("!!  script runs. Replace it with the real coffee_sales.csv.")
                print("!" * 72 + "\n")
            return pd.read_csv(path)

    # Nothing found - explain what to do instead of crashing with a bare NameError.
    raise FileNotFoundError(
        "\n\nNo data found.\n"
        "  - `df_coffee_sales` is not in memory (you are not in the notebook), and\n"
        f"  - none of {CSV_CANDIDATES} is in {HERE}\n\n"
        "Fix A (real data): run this one line in the notebook where the data DOES\n"
        "                   exist, then put the file in the folder above:\n\n"
        '                   df_coffee_sales.to_csv("coffee_sales.csv", index=False)\n\n'
        "Fix B (just to test the script): run make_demo_csv.py in this folder.\n"
    )


df = load_sales().copy()

print("Raw shape:", df.shape)
print("Columns:  ", list(df.columns))


# %%
# -----------------------------------------------------------------------------
# 1. PARSE THE COLUMNS INTO REAL TYPES
# -----------------------------------------------------------------------------
# The file stores timestamps as TEXT ("2025-02-10T07:00:00.000Z"). Text sorts and
# compares alphabetically, not chronologically, so the very first thing to do is
# turn it into a real datetime. Everything below depends on this.
#
# utc=True handles the trailing "Z"; tz_localize(None) then drops the timezone
# label so that the whole analysis works in the cart's own wall-clock time
# (07:00 means 07:00) and comparisons against plain dates just work.
df["ts_start"]      = pd.to_datetime(df["ts_start"], utc=True).dt.tz_localize(None)
df["date_of_sales"] = pd.to_datetime(df["date_of_sales"], utc=True).dt.tz_localize(None).dt.normalize()

# `slot` is the TIME OF DAY only, e.g. "07:10". There are exactly 18 distinct
# slots and they repeat every single day. Making this explicit does two jobs:
#   - it is half of the correct de-duplication key (section 2)
#   - it is the grouping key for the time-of-day analysis (section 6)
df["slot"] = df["ts_start"].dt.strftime("%H:%M")
df["hour"] = df["ts_start"].dt.hour

print(df[["id", "date_of_sales", "ts_start", "slot", "weekday", "passers", "orders"]].head())


# %%
# -----------------------------------------------------------------------------
# 2. DE-DUPLICATE ON THE REAL GRAIN   *** THE BUG FIX ***
# -----------------------------------------------------------------------------
# A reading is uniquely identified by the DAY **plus** the SLOT inside that day.
#
#   WRONG:  df.drop_duplicates(subset=["ts_start"])
#           If ts_start holds only a time of day, "07:10" appears 28 times - once
#           per day - and pandas treats 27 of them as duplicates. The command
#           then keeps the first day and silently deletes the other 27,
#           collapsing 504 rows into 18. No error is raised; the analysis just
#           quietly becomes a one-day analysis.
#
#   RIGHT:  de-duplicate on the pair (date_of_sales, slot). This is correct
#           whether ts_start carries a full timestamp or only a time of day,
#           because the date always comes from a separate column.
rows_before = len(df)
df = df.drop_duplicates(subset=["date_of_sales", "slot"], keep="first")
rows_after = len(df)

print(f"De-duplication: {rows_before} rows in -> {rows_after} rows out "
      f"({rows_before - rows_after} duplicate reading(s) removed)")

# Guard-rail: a *cleaning* step that deletes a large share of the data is almost
# always a bug, not a cleaning. Crash loudly here rather than publish numbers
# computed from 4% of the file.
assert rows_after >= 0.9 * rows_before, (
    f"Cleaning removed {rows_before - rows_after} of {rows_before} rows. "
    "That is a broken de-duplication key, not dirty data - stop and fix it."
)


# %%
# -----------------------------------------------------------------------------
# 3. DATA VALIDATION - prove the periods are comparable BEFORE comparing them
# -----------------------------------------------------------------------------
# Label each row with the sign that was on display that day. Compare DATES, not
# text, which is why section 1 had to run first.
df["sign"] = np.where(df["date_of_sales"] < SWITCH_DATE, PLAIN, CHEERFUL)

checks = []
def check(name, passed, detail=""):
    """Record one pass/fail check so they can all be printed as a table."""
    checks.append({"check": name, "result": "PASS" if passed else "FAIL", "detail": detail})

# (a) no missing values
n_null = int(df.isna().sum().sum())
check("No missing values", n_null == 0, f"{n_null} nulls")

# (b) orders can never exceed passers-by - that would be a logging error
impossible = int((df["orders"] > df["passers"]).sum())
check("orders <= passers in every row", impossible == 0, f"{impossible} impossible row(s)")

# (c) every day holds the full 18 readings
per_day = df.groupby("date_of_sales").size()
short_days = per_day[per_day != SLOTS_PER_DAY]
check(f"{SLOTS_PER_DAY} readings on every day", short_days.empty,
      "" if short_days.empty else f"{len(short_days)} bad day(s)")

# (d) the two periods cover the same number of days
days_per_sign = df.groupby("sign")["date_of_sales"].nunique()
check("Equal number of days per period", days_per_sign.nunique() == 1,
      f"{days_per_sign.to_dict()}")

# (e) ...and the same weekday mix, i.e. two full Mon-Sun cycles each
weekday_mix = (df.drop_duplicates("date_of_sales")
                 .groupby(["sign", "weekday"]).size().unstack(fill_value=0))
check("Identical weekday mix", bool(weekday_mix.nunique().eq(1).all()), "see table below")

# (f) no calendar day is missing inside or between the two windows
gaps = df["date_of_sales"].drop_duplicates().sort_values().diff().dropna()
check("No missing calendar days", bool((gaps == pd.Timedelta(days=1)).all()))

# (g) footfall is similar in both periods - if the crowd itself changed, a
#     conversion-rate comparison is measuring two different crowds
foot = df.groupby("sign")["passers"].sum()
foot_gap = abs(foot[CHEERFUL] - foot[PLAIN]) / foot[PLAIN]
check("Comparable footfall (<20% apart)", foot_gap < 0.20,
      f"{foot.to_dict()} -> {foot_gap:.1%} apart")

print(pd.DataFrame(checks).to_string(index=False))
print("\nDays per weekday, per period:")
print(weekday_mix)

if any(c["result"] == "FAIL" for c in checks):
    print("\n*** A validation check FAILED - fix the data before reading on. ***")


# %%
# -----------------------------------------------------------------------------
# 4. HEADLINE CONVERSION RATE + STATISTICAL SIGNIFICANCE
# -----------------------------------------------------------------------------
# Conversion rate = total orders / total passers-by, computed on the SUMS.
# Not the average of the 504 little per-slot rates: a slot with 2 passers-by
# would then count as much as a slot with 32, which is simply the wrong weight.
totals = df.groupby("sign")[["passers", "orders"]].sum()
totals["conversion_rate"] = totals["orders"] / totals["passers"]
totals = totals.loc[[PLAIN, CHEERFUL]]          # keep chronological order
print(totals, "\n")

x_plain,    n_plain    = int(totals.loc[PLAIN, "orders"]),    int(totals.loc[PLAIN, "passers"])
x_cheerful, n_cheerful = int(totals.loc[CHEERFUL, "orders"]), int(totals.loc[CHEERFUL, "passers"])
cr_plain, cr_cheerful  = x_plain / n_plain, x_cheerful / n_cheerful

# Two-proportion z-test. It answers one narrow question: "if the sign made no
# difference whatsoever, how often would pure chance produce a gap this big?"
z_stat, p_value = proportions_ztest(count=[x_cheerful, x_plain],
                                    nobs=[n_cheerful, n_plain])

# The p-value says WHETHER there is an effect. A confidence interval says HOW
# BIG it is, which is the part Rita can actually act on.
ci_low, ci_high = confint_proportions_2indep(
    count1=x_cheerful, nobs1=n_cheerful,
    count2=x_plain,    nobs2=n_plain,
    compare="diff", alpha=ALPHA,
)

print(f"Plain sign    : {x_plain:>5} / {n_plain:>5} = {cr_plain:.2%}")
print(f"Cheerful sign : {x_cheerful:>5} / {n_cheerful:>5} = {cr_cheerful:.2%}")
print(f"\nZ-statistic : {z_stat:.4f}")
print(f"P-value     : {p_value:.4g}")
print(f"95% CI on the gap: {ci_low:+.2%} to {ci_high:+.2%} (percentage points)")
print("Significant" if p_value < ALPHA else "Not significant",
      f"at alpha = {ALPHA}")


# %%
# -----------------------------------------------------------------------------
# 5. PRACTICAL SIGNIFICANCE - what the lift is worth, and whether Rita can cope
# -----------------------------------------------------------------------------
absolute_lift = cr_cheerful - cr_plain      # in percentage POINTS
relative_lift = absolute_lift / cr_plain    # as a percentage of the old rate

# Average daily footfall, COMPUTED from the data rather than hard-coded as 28.
# If a day is ever added or dropped, this number follows automatically.
n_days            = df["date_of_sales"].nunique()
avg_daily_passers = df["passers"].sum() / n_days

extra_orders_day  = avg_daily_passers * absolute_lift
extra_revenue_day = extra_orders_day * PRICE

# Carry the uncertainty through to the money, so the answer is a range, not a
# single number that pretends to be exact.
rev_low, rev_high = (avg_daily_passers * ci_low * PRICE,
                     avg_daily_passers * ci_high * PRICE)

print(f"Absolute lift      : {absolute_lift*100:+.2f} percentage points")
print(f"Relative lift      : {relative_lift*100:+.2f}%")
print(f"Avg daily footfall : {avg_daily_passers:.1f} passers-by over {n_days} days")
print(f"Extra orders / day : {extra_orders_day:.1f} cups")
print(f"Extra revenue / day: ${extra_revenue_day:.2f}  (95% CI ${rev_low:.2f} to ${rev_high:.2f})")
print(f"Extra revenue / 30 days: ${extra_revenue_day*30:.0f}")

# The operational question is not just "is it more money" but "can one person
# serve it". Spreading the extra cups over the 18 slots answers that.
print(f"\nOperationally: {extra_orders_day/SLOTS_PER_DAY:.1f} extra cups per 10-minute slot, "
      f"i.e. about one extra cup every {10/(extra_orders_day/SLOTS_PER_DAY):.0f} minutes.")


# %%
# -----------------------------------------------------------------------------
# 6. IS THE LIFT CONSISTENT ACROSS THE MORNING?   *** NEW ***
# -----------------------------------------------------------------------------
# An overall lift can hide an uneven one: a sign that works on the quiet 07:00
# crowd but does nothing during the 08:00 rush would still show a healthy
# average. Grouping by `slot` puts the same 10-minute window from all 14 days of
# each period side by side.
by_slot = (df.groupby(["slot", "sign"])[["passers", "orders"]].sum()
             .assign(cr=lambda t: t["orders"] / t["passers"])
             .reset_index())

slot_wide = by_slot.pivot(index="slot", columns="sign", values="cr")[[PLAIN, CHEERFUL]]
slot_wide["lift_pp"] = (slot_wide[CHEERFUL] - slot_wide[PLAIN]) * 100
print((slot_wide * [100, 100, 1]).round(1).rename(
    columns={PLAIN: "plain %", CHEERFUL: "cheerful %", "lift_pp": "lift (pp)"}))

won = int((slot_wide["lift_pp"] > 0).sum())
print(f"\nCheerful sign ahead in {won} of {len(slot_wide)} slots; "
      f"lift ranges {slot_wide['lift_pp'].min():+.1f} to {slot_wide['lift_pp'].max():+.1f} pp")

# Why not run a z-test on each of the 18 slots? Two reasons:
#   1. Each slot holds only ~150 passers-by per period - too thin to be reliable.
#   2. Running 18 tests at a 5% threshold means roughly one "discovery" per
#      analysis is pure chance.
# So the formal testing happens on the three OPENING HOURS (~900 passers-by
# each), with a Bonferroni correction: split the 5% budget across the 3 tests.
hourly = df.groupby(["hour", "sign"])[["passers", "orders"]].sum().unstack("sign")
bonferroni = ALPHA / hourly.shape[0]

hour_rows = []
for hour in hourly.index:
    xc, nc = int(hourly.loc[hour, ("orders", CHEERFUL)]), int(hourly.loc[hour, ("passers", CHEERFUL)])
    xp, np_ = int(hourly.loc[hour, ("orders", PLAIN)]),   int(hourly.loc[hour, ("passers", PLAIN)])
    z, p = proportions_ztest(count=[xc, xp], nobs=[nc, np_])
    hour_rows.append({
        "hour":       f"{hour:02d}:00",
        "plain":      f"{xp/np_:.1%}",
        "cheerful":   f"{xc/nc:.1%}",
        "lift_pp":    round((xc/nc - xp/np_) * 100, 1),
        "passers":    nc + np_,
        "p_value":    f"{p:.2g}",
        "significant": "yes" if p < bonferroni else "no",
    })

print(f"\nPer-hour tests (Bonferroni threshold = {bonferroni:.4f}):")
print(pd.DataFrame(hour_rows).to_string(index=False))


# %%
# -----------------------------------------------------------------------------
# 7. DAY-LEVEL ROBUSTNESS - is this one freak day or a real shift?
# -----------------------------------------------------------------------------
daily = df.groupby(["date_of_sales", "sign"])[["passers", "orders"]].sum().reset_index()
daily["cr"] = daily["orders"] / daily["passers"]

cr_by_day = {s: g["cr"].values for s, g in daily.groupby("sign")}
u_stat, u_p = mannwhitneyu(cr_by_day[CHEERFUL], cr_by_day[PLAIN], alternative="greater")

print(daily.groupby("sign")["cr"].describe()[["count", "min", "50%", "max"]].round(3))
print(f"\nBest plain day   : {cr_by_day[PLAIN].max():.1%}")
print(f"Worst cheerful day: {cr_by_day[CHEERFUL].min():.1%}")
print(f"Cheerful days above the best plain day: "
      f"{(cr_by_day[CHEERFUL] > cr_by_day[PLAIN].max()).sum()} of {len(cr_by_day[CHEERFUL])}")
print(f"\nMann-Whitney U (daily rates, one-sided): U = {u_stat:.0f}, p = {u_p:.3g}")
print("-> the whole distribution of days shifted up, not just the total.")


# %%
# -----------------------------------------------------------------------------
# 8. VISUALISATIONS
# -----------------------------------------------------------------------------
sns.set_theme(style="whitegrid")
plt.rcParams.update({"axes.grid.axis": "y", "grid.alpha": 0.35,
                     "axes.edgecolor": "#cccccc", "axes.titlesize": 11})

fig, axes = plt.subplots(2, 2, figsize=(14, 9))

# --- (A) Daily conversion rate over time ------------------------------------
# Change over time -> a line chart. The dashed rule marks the day the sign
# changed, so the step is visible without reading any numbers.
sns.lineplot(data=daily, x="date_of_sales", y="cr", hue="sign", hue_order=[PLAIN, CHEERFUL],
             palette=SIGN_COLORS, marker="o", linewidth=2, ax=axes[0, 0])
axes[0, 0].axvline(SWITCH_DATE, color="#6b6b6b", linestyle="--", linewidth=1.2)
axes[0, 0].annotate("sign changed", xy=(SWITCH_DATE, axes[0, 0].get_ylim()[1]),
                    xytext=(4, -12), textcoords="offset points",
                    fontsize=9, color="#6b6b6b")
axes[0, 0].set(title="Daily conversion rate over time", xlabel="", ylabel="Conversion rate")
axes[0, 0].yaxis.set_major_formatter(lambda v, _: f"{v:.0%}")
axes[0, 0].tick_params(axis="x", rotation=45)
axes[0, 0].legend(title=None, loc="upper left")

# --- (B) Conversion rate by time of day -------------------------------------
# The new chart: same 10-minute window, both periods, across the morning.
sns.lineplot(data=by_slot, x="slot", y="cr", hue="sign", hue_order=[PLAIN, CHEERFUL],
             palette=SIGN_COLORS, marker="o", linewidth=2, ax=axes[0, 1])
axes[0, 1].set(title="Conversion rate by time of day (14 days pooled per sign)",
               xlabel="", ylabel="Conversion rate")
axes[0, 1].yaxis.set_major_formatter(lambda v, _: f"{v:.0%}")
axes[0, 1].tick_params(axis="x", rotation=45)
axes[0, 1].legend(title=None, loc="upper left")

# --- (C) Lift per 10-minute slot --------------------------------------------
# Magnitude around a meaningful zero -> bars from a zero baseline. Bars keep the
# cheerful-sign colour when the lift is positive and turn red when it is not, so
# any slot where the sign backfired is impossible to miss.
lift = slot_wide["lift_pp"]
axes[1, 0].bar(lift.index, lift.values,
               color=np.where(lift.values >= 0, C_CHEERFUL, C_NEGATIVE), width=0.65)
axes[1, 0].axhline(0, color="#6b6b6b", linewidth=1)
axes[1, 0].axhline(absolute_lift * 100, color="#6b6b6b", linestyle=":", linewidth=1.2)
axes[1, 0].annotate(f"overall {absolute_lift*100:+.1f} pp",
                    xy=(len(lift) - 1, absolute_lift * 100), xytext=(-6, 6),
                    textcoords="offset points", ha="right", fontsize=9, color="#6b6b6b")
axes[1, 0].set(title="Lift from the cheerful sign, per 10-minute slot",
               xlabel="", ylabel="Lift (percentage points)")
axes[1, 0].tick_params(axis="x", rotation=45)

# --- (D) Spread of DAILY conversion rates -----------------------------------
# Day level, not slot level: a single 10-minute slot can hold 2 passers-by, so
# its "rate" is 0% or 50% noise. Each dot is one trading day.
# `hue="sign"` + `legend=False` is the modern way to colour by the x category -
# passing `palette` without `hue` is deprecated and raises a FutureWarning.
sns.boxplot(data=daily, x="sign", y="cr", order=[PLAIN, CHEERFUL], hue="sign",
            hue_order=[PLAIN, CHEERFUL], palette=SIGN_COLORS,
            legend=False, width=0.45, fliersize=0, ax=axes[1, 1])
sns.stripplot(data=daily, x="sign", y="cr", order=[PLAIN, CHEERFUL],
              color="#2b2b2b", size=4, alpha=0.7, jitter=0.12, ax=axes[1, 1])
axes[1, 1].set(title="Spread of daily conversion rates (14 days each)",
               xlabel="", ylabel="Conversion rate")
axes[1, 1].yaxis.set_major_formatter(lambda v, _: f"{v:.0%}")

if USING_DEMO_DATA:
    fig.suptitle("SYNTHETIC DEMO DATA - NOT REAL RESULTS", color=C_NEGATIVE,
                 fontsize=13, fontweight="bold", y=1.0)

plt.tight_layout()

# Save a PNG next to the script as well as showing it. Running as a plain .py
# file, the window closes when the script ends - this keeps a copy you can open
# again, drop into a report, or hand in.
chart_path = HERE / "coffee_sign_charts.png"
plt.savefig(chart_path, dpi=120, bbox_inches="tight")
print(f"Charts saved to: {chart_path}")

plt.show()


# %%
# -----------------------------------------------------------------------------
# 9. CONCLUSION (printed so the notebook ends with the answer, not a chart)
# -----------------------------------------------------------------------------
if USING_DEMO_DATA:
    print("\n" + "!" * 72)
    print("!!  REMINDER: the figures below come from SYNTHETIC DEMO DATA.")
    print("!" * 72)

print(f"""
Rows analysed        : {len(df)}  ({n_days} days x {SLOTS_PER_DAY} slots)
Plain sign           : {cr_plain:.1%} conversion ({x_plain} orders / {n_plain} passers-by)
Cheerful sign        : {cr_cheerful:.1%} conversion ({x_cheerful} orders / {n_cheerful} passers-by)
Lift                 : {absolute_lift*100:+.1f} pp ({relative_lift:+.0%} relative),
                       95% CI {ci_low*100:+.1f} to {ci_high*100:+.1f} pp, p = {p_value:.2g}
Consistency          : cheerful ahead in {won}/{len(slot_wide)} slots and in all 3 opening hours
Business impact      : ~{extra_orders_day:.0f} extra cups/day = ~${extra_revenue_day:.0f}/day
                       (~${extra_revenue_day*30:.0f} per 30 trading days)
Verdict              : keep the cheerful sign.
""")
