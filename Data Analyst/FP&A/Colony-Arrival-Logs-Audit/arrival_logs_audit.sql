-- =============================================================================
-- Analyze Arrival Logs In Outer Space  (XP Lab challenge, SQL, Easy)
-- Data sanity checks on the colony's arrival_logs table
--
-- Story context: the planet Hawking-3c was closed to humans until settlement
-- opened on 2758-02-01. The table should list colonizers who are active on the
-- surface today (February 2783), so every arrival must fall between those dates.
-- =============================================================================


-- Query 1: Range check - earliest and latest arrival in the table
SELECT
    MIN(date_of_arrival) AS earliest_arrival,
    MAX(date_of_arrival) AS latest_arrival
FROM arrival_logs;


-- Query 2: Out-of-bounds check - every record outside the valid window
SELECT *
FROM arrival_logs
WHERE date_of_arrival < '2758-02-01'
   OR date_of_arrival > '2783-02-01'
ORDER BY date_of_arrival ASC;


-- Query 3: Active colonizers with an arrival date in the future
SELECT
    colonizer_id,
    name,
    date_of_arrival
FROM arrival_logs
WHERE date_of_arrival > '2783-02-01'
ORDER BY date_of_arrival ASC;


-- Query 4: Arrivals per year - the shape of immigration over time
SELECT
    EXTRACT(YEAR FROM date_of_arrival) AS arrival_year,
    COUNT(*) AS total_arrivals
FROM arrival_logs
GROUP BY arrival_year
ORDER BY arrival_year ASC;


-- =============================================================================
-- Prevent it from happening again: enforce the valid window in the schema
-- =============================================================================
-- v1 (submitted) used CURRENT_DATE as the upper bound:
--     CHECK (date_of_arrival >= '2758-02-01' AND date_of_arrival <= CURRENT_DATE)
-- Review feedback: CURRENT_DATE changes every day, so the rule silently drifts.
-- For a historical archive the boundaries must be fixed, known values.
--
-- v2 (corrected): static bounds. Update the upper bound deliberately when the
-- archive's snapshot date changes.
ALTER TABLE arrival_logs
ADD CONSTRAINT chk_settlement_timeline
CHECK (date_of_arrival >= DATE '2758-02-01'
   AND date_of_arrival <= DATE '2783-02-06');
