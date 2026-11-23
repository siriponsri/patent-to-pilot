# A3r1 amendment R: run the frozen pilot evaluation on RunPod pods with rebuilt inputs. Declared before any A3r1 number

**Amends:** the host and the input provenance of the frozen A3r1 Stage A pilot queue
([`g03_queue_a3r1_pilot.sh`](../../../../scripts/research/g03_queue_a3r1_pilot.sh); protocol
[G03-DEV-AMENDMENT-3R1-PROPOSED.md](G03-DEV-AMENDMENT-3R1-PROPOSED.md), frozen by the
[P1-T03 freeze receipt](../../../tracking/owner-note-22112026/receipts/P1-T03_freeze_receipt.json)). Nothing in the
effectiveness rules (§7 of the protocol) changes.

**Declared:** 23 Nov 2026, night. No A3r1 retrieval number exists. Pilot generation is complete
([P1-T04 receipt](../../../tracking/owner-note-22112026/receipts/P1-T04_pilot_generation.md)), but no route has been built,
no arm evaluated and no GO/STOP applied.

**Owner authority:** D22 (RunPod envelope R2, USD 60, notify at USD 45, parallel pods) and D23 (the A3r1 pilot evaluation
runs on RunPod now; dr-train-only inputs are rebuilt under a declared amendment, with a rebuild gate against the archived
records **before** the frozen GO/STOP rule; the PatEmbed and Qwen3 weights are the previously approved items at their
recorded revisions) in [OWNER-DECISIONS-20261122.md](../../../maintenance/OWNER-DECISIONS-20261122.md).
The precedent is P2-T02 amendment A1 ([P2-T02-AMENDMENT-A1-RUNPOD.md](../p2-coverage/P2-T02-AMENDMENT-A1-RUNPOD.md)).

## 1. Why

dr-train has been unreachable since about 07:00 Bangkok on 23 Nov. The frozen queue reads these inputs, which exist only on
dr-train:

| Input | Used for | Local record |
|---|---|---|
| `bridgeret/runs/z-qwen3/run-P1-DEV.tsv.gz` | route Q | archived `units.json`, `eval-P1-DEV.json` (per query), `summary-P1-DEV.json` |
| `bridgeret/runs/z-patembed/{run-P1-DEV.tsv.gz, passages.f16.npy, units.json}` | route P; corpus vectors of route H | as above |
| `bridgeret/runs/bm25/run-P1-DEV.tsv.gz` | route L | archived `eval-P1-DEV.json`; **rebuilt and gated on the P2-T02 pod** |
| `bridgeret/ser-patembed-v1/queries.jsonl` | query text of route H | none (rebuilt from texts-v1) |
| `bridgeret/ser-arctic-v1/passages.jsonl` | index of route K | **rebuilt and gated on the P2-T02 pod** |
| `g03-dev/evals/P1-DEV/alloc-L0-Q2-P2-A0.json` (G03 v0 F\*) | the pilot's F\* baseline and integrity check | archived 22 Nov (per query, sha256 `a4f7bb3d…`) |
| `splits/private/tasks.tsv` | masks and evaluation | rebuilt P1-DEV-only from `am7/prep-v1/meta.pkl` (as A1) |

Local and unchanged: `texts-v1/corpus.jsonl` (the local LF build, byte-identical to dr-train, A1 §6),
`texts-v1/queries.jsonl` (P1-DEV), corpus units, P1-DEV pairs, `meta.pkl`, the archived C0 scripts and their exact
original commands (`*.time`), the four pilot ledgers and costs, `apps-pilot.json` (sha256 `c6653b6f…`) and
`apps-P1-DEV.json` (25,626).

## 2. What changes

1. **Host.** Dedicated community or secure GPU pods on RunPod, each with **one GPU of at least 32 GB** (so the frozen
   memory fractions 0.15 and 0.12 give at least the V100's absolute caps), instead of the shared V100. The pods mirror
   the dr-train paths (`/data/ptp-paper2/...` and the `/home/chaw/.../models/` directory that holds the PatEmbed weights
   and the GPU lock file), so the archived C0 scripts and the frozen queue run unchanged. Several pods may run at once
   (D22): pod A encodes Qwen3; pod B encodes PatEmbed, builds the H routes and runs the assembly. Pods are deleted after
   use; reusable outputs may go to the D21 volume.
2. **Qwen3 C0 and PatEmbed C0 are rebuilt** on P1-DEV with the archived scripts and the archived commands:
   - `serialise_bridgeret_texts.py texts-v1 <Qwen3> "Instruct: Given a patent application, retrieve prior art cited against it\nQuery: " ser-qwen3-v1 24`,
     then `dense_bridgeret_v2.py <Qwen3> last <same prompt> ser-qwen3-v1 … runs/z-qwen3 0.15 P1-DEV` with `BS=8`
     (the settings of the successful `queue_qwen3_v2.sh` run);
   - `serialise_bridgeret_texts_v2.py texts-v1 <PatEmbed> "encode query for mixed document retrieval: " ser-patembed-v1 24 "encode document for mixed retrieval: "`,
     then `dense_bridgeret_v3.py <PatEmbed> mean <query prompt> ser-patembed-v1 … runs/z-patembed 0.15 P1-DEV` with
     `BS=16` and `DOC_PROMPT` (as `queue_patembed.sh`).
   - The original runs also encoded VAL queries in the same call. Query encoding is per block and the corpus side does not
     depend on the blocks, so dropping VAL changes no P1-DEV value.
   - Serialisation worker counts follow the pod's CPU quota (at most 24); `imap` keeps the output order, so the files do
     not depend on it.
3. **Weights at their recorded revisions, verified by sha256 before any encoding**
   ([`g03_a3r1_runpod_models.py`](../../../../scripts/research/g03_a3r1_runpod_models.py)):
   - `Qwen/Qwen3-Embedding-0.6B` @ `97b0c614be4d77ee51c0cef4e5f07c00f9eb65b3` (owner decision of 18 Nov), 11 files pinned by
     [`paper1-bridgeret/models.sha256`](../paper1-bridgeret/models.sha256);
   - `datalyes/patembed-large` @ `2d5c0f92a3e5dc3d5415c08e612c57543c0e03ad`, 10 files pinned by the dr-train download script
     `org-adaptive-20261105/code/dl_patembed_large.py` (archived 21 Nov) and by `MODEL_PINS` in
     [`run_dapfam_native_baseline.py`](../../../../scripts/healthtech/run_dapfam_native_baseline.py) (weights `234ea36a…`);
   - Arctic (`95c27414…`, D20) only if ser-arctic-v1 is rebuilt rather than copied (item 5).
   A mismatch stops the pod before any encoding.
   **Caveat:** the dr-train directory `models/patembed-large` itself was not hashed in the archive. The repository records
   only one patembed-large revision and one weight hash, used on dr-train in the DAPFAM and paper-2 pre-check runs.
   The rebuild gate (§3 E) is what shows that the rebuilt PatEmbed C0 reproduces the archived one.
4. **Library pins** as on dr-train: torch 2.8.0 (cu128), transformers 4.55.2, tokenizers 0.21.4, numpy 2.2.6. The pod
   script refuses other versions. scikit-learn and scipy versions are logged.
5. **Route L and the K-route index.** The P2-T02 pod rebuilt `ser-arctic-v1` and `runs/bm25` and passed its gate C (BM25)
   against the same archived records. They are **copied pod to pod** with sha256 checked at both ends. The fallback,
   rebuilding them with the archived commands (`serialise_bridgeret_texts.py … 'query: ' ser-arctic-v1 24`,
   `bm25_bridgeret.py … runs/bm25 P1-DEV`), is equally valid. In either case BM25 is re-evaluated and gated here (§3 C).
6. **G03 v0 F\* is regenerated** from the rebuilt L, Q and P runs with the unchanged harness
   ([`g03_a3r1_runpod_v0.py`](../../../../scripts/research/g03_a3r1_runpod_v0.py) calls
   `g03_route_acquisition.run_arm` for `alloc-L0-Q2-P2-A0`, budget 4). Route A (z-arctic) has a zero allocation in F\*, and
   its only harness effect is to add apps that get no rows, so it is not needed. The regenerated evaluation is the
   queue's `--v0-evals evals`. **Reason:** the frozen integrity check requires the A3r1 F\* (`alloc-L0-Q2-P2-H0-K0`, built
   from the rebuilt Q and P runs) to equal the v0 F\* per query, so both must come from the same runs. The archived v0 F\*
   is the gate reference (§3 F). It is never mixed into the decision.
7. **Pilot population.** `apps-pilot.json` is the frozen file (sha256 `c6653b6f…`). On the pod it is also regenerated
   from the rebuilt F\* run with the frozen rule (`g03_a3_routes.py apps` / `sample`, n = 2,000). Both must be identical
   (§3 G).
8. **Task file and labels.** The pod gets a P1-DEV-only `tasks.tsv` (26,575 tasks from `meta.pkl`) and `pairs-dev.tsv`
   with its P1-DEV rows only. The evaluator filters by block, so every number is unchanged. The frozen manifest, which
   lists TEST tasks, is neither read nor uploaded. No TEST block, sealed file or per-query TEST output exists on any pod,
   and the pod preflight refuses to run if one appears.
9. **Code edits: environment overrides only, dr-train defaults unchanged.**
   - `g03_queue_a3r1_pilot.sh`: `G03_PY`, `G03_GPU_DEVICE` (pod: 0), `G03_WORKERS`, `G03_EVAL_PAR`.
   - `g03_a3_routes.py`: `G03_A3_GPU_MATCH` (default `V100`). The pod sets the name of its single GPU; the GPU lock and
     the memory fraction are unchanged.
   These change host and speed only, not outputs. The H routes are built on pod B with the queue's own first command
   (label-free runtime side), and the queue later skips them.

## 3. Rebuild gate (must pass before the frozen GO/STOP rule is applied)

[`g03_a3r1_runpod_gate.py`](../../../../scripts/research/g03_a3r1_runpod_gate.py) checks against the archived dr-train
records (verified against the 21/22 Nov pull manifests at staging). Parts `qwen3` and `patembed` run on their pods to fail
fast. Part `full` runs on the assembly pod **before** the frozen queue builds any arm.

| Check | Pass condition |
|---|---|
| A. Corpus text | `texts-v1/corpus.jsonl` sha256 = archived `287ef7e0…7a86` (also checked before any GPU time) |
| A2. Query text | the 26,575 P1-DEV query records (app_id, block, title, abstract, claim) equal the dr-train extract (`g03-a3/inputs/queries-dev-val.jsonl`); order reported only |
| B. Unit order | rebuilt `runs/z-qwen3/units.json` and `runs/z-patembed/units.json` equal the archived ones |
| C. BM25-C0 | every P1-DEV mean (ALL/IN/OUT R@200 and R@1000) within **0.0005**; ALL R@200 identical per query for **≥ 99%**; same `n_queries_run` |
| D. Qwen3-C0 | every mean within **0.002**; ALL R@200 identical per query for **≥ 90%**; same `n_queries_run` |
| E. PatEmbed-C0 | as D |
| F. G03 v0 F\* | regenerated `alloc-L0-Q2-P2-A0` vs archived: as D. Also the pilot-subset means of ALL/IN/OUT R@200 within **0.002**, and the archived means equal the repository record ([g03-dev-tables.md](g03-dev-tables.md): 0.4230 / 0.4940 / 0.3334) |
| G. Pilot population | apps of the regenerated F\* run = `apps-P1-DEV.json` (25,626); the regenerated sample = `apps-pilot.json` (2,000, sha256 `c6653b6f…`) |
| H. Ledgers | every ledger record is P1-DEV; every usable app is a pilot app (file sha256s are checked by the upload manifest) |

The tolerances are those of A1, because the GPU and kernels differ from the V100. If any check fails, the pod stops
with `G03_A3R1_RUNPOD_FAILED:rebuild-gate-<part>`. No arm is built, the GO/STOP rule is not applied, the failure is
reported as it is, and nothing is repaired silently.

When the gate passes, the frozen queue runs unchanged: K routes, 75 arms per model on the 2,000 pilot apps, the
unchanged evaluator, and `g03_a3_decide.py pilot` with the frozen GO rule. All arms, including F\*, share the rebuilt
routes. The gate record is reported next to the result.

## 4. Spend and stop rules

- Envelope R2 (D22): USD 60 across parallel pods, notify at USD 45. Each pod's hourly price is stated before creation and
  recorded with its id. The expected spend for this evaluation is about USD 4–8 (see the
  [runbook](A3R1-RUNPOD-RUNBOOK.md)). A pod that has run for twice its planned hours is stopped, and the owner is told.
- No paid API is called by this evaluation (the ledgers are reused). Stage B on GO follows D16 within E1R and is not
  part of this amendment.
- Results are pulled to `../_private_artifacts/g03-a3r1-runpod/` (aggregates and the gate go into the P1-T04 receipt).
  The pods are then deleted, and billing is read and recorded.

## 5. What this cannot show

Everything in the A3r1 protocol's §9 still holds. A C0 that passes the gate is a reproduction within the stated
tolerances, not a bit-identical copy of the V100 runs. The pilot Δ is measured between arms that share the rebuilt routes,
so the comparison is internally consistent. Its absolute values may differ from a dr-train run by up to the gate
tolerances.
