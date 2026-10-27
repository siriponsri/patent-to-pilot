# Next actions — HealthTech

Record: HT-NEXT-001 · Scope: research/patent-to-pilot · Date: 2026-10-27 · Status: OBSERVED_LOCAL / DECISION

Supersedes NEXT-004 as the current work order. Owner supplied the HealthTech Pack and authorized migration, recoverable cleanup and commit/push to main. Paid model runs/deployment remain outside this task

Implemented: HT-W01 alignment, HT-W02 contracts/schema, HT-W06 known-link evaluator/source integrity, local 510(k) snapshot adapter, offline lexical/fixed-query synthetic dossier runner. These are engineering slices, not completed HT-G2/G3 or a scientific benchmark See [progress](../docs/healthtech/progress.json) and [verification](../docs/healthtech/verification.json)

Completed package: local SciFact reader/evaluator with runtime/gold split, bounded openFDA 510(k) inputs for K190167/K163345/K121849, three fresh bilingual public-source dossier drafts, local source/history inspection, and an HT-specific API dry-run. Guarded public and all suites both pass 269/269 with zero network attempts, credential-file reads, provider calls, and paid cost. See [pre-live receipt](../docs/healthtech/PRELIVE_OFFLINE_RECEIPT_2026-10-27.md). These are engineering outputs, not scientific benchmark or publication results

Next ready package: W05/W12 rights-cleared patent corpus for one real public named device, with frozen cohort/provenance rules and disclosed-link evidence. Keep W04 official evaluator integration as a separate engineering package. Do not reuse the synthetic fixture as a real device result

Main Bridge study: BLOCKED_LOCAL on reuse rights/cohort reconciliation/split reproducibility. Source: pack audit at upstream `f3990a207949f25012d1070a08ac303e140387e6` plus PDF P01; it was not reexecuted here Resume after permitted-use terms and chosen cohort/group rules are recorded. Other work continues

Remaining: rights-cleared patent corpus and disclosed-link cases, official SciFact evaluator integration, fixed hybrid/reranker validation, adaptive policies/LLM controller, full resource accounting for live inference, no-code TH/EN UI, persistent service-backed edit history, scientific/user/commercial evidence and manuscript. Do not infer DONE from file names or passing engineering tests

Audit follow-up: public regression selection now includes all published provider security modules; paired tests use mock-seeded tmp journals. Original 262-local/185-clean receipt remains a dated record. See `docs/healthtech/REPRODUCIBILITY_AUDIT.md` for corrected clean-checkout evidence. Research/product next actions above are unchanged.
