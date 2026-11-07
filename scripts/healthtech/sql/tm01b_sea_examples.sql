-- tm01b: pick a few US B2 grants of January 2018 that have both examiner (SEA) and applicant (APP) citations, so the
-- SEA meaning can be cross-checked against the public patent pages ("* Cited by examiner"). A 2% table sample keeps the
-- scan small. Returns publication numbers and citation categories only.
SELECT p.publication_number,
  ARRAY(SELECT AS STRUCT c.publication_number, c.category FROM UNNEST(p.citation) AS c
        WHERE STARTS_WITH(c.publication_number, 'US-') ORDER BY c.publication_number LIMIT 12) AS us_citations
FROM `patents-public-data.patents.publications` AS p TABLESAMPLE SYSTEM (2 PERCENT)
WHERE p.country_code = 'US' AND p.kind_code = 'B2' AND p.grant_date BETWEEN 20180101 AND 20180131
  AND EXISTS (SELECT 1 FROM UNNEST(p.citation) AS c WHERE c.category LIKE '%SEA%' AND STARTS_WITH(c.publication_number, 'US-'))
  AND EXISTS (SELECT 1 FROM UNNEST(p.citation) AS c WHERE c.category = 'APP' AND STARTS_WITH(c.publication_number, 'US-'))
ORDER BY p.publication_number
LIMIT 3
