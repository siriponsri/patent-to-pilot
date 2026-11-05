# Cross-industry solution atlas: headroom check plan (dev only), 6 Nov 2026

Status: pre-declared before any headroom number was computed. The owner approved this direction on 6 Nov 2026.

## 1. Question

The IPC3-masked dense search already holds every possible strict-OUT target in its candidate set. Within that search, does knowing **which** far classes hold the cross-domain prior art leave enough room to change what an analyst reads in the first 20–50 results?

## 2. Data

- DAPFAM, Stage 0 split, dev only: 474 queries, 349 strict-OUT eligible. The test split is not read.
- **Primary ranking:** brief P under the IPC3 mask (`rankings-x-P-dev.jsonl` from the feasibility check).
- **Secondary rankings:** brief T under the mask; full-patent dense under the mask.
- **Classes:**
  - query classes are the `own_ipc3` used by the mask;
  - target classes come from the Stage 1 `family-ipc3` file (sha256 `b401e1d0…`).

## 3. Measures

**Reordering.** All reorderings are stable partitions of the existing masked Top-200: families with any IPC3 code in a class set C come first, in their dense order, and the rest follow. Recall@200 cannot change, so the endpoints are Recall@20 and Recall@50.

1. **Oracle bound.** C is the set of IPC3 classes of the query's own strict-OUT positives. This is an upper bound only, since it uses the labels.
2. **Learned prior (cross-fitted).**
   - A class-transition prior is learned from the strict-OUT pairs of the other folds.
   - For each training pair (q′, t), weight 1 / (|own(q′)| · |ipc3(t)|) is added to every (own class of q′ → class of t) cell.
   - A query's score for class c is the sum over its own classes; its own classes are excluded.
   - C is the top m = 5 classes; m = 3 and 10 are reported as well.
   - Folds: 5, stratified by first-IPC section, seed `20261105` (the same as Amendment 1).
3. **Concentration (descriptive).**
   - target classes per query;
   - normalized entropy of target classes by first-IPC section of the query;
   - share of strict-OUT pairs covered by each section's top 5 target classes.

**Statistic.** Paired query bootstrap, 5,000 resamples, seed `20261105`.

## 4. Gates

| Status | Condition on brief P | Consequence |
|---|---|---|
| **STOP** | Oracle R@50 − masked R@50 < 0.02 | The atlas direction stops before any external data is downloaded |
| **GO_ORACLE_ONLY** | Oracle gate met, but the learned-prior R@50 gain (m = 5) has 95% lower bound ≤ 0 | Headroom exists but dev-only counts are too sparse. Owner decision on building the external citation prior |
| **GO** | Oracle gate met and learned-prior R@50 gain (m = 5) has 95% lower bound > 0 | Write a pre-declared feasibility plan with an external citation prior; test stays closed |

R@20, brief T and the full patent are secondary, with no decision attached.

## 5. Limitations noted in advance

- **Shared targets across folds.** The giant shared-target component means other folds can contain the same targets. The cross-fitted prior counts classes, not family identities, but it is still somewhat optimistic. An external prior built from citations that exclude DAPFAM families removes this.
- **Within-list reordering only.** Reordering cannot recover targets missing from the masked Top-200. A real class-restricted search could go deeper.

## 6. Compute

CPU only, a few minutes. No GPU, no paid calls, no new data.
