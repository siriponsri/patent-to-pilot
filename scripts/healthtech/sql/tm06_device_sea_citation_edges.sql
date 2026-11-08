-- tm06: examiner-citation edges of earlier US device grants, for the MTM phase-3b citation-reuse gating probe
-- (methods log, phase 3b). No text, no labels. Citing grants: US B1/B2, granted 2001-01-01..2016-12-31, with a
-- device CPC subclass (A61B/F/G/H/J/L/M/N). Edges: their examiner (category contains SEA) citations to US
-- publications, mapped to the cited family. Output: one row per distinct (citing family, citing grant date,
-- cited family).
WITH citing AS (
  SELECT p.family_id AS citing_family, p.grant_date AS citing_grant, p.citation
  FROM `patents-public-data.patents.publications` AS p
  WHERE p.country_code = 'US'
    AND p.kind_code IN ('B1', 'B2')
    AND p.grant_date BETWEEN 20010101 AND 20161231
    AND p.family_id IS NOT NULL AND p.family_id != '-1'
    AND EXISTS (SELECT 1 FROM UNNEST(p.cpc) AS c
                WHERE SUBSTR(c.code, 1, 4) IN ('A61B', 'A61F', 'A61G', 'A61H', 'A61J', 'A61L', 'A61M', 'A61N'))
),
edges AS (
  SELECT ci.citing_family, ci.citing_grant, c.publication_number AS cited_pub
  FROM citing AS ci, UNNEST(ci.citation) AS c
  WHERE c.category LIKE '%SEA%' AND STARTS_WITH(c.publication_number, 'US-')
),
fam AS (
  SELECT publication_number, family_id
  FROM `patents-public-data.patents.publications`
  WHERE country_code = 'US' AND family_id IS NOT NULL AND family_id != '-1'
)
SELECT DISTINCT e.citing_family, e.citing_grant, f.family_id AS cited_family
FROM edges AS e
JOIN fam AS f ON f.publication_number = e.cited_pub
