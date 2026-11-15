# Paper 1 amendment A2: pre-declaration (written BEFORE any A2 computation)

Date 2026-11-15. Owner approval to prepare: ../owner-paper1-a2-prepare-approval.json.
Nothing in this file was chosen after seeing an A2 result. The S5 dev results (PAPER1-S5-SUMMARY.json) WERE seen; that
is disclosed. The test qrels are sealed and have not been opened.

## Motivation (from S5 dev, descriptive)
FA standalone vs B0 on OUT: arm-only exposure 15 queries, reference-only 32. RRF (k=60) lets the FA list push B0
families out of the top 200, so naive fusion trades gains for losses. Hypothesis: protecting B0's head and using the
arm only to fill the tail keeps B0's exposure and adds the arm's new families.

## Candidate family (fixed now)
Tail fusion T-X(k): keep B0's top-k families unchanged and in order; fill ranks k+1..200 with arm X's ranking in its
own order, skipping families already placed; if the arm list runs out, continue with B0's remaining families.
- X in {FA, GR, SACR, shuffle} (the same panels as S5: arm ranking where used, reference ranking on fallback).
- k in {50, 100, 150}. 12 variants. No other variants will be computed.

## Selection rule on dev (fixed now)
Choose k* for FA only:
1. eligible k: dev IN Recall@200 of T-FA(k) minus B0 >= -0.010 (half the frozen 0.020 harm margin);
2. among eligible k, the largest dev OUT Recall@200 of T-FA(k);
3. ties (equal to 5 decimals): the larger k (closer to B0);
4. if no k is eligible: A2 is reported as "no admissible tail fusion on dev" and is NOT carried to test.
The same k* is then used for T-GR, T-SACR and T-shuffle (matched controls). No re-selection after this.

## What would be frozen for test (only after the second owner approval)
Secondary, pre-specified, outside the H1-H3 gatekeeping (which is unchanged and reported first):
- S1: T-FA(k*) vs B0, OUT Recall@200, superiority (same cluster bootstrap 10k, seed 20261113, alpha 0.05 two-sided).
- S2: T-FA(k*) vs T-GR(k*), OUT Recall@200, superiority.
- Multiplicity: Holm across S1 and S2.
- Harm: IN and ALL Recall@200, T-FA(k*) vs B0, non-inferiority margin 0.020.
- Descriptive: T-SACR(k*), T-shuffle(k*) (C2-style control), exposure strata, all secondary metrics.
- Interpretation with the frozen delta 0.010 (superior / inferior / practically equivalent / inconclusive).

## Constraints
CPU only; no new generation, no GPU, no corpus re-encoding; uses the S5 dev rankings already produced; dev qrels only.
