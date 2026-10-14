# Data Analyst

Turning messy business data into decisions: cleaning and validating data, testing hypotheses statistically, and translating results into money, risk and next actions.

**Core skills shown here:** SQL (joins, aggregation, window functions, constraints) · Python (pandas, NumPy, SciPy, statsmodels) · experiment evaluation · data-quality auditing · financial modelling · stakeholder-ready write-ups

## Projects

| Project | Business question | Tools | Highlights |
|---|---|---|---|
| [Coffee Cart Conversion](Coffee-Cart-AB-Test/) | Did a cheerful sign convert more passers-by into buyers? | Python · pandas · statsmodels | +10.5 pp conversion (19.3% → 29.7%), p < 0.001, ≈ $42/day; fixed a silent de-duplication bug |
| [VetNet Data Quality Audit](VetNet-Data-Quality-Audit/) | Can four merged clinic databases be trusted? | PostgreSQL | Generic column profiling with `jsonb_each`, regex type checks, audit framework |
| [Colony Arrival Logs Audit](Colony-Arrival-Logs-Audit/) | Are there impossible records in the residents registry? | PostgreSQL | All 19 anomalies found (3.8%), hypotheses, schema constraint |

## FP&A

Finance-focused analysis — cost of credit, revenue, promotions and pricing.

| Project | Business question | Tools | Highlights |
|---|---|---|---|
| [Loan Amortization Calculator](FP%26A/Loan-Amortization-Calculator/) | What does a loan really cost each month — and what does a grace period add? | Python · SQLite · SQL | Spitzer formula, one-to-many schema, cost of a 6-month grace = ₪1,172 |
| [Grocery Basket Analysis](FP%26A/Grocery-Basket-Analysis/) | Which products belong in a bundle, and which promotions pay off? | Python · pandas · Jupyter | Lift-based affinity, promo-code evaluation, RFM segments |

See the [FP&A folder](FP%26A/) for details.

Each project README covers the business question, the data, the solution process, results, and what I improved after review.

[← Portfolio home](../README.md)
