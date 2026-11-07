-- tm02: population size for the medtech time-machine benchmark (counts only; no text, no outcomes).
-- Queries: US granted utility patents (B1/B2) 2010-2023 with a device CPC subclass (A61B/F/G/H/J/L/M/N).
-- Targets: US patents the examiner cited (category contains SEA), sharing no 3-character CPC code with the
-- query (IPC3-equivalent "other field"), filed at least 5 years before the query.
WITH q AS (
  SELECT
    p.publication_number,
    DIV(p.grant_date, 10000) AS grant_year,
    DIV(p.filing_date, 10000) AS filing_year,
    ARRAY(SELECT DISTINCT SUBSTR(c.code, 1, 3) FROM UNNEST(p.cpc) AS c) AS q3,
    p.citation
  FROM `patents-public-data.patents.publications` AS p
  WHERE p.country_code = 'US'
    AND p.kind_code IN ('B1', 'B2')
    AND p.grant_date BETWEEN 20100101 AND 20231231
    AND EXISTS (SELECT 1 FROM UNNEST(p.cpc) AS c
                WHERE SUBSTR(c.code, 1, 4) IN ('A61B', 'A61F', 'A61G', 'A61H', 'A61J', 'A61L', 'A61M', 'A61N'))
),
totals AS (
  SELECT grant_year, COUNT(*) AS device_queries FROM q GROUP BY grant_year
),
cites AS (
  SELECT q.publication_number AS qid, q.grant_year, q.filing_year, q.q3, c.publication_number AS tid
  FROM q, UNNEST(q.citation) AS c
  WHERE c.category LIKE '%SEA%' AND STARTS_WITH(c.publication_number, 'US-')
),
t AS (
  SELECT
    publication_number,
    DIV(filing_date, 10000) AS filing_year,
    ARRAY(SELECT DISTINCT SUBSTR(c.code, 1, 3) FROM UNNEST(cpc) AS c) AS t3
  FROM `patents-public-data.patents.publications`
  WHERE country_code = 'US'
),
eligible AS (
  SELECT ci.grant_year, ci.qid, ci.filing_year - t.filing_year AS gap
  FROM cites AS ci
  JOIN t ON t.publication_number = ci.tid
  WHERE ARRAY_LENGTH(t.t3) > 0
    AND ci.filing_year > 0 AND t.filing_year > 0
    AND NOT EXISTS (SELECT 1 FROM UNNEST(t.t3) AS x WHERE x IN UNNEST(ci.q3))
    AND ci.filing_year - t.filing_year >= 5
)
SELECT
  totals.grant_year,
  totals.device_queries,
  COUNT(DISTINCT e.qid) AS queries_with_old_cross_field_examiner_targets,
  COUNT(e.qid) AS pairs,
  APPROX_QUANTILES(e.gap, 4)[OFFSET(2)] AS median_gap_years
FROM totals
LEFT JOIN eligible AS e USING (grant_year)
GROUP BY totals.grant_year, totals.device_queries
ORDER BY totals.grant_year
