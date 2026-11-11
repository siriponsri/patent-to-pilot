# S/G R2: explicit action/operand candidate feasibility

Prospective revision authorized by the owner's new-round instruction. R1 remains
failed and immutable. This revision is informed by R1's aggregate low coverage
and lack of exact whole-clause pairs, not by new retrieval scores. No R2 corpus
extraction outcome has been inspected at this declaration.

Use the original pinned100-family sample and45,336-family corpus. Preserve all
four length strata and every empty/failed source. No qrels, query rankings,
protected tests, training, embeddings, model calls or Neo4j imports in this step.
The same sample is exposed development data, not independent validation.

R2 splits explicit statement units at newlines, semicolons and sentence boundaries.
It scans configured/adapted/operable-to cues within each unit. A fixed22-verb list
permits literal action candidates. The operand is the following contiguous text
before declared connectors or punctuation, at most8 words. Decimal punctuation
inside numbers stays intact. Units above4000 characters abstain; retain at most8
records per family and count omitted candidates. No inferred subjects or effects.

Each record preserves exact field hash, unit span, cue, action, operand and full
trailing context. Alias keys use literal action+operand with casefolding,
whitespace collapse and removal of a leading a/an/the only. No stemming, synonyms,
ontology expansion or output-dependent rules. Identical keys are **candidate
links**, not semantic equivalence or compatible conditions: e.g. detection at5kPa
and10kPa can share a key while being incompatible. The compatibility decision
must examine both full source units. Until fidelity review, accepted edges=0.

Enumerate distinct cross-family record pairs sharing a key. Select up to100 pairs
by the existing alias-sampling salt and canonical unordered endpoint IDs. Save
source candidates and sampled pairs privately. Report coverage, all abstention
counts, pair count, costs and failures. Zero cross-family pairs stops this
configuration. Fewer than10 source-bearing families also stops it. Otherwise the
outcome is CANDIDATES_REQUIRE_FIDELITY_SCREENING, never PASS or graph usefulness.

The existing S/G review policy remains binding: all ambiguous source/alias units
flagged after automated triage, maximum20 risk cards plus10 fixed sentinels,
separate SG30 allocation and global60. Source/alias sentinel mix and salts remain
in SG-FIDELITY-SAMPLE.md. No automatic card borrowing. Critical sentinel errors
stop the configuration; missing judgments cannot pass. A positive candidate count
does not justify full-corpus extraction. Such extraction still needs fidelity,
deterministic-only resource projection and the approved limits. S and G must use
identical accepted information; Neo4j availability does not replace these gates.

One extraction pass: CPU wall<=120s, serial execution, output<=128MiB, at most100
selected families,0GPU/model calls. No automatic retry or replacement source.
The runner and configuration hashes are frozen in the R2 audit declaration before
execution. New per-family or alias rules after this outcome would constitute
another configuration, not repair of this one.
