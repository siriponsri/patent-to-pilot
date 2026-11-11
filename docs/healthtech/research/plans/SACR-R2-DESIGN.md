# SACR round 2: prospective design and admission requirements

Status: DESIGN_IN_PROGRESS, not an executable experiment freeze. Owner authorized
a new round on 11 November 2026. This document does not reset budgets or reopen
round 1. No R2 model or retrieval outcome has been inspected.

## Problem and intended comparison

R1 stopped at 21 required risk cards over the frozen limit of 20. Its 56 normal
returns contain 14 rejected profiles and seven additional compact lexical flags.
The retained-output audit reproduced the structural classifications; these are
not independently adjudicated semantic errors. Nine rejected profiles had absent
or ambiguous quotations. Source-order and condition-grounding violations also
occurred, and three generations reached their output limit.

The method remains selective functional representation with source-linked
conditions, evaluated against the native dense anchor, generic abstraction,
source-anchor and matched-coverage controls. Replacing it with sentence selection
alone would change the research question and is not an acceptable silent fix.
Structured roles, condition attachment and selective abstraction must remain
explicit and independently screenable.

## Engineering changes

1. Compact composition uses the implemented source-interval union renderer v2.
   It merges repeated references to the same source occurrence, retains distinct
   identical occurrences and source order, includes retained context, and abstains
   on unresolved evidence. This is not a semantic acceptance rule. R1 output and
   renderer remain immutable. Engineering checkpoint and source hash:
   [receipt](../../audits/ptp-sacr-r2-engineering-20261111/checkpoint.json).
2. Source reference generation must disambiguate repeated exact quotations
   prospectively. The engineering candidate is sacr-profile-token-spans-v1: zero-based half-open ranges of maximal non-whitespace source runs. Exact internal whitespace and punctuation are preserved. The source catalogue and prompt are bound by hashes; functional-profile fields remain unchanged. This candidate is implemented and fixture-tested, but not yet frozen for model execution. Any occurrence
   IDs or offsets must bind exact original code-point intervals and source hash;
   no arbitrary first-match choice, fuzzy matching, normalization or post-hoc
   repair is allowed. Fixtures must cover repeated/overlapping quotations,
   Unicode, absent text, wrong source, invalid identifiers and out-of-order blocks.
3. Output length should be reduced through reference representation, not by
   dropping conditions or shrinking the fidelity sample. Any changed prompt,
   schema or decoder gets a new hash and declaration before one synthetic smoke.
4. Full bundle execution remains required: profile, compact, selective and
   declared generic controls, plus same-attempt local critic/cost binding. A
   renderer-only success does not satisfy this gate.

## Sampling, review and exposure

Keep the existing fixed 100 DAPFAM queries and sentinel hash rule. Retained R1
outputs are development evidence, so R2 is a disclosed revision on exposed dev,
not an independent replication. Do not choose replacement queries by failure or
retrieval outcome. All R2 attempts have new immutable identities; preserve old
attempts and costs. No automatic retries or output repair.

The global human ceiling stays 60 cards across configurations and benchmarks.
SACR has at most 30 cards: all required risk cases up to 20, plus 10 hash-selected
unflagged sentinels. Risk above 20 stops the configuration. Any critical error,
including in an automatically passed sentinel, stops and triggers configuration
review. Incomplete judgments never pass. S/G retains its separate 30 allocation;
the conditional MTM transfer is not active until DAPFAM fidelity and pilot pass.
No cards have been issued. Do not silently reuse quota after issuing failed-round
cards or treat owner absence as approval.

## Resource admission

The inspected ledger has 20235.73218671605 seconds of combined fidelity time
remaining, and 250356.84536186745 seconds of GPU time. These are remaining limits,
not a fresh allocation. A complete prospective budget must reserve every R2
generation stage, including controls/critic and shutdown, before dispatch. Use
the existing model, one GPU job, at most 8 CPU threads and 32 GiB RAM; total added
disk remains bounded by 40 GiB. Refresh usage and disk before staging. Do not
launch a profile stage that leaves no feasible allowance for required bundles.

No training, corpus re-encoding, paid API, protected-test access or full-corpus
LLM extraction. Native B0 is reused. S/G needs its own new feasibility declaration
and identical-content S/G comparison; a working Neo4j connection is infrastructure
evidence only, not an extraction or fidelity pass.

## Remaining admission evidence

- Final source-reference format, prompt/schema/decoder hashes and fixtures.
- Complete bundle runner with immutable reservation, normal-return and cost pins.
- One bounded synthetic smoke declaration and verified resource allowance.
- Stage budget proving the fixed cohort and required controls can be attempted.
- Fresh runtime isolation and single-GPU checks before dispatch.
- Human review before retrieval gates; no claim of independent expert review.

Until these exist, new model generation, R2 fidelity measurement, pilot and full
development comparisons remain NOT_RUN. Independent documentation and engineering
work may continue without additional routine approval.

Engineering update: source-token adapter, explicit profile_tokens prompt/validation dispatch and 47 fixtures pass. Independent adapter review found no blocker. Input-token overhead, per-query constrained schema, same-attempt generation/cost replay and complete bundle runner remain pending; do not dispatch from prompt availability alone.
