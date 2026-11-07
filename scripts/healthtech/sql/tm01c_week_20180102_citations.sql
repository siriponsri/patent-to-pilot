-- tm01c: US B1/B2 grants of 2 January 2018 (the week of USPTO file ipg180102.zip) with their US patent citations and
-- Google citation categories, to compare SEA/APP/TPO with the USPTO XML "cited by examiner/applicant/third party".
SELECT p.publication_number,
  ARRAY(SELECT AS STRUCT c.publication_number, c.category FROM UNNEST(p.citation) AS c
        WHERE STARTS_WITH(c.publication_number, 'US-')) AS us_citations
FROM `patents-public-data.patents.publications` AS p
WHERE p.country_code = 'US' AND p.kind_code IN ('B1', 'B2') AND p.grant_date = 20180102
