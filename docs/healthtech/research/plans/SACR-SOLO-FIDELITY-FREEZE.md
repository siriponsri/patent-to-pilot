# Native SACR solo fidelity protocol v1

Status: prospective screening specification, 10 November 2026. Frozen before any
native SACR generation or new SACR retrieval outcome. B0 dev aggregate scores
have already been inspected; this is not whole-study preregistration.

## Population and review budget

Use the existing fixed 100-query sample from the 474 native TA dev queries.
The private sample SHA256 is
`cf0bce973696c6d71c06d2387a36bd024b0ddbdc2a36a2c77bc6ce17ba4bd767`.
Selection sorts ascending by SHA256 of UTF-8
`sacr-v0-fidelity-20261110|DAPFAM|<query_id>`, then query ID, taking 100.
Do not replace failed, long, empty or difficult queries. No qrels, rankings,
scores, protected input or corpus search enters sampling or screening.

One SACR configuration uses at most 30 human cards cumulatively: every flagged
or unassessable query, at most 20, plus exactly 10 unflagged sentinels selected
by ascending SHA256 of `sacr-solo-sentinel-20261110|DAPFAM|<query_id>`, then ID.
A card bundles the exact source, profile, compact and selective/generic views
for one query; it is not a separate card per view. Complete the bundle before
issuing cards. Do not use early profile-only review to claim later views passed.
More than 20 flagged queries or fewer than 10 unflagged queries stops this
configuration without issuing an incomplete review set or sampling away risk.

The separate S/G pool remains 30 cards, total 60 across all configurations;
MTM allocation is zero. No automatic transfer, refund or reissue. Reuse the
existing durable card ledger, never replace it. S/G's failed fixed feasibility
configuration does not release its allocation.

## Automated screening, before any SACR retrieval scores

1. Bind source/sample/prompt/model/decoder/output hashes and normally returned
   generation records. Infrastructure errors or unknown termination stop the
   dependent run. Completed unusable outputs remain rejected, charged and
   retained, without repair, regeneration or query deletion.
2. Apply existing schema, exact quotation, source-order, role/condition and
   identity validation. Preserve raw output and canonical alignment separately.
   Derive compact text deterministically; do not edit it based on screen results.
3. For each proposed retrieval view, record the existing lexical checks for
   numeric/polarity inventories, source-backed protected phrases, length and
   novel vocabulary. A lexical discrepancy flags the query for review; it is
   not, by itself, proof of a semantic error. Any structurally unusable required
   artifact, unresolved profile or absent bundle is unassessable and flagged.
4. Run one local Qwen3-8B critic call per complete query bundle, maximum 100,
   using the existing pinned weights, fp16/eager, greedy non-thinking decoder.
   The critic sees only the exact allowed TA source and generated bundle. It
   sees no qrels, retrieved documents, scores, or pass-rate targets. Use the
   versioned `sacr_fidelity_screen_v1.txt` prompt. Input limit 8192, output limit
   4096, context 40960, response 65536 bytes; no truncation, retries or repair.
   Missing, over-limit, malformed, non-EOS or ambiguous critic results flag the
   query. If artifact generation fails, record unassessable without a substitute
   critic call; every planned query remains in the denominator.
5. A query is unflagged only when all structural/lexical checks pass and the
   critic reports `supported` for every required dimension. Model allegations
   require human judgment and cannot be upgraded to independently confirmed
   errors. No automatic screen result alone is a semantic PASS.

Dimensions: relation/role/direction preservation; quantities/units/comparisons;
polarity and exceptions; attachment of explicit conditions; coverage of all
essential functional requirements; support for normalized or abstracted terms;
preservation of material/anatomical context where removal changes meaning.
Exact copies can still omit essential constraints. Existing vocabulary can
still reverse roles or invent relations. Do not equate compression with fidelity.

## Human gate and stop rules

Owner sees source/output cards and reasons before any new SACR scores. Record
`faithful`, `unsupported`, `ambiguous` or `unassessable` for each whole bundle.
Critical error means an unsupported/reversed functional relation, changed
quantity/unit/comparison/polarity, lost essential condition, incorrect attachment,
or context removal that changes the technical requirement. A critical error in
any card, including an automatic-pass sentinel, stops and requires configuration
review. Do not conclude PASS from the remaining cards or repair only that query.
Any pending/ambiguous/unassessable judgment means INCOMPLETE_NO_PASS.

Only complete automated screening, exactly the required reserved card set,
all faithful human judgments, and zero confirmed critical errors yield
`SOLO_SCREEN_AND_SENTINEL_GATE_PASS`. This gate authorizes only the next already
approved dev stage. It does not certify all corpus/query semantics or authorize
test access, a new configuration, or further generation retries.

## Resource and interpretation limits

All profile, generic, selective and critic generation share the existing 8-hour
fidelity cap, within the cumulative 72-hour GPU ledger. Stage declarations must
reserve disjoint remaining budget before dispatch; no stage resets the ledger.
Use one GPU job at a time and the established runtime isolation. This document
does not itself dispatch a job. Pin prompt/code hashes with each declaration.

Same-model self-critique has correlated blind spots; greedy output is not an
independent expert review. Ten sentinels offer limited coverage, and literal
rules cannot establish entailment. Report all failure/flag rates and costs,
remaining uncertainty, owner review workload and any stopped configuration.
No general fidelity or retrieval-benefit claim follows from this limited gate.
