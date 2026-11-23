# P2-T02 amendment A2: complete-content follow-up for PatEmbed and Qwen3 (owner D19). Declared before any number

**Amends:** [P2-T02-COVERAGE-CONTROL-PROTOCOL.md](P2-T02-COVERAGE-CONTROL-PROTOCOL.md) (frozen bd30d3f7), §4 item 3: "If Arctic
shows a coverage effect, [PatEmbed and Qwen3 complete-content arms] become a declared follow-up." This file is that
declaration. Amendment [A1 (RunPod)](P2-T02-AMENDMENT-A1-RUNPOD.md) stays in force for the Arctic and BM25 results.
**Declared:** 24 Nov 2026. **No PatEmbed or Qwen3 complete-content number exists.** Nothing has been built, encoded,
retrieved or evaluated for either model. The commit that adds this file is the freeze; later changes go into a dated
addendum below.
**Owner authority:** D19 (the follow-up runs if Arctic shows a coverage effect, under a declared amendment), D22 (envelope
R2, USD 60, notify at USD 45; scope (b) is these follow-ups on RunPod; parallel pods), D21 (an optional network volume for
reusable data) in [OWNER-DECISIONS-20261122.md](../../../maintenance/OWNER-DECISIONS-20261122.md).
**Trigger (met):** the [P2-T02 results](../../../tracking/owner-note-22112026/receipts/P2-T02_coverage_control_results.md)
show Arctic C1 − C0 = +0.0165 ALL R@200 [0.0144, 0.0186], IN and OUT lower bounds > 0: Arctic C1 became the Arctic baseline.
**Runbook:** [P2-T02-D19-RUNPOD-RUNBOOK.md](P2-T02-D19-RUNPOD-RUNBOOK.md). **Status: package prepared, not run; no pod.**

## 1. Arms: C1 only, for each model

| Model | C0 (reference, not re-encoded) | Follow-up arm |
|---|---|---|
| Qwen3 (`Qwen/Qwen3-Embedding-0.6B` @ `97b0c614…`) | `z-qwen3`, the gated A3r1 RunPod rebuild | **Qwen3-C1**: flat complete content, the model's own windows, max-p |
| PatEmbed (`datalyes/patembed-large` @ `2d5c0f92…`) | `z-patembed`, the gated A3r1 RunPod rebuild | **PatEmbed-C1**: as above |

**Why C1 and not C2.** The protocol's §4 item 3 names "complete-content arms" and does not require the structural arm.
In P2-T02, structure got no credit: Arctic C2 − C1 = −0.0087 [−0.0105, −0.0069], worse on ALL, IN and OUT, so the
representation baseline is the flat C1 index. The follow-up asks only whether the coverage effect carries to the other
dense routes, so it builds the arm that became the baseline. C2 is not repeated. It would roughly double the encode cost
(Arctic C2 took 2 h 01 min and C1 took 1 h 58 min), and with C2 − C1 already negative on Arctic it cannot change the
representation choice. This choice is informed by the Arctic result; that is stated here, not hidden. No PatEmbed or
Qwen3 number informed it.

## 2. Content rule per model: own tokenizer, own window

C1_m and C0_m are compared **within each model**, so each model's windows come from **its own tokenizer at its own C0
maximum length (512 positions)**. Arctic's 510-token windows are not reused: a window of another tokenizer would be cut
differently or exceed 512 positions after re-tokenisation.

- **Content.** The P2-T02 complete content, unchanged: title + abstract (seg0, the C0 join), then every live claim of the
  same publication in claim-number order (cancelled rows dropped). The same frozen builder
  [`p2t02_build_content.py`](../../../../scripts/research/p2t02_build_content.py) produces it, with environment overrides
  only.
- **Tokens.** Each segment is tokenised separately with the model's tokenizer (`add_special_tokens=False`), as in P2-T02.
  **Separator:** every claim segment is preceded by the token ids of `"\n"`, the C0 join string
  (`P2T02_SEG_SEP="\n"`). For WordPiece (PatEmbed) these ids are empty, so nothing changes. For byte-level BPE (Qwen3),
  `"\n"` is a real token, and without it adjacent claims would run together with no boundary. The builder reports a
  1-in-500 sample of the token-count difference against tokenising the joined text, because BPE can merge `".\n"` at
  boundaries.
- **Window.** `W_m = 512 − |leading special tokens| − |document-prompt ids| − |trailing special tokens|`. The wrap is read
  from the tokenizer itself (`p2t02_d19_encode.py window`) before the build, and the build runs with `P2T02_WIN=W_m`.
  - Qwen3 has no document prompt. W = 511 if the tokenizer appends `<|endoftext|>`, otherwise 512.
  - PatEmbed has CLS + SEP and the document prompt `encode document for mixed retrieval: `. W = 510 − |prompt ids|,
    expected to be about 503–505.
  - The exact values are recorded in `window.json` before any encoding. They follow from the rule, not from a result.
- **Cut.** Consecutive W_m-token windows in reading order, no overlap. Max-p aggregation, the C0 masks at unit level after
  aggregation, top 1,000 units: the frozen [`p2t02_retrieve.py`](../../../../scripts/research/p2t02_retrieve.py),
  unchanged.
- **Encoding.** Each window is encoded exactly as the C0 text path would encode (document prompt + window text):
  - **Qwen3:** last-token pooling, left padding, fp16 (`dense_bridgeret_v2.py`);
  - **PatEmbed:** mean pooling over the attention mask in the model dtype, right padding, fp16 (`dense_bridgeret_v3.py`).
  The new [`p2t02_d19_encode.py`](../../../../scripts/research/p2t02_d19_encode.py) builds the tensors from token ids
  (head + window ids + tail). Gate V (§4) proves on the pod that these tensors equal the text-path tokens and vectors.
- **Queries.** Unchanged: the C0 query texts (`ser-qwen3-v1` / `ser-patembed-v1`, rebuilt on the pod with the archived
  command) with the C0 query prompts, through the C0 text path. P1-DEV only.

**Equal content within a model.** C1_m holds every live claim token of the unit under model m's tokenizer. C0_m holds
title + abstract + first independent claim under the same tokenizer, capped at 512. The only difference is the coverage
of the text, which is the question.

## 3. What is reused, and what changes (environment overrides only)

| Item | Source | Check |
|---|---|---|
| C0 runs and per-query evaluations (P1-DEV) | A3r1 RunPod rebuilds `z-qwen3` and `z-patembed` (relays in `../_private_artifacts/g03-a3r1-runpod/`) | Their A3r1 rebuild gates passed against the dr-train archive (Qwen3 ALL R@200 0.34736 vs 0.34734; PatEmbed 0.41806 vs 0.41797); gate C-R |
| Corpus and query texts | `texts-v1` of the A3r1 stage (corpus sha256 `287ef7e0…`, byte-identical to dr-train) | MANIFEST sha256 at staging and on the pod |
| Claims | the 54 local PatentsView claims files, **filtered at staging to the rows of the 1M corpus documents** (11.28 GB → 1.40 GB; 21.6 M of 168.0 M rows) | output-neutral by construction (the builder keeps only those rows, in the same order, with identical field values). Proven by a fixture test and on the pod by gate C-A |
| Cluster ids for the bootstrap | `meta-p1dev.pkl`: P1-DEV app → art unit only, derived from `am7/prep-v1/meta.pkl` | identical cluster map (staging check). `meta.pkl` itself, which also holds VAL labels, is not uploaded |
| Weights | Qwen3 @ `97b0c614…`, PatEmbed @ `2d5c0f92…` (the D23 items); Arctic @ `95c27414…` (tokenizer for gate C-A) | per-file sha256 pins (`g03_a3r1_runpod_models.py`) |

Code changes:
- `p2t02_build_content.py` gains three environment overrides: `P2T02_TOKDIR`, `P2T02_WIN` and `P2T02_SEG_SEP`. With
  none set, the build is unchanged; gate C-A proves this on the pod. The overrides in force are written into
  `stats.json` and `manifest.json`.
- New scripts:
  - `p2t02_d19_encode.py` (encoder);
  - `p2t02_d19_gate.py` (gates);
  - `p2t02_d19_decide.py` (contrast and decision, using the frozen `p2t02_analyse.py` functions);
  - `p2t02_d19_runpod.sh` (pod pipeline);
  - `p2t02_d19_inputs.py` (local staging).
- Speed-only settings, which do not change what is computed:
  - batch size 32 (`P2T02_D19_BS`; C0 used 8 for Qwen3 and 16 for PatEmbed, chosen for the shared V100);
  - memory fraction 0.5 on a dedicated GPU;
  - CPU worker counts.
  Gates V and Q run at the same batch size as the C1 encode, so any numerical effect of the batch size is inside the
  measured tolerance.

**Not re-encoded: C0.** C0 is the A3r1 run, encoded on an A100 80 GB. C1 is encoded on the follow-up pod. The two arms
therefore differ in GPU and kernels as well as content. Gate Q bounds this: this pod's query and C0-passage vectors must
reproduce the recorded C0 scores. The A3r1 gates already showed 99.8–99.9% per-query identity between A100 and V100 C0.
Re-encoding C0 on the follow-up pod would cost about 2 h more for Qwen3 and about 1 h more for PatEmbed, and it is not
done.

## 4. Gates (all must pass before any C1 number is interpreted)

| Gate | Where | Pass condition |
|---|---|---|
| P. Preflight | pod, before anything | library pins (torch 2.8.0, transformers 4.55.2, tokenizers 0.21.4, numpy 2.2.6); tasks, pairs and queries P1-DEV only; no TEST path, frozen manifest or `meta.pkl`; every uploaded file matches `MANIFEST-d19-<m>.sha256`; GPU ≥ 32 GB; RAM ≥ 60 GB |
| W. Weights | pod | every pinned file of the model (and of Arctic) matches its recorded sha256 |
| C-R. C0 reference | pod | relay gate passed; relay evaluation is P1-DEV with `n_queries_run` = 25,626 and per-query values; relay unit order = corpus order |
| C-A. Content reproduction | pod (CPU, in parallel with gate V/Q) | the builder **with no override** (Arctic tokenizer) over the uploaded filtered claims reproduces every P2-T02 data output byte for byte (`units.json`, `c1.*`, `c2.*`, `ser-full/passages.jsonl` sha256 equal to the P2-T02 manifest) |
| V. Id path = text path | pod (GPU) | first 2,048 C0 serialised passages: head + ids + tail equals the text-path tokens for **100%**; min cosine of id-path vs text-path vectors > 0.9999 |
| Q. C0 score reproduction | pod (GPU) | the first 256 P1-DEV queries of the gated C0 run and their top-50 units: this pod's text-path vectors reproduce the recorded C0 scores with median \|Δ\| ≤ 0.001 and \|Δ\| ≤ 0.005 for ≥ 99% of pairs |
| F. Final | pod | P, W, C-R, C-A, V and Q passed, and the C1 content was built with the window in `window.json` |

Gate C-A must pass before the C1 encode starts. If any gate fails, the pod stops with `P2T02_D19_FAILED:<stage>`. No
contrast is computed, the failure is reported as it is, and nothing is repaired silently.

## 5. Endpoints and decision (frozen, unchanged from P2-T02 §5)

- **Primary:** ALL R@200, query-macro, unchanged evaluator `eval_bridgeret_dev.py`, P1-DEV (25,626 queries run;
  evaluator population 26,547).
- **Paired contrast per model:** model-C1 − model-C0. Cluster bootstrap by examiner art unit (the G03
  `cluster_bootstrap`, B = 10,000, seed 20261119), with 95% CIs for ALL, IN and OUT R@200.
- **Decision rule (P2-T02 §5, applied per model):** model-C1 becomes that model's **representation baseline** if the ALL
  lower bound is > 0 **and** the IN and OUT lower bounds are > −0.005. Otherwise the result is **NO_GAIN** for that model,
  and model-C0 stays.
  - The two models are decided separately. No multiplicity correction is applied: there was none in the frozen rule, and
    each decision only sets an engineering baseline.
  - The Arctic row is shown next to the results for reading only.
- **Reported regardless of outcome:**
  - both arms' ALL/IN/OUT R@200 and R@1000, OUT MRR and OUT nDCG@10;
  - new candidates vs C0 at 200 and 1000;
  - new judged-positive recovery `|G ∩ (P1 \ P0)|` and displaced positives (evaluator side);
  - per-query wins and losses;
  - content stats (passages, tokens, separator ids, join-difference sample);
  - window spec;
  - build, encode and retrieval wall time and peak memory;
  - every gate record.
- **Deferred, as in A1:**
  - the descriptive G03 fusion check with substituted arms;
  - the deeper original-query control.
  Neither changes the decision.

## 6. Spend estimate (RunPod, envelope R2)

Basis: measured rates, not vendor figures.
- **Arctic, RTX PRO 4500:**
  - C0 text path: 1 M passages in 37 min (about 0.36 B tokens);
  - C1 id path: 3.97 M windows and 1.77 B tokens in 1 h 58 min;
  - so C1 cost **about 3.1× C0** at the same batch size.
- **Qwen3 C0 (BS 8):** about 1 h 50 min on the A100 and about 3 h 50 min on the V100.
- **PatEmbed C0 (BS 16):** about 47 min of encoding on the A100 and about 1 h 40 min on the V100.
- **Relative GPU speed:** for these small-batch jobs the RTX PRO 4500 and the A100 each ran at about 2× V100 speed, so
  they are about equally fast here.
- **Assumption:** C1 tokens per model are about 1.75–1.9 B, about the same as Arctic.

| Item | Qwen3 pod | PatEmbed pod |
|---|---|---|
| Setup, upload (3.56 GB; about 2.6 GB on the wire), weights, serialisation, content build | 0.6 h | 0.6 h |
| Gates V/Q, queries (gate C-A runs in parallel) | 0.2 h | 0.2 h |
| **C1 encode** (3.1×–5× C0; central 3.1×, with BS 32 assumed to offset the longer windows) | **4–6.5 h** (central 5 h; worst case 9.5 h) | **2–3 h** (central 2.6 h; worst case 4 h) |
| Retrieve (1024-dim, about 4.2 M windows), evaluate, decide, pack, pull | 0.5 h | 0.5 h |
| **Pod hours** | **about 6.3 h** (5.3–7.8; worst 10.8) | **about 3.9 h** (3.3–4.3; worst 5.3) |

| GPU (≥ 32 GB, ≥ 60 GB RAM, 150 GB disk) | Price | Both pods, central | Range | Worst case |
|---|---|---|---|---|
| **RTX PRO 4500 Blackwell (recommended; used for P2-T02)** | USD 0.72/h | **USD 7.3** | USD 6.2–8.7 | USD 11.6 |
| A100 80 GB (used for A3r1) | USD 2.19/h | about USD 18 (if about 1.3× faster at BS 32) | USD 15–22 | **USD 35, over the ~USD 25 flag** |

**Flag.** On RTX PRO 4500-class pods (also L40S, RTX 6000 Ada, A40 at ≤ USD 0.9/h) the follow-up stays well under USD 25
even in the worst case. **On A100 pods the worst case is about USD 35, which exceeds the ~USD 25 line and the roughly
USD 35 left in R2. A100 pods are used only after the owner says so.** If C2 were added (not planned), the encode hours
would roughly double: about USD +5.5 on the RTX class, or USD +15–25 on A100s.

**Storage.** No network volume by default: everything is on pod disk and goes when the pod is deleted (as in P2-T02).
Optionally, under D21, the C1 vectors (about 8.6 GB per model) and C1 token ids (about 7 GB per model) can be kept on a
volume, about 31 GB ≈ USD 2.2 per month. This needs an owner choice (runbook §8).

## 7. Stop rules

- **Sub-cap for this follow-up: USD 15** inside R2, with **stop and report at USD 12**. R2's own rule still applies
  (USD 60, notify at USD 45).
- **Price before creation.** Each pod's hourly price is stated before it is created and recorded with its id. A100 pods
  only with owner approval (§6).
- **Hours per pod.** Planned hours on RTX-class pods are 7 h (Qwen3) and 4.5 h (PatEmbed). A pod that reaches **twice
  its planned hours** (14 h / 9 h) is stopped and the owner is told, as in the A3r1 precedent. A retry after an
  out-of-memory error may lower the batch size (encoding resumes from finished shards); it is recorded.
- **One run per model.** After the results are pulled and checked by sha256, each pod is deleted, `list-pods` must be
  empty, and billing is read and recorded in the receipt.
- **Data on pods.** No TEST block, sealed file, VAL label, frozen manifest, `meta.pkl` or credential goes to a pod.

## 8. What this cannot show

- Everything in protocol §6 still holds. This is P1-DEV only, the representation is chosen on the same data, and the
  results make no acquisition-method claim, no DAPFAM or Thai claim, and no confirmatory claim.
- A C1 gain means "more eligible text was indexed for this model". It is an engineering control that raises the bar for
  P2-T04. It is not evidence for the acquisition method.
- C0 comes from another GPU (an A100 for A3r1). Gate Q bounds that difference, but it is not a bit-identical
  same-software contrast.
- Results are not transferred between models. Each model's decision stands alone.
- PatEmbed on DAPFAM keeps its training-overlap caveat. That caveat is unrelated to this Challenge-1M P1-DEV control.
