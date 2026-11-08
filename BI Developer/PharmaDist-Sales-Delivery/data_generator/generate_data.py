"""
Synthetic ERP extract for a fictional Israeli pharmaceutical distributor ("PharmaDist").
All names are invented. Output: CSV files as a raw ERP export would look, including
deliberate data-quality issues that the Power Query layer must fix.

Usage:  python generate_data.py ../data            (portfolio version)
        python generate_data.py out_dir 12345     (new random version, e.g. for a new class)
"""
import os
import sys
from datetime import date, timedelta

import numpy as np
import pandas as pd

OUT = sys.argv[1]
SEED = int(sys.argv[2]) if len(sys.argv) > 2 else 20261028   # new seed = new exercise version
os.makedirs(OUT, exist_ok=True)
rng = np.random.default_rng(SEED)

START = date(2024, 1, 1)
ASOF = date(2026, 9, 30)  # ERP extract date

def dmy(d):
    return "" if d is None or pd.isna(d) else d.strftime("%d/%m/%Y")

def add_workdays(d, n):
    """Add n days, skipping Saturdays (no deliveries on Shabbat)."""
    while n > 0:
        d += timedelta(days=1)
        if d.weekday() != 5:
            n -= 1
    if d.weekday() == 5:
        d += timedelta(days=1)
    return d

def month_end(d):
    nxt = date(d.year + (d.month == 12), d.month % 12 + 1, 1)
    return nxt - timedelta(days=1)

# ---------------------------------------------------------------- sales reps
reps = pd.DataFrame([
    ("R01", "Noa Ben-Ami", "Institutional", None),
    ("R02", "Yossi Katz", "Institutional", None),
    ("R03", "Michal Levinson", "Institutional", None),
    ("R04", "Daniel Mor", "Retail", "North"),
    ("R05", "Shira Golan", "Retail", "Sharon"),
    ("R06", "Avi Peretz", "Retail", "Center"),
    ("R07", "Tamar Shani", "Retail", "Center"),
    ("R08", "Eitan Bar", "Retail", "Jerusalem"),
    ("R09", "Lior Hadad", "Retail", "South"),
], columns=["SalesRepID", "RepName", "Team", "HomeRegion"])

# ---------------------------------------------------------------- customers
regions = {
    "North": ["Haifa", "Nazareth", "Afula", "Tiberias", "Karmiel"],
    "Sharon": ["Netanya", "Kfar Saba", "Raanana", "Herzliya", "Hadera"],
    "Center": ["Tel Aviv", "Petah Tikva", "Rishon LeZion", "Holon", "Rehovot"],
    "Jerusalem": ["Jerusalem", "Modiin", "Beit Shemesh"],
    "South": ["Beer Sheva", "Ashdod", "Ashkelon", "Eilat"],
}
city_region = {c: r for r, cs in regions.items() for c in cs}
all_cities = list(city_region)
city_w = np.array([5 if c in ("Tel Aviv", "Jerusalem", "Haifa") else 2 for c in all_cities], float)
city_w /= city_w.sum()

rows = []
cid = 1001
hosp_brands = ["Ofek", "Rimon", "Tavor", "Dekel", "Shaked", "Narkis", "Alon", "Gefen", "Erez", "Hadas", "Yarden", "Brosh", "Arava", "Kinneret"]
hosp_cities = ["Haifa", "Nazareth", "Afula", "Tiberias", "Netanya", "Hadera", "Tel Aviv", "Petah Tikva",
               "Rehovot", "Jerusalem", "Jerusalem", "Beer Sheva", "Ashkelon", "Eilat"]
for b, c in zip(hosp_brands, hosp_cities):
    rows.append((f"C{cid}", f"{b} Medical Center - {c}", "Hospital", c, int(rng.choice([90, 120]))))
    cid += 1
hmo_city = {"North": "Haifa", "Center": "Tel Aviv", "Jerusalem": "Jerusalem", "South": "Beer Sheva"}
for hmo in ["Briut Plus HMO", "Shefa HMO"]:
    for r, c in hmo_city.items():
        rows.append((f"C{cid}", f"{hmo} - {r} District", "HMO", c, 90))
        cid += 1
for i in range(46):
    chain = "PharmaNet" if i < 30 else "CarePoint Pharmacy"
    c = rng.choice(all_cities, p=city_w)
    rows.append((f"C{cid}", f"{chain} #{i + 101} {c}", "Pharmacy Chain", c, 60))
    cid += 1
surnames = ["Cohen", "Levi", "Mizrahi", "Peretz", "Biton", "Dahan", "Avraham", "Friedman", "Azoulay", "Katz",
            "Malka", "Amar", "Ohana", "Shapiro", "Gabay", "Ben David", "Haddad", "Yosef", "Golan", "Shalom",
            "Weiss", "Rosen", "Klein", "Sasson", "Elbaz", "Vaknin", "Tal", "Segal", "Ashkenazi", "Nachum"]
used = set()
while len(used) < 72:
    s = rng.choice(surnames)
    c = rng.choice(all_cities, p=city_w)
    if (s, c) in used:
        continue
    used.add((s, c))
    rows.append((f"C{cid}", f"{s} Pharmacy - {c}", "Independent Pharmacy", c, int(rng.choice([30, 45]))))
    cid += 1

cust = pd.DataFrame(rows, columns=["CustomerID", "CustomerName", "CustomerType", "City", "PaymentTermsDays"])
cust["Region"] = cust["City"].map(city_region)

def assign_rep(r):
    if r.CustomerType in ("Hospital", "HMO"):
        return ["R01", "R02", "R03"][hash(r.CustomerID) % 3]
    cands = reps[(reps.Team == "Retail") & (reps.HomeRegion == r.Region)].SalesRepID.tolist()
    return cands[int(r.CustomerID[1:]) % len(cands)]

cust["SalesRepID"] = cust.apply(assign_rep, axis=1)
# deterministic institutional assignment (python hash is salted) -> use numeric id
inst = cust.CustomerType.isin(["Hospital", "HMO"])
cust.loc[inst, "SalesRepID"] = cust.loc[inst, "CustomerID"].map(lambda x: ["R01", "R02", "R03"][int(x[1:]) % 3])

# account creation date: most existed before 2024, some opened during the period
created = []
for t in cust.CustomerType:
    if t in ("Hospital", "HMO") or rng.random() < 0.8:
        created.append(date(2019, 1, 1) + timedelta(days=int(rng.integers(0, 1700))))
    else:
        created.append(START + timedelta(days=int(rng.integers(30, 900))))
cust["CreatedDate"] = created

cust["CityClean"] = cust["City"]
# --- deliberate DQ issue #1: inconsistent Region text (case / trailing spaces)
dirty_idx = rng.choice(cust.index, size=28, replace=False)
for k, i in enumerate(dirty_idx):
    r = cust.at[i, "Region"]
    cust.at[i, "Region"] = [r.upper(), r.lower(), r + " ", " " + r.lower() + "  "][k % 4]
# --- deliberate DQ issue #1b: City with stray spaces / lower case
for i in rng.choice(cust.index, size=12, replace=False):
    cust.at[i, "City"] = "  " + cust.at[i, "City"].lower()

# ---------------------------------------------------------------- products
# (name, category, list price NIS 2024, cold chain, shelf life months, demand weight)
P = [
    ("Atorvastatin 20mg x30", "Cardiology", 24, 0, 36, 10), ("Atorvastatin 40mg x30", "Cardiology", 32, 0, 36, 7),
    ("Amlodipine 5mg x30", "Cardiology", 18, 0, 36, 9), ("Bisoprolol 5mg x30", "Cardiology", 21, 0, 36, 7),
    ("Ramipril 5mg x28", "Cardiology", 26, 0, 30, 6), ("Clopidogrel 75mg x28", "Cardiology", 48, 0, 30, 6),
    ("Rivaroxaban 20mg x28", "Cardiology", 310, 0, 30, 4), ("Enoxaparin 40mg inj x10", "Cardiology", 165, 1, 24, 5),
    ("Metformin 850mg x60", "Diabetes", 22, 0, 36, 10), ("Sitagliptin 100mg x28", "Diabetes", 175, 0, 30, 5),
    ("Empagliflozin 10mg x30", "Diabetes", 215, 0, 30, 6), ("Insulin Glargine 100U pen x5", "Diabetes", 240, 1, 24, 6),
    ("Insulin Aspart 100U pen x5", "Diabetes", 205, 1, 24, 5), ("Semaglutide 1mg pen", "Diabetes", 690, 1, 24, 1.5),
    ("Amoxicillin 500mg x20", "Antibiotics", 19, 0, 24, 9), ("Amoxicillin-Clav 875mg x14", "Antibiotics", 42, 0, 24, 7),
    ("Azithromycin 250mg x6", "Antibiotics", 36, 0, 36, 6), ("Ciprofloxacin 500mg x10", "Antibiotics", 28, 0, 36, 4),
    ("Ceftriaxone 1g vial x10", "Antibiotics", 120, 0, 36, 4), ("Piperacillin-Tazo 4.5g vial x10", "Antibiotics", 390, 0, 24, 3),
    ("Salbutamol inhaler 100mcg", "Respiratory", 29, 0, 24, 8), ("Budesonide-Formoterol inhaler", "Respiratory", 165, 0, 24, 6),
    ("Montelukast 10mg x28", "Respiratory", 54, 0, 36, 5), ("Fluticasone nasal spray", "Respiratory", 47, 0, 24, 5),
    ("Trastuzumab 440mg vial", "Oncology", 6900, 1, 18, 1.2), ("Bevacizumab 400mg vial", "Oncology", 5200, 1, 18, 1.0),
    ("Pembrolizumab 100mg vial", "Oncology", 11800, 1, 18, 0.8), ("Capecitabine 500mg x120", "Oncology", 1350, 0, 24, 1.5),
    ("Imatinib 400mg x30", "Oncology", 2400, 0, 24, 1.2), ("Ondansetron 8mg x10", "Oncology", 64, 0, 36, 3),
    ("Paracetamol 500mg x20", "OTC", 9, 0, 36, 14), ("Ibuprofen 400mg x24", "OTC", 16, 0, 36, 12),
    ("Vitamin D3 1000IU x100", "OTC", 39, 0, 24, 8), ("Omeprazole 20mg x28", "OTC", 27, 0, 36, 9),
    ("Loratadine 10mg x20", "OTC", 22, 0, 36, 7), ("Saline nasal drops", "OTC", 14, 0, 24, 6),
    ("Influenza vaccine 2025-26", "Vaccines", 58, 1, 9, 0), ("Influenza vaccine 2026-27", "Vaccines", 61, 1, 9, 0),
    ("Hepatitis B vaccine", "Vaccines", 85, 1, 24, 2), ("Tetanus-Diphtheria vaccine", "Vaccines", 49, 1, 24, 2),
]
mfrs = ["Alpha Generics", "Negev Pharma", "Galilee Biologics", "Medica Global", "Carmel Labs", "BioNova Europe"]
prod = pd.DataFrame(P, columns=["ProductName", "Category", "ListPrice2024", "ColdChain", "ShelfLifeM", "W"])
prod.insert(0, "ProductID", [f"P{101 + i}" for i in range(len(prod))])
prod["Manufacturer"] = [mfrs[(i * 7) % len(mfrs)] if c != "Oncology" else ["Galilee Biologics", "BioNova Europe"][i % 2]
                        for i, c in enumerate(prod.Category)]
prod["StandardCost"] = (prod.ListPrice2024 * rng.uniform(0.55, 0.78, len(prod))).round(2)
cat_true = prod.Category.copy()
# --- deliberate DQ issue #2: missing category on two products
prod.loc[prod.ProductName.str.startswith("Saline"), "Category"] = ""
prod.loc[prod.ProductName.str.startswith("Fluticasone"), "Category"] = ""

price_idx = {2024: 1.0, 2025: 1.03, 2026: 1.03 * 1.03}

# demand mix per customer type: multiplier on category
mix = {
    "Hospital": {"Cardiology": 1.0, "Diabetes": 0.7, "Antibiotics": 2.0, "Respiratory": 0.6, "Oncology": 5.0, "OTC": 0.3, "Vaccines": 1.0},
    "HMO": {"Cardiology": 1.2, "Diabetes": 1.5, "Antibiotics": 1.0, "Respiratory": 1.0, "Oncology": 1.5, "OTC": 0.6, "Vaccines": 2.0},
    "Pharmacy Chain": {"Cardiology": 1.0, "Diabetes": 1.0, "Antibiotics": 0.9, "Respiratory": 1.0, "Oncology": 0.15, "OTC": 1.8, "Vaccines": 0.3},
    "Independent Pharmacy": {"Cardiology": 1.0, "Diabetes": 0.9, "Antibiotics": 0.9, "Respiratory": 1.0, "Oncology": 0.05, "OTC": 2.0, "Vaccines": 0.1},
}
inj_hosp_only = prod.ProductName.str.contains("vial|Piperacillin|Ceftriaxone")

def season(cat, d):
    m = d.month
    if cat in ("Antibiotics", "Respiratory"):
        return {12: 1.6, 1: 1.7, 2: 1.5, 3: 1.2, 6: 0.75, 7: 0.7, 8: 0.75}.get(m, 1.0)
    return 1.0

def flu_weight(pname, d):
    # each season's vaccine is sold Sep-Dec of its season
    if "2025-26" in pname:
        return 18.0 if (d.year == 2025 and d.month in (9, 10, 11, 12)) else 0.0
    if "2026-27" in pname:
        return 18.0 if (d.year == 2026 and d.month >= 9) else 0.0
    return None

qty_base = {"Hospital": 30, "HMO": 60, "Pharmacy Chain": 18, "Independent Pharmacy": 7}
lines_rng = {"Hospital": (4, 12), "HMO": (5, 14), "Pharmacy Chain": (3, 9), "Independent Pharmacy": (1, 5)}
p_order = {"Hospital": 0.18, "HMO": 0.32, "Pharmacy Chain": 0.11, "Independent Pharmacy": 0.065}
disc_rng = {"Hospital": (0.08, 0.15), "HMO": (0.12, 0.18), "Pharmacy Chain": (0.05, 0.10), "Independent Pharmacy": (0.0, 0.04)}

ctype = dict(zip(cust.CustomerID, cust.CustomerType))
ccity = dict(zip(cust.CustomerID, cust.CityClean))
ccreated = dict(zip(cust.CustomerID, cust.CreatedDate))
cterms = dict(zip(cust.CustomerID, cust.PaymentTermsDays))
# three independents that stop paying in 2026 (bad debt story)
bad_payers = set(cust[cust.CustomerType == "Independent Pharmacy"].CustomerID.sample(3, random_state=7))

hdr, lines = [], []
oid = 500001
d = START
while d <= ASOF:
    if d.weekday() == 5:  # Saturday - closed
        d += timedelta(days=1)
        continue
    years = (d - START).days / 365.25
    growth = 1.06 ** years
    fri = 0.45 if d.weekday() == 4 else 1.0
    for c in cust.CustomerID:
        if d < ccreated[c]:
            continue
        t = ctype[c]
        if rng.random() > p_order[t] * growth * fri:
            continue
        # product weights for this customer/date
        w = np.array([
            (flu_weight(pn, d) if flu_weight(pn, d) is not None else pw)
            * mix[t][cat] * season(cat, d)
            * (0.02 if (inj and t not in ("Hospital", "HMO")) else 1.0)
            * ({"Oncology": 1.10, "Diabetes": 1.08}.get(cat, 1.0) ** years)
            for pn, cat, pw, inj in zip(prod.ProductName, cat_true, prod.W, inj_hosp_only)
        ])
        w = w / w.sum()
        nlines = int(rng.integers(lines_rng[t][0], lines_rng[t][1] + 1))
        nlines = min(nlines, int((w > 0).sum()))
        pids = rng.choice(prod.index, size=nlines, replace=False, p=w)
        cold = prod.loc[pids, "ColdChain"].max() == 1
        req = add_workdays(d, 1 if (cold or t == "Hospital") else int(rng.integers(2, 4)))
        city = ccity[c]
        p_on = 0.91
        if city_region[city] == "South":
            p_on = 0.80
        if city == "Eilat":
            p_on = 0.62
        delay = 0 if rng.random() < p_on else int(rng.integers(1, 4))
        act = add_workdays(req, delay) if delay else req
        r = rng.random()
        if r < 0.015:
            status, act = "Cancelled", None
        elif act > ASOF:
            status, act = "Open", None
        else:
            status = "Delivered"
        hdr.append((oid, d, c, req, act, status))
        dlo, dhi = disc_rng[t]
        for ln, pi in enumerate(pids, start=1):
            p = prod.loc[pi]
            cat = cat_true[pi]
            base = qty_base[t] * (0.08 if cat == "Oncology" else 1.0) * (2.0 if cat == "OTC" else 1.0)
            if p.ListPrice2024 > 1000:
                base = max(1.5, base * 0.25)
            q = max(1, int(rng.poisson(max(base, 1.0))))
            price = round(p.ListPrice2024 * price_idx[d.year], 2)
            disc = round(float(rng.uniform(dlo, dhi)), 2)
            if status == "Delivered":
                short = p.ProductName.startswith("Amoxicillin") and date(2025, 11, 1) <= d <= date(2026, 1, 31)
                pin = 0.35 if short else 0.975
                qd = q if rng.random() < pin else int(np.floor(q * rng.uniform(0.3 if short else 0.5, 0.95)))
            else:
                qd = 0
            lines.append((oid, ln, p.ProductID, q, qd, price, disc))
        oid += 1
    d += timedelta(days=1)

oh = pd.DataFrame(hdr, columns=["OrderID", "OrderDate", "CustomerID", "RequestedDeliveryDate", "ActualDeliveryDate", "OrderStatus"])
ol = pd.DataFrame(lines, columns=["OrderID", "LineNo", "ProductID", "Quantity", "QtyDelivered", "UnitPrice", "DiscountPct"])

# ---------------------------------------------------------------- invoices (from clean data)
ol["LineNet"] = (ol.QtyDelivered * ol.UnitPrice * (1 - ol.DiscountPct)).round(2)
amt = ol.groupby("OrderID").LineNet.sum().round(2)
inv = []
iid = 700001
for o in oh[oh.OrderStatus == "Delivered"].itertuples():
    a = float(amt.get(o.OrderID, 0))
    if a <= 0:
        continue
    t = ctype[o.CustomerID]
    idate = o.ActualDeliveryDate
    due = month_end(idate) + timedelta(days=int(cterms[o.CustomerID]))  # Israeli "shotef + N"
    mu, sd = {"Hospital": (28, 22), "HMO": (9, 10), "Pharmacy Chain": (0, 7), "Independent Pharmacy": (4, 11)}[t]
    paid = due + timedelta(days=int(max(-15, rng.normal(mu, sd))))
    if o.CustomerID in bad_payers and idate >= date(2026, 2, 1):
        paid = None
    if paid is not None and paid > ASOF:
        paid = None
    inv.append((f"INV{iid}", o.OrderID, idate, due, a, paid))
    iid += 1
inv = pd.DataFrame(inv, columns=["InvoiceID", "OrderID", "InvoiceDate", "DueDate", "InvoiceAmount", "PaidDate"])
ol = ol.drop(columns="LineNet")

# ---------------------------------------------------------------- inventory snapshot
wh = pd.DataFrame([("WH01", "DC Center - Modiin", "Modiin"), ("WH02", "DC North - Haifa", "Haifa")],
                  columns=["WarehouseID", "WarehouseName", "City"])
_m = ol.merge(oh[["OrderID", "OrderDate"]], on="OrderID")
monthly = _m[_m.OrderDate >= date(2026, 1, 1)].groupby("ProductID").Quantity.sum() / 9
inv_rows = []
bn = 1
for p in prod.itertuples():
    for w_id, share in (("WH01", 0.65), ("WH02", 0.35)):
        if "2025-26" in p.ProductName:
            # leftover last-season flu vaccine: expired 30/06/2026, still on the shelf (quarantine story)
            if w_id == "WH02":
                inv_rows.append((ASOF, w_id, p.ProductID, f"B{bn:05d}", date(2026, 6, 30), 1450, p.StandardCost)); bn += 1
            continue
        nb = int(rng.integers(1, 4))
        for k in range(nb):
            dem = float(monthly.get(p.ProductID, 50)) * share
            qty = max(5, int(dem * rng.uniform(0.4, 1.6)))
            life_days = int(p.ShelfLifeM * 30.4)
            exp = ASOF + timedelta(days=int(rng.integers(20, life_days)))
            inv_rows.append((ASOF, w_id, p.ProductID, f"B{bn:05d}", exp, qty, p.StandardCost)); bn += 1
# planted risks: slow-moving oncology batch near expiry, a few short-dated / expired batches
onc = prod[prod.ProductName.str.startswith("Bevacizumab")].iloc[0]
inv_rows.append((ASOF, "WH01", onc.ProductID, f"B{bn:05d}", ASOF + timedelta(days=52), 38, onc.StandardCost)); bn += 1
for name, days, q in [("Insulin Aspart", 75, 420), ("Ceftriaxone", 33, 260), ("Montelukast", -12, 180), ("Enoxaparin", 88, 300)]:
    p = prod[prod.ProductName.str.startswith(name)].iloc[0]
    inv_rows.append((ASOF, "WH02" if days < 0 else "WH01", p.ProductID, f"B{bn:05d}", ASOF + timedelta(days=days), q, p.StandardCost)); bn += 1
invb = pd.DataFrame(inv_rows, columns=["SnapshotDate", "WarehouseID", "ProductID", "BatchNo", "ExpiryDate", "QtyOnHand", "UnitCost"])

# ---------------------------------------------------------------- deliberate DQ issues on transactions
# #3: ~3% of order headers carry a lower-case / padded CustomerID (manual entry in ERP)
idx = rng.choice(oh.index, size=int(len(oh) * 0.03), replace=False)
oh.loc[idx, "CustomerID"] = oh.loc[idx, "CustomerID"].str.lower()
idx2 = rng.choice(idx, size=len(idx) // 3, replace=False)
oh.loc[idx2, "CustomerID"] = oh.loc[idx2, "CustomerID"] + " "
# #4: zero-quantity lines (lines deleted in ERP but exported with qty 0)
zero = ol.sample(frac=0.004, random_state=3).copy()
zero["LineNo"] = zero.groupby("OrderID").cumcount() + 50
zero["Quantity"] = 0
zero["QtyDelivered"] = 0
ol = pd.concat([ol, zero])
# #5: exact duplicate rows from a double export
dups = ol[ol.Quantity > 0].sample(frac=0.006, random_state=5)
ol = pd.concat([ol, dups]).sort_values(["OrderID", "LineNo"], kind="stable").reset_index(drop=True)

# ---------------------------------------------------------------- write CSVs
# Power BI version: 4 files, ISO dates (YYYY-MM-DD) so no locale issues on import.
# Invoices and inventory are still simulated above (keeps the random sequence
# identical to the full ERP version) but are not exported for this project.
iso = lambda d: "" if d is None or pd.isna(d) else d.strftime("%Y-%m-%d")
cust[["CustomerID", "CustomerName", "CustomerType", "City", "Region"]].to_csv(f"{OUT}/Customers.csv", index=False)
prod[["ProductID", "ProductName", "Category", "Manufacturer", "ColdChain", "StandardCost", "ListPrice2024"]] \
    .rename(columns={"ColdChain": "ColdChainFlag", "ListPrice2024": "ListPrice"}) \
    .assign(ColdChainFlag=lambda x: x.ColdChainFlag.map({1: "Y", 0: "N"})) \
    .to_csv(f"{OUT}/Products.csv", index=False)
for col in ["OrderDate", "RequestedDeliveryDate", "ActualDeliveryDate"]:
    oh[col] = oh[col].map(iso)
oh.to_csv(f"{OUT}/Orders.csv", index=False)
ol.to_csv(f"{OUT}/OrderLines.csv", index=False)

print("customers", len(cust), "| products", len(prod), "| orders", len(oh), "| order lines", len(ol))
