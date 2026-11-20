# AM-7.1: controls, comparators and selection rule for AM-7

**Status: FROZEN 2026-11-20 (Bangkok), before any E2 number and before any number for a system defined in AM-7 or here.** The freeze commit and sha256 are in `am7/AM-7.1-FREEZE-RECEIPT.json`.

**Authority:** the owner, in chat on 20 Nov 2026: "Freeze AM 7.1 ตาม ผลรีวิว". The review is owner file `12_AM71_REVIEW_AND_GO_DECISION.md` (verdict: GO with conditions, fix items 1-10 and section 4 before freezing).

**Draft and history:** the draft and its discussion are in `am7/AM-7.1-PROPOSAL-20261120.md` (not frozen). This file supersedes that draft.

**Scope:**

- AM-7.1 amends AM-7 (`am7/AM-7-MISSING-REFERENCE.md`) §3-§6 only for the items below.
- α (0.025 per family), the number of confirmatory hypotheses (E1: C1-C3 + C4; E2: D1, D2) and the decision rule are unchanged.
- AM-7 §4.4 is amended explicitly by item 3.

**Known at freeze:**

- AM-7 freeze state.
- PANORAMA label measurement (`am7/panorama-combo-precision.json`).
- Power proxies from systems that had already been reported (`am7/power-proxy-dev.json`).

**Not known at freeze:** any number for U0-conditional, N1-N5, A1-A4, A3, MMR, P\* or the decoy on any block. No TEST data has been read.

**Intended effect:** these changes make C4 and D2 harder to pass on purpose. Credibility is the aim, not a higher pass rate.

## 1. N4: label-free IPC-demotion baseline (review item 3)

**IPC3 sets:**

- IPC3(q) is built by the same rule and from the same source as the task's `dom_ipc3`: the application IPC set used in `oa_temporal_splits.py`.
- IPC3(u), for a Challenge-1M unit, is the union of IPC3 over all of the unit's documents in PatentsView `g_ipc_at_issue` and `pg_ipc_at_issue`.
- shared(u) holds if IPC3(q) ∩ IPC3(u) ≠ ∅.
- A unit with no IPC record has shared = false (it is not demoted).
- IPC coverage is reported for corpus units and for queries, and results are also reported separately for units with no IPC.

**Score:**

- N4(γ): s(u) = cos(q, u) − γ·1[shared(u)], with γ ∈ {0.05, 0.10, 0.20, ∞}.
- γ = ∞ is the hard filter: every shared unit is ranked after every non-shared unit, and units within each group are ordered by cos. The depth stays 1000.

**Versions and parameter choice:**

- N4-E1 is the version without an anchor. N4-E2 uses the same score, and the anchor is only removed from the ranking.
- γ is chosen on P1-DEV for each endpoint separately: OUT R@200 for N4-E1 and MR@200 for N4-E2.
- Ties within 0.001 go to the smaller γ, with ∞ treated as largest.

## 2. MMR: label-free diversification baseline for E1 (review item 4)

**Definition:**

- MMR(λ) is greedy MMR over U0's top-1000: at each step it picks argmax over d of λ·cos(q, d) − (1 − λ)·max over s in S of cos(s, d), where S is the set already selected.
- λ ∈ {0.5, 0.7, 0.9}, chosen on P1-DEV OUT R@200. Ties within 0.001 go to the larger λ.

**Relation to A2, stated before any number:**

- When S = {p(q)}, MMR's ordering equals A2's at γ = (1 − λ)/λ.
- So P\* − L\* separates only the RRF fusion with U0, A1, and the effect of diversifying over many steps.
- The true C4 effect may therefore be smaller than the MDE (section 8).
- C4 is kept anyway.

## 3. N5 co-citation prior and hybrids A4/A4′; AM-7 §4.4 amended (review item 5; section 4)

**Source actions S(q).** S(q) includes every office action in `oa2017` (`citations.csv` rows with citation_in_oa = 1 and action_type 102 or 103) that meets all of these:

- it was mailed strictly before the mail_dt of q's chosen action;
- it does not belong to an application in P1-TEST, P2-TEST or P3-TEST;
- it does not belong to q;
- it does not belong to an application in q's continuity group. The group is the transitive closure of continuity links among OA applications, from the same continuity source as manifest-v2 (ODP release 2026-04-10).

DEV and TEST queries follow the same rule. A TEST query can therefore use earlier actions of TRAIN, VAL and DEV applications, and of applications outside every block.

The graph grows over time (later mail dates give a larger S(q)). This non-stationarity between DEV and TEST is reported, not corrected.

**Score:**

- Cited documents map to Challenge-1M units by the builder's unit mapping.
- N5(u | a) = the number of actions in S(q) that cite both a and u.
- Units with a positive score are ranked first, by score; ties are broken by U0 rank.
- All other units follow in U0 order. N5 therefore falls back to U0 when it has no signal.
- N5 has no tuning parameter.
- Reported:
  - coverage, meaning the share of cohort tasks with at least one positive-score unit other than the anchor;
  - the number of source actions per query.

**Hybrids:**

- A4 = RRF(Ā, N5) and A4′ = RRF(U0, N5), both with k = 60 and depth 1000 per list.
- Ā is the selected stage-2a candidate among A1 and A2 only (section 6).

**AM-7 §4.4 amended:**

- A "trained candidate" means a system with parameters fitted to labels by optimisation.
- N5, A4 and A4′ fit no parameter: they use counts and fixed RRF. They are allowed here as a baseline (N5) and as candidates (A4, A4′) without AM-8.
- Any learned weighting of the co-citation signal needs AM-8.

**Classification and novelty:**

- N5, A4 and A4′ are label-derived, because they use examiner citations of other applications. They are reported that way.
- If A\* is A4 or A4′, the contribution claim moves to "examiner co-citation prior combined with text for cross-domain missing references".
- Co-citation re-ranking has prior work (to be cited after a full-text check): Mahdabi & Crestani CIKM 2014, and TREC-CHEM 2010. Idea A is then not claimed as the method.

## 4. Comparator sets (review items 3-5)

- **N\*** (D2) is the strongest by P1-DEV MR@200 among N1, N2, N3, N4-E2(γ\*) and N5. Ties within 0.001 go to the lower index.
- **C4 = P\* − L\***. L\* is the strongest label-free E1 comparator by P1-DEV OUT R@200 among Z-PatEmbed-large, N4-E1(γ\*) and MMR(λ\*). Ties within 0.001 go to the first listed.
- P\* is built as in AM-7 §4.6, with the A\* chosen in section 6. If A\* contains N5, P\* uses N5 with the pseudo-anchor p(q) under the same S(q) rule.

## 5. Matched decoy anchor (validity, descriptive; review item 7)

**Choosing d(q).** d(q) is picked from U0's top-1000 units u that meet all of these:

- shared(u) holds (section 1);
- u is not in any K(q) row of q (any basis, any domain);
- u ≠ a(q).

Among these, d(q) is the unit that minimises |cos(q, u) − cos(q, a(q))|. Ties go to the unit id. Tasks without a candidate are excluded from this analysis and counted.

**Reporting:**

- Report A\*(q, a) − A\*(q, d) on MR@200 over the cohort, for P1-DEV and for P1-TEST at the single opening.
- Use the AM-7 §5 bootstrap: art unit, B = 10,000, seed 20261119.
- If the 95 % interval includes 0, E2 gains are described as domain or perturbation effects, not as anchor complementarity.

## 6. Selecting A\* (replaces AM-7 §4.5 across candidate types; review item 6)

**Complexity order:** A1 < A2 < A4′ < A4 < A3 < trained (AM-8).

**Step 1, within a type:** the parameter is the one with the highest P1-DEV MR@200. Ties within 0.001 go to the smaller parameter.

**Step 2, across types:**

- The incumbent starts as A1.
- Each later type in the order replaces the incumbent only if both hold:
  - its P1-DEV MR@200 exceeds the incumbent's by ≥ 0.010;
  - the paired 95 % bootstrap interval of the difference excludes 0. The bootstrap is clustered by art unit, B = 10,000, seed 20261119, on the P1-DEV cohort. If A3 is compared, it is done on the AM-7 hash sample of 2,000.
- Ā is the incumbent after A1 and A2.
- A3 still needs an owner envelope (AM-7 §4.3). The 2,000-task sample gives an MDE of about 0.014-0.024 (section 8). With that, A3 can replace the incumbent only if its gain is large.

## 7. Wording and limits (review items 1, 2, 8, 9, 10; section 4)

**PANORAMA label measurement** (`am7/panorama-combo-precision.json`):

- **What is stated:**
  - 73.6 % of co-cited §103 reference pairs (micro; 88.1 % per-action macro) appear together in at least one claim-level §103 rejection.
  - 49.5 % of pairs include the first-listed reference of a §103 reason that lists both.
- **What is not stated:**
  - The 49.5 % is not the probability that the hash anchor is the primary reference.
  - Pairs that are not combined are not called "wrong labels". The AM-7 label is "co-cited under §103 in the same first non-final action".
- **Caveats:**
  - "First-listed = primary" is an ordering heuristic of `parsed_CTNF`, not a legal definition.
  - PANORAMA is a heavily filtered sample from later years, so it is an external estimate only.

**Pre-declared descriptive follow-up on PANORAMA:**

- Stratify pairs by IN×OUT relative to the application. IPC3 for the application and the references comes from PatentsView, matched by number.
- Report micro and per-action macro precision. The E2-aligned headline is the per-action macro on IN×OUT pairs, because E2 is query-macro. Micro is always reported next to it.
- Report P(hash anchor = first-listed) under the AM-7 anchor rule, applied to PANORAMA actions that have an IN reference and an OUT co-reference.
- PANORAMA is not used to build an external validation corpus before stage 2a.

**Contamination:**

- PatEmbed-large was trained (PatenTEB, arXiv:2510.22264) on Lens.org citation pairs. Its retrieval_OUT task (train 150,000) uses disjoint IPC3 and `CITED_BY` positives, with a non-temporal IPC3-stratified split of patents from 1980 onwards.
- This is similar to the P1 OUT definition, not identical: PatenTEB uses Lens citations of all kinds and worldwide families, while P1 uses examiner §102/103 citations in USPTO first actions.
- Training contamination cannot be checked, because the train and validation splits are not public.
- The primary evidence is a descriptive sensitivity: A\* is rebuilt on the Qwen3-Emb zero-shot backbone with the same rule and no new selection. If A\* contains N5, RRF(BM25, N5) is also reported.
- A comparison against the public PatenTEB test split would show only scope and similarity, not training contamination. It is not approved at freeze and is not a gate. Its CC BY-NC-SA 4.0 terms must be decided before any use.

**Other sources:**

- The Patently-O 2026 figures (a mean of 3.08 references; 2-3 references in 65 %) describe the largest §103 combination per final office action in 2026. They are context only.
- arXiv:2605.24297 is not used as a source.

**Literature:**

- No citation audit has been run on AM-7.1.
- One is required before any literature claim here enters a manuscript.
- TRP-Pat (J. Intellectual Property 2025) is the closest known work. "First" and "new task" are not claimed.

**If the results are negative:**

- This applies if E2 gains are explained by N4 or N5: the decoy interval includes 0, or N\* = N5 and D2 fails.
- In that case the E2 finding reported is the benchmark, the measured label precision and the control suite.
- The co-citation result is passed to P2 as a proposed acquisition arm, to be decided in P2's pre-declaration, not here.

## 8. Power and TEST size (review items 4, 6; AM-7 item 5)

**Proxies before any new-system number** (`am7/power-proxy-dev.json`):

- Source: existing P1-DEV per-query OUT R@200 differences between systems that had already been reported.
- Paired SD 0.20-0.34; correlation 0.64-0.85.
- MDE at 80 % power, two-sided α = 0.025, iid (art-unit design effect not included):

| N | MDE |
|---|---|
| 10,000 | 0.006-0.011 |
| 7,600 | 0.007-0.012 |
| 2,500 | 0.012-0.021 |

**Consequences:**

- δ = 0.010 is kept.
- For highly correlated pairs such as P\* and L\* when MMR ≈ A2, the true effect may be below the MDE. This is accepted and reported.
- Power is recomputed from the DEV σ_diff after stage 2a, with the design effect, as AM-7 §5 requires.

**TEST cohort size before opening**, from the TRAIN and DEV rates, out of n₁ = 10,000:

- A-eligible: about 7,360-7,850.
- Clean: about 2,420-2,570.

Observed sizes are reported only once the cohort is built at the single opening.

## 9. Order of work (adds to AM-7 §6)

1. Freeze AM-7.1: commit it and write the receipt.
2. Write the code, with synthetic tests:
   - IPC3 unit table and N4;
   - S(q) builder, continuity-group closure and N5, which must refuse any source action of a TEST-block application;
   - MMR;
   - matched decoy;
   - the selection procedure of section 6.
3. Encode the P1-DEV and VAL queries for PatEmbed and Qwen3-Emb on the approved V100 only (USD 0).
4. Run all baselines and stage-2a candidates on P1-DEV and VAL; select A\*, L\* and N\*; recompute power; report to the owner.
5. Paid stages and TEST follow AM-7 §6 unchanged.
