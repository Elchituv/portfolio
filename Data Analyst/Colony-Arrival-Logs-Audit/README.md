# Colony Arrival Logs — Data Sanity Audit

> A space colony's registry of active residents contains people who arrived before the planet was open — and people who haven't arrived yet. Find every impossible record, explain it, and stop it from happening again.

![SQL](https://img.shields.io/badge/SQL-PostgreSQL-4169E1?logo=postgresql&logoColor=white)
![Topic](https://img.shields.io/badge/Topic-Data%20Validation-F57C00)
![Source](https://img.shields.io/badge/XP%20Lab-challenge%20%C2%B7%20Easy-6A1B9A)

---

## The business question

The colony on Hawking-3c keeps an `arrival_logs` table of colonizers currently living on the surface. Two hard facts bound every valid record:

- The planet was **closed to humans** during terraforming, until **1 February 2758**.
- The table lists people **active today (February 2783)**.

**Task:** run sanity checks, find out whether something is wrong in the dataset, form hypotheses, and recommend a fix.

## Solution process

| Step | Query | Purpose |
|---|---|---|
| 1 | `MIN` / `MAX` of `date_of_arrival` | Does the range even make sense? |
| 2 | Records before 2758-02-01 or after 2783-02-01 | List every out-of-bounds record |
| 3 | Active colonizers with future arrival dates | Isolate the "not here yet" group |
| 4 | `COUNT(*)` per `EXTRACT(YEAR …)` | See the shape of immigration over time |

All queries are in [`arrival_logs_audit.sql`](arrival_logs_audit.sql).

## Findings

Of **503** active records, **19 (3.8%)** are chronologically impossible:

| Anomaly | Records | Detail |
|---|---|---|
| Pre-settlement arrivals | **14** | 7 in 2756 and 7 in 2757 — before humans were allowed on the planet |
| Future arrivals | **5** | Dated March–July 2783 — after "today", yet marked as active |

Other observations:
- Every timestamp is exactly `00:00:00.000Z`, so arrival *time* carries no information — only the date is usable.
- The majority of today's residents arrived in the 2758 founding wave, and arrivals come in discrete waves rather than a steady flow.

## Hypotheses

1. **Pre-settlement records** are data-entry typos (2756/2757 instead of 2758) from the chaotic first registration wave — or leftover tracking profiles of robotic terraforming units that were never purged.
2. **Future records** are administrative pre-clearance: profiles created for passengers on incoming transports and marked "active" too early.
3. **Wave pattern:** immigration likely depends on orbital launch windows rather than continuous travel.

## Recommendation — enforce the rule in the database

Add a `CHECK` constraint so impossible dates can't be inserted again:

```sql
ALTER TABLE arrival_logs
ADD CONSTRAINT chk_settlement_timeline
CHECK (date_of_arrival >= DATE '2758-02-01'
   AND date_of_arrival <= DATE '2783-02-06');
```

Next step: with access to the deceased and off-world departure logs, cross-reference them to rebuild a true year-by-year population curve, not just a snapshot of current residents.

---

## Feedback & iteration

The review confirmed the main goal was met — **all 19 anomalies found (14 too early, 5 too late)** — and called the report well structured with logical hypotheses and clear SQL. It also caught two mistakes worth learning from:

| Review point | What I changed / learned |
|---|---|
| My v1 constraint used `CURRENT_DATE` as the upper bound. It changes every day, so the rule drifts over time — wrong for a historical archive | Replaced with fixed, known boundary dates (above) |
| A headline number about post-2758 immigration ("average of 5 per year") was miscalculated | Removed from the findings; lesson: re-check every number a conclusion rests on |
| Claims like "58% of residents arrived in 2758" weren't backed by a shown result | Every key finding should point to the query and output that supports it |

---

## Files

| File | Description |
|---|---|
| `arrival_logs_audit.sql` | Sanity-check queries + corrected constraint |

**Tools:** PostgreSQL · date functions · constraints

**Challenge:** [XP Lab](https://www.xp-lab.com) — "Analyze Arrival Logs In Outer Space"

[← Back to Data Analyst](../README.md) · [Portfolio home](../../README.md)
