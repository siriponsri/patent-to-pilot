# S/G prospective sample and shared review allocation

2026-11-10. One shared extraction/alias configuration for S and G. Sampling fixed before S/G extraction or retrieval outcomes. B0 dev aggregate scores are already known and are not used for sample selection. This is not a claim that the whole study was preregistered before all results.

## Corpus sample

Use only the staged45,336-family TAC corpus with SHA25642f895cd411b344f7be4de4c77bfab66797aa2a1d92353dbee82669fc569af0d. No qrels, IPC-derived relevance, retrieval rankings or protected query files. Compute raw character count as len(title)+len(abstract)+len(claims), without normalization. Sort all records by(length,id), assign stratum floor(4*rank/N), take25 per stratum by SHA256(`ptp-sg-corpus-stratified-v1-20261110|id`),tie by id. Total100unique records. Empty/partial sources remain eligible; no substitutions for extraction failures. Save private selected IDs/lengths/strata and source digest before extraction. Small-fixture rule is all available records up to25 per stratum.

## Alias sample and automated screen

Extractor/schema and exact alias policy must still be frozen before extraction. Only accepted same-role descriptors may connect records; ungrounded synonyms, uncertain condition compatibility and gold/citation-derived mappings cannot create edges. S and G receive identical extraction and accepted-alias bytes.

After extracting the fixed100-source sample, enumerate all proposed cross-record alias pairs, canonicalize unordered endpoint IDs and role, and sort by SHA256(`ptp-sg-alias-sample-v1-20261110|canonical_pair_key`),tie by key. Screen the first min(100,number_of_pairs) without scores. No alias sampling by eventual retrieval benefit. Report total/screened pairs, rejected/unknowns and missing coverage. Any later change in extraction/alias policy is a new configuration, not an in-place repair.

Automatically check exact source spans, role/condition/negation/number preservation and alias provenance/role compatibility. Local-model screening is triage, not an independent semantic oracle. Incomplete/malformed/disagreeing screening is escalated. Confirmed critical defects stop the configuration; no human review can silently waive them.

## Maximum human workload and gates

Owner-approved SG pool is30 cards total across configurations, separate from SACR30; combined60,MTM0. SG risk cards include every unresolved/ambiguous source-record or sampled-alias case; >20 means stop configuration before issuing cards. One alias card contains both grounded endpoints and the proposed relation, so the human can assess compatibility. Deduplicate by immutable review-unit key, never by outcome.

Ten sentinel cards from units automation marked acceptable:8 source records and2 sampled alias pairs. Select each group by SHA256(`ptp-sg-sentinel-v1-20261110|unit_key`),tie by key. If fewer than2 acceptable aliases exist, inspect all available acceptable aliases and fill the remaining sentinel slots with acceptable source records. If fewer than10 total acceptable units exist, stop for insufficient coverage; do not shrink the sentinel requirement. Alias absence may independently make traversal feasibility fail; a valid record extractor does not establish a useful graph.

Persist the complete risk+sentinel reservation in the existing private ledger under review_pool=SG before showing cards. Count all issued cards permanently. Critical error in any sentinel stops and requires configuration review; unresolved/missing human decisions cannot pass. PASS is only automated screening plus limited solo human review, not certified fidelity. No per-query repair or outcome-driven replacement. No full-corpus extraction until these gates and the existing deterministic-only resource projection pass.

Current status: corpus sampling implementation tested; extraction schema/alias implementation/screening NOT_RUN. Sampling itself issues0cards and calls0models.
