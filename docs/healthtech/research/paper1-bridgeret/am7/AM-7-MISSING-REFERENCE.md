# AM-7: second co-primary endpoint, missing-reference recall (Idea A)

**Status: FROZEN 2026-11-20 (Bangkok), before any missing-reference number exists for any system.** The freeze commit and the sha256 of this file are recorded in `am7/AM-7-FREEZE-RECEIPT.json`.

This amendment applies to `docs/healthtech/research/plans/P1-BRIDGERET-PREDECLARATION.md` (the pre-declaration and AM-1..AM-6). Every rule there stays in force unless this file changes it.

**Authority:**

- Owner note `docs/owner/owner-note-20112026/10_P1_RETHINK_IDEA_OPTIONS.md`, decisions 1-2.
- Owner chat instruction of 20 Nov 2026: run the CPU label check; if it passes, write and freeze AM-7 with a dual endpoint of the original OUT R@200 and missing-reference recall.

**Gate evidence:** `am7/OA-COCITE-CHECK-PREDECLARATION.md` was declared at commit 30a60b3c, before the check ran. The result is `am7/oa-cocite-check.json`:

- Outcome **SUFFICIENT**; all of G1-G3 pass.
- P1-DEV: 20,857 A-eligible tasks, 6,823 of them clean.
- TRAIN: 73,897 A-eligible tasks.
- VAL: 1,576 A-eligible tasks.

**Known at freeze:**

- Every P1-DEV/VAL OUT/IN/ALL number in `ft-grid30k/sstar-grid30k.md` and the AM-6 tables. These are descriptive.
- The label counts above.

**Not known at freeze:** any E2 number, any number for the new systems defined below, any TEST data.

## 1. Why

The registered E1 task scores each cited document on its own. A §103 rejection usually combines references, and Paper 53 and the P1 grid both show that single-document similarity misses cross-domain (OUT) prior art. E2 asks a question that sits closer to examination practice: given the application and one co-cited reference that has already been found, does the system retrieve the cross-domain reference that the examiner combined with it?

## 2. Unchanged

The following are carried over without change:

- the split (manifest-v2 `c8443600…`);
- Challenge-1M and its sealed P1-TEST gold;
- the text serialisation (§3);
- RPD visibility (a unit is a target only if `first_pub < filing_date(q)`, and never q's own unit);
- the E1 definition (§2): conditional OUT Recall@200 over P1-TEST tasks;
- the S\* rule and S\* = S2-t0.02 (AM-5);
- the comparators;
- the bootstrap design (§5);
- the unseen-document rule;
- the seen-family stratum;
- the isolation rules (§6).

The S\* checkpoint used in C1-C3 is S\*-full if the owner approves the full-TRAIN retrain and it finishes before the TEST freeze, and S\*-30k otherwise. This choice does not depend on any S\*-full DEV number.

## 3. E2 task and label

**Cohort (A-eligible).** A task q joins the cohort when its C103(q) holds at least one IN3 unit and at least one OUT3 unit.

- **C103(q)** is the set of units of q that pass all of these:
  - the basis is 103 or both;
  - the unit is present and its first_pub is known;
  - first_pub < filing_date(q);
  - the unit is not q's own unit;
  - the unit is in Challenge-1M.

This is the same definition the check used (`scripts/healthtech/oa_cocite_check.py`).

**Anchor a(q).** The anchor is the IN3 unit of C103(q) with the smallest `sha256('p1-am7-anchor-v1|' + app_id + '|' + unit)`. It is chosen by hash and does not depend on any system. The anchor is "an IN co-reference". The OA data do not record which reference was primary.

**Targets T(q).** The targets are the OUT3 units of C103(q). They are disjoint from the anchor by construction.

**System input.** The system receives two things:

- the query application text (§3 serialisation);
- the anchor unit, as its Challenge-1M passage and vector.

The anchor unit is removed from every ranking before scoring.

**Primary E2 metric: missing-reference Recall@200 (MR@200).** For each query, MR@200 = |T(q) ∩ top-200| / |T(q)|. The metric is the query-macro average over the cohort. A query with no output scores 0.

**Secondary E2 metrics (descriptive):**

- MR@50 and MR@1000;
- MRR of the first target;
- MR@200 on the **clean** subset: n103_all = cite103_max ≥ 2, so one 103 rejection cites every 103 reference of the action;
- strict MR@200: the denominator also counts 103 OUT3 cited units that are absent from Challenge-1M;
- an all-co-reference variant: targets = C103(q) minus the anchor, IN and OUT;
- strata by |T(q)|;
- the unseen-document subset.

**Label limits (stated in every report):**

- The label is "co-cited under §103 in the same first non-final action".
- `rejections.csv` holds one row per action type per action (99.9 % of eligible P1-DEV actions have exactly one 103 row). The row count therefore says nothing about combinations, and references cannot be linked to claim numbers.
- The clean subset is the only same-rejection proxy.
- Not-cited is not a verified negative.

## 4. Systems

All systems use PatEmbed-large, run the same way as Z-PatEmbed (same model, prompts and query serialisation):

- corpus vectors: `bridgeret/runs/z-patembed/passages.f16.npy` (1,000,000 × 1024, rows as in `units.json`);
- query vectors: re-encoded with the identical Z-PatEmbed settings;
- vectors are L2-normalised and scored by cosine;
- ties are broken by unit id.

### 4.1 E2 baselines (never candidates)

- **U0**: Z-PatEmbed with the query only; the anchor is ignored, apart from being removed from the ranking.
- **N1**: the anchor only; rank by cos(a, d).
- **N2**: RRF(U0, N1), k = 60, depth 1000 per list.
- **N3**: the sum vector normalize(q + a).
- **N\***: the strongest of N1-N3 by P1-DEV MR@200. Ties go to the lower index.

### 4.2 E2 candidates, stage 2a (training-free, USD 0)

- **A1(β)**, complement query: q′ = normalize(q − β (q·a) a), β ∈ {0.5, 1.0}. This removes the part of the query that the anchor already covers.
- **A2(γ)**, anchor-repelled score: s(d) = cos(q, d) − γ · cos(a, d), γ ∈ {0.25, 0.5}.

### 4.3 E2 candidate, stage 2b (GPU)

- **A3**: a conditional zero-shot cross-encoder.
  - Model: Qwen3-Reranker-0.6B @ the pinned revision in `b53-readiness-20261119.json`.
  - Pool: re-ranks the top-200 of the best stage-2a candidate.
  - Instruction: `Given a patent application and a prior-art reference already cited against it, judge whether the document is a second reference that supplies what the first reference lacks`.
  - Input:
    - query = application text + "\nFirst reference: " + anchor text, with the anchor tail truncated first to fit 1,024 tokens;
    - document = passage text, 512 tokens.
  - Feasibility rule: A3 runs only after the owner approves a GPU envelope for it. If it does not run, it is not a candidate, and this is reported.
  - On DEV, A3 is scored on a hash sample: 2,000 cohort tasks ordered by `sha256('p1-am7-dev-sample-v1|' + app_id)`.

### 4.4 Trained candidates (stage 3)

Trained candidates are allowed only through AM-8. AM-8 must be committed before the first DEV number of any trained system, and it may not change sections 3, 5 or 6.

### 4.5 Selecting A\*

**A\*** is the executed candidate with the highest P1-DEV MR@200.

- The comparison set is the full DEV cohort. If A3 runs, all candidates are compared on the A3 hash sample instead.
- Ties within 0.001 go to the simpler candidate: A1 < A2 < A3 < trained. Remaining ties go to the smaller parameter.
- Only P1-DEV is used for the choice. VAL is reported.

### 4.6 New E1 system P\* (label-free, no new selection)

P\* tests whether Idea A also helps the original task without any label input.

- The pseudo-anchor p(q) is U0's top-1 unit for q.
- P\* = RRF(U0, A\*(q, p(q))), k = 60, depth 1000 per list. For A3, the pool is A\*'s stage-2a base list built with p(q).
- P\* is fixed by A\* and is never chosen on E1 numbers.
- E1 DEV numbers for P\*, and P\*'s IN R@200 harm (margin −0.020, descriptive), are reported.

### 4.7 Controls (descriptive)

- **Shuffled anchor**: A\* given an IN3 anchor from a different cohort task, taken by hash: the task whose `sha256('p1-am7-shuffle-v1|' + app_id)` follows q's in sorted order. This tests whether a gain comes from the anchor's content rather than from the perturbation itself.
- **Best-found anchor**: the IN3 unit of C103(q) that U0 ranks highest. This is a semi-oracle and is reported only.

## 5. Confirmatory families on P1-TEST (opened once, owner go unchanged)

Two co-primary families are tested, each at α = 0.025, with Holm within each family. The family-wise error over both is ≤ 0.05 (Bonferroni). The decision rule is unchanged from §5: for each contrast, the Holm-adjusted bootstrap lower bound must be > 0.

**Family E1, OUT R@200 over the registered P1-TEST population:**

- C1-C3 as amended by AM-1/AM-3. When C1 and C2 coincide, the family is {C1, C3}, as AM-3 states.
- **C4 = P\* − Z-PatEmbed-large.**

**Family E2, MR@200 over the TEST A-eligible cohort:**

- **D1 = A\* − U0**
- **D2 = A\* − N\***

**Shared design:**

- paired cluster bootstrap by art unit, B = 10,000, seed 20261119;
- sign-flip permutation as a check;
- practical-effect target δ = 0.010 for every contrast;
- the unseen-document and seen-family rules of §5 apply to all contrasts.

**TEST cohort:**

- The TEST cohort, anchors and targets are built only at the single TEST opening, by the frozen anchor code, from `sealed/qrels-p1-test.tsv`. That file already carries `basis` and `dom_ipc3`.
- The TEST clean flag needs the OA tables for TEST apps and is computed in the same opening. No TEST field is read earlier.
- The DEV-rate estimate is about 7,800 A-eligible and about 2,600 clean of n₁ = 10,000.
- Power is recomputed from the DEV σ_diff after stage 2a, as in §5.

## 6. Order of work and gates

1. Freeze this file: commit it, then record the receipt with sha256.
2. Write the code and test it on synthetic data: the anchor/cohort builder; the E2 evaluator, which refuses TEST blocks before the TEST opening; the stage-2a scorer.
3. Encode the P1-DEV and VAL query vectors with PatEmbed-large on the approved V100 only, under the GPU lock and alongside B53. USD 0.
4. Run stage 2a and all baselines on P1-DEV/VAL, report descriptively, then select A\* if no stage 2b or 3 follows.

   Owner gate (descriptive, not a protocol stop): if no stage-2a candidate beats both U0 and N\* by ≥ 0.010 on DEV MR@200, report to the owner before any paid step.
5. Stage 2b and stage 3 run only with an owner-approved envelope. Stage 3 also needs AM-8.
6. TEST opens once, with the owner's explicit go, after A\* and P\* are frozen with their config and hash records.

## 7. Cost

- Steps 2-4 of the work order (code, query encoding, stage 2a) run on CPU and the V100, at USD 0.
- Stage 2b needs a new envelope. Its cost will be measured on 50 DEV queries before any request is made.
- The remaining P1 FT envelope (USD 11.46) is not used by AM-7.
