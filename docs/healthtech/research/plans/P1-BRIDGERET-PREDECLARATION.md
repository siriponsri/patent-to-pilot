# P1-BridgeRet pre-declaration (FROZEN 2026-11-18, before any P1-BridgeRet retrieval number)

Authority: owner, 2026-11-18 evening ("อนุมัติ Freeze แผนได้ทันที ตอนเช้ารายงานผลให้ผมพอ"), recorded in
`docs/healthtech/research/paper1-bridgeret/owner-decisions-20261118.json`. Drafted by the agent from the owner set
`owner-note-18112026` (SOT-0.2, files 01/02, MS1-0.1) and the owner decisions of 17 Nov. Items that were open are fixed here
with the default named in the owner documents; each is marked **[DEFAULT]**. Any later change is a logged amendment
(old/new sha256, rationale, author, statistical impact) and is only allowed before the first P1-DEV retrieval number of the
affected system. No retrieval number for P1-BridgeRet exists at freeze time (the closed P1-DAPFAM numbers are a different study).

## 1. Frozen inputs
| Item | Value |
|---|---|
| Split | manifest-v2, sha `c8443600d74fed015213237e070882efd1ddeefef7e66b6f3d6f7bb2f31e8039` (`paper1-bridgeret/manifest-v2/FREEZE-RECEIPT.json`): TRAIN 100,376 · VAL 2,000 · P1-DEV 26,575 · P2-DEV 26,231 · P1-TEST 10,000 · P2-TEST 43,587 · P3-TEST 55,307; family-aware (US continuity), L-B PASS |
| Corpus | Challenge-1M v1, 1,000,000 application-level units, window 1976-01-01..2012-12-31 **[DEFAULT corpus start 1976]**, tiers declared in `scripts/healthtech/build_challenge1m_sealed.py` (commit 2ed49e9); `corpus-units.tsv` sha `18b56815dff32ab90d92aa7b70a170d8d66e89bd874a622a53cd8f4b3db1edba`; P1-TEST gold sealed (`sealed/qrels-p1-test.tsv` sha `0dc97418b5c2af899db55d76aba36a2018c262466ab29893545d89d8418e5ec7`) |
| Text | PatentsView ODP release 2026-04-10 (titles, abstracts, claims); hashes in `paper1-bridgeret/claims-download-receipt.json` and the build receipts |
| Models | Arctic-embed-m-v2.0 @`95c2741480856aa9666782eb4afe11959938017f`; Qwen3-Embedding-0.6B @`97b0c614be4d77ee51c0cef4e5f07c00f9eb65b3` (`paper1-bridgeret/models.sha256`) |

## 2. Task, relevance, visibility
- Task = application; K(q) = US documents cited under §102/§103 in the earliest non-final rejection (OA-SPLITS R1). Labels are `examiner_cited`; `not_cited` is not a verified negative.
- Relevance is at **unit** level (application; a grant and its pre-grant publication are one unit).
- OUT = no shared IPC3 between task application and cited document (proxy). Positives with no IPC on the cited side are neither IN nor OUT.
- RPD visibility: a unit is retrievable for q only if `first_pub < filing_date(q)`; the task's own unit is never a target (L-E).
- **Primary endpoint:** query-macro OUT Recall@200 over P1-TEST tasks with ≥ 1 OUT positive that is RPD-visible and present in Challenge-1M (**conditional** recall) **[DEFAULT: conditional primary]**. Strict recall (denominator = all RPD-visible OUT positives with a known date; absent units count as misses) and coverage are co-reported. A query whose system output is missing scores 0.
- Secondary (descriptive): OUT Recall@1000, OUT nDCG@10, MRR, IN Recall@200 (harm, margin −0.020 descriptive), ALL Recall@200, §102/§103 strata, `seen_family` strata, unseen-document subset.

## 3. Query and passage text
`bridgeret_query.serialise`: Title + "\n" + Abstract + "\n" + First Independent Claim; cap 512 tokens of each model's tokenizer; claim tail truncated first, then abstract, never the title. Query document = the task application's earliest pre-grant publication. Passage = the unit's earliest publication. Model prompts = developer-recommended (owner proposal 4): Arctic query prefix `"query: "`, documents without prefix; Qwen3 query `"Instruct: Given a patent application, retrieve prior art cited against it\nQuery: "`, documents without prefix **[DEFAULT instruction text]**. Truncation statistics are reported (spec 01 §5), not used to choose systems.

## 4. Systems
- **B-BM25**: k1 = 1.5, b = 0.75, lowercase alphanumeric tokens, no stemming, no stop list, over the same passage text.
- **Z-Arctic**, **Z-Qwen3**: zero-shot, prompts above.
- **E0**: RRF(BM25, best zero-shot dense on P1-DEV by OUT Recall@200), k = 60, depth 1000 per list.
- **Z-PatEmbed-large** (optional; CC BY-NC-SA, research lane only): run if its P1-DEV and P1-TEST runs complete before the S* freeze; this is a feasibility rule, not a result rule.
- **S1–S4** (DEV): InfoNCE with multi-positive guards (mask all of K(q), same-application citations, exact-text duplicates). S1 in-batch + BM25 negatives; S2 + dense hard negatives from ranks 20–200 of Z-Arctic; S3 = S2 with IN:OUT 1:1 and w_OUT ∈ {1, 1.5, 2}; S4 = S2 + denoising. Denoising = owner O4: **reranker denoise** (drop a mined negative whose zero-shot reranker score is ≥ the positive's 10th-percentile score; bge-reranker-v2-m3 used only as a scorer); rule-only denoise (margin 0.95 × positive score) kept as an ablation. τ ∈ {0.02, 0.05}.
- **Training**: full fine-tuning (O10), LoRA only if VRAM/cost forces it (switch recorded). Learning rate 2e-5 **[DEFAULT]**, 1 epoch over TRAIN pairs **[DEFAULT]**, warm-up 5 %, max length 512, early stopping / checkpoint choice on VAL OUT Recall@200 only. fp16 mixed or fp32 (no BF16 on V100), stated per run.
- **S\*** = the registered configuration with the highest P1-DEV OUT Recall@200; ties within 0.001 go to the simpler recipe (lower S index, then smaller grid value). S5 = RRF(BM25, S\*) and S6 = S\* + zero-shot reranker are KEY-SEC/DIAG, never in the confirmatory family.
- 2×2 diagnostic (S2/S3 × denoise off/on), DEV only, matched negative counts, 3 seeds at 30k TRAIN tasks; interpretation rule as in MS1 §6.

## 5. Confirmatory family and inference (P1-TEST, opened once)
- C1 = S\* − Z-Arctic; C2 = S\* − E0; C3 = S\* − Z-PatEmbed-large only if run. Holm over the executed members, α = 0.05; decision = Holm-adjusted lower bound > 0.
- Paired cluster bootstrap by art unit, B = 10,000, seed **20261119**; sign-flip permutation as a check. δ = 0.010 is the practical-effect target (fixed), separate from the significance rule.
- **n₁ = 10,000** (owner O2). Power is recomputed from P1-DEV σ_diff and design effect; if the required n exceeds 10,000 the paper states the larger MDE.
- **Unseen-document rule (owner proposal 2):** the primary contrasts are co-reported on the subset of P1-TEST positives never seen as a TRAIN positive or TRAIN query application. If a contrast's sign differs between the full set and this subset, the result is reported as "not robust to memorisation".
- **Seen-family stratum** (581 P1-TEST tasks share a family with earlier blocks): reported, not deleted.

## 6. Isolation and order of work
1. TEST query texts and TEST gold are not read before S\* is frozen and its checkpoint/config/script hashes are recorded (G1.4). The gold is opened once through `canonical_split_manifest.ProtectedGoldGate` with an approval bound to manifest `c8443600…`. The freeze approval does NOT open TEST: the single TEST look needs the owner's explicit go.
2. DEV order: zero-shot baselines and BM25 → E0 → hard-negative mining on TRAIN → S1–S4 grid → S\* → 2×2 diagnostic.
3. Paid compute: only the approved RunPod pilot (cap USD 10) until a fine-tuning cost estimate exists; the full fine-tuning dispatch needs its own owner cost approval inside A+ (GPU USD 75). No paid API in P1.
4. DAPFAM single look (O5): local only, on the frozen S\*, labelled external/exploratory.

## Amendments (logged before any S* or fine-tuning number; owner decisions 2026-11-19, `paper1-bridgeret/owner-decisions-20261118.json`)
| ID | Change | Old -> new | Rationale | Statistical impact |
|---|---|---|---|---|
| AM-1 | Backbone | Arctic-embed-m-v2.0 -> Qwen3-Embedding-0.6B @97b0c614 (last-token pooling, left padding, instruction prompt of §3) | owner O3 change; Qwen3 was the recorded fallback; zero-shot DEV numbers were known (descriptive) when chosen | C1 becomes S* - Z-Qwen3 (same backbone); Z-Arctic stays a reported reference |
| AM-2 | Negatives / grid (amendment A1) | k unspecified, grid on full TRAIN -> k = 3; grid on the 30k-task TRAIN subset (salt ptp-2x2-30k-v1); S* retrained once on full TRAIN; dense negatives from the backbone's own zero-shot ranks 20-200 | cost (RunPod pilot: ~11.5 A40-h per full epoch with 7 negatives) | none on the confirmatory family |
| AM-3 | C2 | S* - E0 -> S* - (strongest pre-registered non-trained comparator on P1-DEV OUT R@200; E0, Z-Arctic, Z-Qwen3 eligible; Z-PatEmbed-large stays C3) | E0 (0.2661) is weaker than Z-Qwen3 (0.2741) on DEV; SOT defines C2 as the strongest non-trained comparator | C2 now uses Z-Qwen3 if it stays strongest; with AM-1, C1 and C2 may coincide - then the family is {C1, C3} and this is reported |
| AM-4 | S4 denoise order (19 Nov, before any S* number) | S4 = reranker denoise (rule = ablation) -> grid runs S4-rule first; S4-reranker added only if the USD 20 envelope still covers its precomputed bge-reranker scores (about 5.5M pairs on the 30k subset) after S1-S3 and S4-rule | cost: the reranker scores alone would take a large share of the envelope | if S4-reranker is not run, the registered S* family is {S1, S2, S3, S4-rule}; this is reported |
| AM-5 | Grid size and encoding site (19 Nov, before any S* number) | 12-config grid encoded on the pod -> 5 configs on the 30k subset, all trained on RunPod A40: S1 t0.02, S2 t0.02, S3 t0.02 w_OUT 1.5, S4-rule t0.02 (the S2/S3 x denoise 2x2 corners) and S2 t0.05 (tau sensitivity). Checkpoints are shipped as fp16, and P1-DEV/VAL encoding + retrieval run on the dr-train V100 with dense_bridgeret.py (the same code as the zero-shot baselines) | measured 6.6 s/step at bq16 on the A40 (3.4 h per 30k config), so 12 configs alone would cost about USD 24, over the USD 20 envelope | S* is chosen among 5 instead of 12 configs; tau 0.05 and w_OUT 1/2 are not explored except S2 t0.05; this is reported |
| AM-6 | Forgetting / domain trade-off report (19 Nov 13:45 UTC, owner request; before any fine-tuned DEV number: pod-1 S2-t0.02 was still encoding, no eval file existed) | none -> descriptive forgetting report, never part of the S* rule or the confirmatory family: (a) for every config and for S*-full, paired OUT/IN/ALL Recall@200 deltas vs Z-Qwen3 on P1-DEV and VAL from the existing per-query eval rows (bootstrap B 10,000 over queries, seed 20261119), label IN_TRADEOFF when the IN point delta < -0.020 (scripts/healthtech/bridgeret_forgetting_report.py); (b) patent-domain transfer: the O5 DAPFAM single look on frozen S* is paired with Qwen3-Emb zero-shot on the same 6 public DAPFAM tasks (nDCG@100, Recall@100), local only; (c) general-domain forgetting: S* vs Qwen3-Emb zero-shot on small public non-patent retrieval tasks (BEIR SciFact, NFCorpus, ArguAna; nDCG@10) only after the owner approves that download (light gate 3), otherwise reported NOT_RUN | full fine-tuning (O10) can trade general or in-domain ability for the OUT gain; the owner asked for this to be measured | wording: 'forgetting' claims only from (a)-(c); no claim about tasks not measured |
