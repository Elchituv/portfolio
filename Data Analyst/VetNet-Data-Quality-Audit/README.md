# VetNet Audit — Data Quality Audit of a Merged Clinic Database

> Four veterinary clinics merged into one shared database — and discovered it badly needs cleaning. The job: audit the data before anyone builds reports on it.

![SQL](https://img.shields.io/badge/SQL-PostgreSQL-4169E1?logo=postgresql&logoColor=white)
![Topic](https://img.shields.io/badge/Topic-Data%20Quality-F57C00)
![Source](https://img.shields.io/badge/XP%20Lab-challenge%20%C2%B7%20Hard-6A1B9A)

---

## The business question

After a merger, four clinics write into a single `visits` table. Each clinic brought its own habits: different codes for the same species or sex, weights typed with units, yes/no flags in several formats. Management wants one trusted source of truth.

**Task:** run a data quality audit — find the problems, explain why each one matters to the business, and group them so stakeholders can prioritise fixes.

## What I built — a column-profiling toolkit

The submission (`data_profiling.sql`) is the profiling layer of the audit: three PostgreSQL queries that scan the whole table quickly.

| Query | Technique | What it surfaces |
|---|---|---|
| Profile every column at once | `to_jsonb(row)` + `jsonb_each()` turns each row into key/value pairs, so a single `GROUP BY key` profiles all columns | Nulls, blank strings and distinct-value counts per column |
| Categorical value counts | Same JSON unpivot, filtered to `species`, `sex`, `clinic_id`, `diagnosis_code`, `sterilized`, `pregnant` | Aliases and inconsistent codes between clinics |
| Malformed weights | Regex `!~ '^-?[0-9]+(\.[0-9]+)?$'` on `weight_kg` | Weights that are not a clean number (units, commas, text) |

The JSON unpivot is the key idea: instead of writing one query per column, the table is profiled generically — the same query works on any table.

## Reviewer feedback

The review praised the efficient `jsonb_each` profiling, the regex check that caught the type inconsistencies in `weight_kg`, and the value counts as a solid base for spotting aliases. It was also clear that profiling alone is **not yet an audit**:

- An audit needs a **narrative** — for each issue: what it is, which clinic it affects, and why it hurts the business.
- The hardest problems were missed: **logical contradictions** (e.g. an animal discharged before it was admitted, or marked both sterilized and pregnant) and **conflicts across records** (the same animal with conflicting data on the same day, or overlapping visits at different clinics).
- Findings should be **grouped into families** so stakeholders can see patterns and prioritise.

## Next iteration — the full audit framework

This is how I'd structure v2, building on the profiling queries:

| Issue family | Checks | Business impact |
|---|---|---|
| **Format & type errors** | Malformed weights, mixed units, inconsistent date formats | Dosage and billing calculations break or silently go wrong |
| **Categorical inconsistencies** | Species / sex / yes-no aliases per clinic, invalid diagnosis codes | The same animal or condition is counted as different things; KPIs split across labels |
| **Temporal errors** | Discharge before admission, visits in the future, dates outside clinic operating periods | Length-of-stay and capacity metrics become meaningless |
| **Biological contradictions** | Sterilized *and* pregnant, sex-specific diagnoses on the wrong sex | Signals data-entry errors that undermine clinical trust in the system |
| **Record conflicts** | Same animal, same day, conflicting values; overlapping visits at two clinics (self-joins / window functions) | Duplicate patients and double billing |

Each finding would be reported with its count, the affected clinic, an example record and a recommended fix (standardise at entry, add constraints, or de-duplicate).

---

## Files

| File | Description |
|---|---|
| `data_profiling.sql` | The three profiling queries, commented |

**Tools:** PostgreSQL · JSONB functions · regular expressions

**Challenge:** [XP Lab](https://www.xp-lab.com) — "VetNet Audit: A single source of woof"

[← Back to Data Analyst](../README.md) · [Portfolio home](../../README.md)
