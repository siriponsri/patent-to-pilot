# P2-T02 amendment A1: run on a dedicated RunPod pod with a rebuilt C0. Declared before any P2-T02 number

**Amends:** [P2-T02-COVERAGE-CONTROL-PROTOCOL.md](P2-T02-COVERAGE-CONTROL-PROTOCOL.md) (frozen bd30d3f7).
**Declared:** 23 Nov 2026, afternoon. No P2-T02 number exists: the only full launch (23 Nov, dr-train) died in the content
build and produced no run, evaluation or contrast ([run notes](P2-T02-RUN-NOTES.md) §4).
**Owner authority:** D20 (RunPod envelope R1, USD 20, stop and report at USD 15, no network volume) and the owner's
"Yes, run now" to running on RunPod without waiting for dr-train
([OWNER-DECISIONS-20261122.md](../../../maintenance/OWNER-DECISIONS-20261122.md)).

## 1. Why

dr-train has been unreachable since about 07:00 on 23 Nov after our first content build exhausted its memory. The frozen
protocol reads four C0 inputs that exist only on dr-train: `texts-v1/corpus.jsonl`, `ser-arctic-v1`, the C0 runs
(`runs/z-arctic` vectors and P1-DEV run, `runs/bm25` P1-DEV run) and `splits/private/tasks.tsv`. Everything else is local:
the PatentsView sources in `data/raw/uspto/` (git-ignored; the same 54 claims files the original text build used) and the
dr-train archive of 21 Nov (corpus units, P1-DEV pairs, `am7/prep-v1/meta.pkl`, the C0 code, and the archived C0
P1-DEV evaluator records with per-query values).

## 2. What changes

1. **Host.** One dedicated community GPU pod on RunPod (RTX 6000 Ada or RTX 4090 class, the cheapest with at least 60 GB
   RAM and 150 GB pod disk), instead of the shared V100. The pod mirrors the dr-train paths so the frozen scripts run
   unchanged. No network volume: the data lives on the pod's own disk and is removed when the pod is deleted.
2. **C0 is rebuilt on the pod** with the archived code and the archived commands (from the `*.time` records):
   `build_bridgeret_texts.py` → `serialise_bridgeret_texts.py` (Arctic tokenizer, prompt `query: `) →
   `dense_bridgeret.py` (Arctic, CLS, memory fraction 0.11, P1-DEV only) and `bm25_bridgeret.py` (P1-DEV only).
   Arctic is `Snowflake/snowflake-arctic-embed-m-v2.0` at the owner-approved revision
   `95c2741480856aa9666782eb4afe11959938017f` (decision of 18 Nov; the same item, now fetched to the pod). Library pins:
   torch 2.8.0 (cu128), transformers 4.55.2, numpy 2.2.6, as on dr-train; the versions actually loaded are logged.
   The text builder imports the flat `bridgeret_query.py` (sha256 identical to `src/patent_to_pilot/research/`), so it
   runs without `-I` on the pod.
3. **Task file.** The pod gets a **P1-DEV-only** `tasks.tsv` (`app_id`, `block`, `filing_date` for the 26,575 P1-DEV
   tasks, from `am7/prep-v1/meta.pkl`) and a P1-DEV-only text manifest. The frozen manifest, which lists TEST tasks, is not
   read and not uploaded. `pairs-dev.tsv` is uploaded with its P1-DEV rows only (the evaluator filters by block, so every
   number is unchanged). No TEST block, sealed file or TEST label exists on the pod.
4. **Device.** The pod's single GPU is device 0 (`P2T02_GPU_DEVICE=0`); the GPU lock and memory-fraction code paths run
   as written. CPU thread and worker counts follow the pod's core count (they change speed, not outputs).
5. **G03-dependent descriptive checks are deferred.** The "deeper original-query control" and the fusion check (protocol
   §5, descriptive only) read G03 route runs that are on dr-train. On the pod they are skipped (`P2T02_NO_G03=1`) and are
   computed later on dr-train from the pulled runs. The primary endpoints, contrasts and the decision rule are unchanged.

## 3. Rebuild gate (must pass before any C1/C2 number is interpreted)

`scripts/research/p2t02_rebuild_gate.py`, against the archived C0 records:

| Check | Pass condition |
|---|---|
| A. Corpus text | rebuilt `texts-v1/corpus.jsonl` sha256 = archived `287ef7e0…7a86` (byte-identical) |
| B. Unit order | rebuilt `runs/z-arctic/units.json` = archived `units.json` |
| C. BM25-C0 | every P1-DEV mean (ALL/IN/OUT R@200 and R@1000) within **0.0005** of the archived evaluation; ALL R@200 identical per query for **≥ 99%** of queries; same `n_queries_run` |
| D. Arctic-C0 | every mean within **0.002** (different GPU and kernels than the V100); ALL R@200 identical per query for **≥ 90%** of queries; same `n_queries_run` |

Check A also runs first, before any GPU time is spent. If any check fails, the pod stops with `P2T02_RUNPOD_FAILED`, no
C1/C2 stage runs, the failure is reported as it is, and nothing is repaired silently.

When the gate passes, **C1, C2 and BM25-full are contrasted against the rebuilt C0** (same pod, same software), with the
frozen contrasts, cluster bootstrap and decision rule. The archived C0 values are reported next to them.

## 4. Spend and stop rules

- Envelope R1 (D20): cap USD 20, stop and report at USD 15. The pod's hourly price is recorded at creation; the local
  watcher stops waiting once the pod has run for (15 / hourly price) hours, so the agent stops and deletes the pod.
- One pod, one run. Results are pulled to `../_private_artifacts/p2t02-runpod/` (aggregates go into the receipt), then
  the pod is deleted. Spend is recorded in the P2-T02 receipt from the RunPod billing read.

## 5. What this cannot show

Everything in protocol §6 still holds. In addition, a C0 that passes the gate is a reproduction within the stated
tolerances, not a bit-identical copy of the V100 run.
