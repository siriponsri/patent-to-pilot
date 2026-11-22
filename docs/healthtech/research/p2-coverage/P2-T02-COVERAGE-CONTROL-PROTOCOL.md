# P2-T02 coverage control: complete-content and stronger simple controls (P1 DEV). FROZEN before any P2-T02 number

**Plan:** owner note 22 Nov 2026, phase P2, task P2-T02 (`METHOD_AND_BASELINES.md` §1; `SCORE_AND_STATISTICAL_CONTRACT.md`).
**Input evidence:** [P2-T01 content coverage audit](../../../tracking/owner-note-22112026/receipts/P2-T01_content_coverage_audit.md).
**Frozen:** 22 Nov 2026. The commit that adds this file is the freeze; no P2-T02 number existed before it. Changes go into a
dated amendment.

## 1. Why

P2-T01 found a real content gap:
- every route indexes only title + abstract + the **first** independent claim;
- that text is capped at 512 tokens, which cuts 7–17% of units;
- the current text holds a median of about 12% of a document's claim tokens;
- BM25 inherits Arctic's truncation;
- the other claims, with resolvable dependency structure, are on disk but never indexed.

The owner's ladder therefore requires an equal-content representation control **before** any acquisition policy is credited.
This is an **engineering control**. A gain here means "more eligible text was indexed" (or "structure helped" only if the
structural arm also beats the equal-content flat arm). It is not evidence for the acquisition method.

## 2. Data, blocks and isolation

- **Corpus:** the Challenge-1M 1M-unit corpus (`challenge1m/out-v1`), with unchanged units, eligibility and masks.
- **Blocks:** **P1-DEV only** (26,575 tasks; 25,626 with query text).
  - **VAL is not used in P2-T02**, so that the next decision (P2-T05) still has a VAL look available. VAL has already been
    seen 3 times in G03.
  - No TEST block, `sealed/` or test label is opened. Every script refuses TEST blocks.
- **Evaluator:** unchanged `eval_bridgeret_dev.py`. Positives are cited units first published before the filing date;
  the own unit is excluded; IN/OUT is by `dom_ipc3`; the mean is query-macro; a missing query scores 0.

## 3. Corpus representations (index side only; queries unchanged)

Content source per unit:
- title and abstract as in `texts-v1`;
- the **claims of the same publication that supplies the unit's current text**: the pre-grant publication where the
  unit uses it, otherwise the grant;
- PatentsView claims files (`patentsview/claims`), live claims only (cancelled rows dropped), in claim-number order.

Using grant claims for a unit whose indexed text is the pre-grant publication is **forbidden**: they may be published after a
query's filing date, which would leak through the date mask.

| Arm | Content | Units for retrieval | Aggregation |
|---|---|---|---|
| **C0** current | title + abstract + first independent claim, 512-token cap (existing runs) | 1 per unit | — |
| **C1** flat, complete content | the same full text as C2 (title + abstract + all live claims), cut into fixed **512-token windows** (no overlap) in reading order | passages | **max-p**: unit score = best passage score |
| **C2** structural, complete content | passage 0 = title + abstract. Then **one passage per independent claim, followed by its dependent claims** (dependency from PatentsView `dependent`, regex fallback). A claim group over 512 tokens is split into 512-token windows that each repeat the independent claim's first 64 tokens as parent context | passages | max-p |

**Equal content:** C1 and C2 are built from the identical token sequence per unit, apart from C2's repeated parent context,
which is counted and reported. Multiplicity is controlled by max-p: a unit contributes at most one score.
- **Query side:** unchanged; the same query texts as the `z-*` routes (title + abstract + first claim, 512 cap).
- **Masks:** filing-date mask and own-unit mask exactly as in `dense_bridgeret_v3.py`, applied at unit level after
  aggregation. Top 1,000 units per query.

## 4. Routes

1. **Arctic** (`Snowflake/snowflake-arctic-embed-m-v2.0`, the `z-arctic` settings and prompts, 512-token windows). This is the
   cheapest dense route (about 4.5 h estimated per complete-content arm on the V100). It builds C1 and C2.
2. **BM25 full text** (C1 content as a whole document, not truncated; the `bm25_bridgeret.py` scoring and masks unchanged),
   compared with BM25 C0 (Arctic-truncated, existing run).
3. PatEmbed and Qwen3 complete-content arms are **not** run in this task. If Arctic shows a coverage effect, they become a
   declared follow-up.

**Hardware:** V100 device 1 only, under the shared GPU lock, with memory fraction ≤ 0.12, because another user's service
holds about 24 GB. CPU retrieval. Spend: USD 0. Indexing time, disk and peak memory are logged separately from query time.

## 5. Endpoints and decision (P1-DEV, single route at depth 200)

- **Primary:** ALL R@200 per route, query-macro (evaluator definition).
- **Paired contrasts** use the cluster bootstrap by examiner art unit (the G03 `cluster_bootstrap`, B = 10,000,
  seed 20261119), with 95% CIs for ALL, IN and OUT:
  - **Coverage effect:** Arctic-C1 − Arctic-C0, and BM25-full − BM25-C0.
  - **Structure effect:** Arctic-C2 − Arctic-C1.
- **Decision rule (written before any number):**
  - A complete-content arm becomes the **new representation baseline** for P2-T04 if, against C0 of the same route, the ALL
    lower bound is > 0 **and** the IN and OUT lower bounds are > −0.005.
  - **Structure is credited** only if Arctic-C2 − Arctic-C1 has ALL lower bound > 0 with IN/OUT > −0.005. Otherwise, if C1
    qualifies, the flat complete-content index is the baseline and structure gets no credit.
  - If neither arm qualifies, record NO_GAIN for coverage and keep C0. P2-T04 then proceeds on the existing routes.
- **Fusion check (descriptive, not a decision):**
  - F\*-style RRF fusions with the qualifying arm substituted, under the G03 action model (B = 4 windows);
  - deeper original-query retrieval (the same route at windows 1–2, i.e. depth 400) as the matched extra-resource control.
- **Reported regardless of outcome:**
  - every arm's ALL/IN/OUT R@200 and R@1000;
  - new-candidate counts vs C0;
  - **new judged-positive recovery** `|G ∩ (P1 \ P0)|`, evaluator side only;
  - displaced positives;
  - per-query win/loss counts;
  - index build cost.

## 6. What this cannot show

- No acquisition-policy claim and no confirmatory claim: this is P1-DEV only, and the representation is selected on the same
  data.
- No DAPFAM or Thai claim.
- Arctic results do not transfer automatically to PatEmbed or Qwen3.
