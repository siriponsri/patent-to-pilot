# M16 next actions

Status: `READY_FOR_REVIEW` after offline verification on `2026-10-29`.

1. Obtain or authorize the semantic review source and reviewer role required by `ht-relevance-judgment-cohort-v1`.
2. Use the local task export without changing the frozen 341-pair denominator, exposing split/family metadata, or converting unjudged pairs into negatives.
3. Ingest only explicit, rights-cleared rows with source revision/hash, locator, basis, and adjudicator role; reject product-disclosure promotion.
4. Recompute frozen controls and group-aware diagnostics only after label intake passes the existing validator.

Keep the task export local-only. Do not send Google-derived patent text or other sources lacking explicit provider-transfer permission to OpenRouter. Keep paid HT-B4, Bridge, deployment, outreach, and Claude UX/UI paused.
