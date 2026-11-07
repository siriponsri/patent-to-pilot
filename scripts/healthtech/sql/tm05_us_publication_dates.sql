-- tm05: publication date of every US publication, so the MTM time filter can use "when was this exact text public"
-- (the representative member's publication date) instead of the family priority date. Metadata only, no text.
SELECT publication_number, publication_date
FROM `patents-public-data.patents.publications`
WHERE country_code = 'US' AND publication_date > 0
