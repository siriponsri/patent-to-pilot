-- tm01: schema check for the medtech time-machine data plan.
-- Counts citation type/category values on US granted utility patents of January 2018,
-- to confirm whether examiner-cited references can be told apart. Aggregates only.
SELECT
  c.type AS citation_type,
  c.category AS citation_category,
  COUNT(*) AS n
FROM `patents-public-data.patents.publications` AS p,
  UNNEST(p.citation) AS c
WHERE p.country_code = 'US'
  AND p.kind_code IN ('B1', 'B2')
  AND p.grant_date BETWEEN 20180101 AND 20180131
GROUP BY citation_type, citation_category
ORDER BY n DESC
