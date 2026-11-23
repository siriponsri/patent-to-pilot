# A3r1 addendum F: the Stage B evaluation (full P1-DEV, then VAL) on one RunPod pod. Declared before any Stage B number

**Amends:** only the host and the input provenance of the frozen Stage B evaluation. That evaluation is A3r0 §4
([G03-DEV-AMENDMENT-3-20261122.md](G03-DEV-AMENDMENT-3-20261122.md)), kept by A3r1 §7
([G03-DEV-AMENDMENT-3R1-PROPOSED.md](G03-DEV-AMENDMENT-3R1-PROPOSED.md)) and frozen by the
[P1-T03 freeze receipt](../../../tracking/owner-note-22112026/receipts/P1-T03_freeze_receipt.json). No effectiveness rule
changes. The precedent is the pilot amendment [A3R1-AMENDMENT-RUNPOD-REBUILD.md](A3R1-AMENDMENT-RUNPOD-REBUILD.md); its
gate tolerances are reused unchanged.

**Declared:** 24 Nov 2026, while Stage B generation is still running on the owner PC.

**State at declaration:**
- The pilot is done. Its frozen decision is GO with m\* = `deepseek/deepseek-v4-flash-0731`
  ([P1-T04 receipt](../../../tracking/owner-note-22112026/receipts/P1-T04_pilot_generation.md)).
- No H or K route exists beyond the 2,000 pilot apps.
- No A3r1 arm has been built or evaluated on full P1-DEV or on any VAL query.
- No A3r1 VAL number exists.

**What was computed locally while preparing this package (free, owner PC):**
- the input hashes;
- the Stage B ledger state;
- a re-evaluation of the archived dr-train VAL C0 runs (L, Q, P) and a regeneration of the protocol-v1 F\* VAL run, both
  compared with the archived files.

These VAL figures were already exposed by G03 v1, A1 and A2. The check printed pass/fail only, and everything matched
exactly. No A3r1 arm was touched.

**Authority and money:**
- D16 covers the Stage B *generation* (E1R).
- The RunPod envelope R2 (D22) names "(a) the A3r1 **pilot** evaluation".
- **This addendum authorises no spend.** The pod starts only after the owner records an envelope or an R2 scope extension
  for it. The expected cost is in §5.

## 1. What runs where (one pod)

| Input | P1-DEV | VAL | Gate (§3) |
|---|---|---|---|
| Route L (BM25-C0) | rebuilt on the pod with the archived command (`bm25_bridgeret.py … runs/bm25 P1-DEV`), or a kept P2-T02 copy checked against its recorded sha256 | archived dr-train `run-VAL.tsv.gz` (pull-manifest sha256) | C, V-L |
| Route Q (Qwen3-C0) | the gated pilot rebuild (qwen3 relay, sha256 `01b78211…`) | archived dr-train run | D, V-Q |
| Route P (PatEmbed-C0) | the gated pilot rebuild (patembed relay; its evaluation is byte-identical to the pilot assembly's) | archived dr-train run | E, V-P |
| PatEmbed corpus vectors for route H | **re-encoded** on the pod with the archived C0 command, blocks P1-DEV and VAL, into `runs/z-patembed-reenc` (the pilot vectors were not kept) | same call | B-re, E-re, E-VAL |
| Query text of route H (`ser-patembed-v1`) | rebuilt from `texts-v1` (P1-DEV records = dr-train extract) | VAL records derived from the dr-train extract (rule below) | A2, A2v, E-VAL |
| Index of route K (`ser-arctic-v1`) | rebuilt with the pinned Arctic tokenizer (D20 item), or the kept P2-T02 copy | – | K0 |
| v0 F\* (integrity reference) | regenerated from the P1-DEV L, Q, P runs | regenerated from the archived VAL runs | F, F-VAL, G |
| `tasks.tsv`, `pairs-dev.tsv` | P1-DEV + VAL rows only (from `meta.pkl` and the archived pairs) | | V, F-VAL |
| Ledgers of m\* | Stage B `P1-DEV.jsonl` (begins with the 2,000 pilot records) | Stage B `VAL.jsonl` | H-full |

**Why this split:**
- **Q on P1-DEV.** The 2-hour Qwen3 corpus re-encode is avoided by reusing the gated pilot runs.
- **VAL.** The VAL routes are the byte-identical dr-train originals. F\* on VAL is therefore exactly the protocol-v1
  F\* that the three earlier VAL looks used (`evals/VAL/alloc-L0-Q2-P2-A0.json`, sha256 `126ad57c…`).
- **P on P1-DEV.** Route P stays the gated pilot run, so every P1-DEV arm except those using H is built from exactly the
  pilot's routes.

**Disclosed consequence.** On both blocks, route H scores against the re-encoded PatEmbed vectors, while route P comes
from the pilot vectors (P1-DEV) or the dr-train vectors (VAL). Gates E-re and E-VAL bound the difference: per-query
agreement of at least 90% and means within 0.002. Within a block, every arm, including F\*, shares one set of route runs.

**VAL query text.** The local `texts-v1/queries.jsonl` holds P1-DEV only. The VAL records are derived from the dr-train
extract `g03-a3/inputs/queries-dev-val.jsonl` (title, abstract and claim, which are the fields the serialisers read):
- a VAL row with a non-empty title gets a `doc` marker;
- a row with an empty title is `no_pgpub` and is not serialised, as in the builder.

The rule reproduces all 26,575 local P1-DEV builder records on these fields (25,626 with a document, 949 without), and
staging stops otherwise. On VAL it gives 1,919 + 81. The 1,919 equal `apps-VAL.json`, the apps of the archived VAL F\*
run.

**Code changes** (environment overrides only; dr-train defaults are unchanged):
- [`g03_a3r1_runpod.sh`](../../../../scripts/research/g03_a3r1_runpod.sh) gains role `full`.
- [`g03_a3r1_runpod_v0.py`](../../../../scripts/research/g03_a3r1_runpod_v0.py) takes an optional block argument
  (P1-DEV by default; VAL allowed; TEST refused).
- New: [`g03_a3r1_full_gate.py`](../../../../scripts/research/g03_a3r1_full_gate.py) (gate),
  [`g03_queue_a3r1_full.sh`](../../../../scripts/research/g03_queue_a3r1_full.sh) (the frozen §4 steps) and
  [`g03_a3r1_full_inputs.py`](../../../../scripts/research/g03_a3r1_full_inputs.py) (staging and local checks).
- Unchanged: `g03_a3_routes.py`, `g03_route_acquisition.py`, `g03_a3_decide.py`, the evaluator and the archived C0
  scripts.
- Library pins: as the pilot (torch 2.8.0+cu128, transformers 4.55.2, tokenizers 0.21.4, numpy 2.2.6). The pod also pins
  scikit-learn 1.7.2 and scipy 1.18.1, the versions of the pilot's BM25 and K routes; role `full` refuses others.

## 2. Order on the pod

1. **F0, gate part `ledger`.** Stage B must be complete and clean before any compute.
2. **F1, route L on P1-DEV and the K-route index** (CPU).
3. **F2, evaluate** L, Q and P on both blocks.
4. **F3, regenerate and evaluate the v0 F\*** of both blocks; regenerate the P1-DEV population and the pilot sample.
5. **Gate part `cpu`.**
6. **F4, re-encode PatEmbed** (GPU, about 1 h on an A100) and evaluate it on both blocks.
7. **Gate part `enc`.**
8. **F5, run [`g03_queue_a3r1_full.sh`](../../../../scripts/research/g03_queue_a3r1_full.sh)** (§4).
9. **Pack.**

The frozen decision is applied only after all three gate parts have passed.

## 3. Gate (declared now; tolerances of the pilot amendment)

| Part | Check | Pass condition |
|---|---|---|
| ledger | H-full: Stage B ledgers of m\* | Every record of `P1-DEV.jsonl` / `VAL.jsonl` has its block, model m\*, protocol A3r1, `max_tokens` 800, and an app in `apps-P1-DEV.json` (25,626) / `apps-VAL.json` (1,919). The two sets are disjoint. Every app has an `ok` or `content_unusable` record, or failed transport on all 3 attempts (A3r1 §5: `transport_failed`, kept in the population without H/K output). An app with an unreconciled unknown cost counts as missing. The P1-DEV file begins with the exact bytes of the pilot ledger (sha256 `e65ae436…`, 7,021,054 bytes). Run first, also at staging |
| cpu | A | `texts-v1/corpus.jsonl` sha256 = archived `287ef7e0…` |
| cpu | A2 | The 26,575 P1-DEV query records equal the dr-train extract |
| cpu | A2v | The 1,919 VAL records with a document equal the extract rows; the 81 `no_pgpub` records are exactly the rows with an empty title |
| cpu | C | BM25-C0 P1-DEV against the archived evaluation: every mean (ALL/IN/OUT R@200 and R@1000) within **0.0005**, ALL R@200 identical per query for **≥ 99%**, same `n_queries_run` |
| cpu | D | Qwen3-C0 P1-DEV (the pilot rebuild, re-evaluated): every mean within **0.002**, **≥ 90%**, same n |
| cpu | E | PatEmbed-C0 P1-DEV (the pilot rebuild, re-evaluated): as D |
| cpu | V-L, V-Q, V-P | The archived VAL runs, re-evaluated with the P1-DEV+VAL task and pair files, against the archived `eval-VAL.json`: L as C, Q and P as D. Exact agreement is expected and is reported |
| cpu | F | v0 F\* P1-DEV regenerated: as the pilot gate F. That is D against the archived evaluation (sha256 `a4f7bb3d…`), the pilot-subset means within 0.002, and the archived means equal the repository record 0.4230 / 0.4940 / 0.3334 |
| cpu | F-VAL | v0 F\* VAL regenerated from the archived VAL runs: as D against the archived VAL evaluation (sha256 `126ad57c…`), and the archived means equal the repository record ([g03-dev-tables.md](g03-dev-tables.md), B = 4: 0.4523 / 0.5306 / 0.3590) |
| cpu | G | The apps of the regenerated F\* runs equal `apps-P1-DEV.json` (25,626) and `apps-VAL.json` (1,919). The regenerated pilot sample equals `apps-pilot.json` (sha256 `c6653b6f…`) |
| cpu | K0 | `ser-arctic-v1/passages.jsonl` sha256 = the P2-T02 record that the pilot K routes used (`e07122ce…`) |
| enc | B-re | Re-encoded `units.json` = archived unit order |
| enc | E-re | Re-encoded PatEmbed-C0 P1-DEV against the archived evaluation: as D |
| enc | E-VAL | Re-encoded PatEmbed-C0 VAL against the archived `eval-VAL.json`: as D. This covers VAL query text, serialisation and the vectors that feed H, end to end |

**Descriptive, never a pass condition:** per-query agreement with the pilot's own evaluations (BM25, Q, P, v0 F\*) and
of the re-encoded P run with the pilot P run.

**On failure.** A failed check stops the pod with `G03_A3R1_RUNPOD_FAILED:rebuild-gate-full-<part>`. No arm is built and
no decision is applied. The failure is reported as it is and nothing is repaired silently. An incomplete Stage B stops at
staging (exit code 2 in `--check-only`) and again at F0.

## 4. The frozen procedure (A3r0 §4 / A3r1 §7, unchanged code)

1. **Routes.** Build H_m\* and K_m\* for every P1-DEV and VAL app with a usable m\* response (A3r0 §2):
   - filing-date and own-unit masks;
   - H with PatEmbed mean pooling, fp16 and memory fraction 0.12 under the GPU lock;
   - K with BM25 k1 1.5 and b 0.75 over `ser-arctic-v1`.
2. **Arms.** On each block, over the F\* apps (25,626 / 1,919): the **70** fixed allocations at B = 4 over (L, Q, P, H, K),
   plus the 5 at B = 1 (descriptive: H alone and K alone at one window). The action model and RRF final scorer are
   unchanged. The unchanged evaluator scores the populations of 26,547 P1-DEV / 1,999 VAL; queries without route runs
   score 0 in every arm.
3. **Integrity.** `alloc-L0-Q2-P2-H0-K0` must equal the regenerated v0 F\* per query on both blocks;
   `g03_a3_decide.py full` stops otherwise.
4. **F3\*.** F3\* is the B = 4 allocation with the highest P1-DEV mean ALL R@200. Allocations within **0.0005** of the
   best tie. Ties break first by fewer routes, then by route order **P, Q, H, K, L** (comparison of the sorted priority
   indices of the routes used), then by the higher mean.
5. **No H or K in F3\*.** If F3\* uses neither H nor K, H-M3 is "not supported on DEV". VAL is then descriptive only and
   no CONTINUE/REVISE/PARK is issued.
6. **VAL principal.** Δ = F3\* − F\* in ALL R@200, paired over the VAL evaluator population. The 95% percentile interval
   comes from the art-unit cluster bootstrap (`meta.pkl` `au`; a query without an art unit is its own cluster),
   **B = 10,000, seed 20261119**. IN and OUT R@200 are computed the same way.
7. **Decision** (δ = 0.005):
   - **CONTINUE** if the ALL lower bound > 0 and the IN and OUT lower bounds are both > −0.005;
   - **PARK** if the ALL upper bound < 0, or if an IN/OUT guard fails;
   - **REVISE** otherwise (the ALL interval includes 0 and both guards hold).
8. **Descriptive** (no selection):
   - the full table on both blocks;
   - P1-DEV F3\* − F\* with its bootstrap.

   Later, from the packed runs and evaluations: H and K alone against P and L; the overlap of H/K top-200 with Q and P;
   the share of F3\*'s relevant units that only H or K acquired.
9. **Disclosure.**
   - This is the **fourth G03 look at VAL** (v1, A1, A2, A3), in an exploratory DEV phase. The confirmatory comparison is
     a later frozen G04 run.
   - The pilot Δ is a spending gate, not a result.
   - One settle: the decision is applied once. A host failure before `results-a3r1-full.json` is written may be resumed;
     nothing is re-run after it exists.

## 5. Spend, time and stop rules

- **Pod:** one GPU with ≥ 32 GB, ≥ 64 GB RAM, ≥ 12 vCPU, 100 GB disk, US data centre. No network volume is needed.
- **Estimated wall time** (setup and upload included):
  - A100 80 GB: **about 4–5.5 h**, about **USD 9–12** at USD 2.19/h.
  - RTX PRO 4500 32 GB: **about 5.5–7.5 h**, about **USD 4–5.5** at USD 0.72/h. The slower GPU affects the 1 h
    PatEmbed re-encode; everything else is CPU-bound.
  - The [runbook](A3R1-RUNPOD-RUNBOOK.md#full-evaluation-after-stage-b) has the stage-by-stage table.
- **Stop rule.** A pod that runs for twice its planned hours is stopped and the owner is told.
- **No paid API.** The evaluation reads the ledgers only.
- **Results.** Results go to `../_private_artifacts/g03-a3r1-full-runpod/`, and the aggregates and gate tables go to a
  receipt. The pod is then deleted and billing is read and recorded.

## 6. What this cannot show

Everything in A3r0 §6 and A3r1 §9 still holds: memorisation and temporal leakage, model drift, and a single m\*. A gated C0
is a reproduction within the stated tolerances, not a bit-identical copy of the V100 runs. The VAL routes L, Q and P are
the originals; route H is not. A VAL result here is a DEV-phase finding after three earlier VAL looks, not a confirmatory
test.
