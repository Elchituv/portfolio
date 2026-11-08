# BI Developer

Dashboards and data models that let business users answer their own questions — reliably and without waiting for an analyst.

**Focus areas**
- **Power BI** — interactive dashboards, DAX measures, drill-downs
- **Data modelling** — star schemas, fact and dimension tables, clean relationships
- **SQL for BI** — views and transformations that feed reporting layers
- **KPI design** — choosing the few metrics that actually drive decisions

## Projects

| Project | Business question | Tools | Highlights |
|---|---|---|---|
| [PharmaDist — Sales & Delivery Performance](PharmaDist-Sales-Delivery/) | Sales are growing, but is service keeping up? Where do orders arrive late or incomplete, and why? | Power BI · Power Query · DAX · SQL | Star schema from a messy ERP export; OTIF 73% vs an 80% target, South 63%; three data bugs caught by SQL reconciliation; ships with a teaching unit |

### FP&A

Finance-focused analysis: the cost of credit, revenue, promotions and pricing.

| Project | Business question | Tools | Highlights |
|---|---|---|---|
| [Loan Amortization Calculator](Loan-Amortization-Calculator/) | What does a loan really cost each month, and what does a grace period add? | Python · SQLite · SQL | Spitzer formula, one-to-many schema, cost of a 6-month grace = ₪1,172 |
| [Grocery Basket Analysis](Grocery-Basket-Analysis/) | Which products belong in a bundle, and which promotions pay off? | Python · pandas · Jupyter | Lift-based affinity, promo-code evaluation (usage, discount rate, basket size), RFM segments |

Each project follows the same structure as the rest of this portfolio: the problem, the data, the solution process, results, and lessons learned.

[← Portfolio home](../README.md)
