-- tm04: uniform ("era-realistic") distractors for the MTM corpus. tm03's matched distractors follow the targets' age
-- profile, so the tm03 corpus has almost no documents with priority after 2012, unlike a real search as of the query
-- date. This draws a uniform sample of US families (English title and abstract, family priority <= 2023-12-31) by
-- sha256 order. Families already in the tm03 corpus are dropped locally afterwards (deterministic).
WITH us AS (
  SELECT
    publication_number, family_id, priority_date,
    ARRAY(SELECT DISTINCT SUBSTR(c.code, 1, 3) FROM UNNEST(cpc) AS c WHERE c.code IS NOT NULL) AS c3,
    (SELECT x.text FROM UNNEST(title_localized) AS x WHERE x.language = 'en' LIMIT 1) AS title,
    (SELECT x.text FROM UNNEST(abstract_localized) AS x WHERE x.language = 'en' LIMIT 1) AS abstract,
    (SELECT SUBSTR(x.text, 1, 1500) FROM UNNEST(claims_localized) AS x WHERE x.language = 'en' LIMIT 1) AS claims_head
  FROM `patents-public-data.patents.publications`
  WHERE country_code = 'US' AND family_id IS NOT NULL AND family_id != '-1'
),
fam AS (
  SELECT family_id, MIN(IF(SAFE.PARSE_DATE('%Y%m%d', CAST(priority_date AS STRING)) IS NOT NULL, priority_date, NULL)) AS fam_priority
  FROM us GROUP BY family_id
),
rep AS (
  SELECT * EXCEPT (rn) FROM (
    SELECT u.family_id, u.publication_number, u.c3, u.title, u.abstract, u.claims_head,
      ROW_NUMBER() OVER (PARTITION BY u.family_id ORDER BY LENGTH(u.abstract) DESC, u.publication_number) AS rn
    FROM us AS u WHERE u.abstract IS NOT NULL AND u.title IS NOT NULL
  ) WHERE rn = 1
)
SELECT 'uniform_distractor' AS role, r.publication_number, r.family_id, f.fam_priority AS priority_date, r.c3,
  r.title, r.abstract, r.claims_head
FROM rep AS r JOIN fam AS f USING (family_id)
WHERE f.fam_priority IS NOT NULL AND f.fam_priority <= 20231231
ORDER BY TO_HEX(SHA256(CONCAT('20261107:u:', r.family_id)))
LIMIT 470000
