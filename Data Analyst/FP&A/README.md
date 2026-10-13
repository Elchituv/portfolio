# FP&A — Completed Projects

Finance-, business- and data-quality analysis projects: from loan amortization modelling to experiment evaluation, basket analysis and database audits. Each project folder has its own README covering the business problem, the solution process, results, and what I learned from review feedback.

| Project | Business question | Tools | Highlights |
|---|---|---|---|
| [Loan Amortization Calculator](Loan-Amortization-Calculator/) | What does a loan really cost each month — and what does a grace period add? | Python · SQLite · SQL | Spitzer formula, one-to-many schema, cost of a 6-month grace = ₪1,172 |
| [Coffee Cart Conversion](Coffee-Cart-AB-Test/) | Did a cheerful sign convert more passers-by into buyers? | Python · pandas · statsmodels | +10.5 pp conversion (19.3% → 29.7%), p < 0.001, ≈ $42/day; fixed a silent de-duplication bug |
| [Grocery Basket Analysis](Grocery-Basket-Analysis/) | Which products belong in a bundle, and for whom? | Python · pandas · Jupyter | Lift-based affinity, RFM segments, promo-code evaluation, 30 region-label variants found |
| [VetNet Data Quality Audit](VetNet-Data-Quality-Audit/) | Can four merged clinic databases be trusted? | PostgreSQL | Generic column profiling with `jsonb_each`, regex type checks, audit framework |
| [Colony Arrival Logs Audit](Colony-Arrival-Logs-Audit/) | Are there impossible records in the residents registry? | PostgreSQL | All 19 anomalies found (3.8%), hypotheses, schema constraint |

Four of these projects are [XP Lab](https://www.xp-lab.com) challenges — realistic analyst assignments reviewed after submission. I include the reviewer's feedback and my fixes in each README, because how an analysis improves matters as much as the first result.

[← Back to Data Analyst](../README.md) · [← Portfolio home](../../README.md)
