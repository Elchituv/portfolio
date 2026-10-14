-- =============================================================================
-- VetNet Audit: A single source of woof  (SQL challenge)
-- Data-profiling queries for the merged `visits` table (PostgreSQL)
--
-- Four vet clinics merged into one shared database. Before anyone can trust
-- reports built on it, the data has to be audited. These queries are the
-- profiling layer of that audit: they scan every column at once and surface
-- nulls, blanks, unexpected categories and malformed numbers.
-- =============================================================================


-- -----------------------------------------------------------------------------
-- 1. Profile EVERY column in one pass: nulls, blanks and distinct values
-- -----------------------------------------------------------------------------
-- to_jsonb(v) turns each row into a JSON object; jsonb_each() unpacks it into
-- (key, value) pairs. Grouping by key then profiles all columns at once,
-- without writing one query per column.
SELECT format('%s | nulls=%s | blanks=%s | distinct=%s',
              key,
              count(*) FILTER (WHERE value = 'null'::jsonb),
              count(*) FILTER (WHERE value::text = '""'),
              count(DISTINCT value)) AS r
FROM visits v, jsonb_each(to_jsonb(v))
GROUP BY key
ORDER BY key;


-- -----------------------------------------------------------------------------
-- 2. Value counts for the categorical columns
-- -----------------------------------------------------------------------------
-- Reveals aliases and inconsistent codes between clinics
-- (e.g. different spellings of the same species, sex or yes/no flags).
SELECT key AS column_name,
       value::text AS raw_value,
       count(*) AS n
FROM visits v, jsonb_each(to_jsonb(v))
WHERE key IN ('species','sex','clinic_id','diagnosis_code','sterilized','pregnant')
GROUP BY key, value
ORDER BY key, count(*) DESC;


-- -----------------------------------------------------------------------------
-- 3. Weights that are not a clean number
-- -----------------------------------------------------------------------------
-- Anything that doesn't match "optional minus, digits, optional decimals"
-- (units typed into the field, commas as decimal separators, text, ...)
-- breaks any calculation that uses weight.
SELECT weight_kg AS raw_value,
       count(*) AS n
FROM visits
WHERE weight_kg !~ '^-?[0-9]+(\.[0-9]+)?$'
GROUP BY weight_kg
ORDER BY count(*) DESC, weight_kg;
