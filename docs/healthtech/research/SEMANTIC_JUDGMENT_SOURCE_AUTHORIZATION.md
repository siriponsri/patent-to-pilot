# Semantic judgment source authorization

This is an owner-facing preflight for a future HT-T1 semantic device–patent
judgment source. It is not a request to acquire data, an approval to contact a
provider, or a source of labels. The validator accepts only an authorization
manifest and creates no judgments.

## Required authorization manifest

Use `ht-semantic-source-authorization-v1` and provide:

- Source identity: `source_id`, pinned `source_revision`, SHA-256, locator, and source class.
- Rights decision: source-specific `rights_policy_id`, rights basis, exact clause or terms, intended use `semantic_relevance_judgment`, local-use decision, attribution requirement, and explicit denial of provider transfer and public redistribution unless separately authorized.
- Acquisition bounds: retrieval method, resumable acquisition, expected/max bytes, expected/max files, relative storage paths, and separate raw/normalized artifacts.
- Judgment contract: only `relevant` and `not_relevant`; exact source locators and adjudicator roles required; absent pairs remain `unjudged_not_negative`.
- Study design: at least two independent company groups, at least two independent family groups, predeclared untouched final holdout, and reject-on-leakage policy.

## Acceptance sequence

1. Validate the authorization manifest with `scripts/healthtech/validate_semantic_source_authorization.py`.
2. Acquire only within the approved storage and byte/file bounds; record raw and normalized hashes plus resumable attempt receipts.
3. Bind the source manifest to `ht-relevance-judgment-cohort-v1`.
4. Ingest explicit reviewer rows through `scripts/healthtech/ingest_relevance_judgments.py` with the same authorization manifest; the CLI rejects missing or mismatched authorization bindings.
5. Rerun HT-B0a/B0b/B1/B2/B3 only after the judgment manifest, frozen denominator, groups, and untouched holdout validate.

The preflight does not authorize paid inference, provider transfer, public
redistribution, clinical/FTO work, or promotion of product disclosures to
semantic gold.
