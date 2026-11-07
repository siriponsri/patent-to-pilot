-- tm03: build the Medtech Time Machine (MTM) benchmark in one pass (rules draft:
-- docs/healthtech/research/MEDTECH_TIME_MACHINE_BENCHMARK_RULES_DRAFT_20261107_EN.md).
-- Output rows: role = query | target | distractor, with family-level priority dates, CPC3 sets and English text
-- (title, abstract, first 1,500 characters of the claims). Seeds and sizes follow the draft rules.
-- Queries: the earliest US B1/B2 grant of each family, device CPC subclasses, grant 2010-2016 (dev) or 2019-2023 (test),
-- 2,000 per split by sha256 order. Targets: examiner-cited (SEA) US families, no shared CPC3, >= 1,826 days older by
-- family priority date, with an English abstract. Distractors: US families matched to the targets' (priority year,
-- CPC section) strata, up to 52 per target in each stratum; `in_small_corpus` marks the nested ~10-per-target subset.
WITH us AS (
  SELECT
    publication_number, family_id, kind_code, grant_date, priority_date, citation,
    ARRAY(SELECT DISTINCT SUBSTR(c.code, 1, 3) FROM UNNEST(cpc) AS c WHERE c.code IS NOT NULL) AS c3,
    ARRAY(SELECT DISTINCT SUBSTR(c.code, 1, 4) FROM UNNEST(cpc) AS c WHERE c.code IS NOT NULL) AS c4,
    COALESCE((SELECT SUBSTR(c.code, 1, 1) FROM UNNEST(cpc) AS c WHERE c.first LIMIT 1),
             (SELECT MIN(SUBSTR(c.code, 1, 1)) FROM UNNEST(cpc) AS c)) AS section,
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
first_grant AS (
  SELECT * EXCEPT (rn) FROM (
    SELECT u.*, ROW_NUMBER() OVER (PARTITION BY u.family_id ORDER BY u.grant_date, u.publication_number) AS rn
    FROM us AS u WHERE u.kind_code IN ('B1', 'B2') AND u.grant_date > 0
  ) WHERE rn = 1
),
qcand AS (
  SELECT g.publication_number, g.family_id, g.c3, g.title, g.abstract, g.claims_head, g.citation, f.fam_priority AS q_priority,
    CASE WHEN g.grant_date BETWEEN 20100101 AND 20161231 THEN 'dev'
         WHEN g.grant_date BETWEEN 20190101 AND 20231231 THEN 'test' END AS split
  FROM first_grant AS g JOIN fam AS f USING (family_id)
  WHERE EXISTS (SELECT 1 FROM UNNEST(g.c4) AS x WHERE x IN ('A61B', 'A61F', 'A61G', 'A61H', 'A61J', 'A61L', 'A61M', 'A61N'))
    AND g.title IS NOT NULL AND g.abstract IS NOT NULL AND f.fam_priority IS NOT NULL
),
cites AS (
  SELECT q.publication_number AS qid, q.family_id AS q_family, q.split, q.q_priority, q.c3 AS q3, c.publication_number AS cited
  FROM qcand AS q, UNNEST(q.citation) AS c
  WHERE q.split IS NOT NULL AND c.category LIKE '%SEA%' AND STARTS_WITH(c.publication_number, 'US-')
),
rep AS (
  SELECT * EXCEPT (rn) FROM (
    SELECT u.family_id, u.publication_number, u.section, u.c3, u.title, u.abstract, u.claims_head,
      ROW_NUMBER() OVER (PARTITION BY u.family_id ORDER BY LENGTH(u.abstract) DESC, u.publication_number) AS rn
    FROM us AS u WHERE u.abstract IS NOT NULL AND u.title IS NOT NULL
  ) WHERE rn = 1
),
tgt AS (
  SELECT DISTINCT ci.qid, ci.split, u.family_id AS t_family, f.fam_priority AS t_priority
  FROM cites AS ci
  JOIN us AS u ON u.publication_number = ci.cited
  JOIN fam AS f ON f.family_id = u.family_id
  JOIN rep AS r ON r.family_id = u.family_id
  WHERE ARRAY_LENGTH(u.c3) > 0
    AND NOT EXISTS (SELECT 1 FROM UNNEST(u.c3) AS x WHERE x IN UNNEST(ci.q3))
    AND f.fam_priority IS NOT NULL
    AND u.family_id != ci.q_family
    AND DATE_DIFF(PARSE_DATE('%Y%m%d', CAST(ci.q_priority AS STRING)),
                  PARSE_DATE('%Y%m%d', CAST(f.fam_priority AS STRING)), DAY) >= 1826
),
qsel AS (
  SELECT * FROM (
    SELECT q.*, ROW_NUMBER() OVER (PARTITION BY q.split ORDER BY TO_HEX(SHA256(CONCAT('20261107:', q.publication_number)))) AS k
    FROM qcand AS q WHERE q.split IS NOT NULL AND q.publication_number IN (SELECT qid FROM tgt)
  ) WHERE k <= 2000
),
gold AS (SELECT t.* FROM tgt AS t JOIN qsel AS q ON q.publication_number = t.qid),
tfam AS (SELECT DISTINCT t_family FROM gold),
tstrata AS (
  SELECT DIV(f.fam_priority, 10000) AS y, r.section, COUNT(*) AS n
  FROM tfam AS t JOIN rep AS r ON r.family_id = t.t_family JOIN fam AS f ON f.family_id = t.t_family
  GROUP BY y, r.section
),
dcand AS (
  SELECT r.family_id, DIV(f.fam_priority, 10000) AS y, r.section,
    ROW_NUMBER() OVER (PARTITION BY DIV(f.fam_priority, 10000), r.section
                       ORDER BY TO_HEX(SHA256(CONCAT('20261107:d:', r.family_id)))) AS k
  FROM rep AS r JOIN fam AS f USING (family_id)
  WHERE f.fam_priority IS NOT NULL AND r.family_id NOT IN (SELECT t_family FROM tfam)
),
distr AS (
  SELECT d.family_id, d.k <= 10 * s.n AS small
  FROM dcand AS d JOIN tstrata AS s ON s.y = d.y AND s.section = d.section
  WHERE d.k <= 52 * s.n
)
SELECT 'query' AS role, q.split, q.publication_number, q.family_id, q.q_priority AS priority_date, q.c3,
  q.title, q.abstract, q.claims_head,
  ARRAY(SELECT AS STRUCT g.t_family, g.t_priority FROM gold AS g WHERE g.qid = q.publication_number) AS targets,
  CAST(NULL AS BOOL) AS in_small_corpus
FROM qsel AS q
UNION ALL
SELECT 'target', CAST(NULL AS STRING), r.publication_number, r.family_id, f.fam_priority, r.c3, r.title, r.abstract, r.claims_head,
  ARRAY<STRUCT<t_family STRING, t_priority INT64>>[], TRUE
FROM tfam AS t JOIN rep AS r ON r.family_id = t.t_family JOIN fam AS f ON f.family_id = r.family_id
UNION ALL
SELECT 'distractor', CAST(NULL AS STRING), r.publication_number, r.family_id, f.fam_priority, r.c3, r.title, r.abstract, r.claims_head,
  ARRAY<STRUCT<t_family STRING, t_priority INT64>>[], d.small
FROM distr AS d JOIN rep AS r USING (family_id) JOIN fam AS f USING (family_id)
