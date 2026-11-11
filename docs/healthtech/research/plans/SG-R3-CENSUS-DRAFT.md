# S/G signature census proposal, R3

Current status: OWNER_APPROVED, STAGING, NOT_RUN on corpus. The owner approved
the frozen census declaration in call_33af8d0ad6914c339e4bd430cd25bcaa. See
`../../audits/ptp-r3-preexecution-20261111/owner-approval.json`. Historical proposal
wording below is retained; the frozen declaration and approval govern execution.
No claim of full-corpus linkage or fidelity before the terminal receipt.

Purpose: distinguish source extraction coverage from cross-family linkage
opportunity. The prior100-family sample cannot establish absence of links in
45,336 families. Keep the exact R2 extractor first, without widening its action
vocabulary based on new results, so the census measures that configuration.

## Proposed bounded execution

One streaming pass over the already curated corpus only, pinned by its existing
SHA256 and expected45,336 unique family IDs. No queries, qrels, protected inputs,
models, embeddings or database mounts. Abstract/claims only, current extractor
cap8 records/family; maximum362,688 records. Validate duplicate family/relation
IDs, field types and source/config hashes; any violation stops the run.

Proposed ceiling:1 CPU thread,2GiB RAM,30minutes whole supervisor time including
cleanup,512MiB additional disk,0 GPU/model calls,0 human cards. These are requested
limits, not measured forecasts. Input file is read-only, network disabled; output
is a new exclusive private directory. No automatic restart or resume. Preserve
terminal/partial receipt and elapsed costs if interrupted. A truncated run is
INCOMPLETE and cannot be reported as a full census. An outer supervisor with
hard memory/time/disk enforcement is still required before dispatch readiness.

No row sampling for counts: the proposed census covers all authorized corpus
families. Inspection sampling, if needed after counts, must be declared separately
before reading raw examples and stay inside the existing S/G30-card allocation.
No raw corpus or per-key member list is published. Public output is aggregate:
families, records, keys, key-family-frequency histogram, maximum records/families
per key, and hub count at a fixed threshold of strictly more than100 families.

Count n*(n-1)/2 for each key using distinct family membership. Report the sum as
pair-key incidences, not unique family pairs: a family pair can share multiple
keys. Do not materialize the quadratic pair list. Zero counts are a descriptive
result; nonzero counts are candidate opportunities, not compatible accepted
edges. Neither result bypasses source fidelity and human sentinel gates.

## Matched control

The implemented family-to-key-to-family one-hop traversal and independent
posting-list join return the same candidate set on hand-computable fixtures.
This equivalence follows from the incidence relation; database storage adds no
retrieval mechanism. Keep identical extraction, aliases, seeds, exclusions,
scorer, budget, tie ordering and family aggregation for the S/G control.
Any multi-hop/different-key composition must be separately specified, bounded
and assessed for condition/direction compatibility before asserting an added
traversal effect. Current fixtures do not validate Neo4j execution parity.

## Remaining before combined approval request

Finish retained-sample rejection diagnosis, prepare an immutable runner and
supervisor with failure receipts, estimate actual staged bytes, verify shared
ledger/card journal, and freeze code/input hashes. Pair this request with the
separate SACR complete-pipeline smoke proposal once that implementation is ready.
No resource reservation or corpus read is authorized by this draft.
