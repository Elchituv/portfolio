# Elchanan Achituv — Data Portfolio

**Data Analyst · BI Developer · AI Builder** | Engineer with 4+ years of biomedical data analysis

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Elchanan%20Achituv-0A66C2?logo=linkedin&logoColor=white)](https://www.linkedin.com/in/elchanan-achituv-data-driven/)
[![GitHub](https://img.shields.io/badge/GitHub-Elchituv-181717?logo=github&logoColor=white)](https://github.com/Elchituv)
![Location](https://img.shields.io/badge/Location-Israel-555555)
<!-- To show a Resume badge: upload your CV to Resume/Elchanan_Achituv_CV.pdf, then delete the first and last lines of this comment block.
[![Resume](https://img.shields.io/badge/Resume-PDF-D32F2F?logo=adobeacrobatreader&logoColor=white)](Resume/Elchanan_Achituv_CV.pdf)
-->

---

## About me

I'm an engineer who moved into data through the lab. For over four years at **MD Biosciences Neuro**, a preclinical CRO, I analysed biological data and helped design in-vitro and in-vivo experiments — statistics in Prism and Python, image processing in ImageJ and Deep Pathology, and automated brain-lesion mapping that replaced manual annotation. I co-authored a peer-reviewed electrophysiology study published in *The Journal of Pain* (2024).

Before that I worked in **GMP quality and product release** at Omrix Biopharmaceuticals and in **R&D** at Daika, with additional training in control and automation (PLC, Arduino). In 2025 I completed the **Biomedical Data Analyst** program (Association of Engineers and Architects in Israel, the Hebrew University and the Israel Innovation Authority).

That mix shapes how I work: I validate data before I trust it, I check that comparisons are fair before I make them, and I translate results into decisions — money, risk, or the next experiment.

### Roles I'm looking for

I'm open to work in three directions — one folder of this portfolio for each — especially in healthtech and pharma:

| Role | What I bring |
|---|---|
| **[Data Analyst](Data%20Analyst/)** | SQL and Python analysis, statistical testing, data-quality audits, financial modelling, clear write-ups for decision makers |
| **[BI Developer](BI%20Developer/)** | Power BI dashboards, data modelling and KPI design that let business users answer their own questions |
| **[AI Builder](AI%20Builder/)** | AI-powered automations (n8n, Make, Zapier) and LLM workflows that take repetitive work off people's plates |

More about me on my [GitHub profile](https://github.com/Elchituv) and [LinkedIn](https://www.linkedin.com/in/elchanan-achituv-data-driven/).

---

## Portfolio structure

```
portfolio/
├── AI Builder/       → AI automations, LLM pipelines, agents   (coming soon)
├── BI Developer/     → Power BI dashboards and data models     (coming soon)
└── Data Analyst/
    └── FP&A/         → completed projects (below)
```

## Featured projects

| Project | Question | Stack | Result |
|---|---|---|---|
| [Coffee Cart Conversion](Data%20Analyst/FP%26A/Coffee-Cart-AB-Test/) | Did a cheerful sign sell more coffee? | Python · statsmodels | +10.5 pp conversion, p < 0.001, ≈ $42 extra revenue/day |
| [Grocery Basket Analysis](Data%20Analyst/FP%26A/Grocery-Basket-Analysis/) | Which products should be bundled, and for whom? | Python · pandas | Lift-based bundles, RFM segments, promo evaluation |
| [Loan Amortization Calculator](Data%20Analyst/FP%26A/Loan-Amortization-Calculator/) | What does a loan — and its grace period — really cost? | Python · SQLite | Full Spitzer schedules stored and summarised in SQL |
| [VetNet Data Quality Audit](Data%20Analyst/FP%26A/VetNet-Data-Quality-Audit/) | Can a merged four-clinic database be trusted? | PostgreSQL | Generic column profiling + audit framework |
| [Colony Arrival Logs Audit](Data%20Analyst/FP%26A/Colony-Arrival-Logs-Audit/) | Are there impossible records in a registry? | PostgreSQL | 19 / 503 anomalies found, schema constraint added |

## How every project is documented

Each project folder has a README with the same structure, so it can be skimmed in two minutes:

1. **The business question** — what decision the analysis supports
2. **Data** — sources, grain and quirks
3. **Solution process** — the steps, and why each one was needed
4. **Results** — numbers and the recommendation
5. **Feedback & iteration** — what review caught and what I changed

New projects start from [`PROJECT_TEMPLATE.md`](PROJECT_TEMPLATE.md).

## Toolbox

- **Data:** Python (pandas, NumPy, SciPy, statsmodels, matplotlib, seaborn) · SQL (PostgreSQL, SQLite, DBeaver) · Excel · GraphPad Prism · MATLAB
- **BI:** Power BI
- **AI & automation:** n8n · Make · Zapier · LLM APIs
- **Domain:** preclinical research (GLP), GMP and quality, image analysis (ImageJ, Deep Pathology)
