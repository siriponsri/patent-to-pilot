# A3r1 pilot evaluation on RunPod: runbook

Executes [A3R1-AMENDMENT-RUNPOD-REBUILD.md](A3R1-AMENDMENT-RUNPOD-REBUILD.md) (owner D22/D23). Envelope R2: USD 60, notify
at USD 45. State each pod's hourly price before creating it, and record the pod id, price and start/stop times in the
P1-T04 receipt. No TEST data, sealed file or credential goes to any pod.

## 0. Local staging (owner PC, USD 0, about 15 s; already run once on 23 Nov)

```bash
python -I scripts/research/g03_a3r1_runpod_inputs.py ../_private_artifacts . ../_private_artifacts/g03-a3r1-runpod-stage
```

Writes `tree/` (40 files), `FILES-qwen3.txt` (about 1.94 GB), `FILES-patembed.txt` (about 2.06 GB),
`FILES-assemble-extra.txt` and `stage-report.json`. It also runs the local pre-checks and stops on any failure:
- A: corpus sha256 `287ef7e0…`;
- A2: 26,575 P1-DEV query records equal the dr-train extract;
- G: the pilot sample regenerated from `apps-P1-DEV.json` equals `apps-pilot.json`;
- H: ledgers are P1-DEV and inside the pilot;
- every archived reference matches the dr-train pull manifests.

Re-run it (after deleting the old stage directory) whenever a script under `scripts/research/g03_*` changes.

## 1. Pods

| Pod | Role | GPU | RAM | vCPU | Disk | Wall time (estimate) |
|---|---|---|---|---|---|---|
| A | `qwen3` | 1 × ≥ 32 GB (RTX PRO 4500 32 GB, A40, L40S, RTX 6000 Ada, V100 32 GB) | ≥ 32 GB | ≥ 8 (12+ better) | 50 GB | setup 0.3 h + ser 0.2 h + encode/retrieve **2–4 h** (V100: 4:00 h with VAL) + eval 0.1 h ≈ **3–4.5 h** |
| B | `patembed` | same class | ≥ 64 GB | ≥ 12 | 80 GB | setup 0.3 h + ser 0.2 h + encode/retrieve **1–2 h** (V100: 1:46 h with VAL) + H routes 0.3 h ≈ **2–3 h** |
| A or B | `assemble` (CPU; runs on whichever pod finishes last) | none needed | ≥ 64 GB on that pod (evaluators: 4 GB each) | ≥ 12 | +10 GB | L-route check + v0 F\* 0.2 h, gate 0.1 h, K routes 0.3 h, 4 × 75 arms + evaluation 0.5–1 h, decision < 0.1 h ≈ **1–1.5 h** |

Expected spend at about USD 0.6–0.8/h: A about USD 2.5–4, B about USD 1.5–2.5 (if B is deleted after its relay), so
**about USD 4–7**. One-pod alternative: role `all` on one ≥ 64 GB RAM pod, about 5–7.5 h, about USD 3.5–6.

Image: the same one used for P2-T02 pod `jd41r4cvv171q6` (torch 2.8.0+cu128; works on Blackwell compute capability
12.0). Use a US data centre (the owner PC uploads at about 1.5–3 MB/s per stream to the US; EU-SE-1 gave 47 KB/s).
No network volume is needed. Optionally keep `runs/z-qwen3/passages.f16.npy` and `runs/z-patembed/passages.f16.npy`
(2 GB each) on the D21 volume for the D19 follow-ups.

## 2. Setup on each new pod

```bash
apt-get update -qq && apt-get install -y -qq time            # GNU time is not in the image
pip install -q "transformers==4.55.2" "tokenizers==0.21.4" "numpy==2.2.6" scikit-learn scipy huggingface_hub
python3 -c 'import torch,transformers,tokenizers,numpy;print(torch.__version__,transformers.__version__,tokenizers.__version__,numpy.__version__)'
# must print 2.8.0+cu128 4.55.2 0.21.4 2.2.6 (the pod script refuses anything else)
```

## 3. Upload (owner PC, Git Bash; `ST=../_private_artifacts/g03-a3r1-runpod-stage`)

```bash
# pod A (about 1.94 GB; gzip -1 roughly halves the corpus on the wire)
tar -C $ST/tree -cf - -T $ST/FILES-qwen3.txt | gzip -1 | ssh -p $PA root@$HA 'tar -C / -xzf - --no-same-owner'
# pod B (about 2.06 GB)
tar -C $ST/tree -cf - -T $ST/FILES-patembed.txt | gzip -1 | ssh -p $PB root@$HB 'tar -C / -xzf - --no-same-owner'
```

The pod script checks every uploaded file against `MANIFEST-a3r1.sha256` (`sha256sum -c --ignore-missing`) before it
starts. Weights are fetched on the pod from Hugging Face at the pinned revisions and verified by sha256
(`g03_a3r1_runpod_models.py`).

## 4. Launch (A and B in parallel)

```bash
ssh -p $PA root@$HA 'setsid nohup bash /data/ptp-paper2/g03-dev/code/g03_a3r1_runpod.sh qwen3 > /data/ptp-paper2/a3r1-qwen3.log 2>&1 < /dev/null &'
ssh -p $PB root@$HB 'setsid nohup bash /data/ptp-paper2/g03-dev/code/g03_a3r1_runpod.sh patembed > /data/ptp-paper2/a3r1-patembed.log 2>&1 < /dev/null &'
```

Watch with `tail -3 /data/ptp-paper2/a3r1-<role>.log`. Each log ends with:
- `G03_A3R1_RUNPOD_<ROLE>_DONE` then `G03_A3R1_RUNPOD_DONE`; or
- `G03_A3R1_RUNPOD_FAILED:<stage>`.

A failure in `rebuild-gate-qwen3` or `rebuild-gate-patembed` stops everything: report it and do not assemble.

## 5. Bring the inputs of the assembly together (on the pod that finishes last; called X below)

```bash
# relay from the other pod via the owner PC; this also keeps a local copy
L=../_private_artifacts/g03-a3r1-runpod; mkdir -p $L
ssh -p $PA root@$HA 'cat /data/ptp-paper2/out/a3r1-qwen3-relay.tar' > $L/a3r1-qwen3-relay.tar          # about 0.3 GB
ssh -p $PA root@$HA 'cat /data/ptp-paper2/out/a3r1-qwen3-relay.tar.sha256'                              # compare with sha256sum $L/...
ssh -p $PX root@$HX 'tar -C / -xf - --no-same-owner' < $L/a3r1-qwen3-relay.tar                         # if X = B
# (if X = A instead: relay a3r1-patembed-relay.tar from B the same way, and upload FILES-assemble-extra.txt to A)

# L route and K-route passages from the P2-T02 pod (its gate C passed): checksums at the source, copy, check at the target
ssh -p 14876 root@216.81.151.69 'cd / && sha256sum data/ptp-paper2/bridgeret/ser-arctic-v1/passages.jsonl data/ptp-paper2/bridgeret/runs/bm25/run-P1-DEV.tsv.gz' > $L/bm25copy.sha256
ssh -p 14876 root@216.81.151.69 'tar -C / -czf - data/ptp-paper2/bridgeret/ser-arctic-v1/passages.jsonl data/ptp-paper2/bridgeret/runs/bm25/run-P1-DEV.tsv.gz data/ptp-paper2/bridgeret/rebuild-gate.json' \
  | ssh -p $PX root@$HX 'tar -C / -xzf - --no-same-owner'
ssh -p $PX root@$HX 'cat > /data/ptp-paper2/bridgeret/runs/bm25/copied-from-p2t02.sha256' < $L/bm25copy.sha256
```

The copy is about 1.5–2 GB through the owner PC, about 10–20 min. Alternative without the P2-T02 pod: launch the
assembly with `A3R1_REBUILD_BM25=1`. It fetches the pinned Arctic files, builds `ser-arctic-v1` (about 10 min) and
BM25-C0 on P1-DEV (about 20–30 min, CPU). The assembly re-evaluates BM25 and gates it in either case.

## 6. Assemble, gate, frozen decision

```bash
ssh -p $PX root@$HX 'setsid nohup bash /data/ptp-paper2/g03-dev/code/g03_a3r1_runpod.sh assemble > /data/ptp-paper2/a3r1-assemble.log 2>&1 < /dev/null &'
```

Order inside: L-route check → evaluations → v0 F\* + pilot population regenerated → **full rebuild gate**
(`/data/ptp-paper2/g03-dev/rebuild-gate-a3r1.json`) → the frozen `g03_queue_a3r1_pilot.sh` (K routes, arms, evaluation,
`g03_a3_decide.py pilot`) → `results-a3r1-pilot.json`. The frozen GO/STOP rule is applied only if the gate passed.

## 7. Pull, record, delete

```bash
for f in a3r1-pilot-results.tgz a3r1-pilot-evals.tgz a3r1-pilot.sha256 a3r1-patembed-relay.tar; do
  ssh -p $PX root@$HX "cat /data/ptp-paper2/out/$f" > $L/$f; done      # evals tgz holds the 300 per-query evaluations
```

Then:
1. Check the sha256s.
2. Write the aggregates, the gate table, pod ids, prices and hours into the P1-T04 receipt.
3. Delete both pods; `list-pods` must be empty.
4. Read billing and record it against R2.
5. Report to the owner in Thai.

On GO, Stage B follows D16 within E1R (not part of this runbook).

## Full evaluation after Stage B

Executes [A3R1-FULL-EVAL-RUNPOD.md](A3R1-FULL-EVAL-RUNPOD.md): one pod, P1-DEV and VAL, m\* =
`deepseek/deepseek-v4-flash-0731`.

**Do not create the pod until both conditions hold:**
1. **Stage B is complete:** step F-1 exits 0.
2. **The owner has recorded an envelope or an R2 scope extension for this evaluation.** R2 names the pilot evaluation
   only.

State the hourly price before creating the pod. No TEST data, sealed file or credential goes to the pod.

### F-1. Local check (owner PC, USD 0, about 30 s; safe to repeat while Stage B runs)

```bash
python -I scripts/research/g03_a3r1_full_inputs.py ../_private_artifacts . ../_private_artifacts/g03-a3r1-full-check --check-only
```

The exit code says whether the pod may start:
- **0:** every input is verified and Stage B is complete;
- **2:** every input is verified but Stage B is not complete (the report gives the counts per block);
- **1:** a check failed.

What it checks:
- the m\* ledgers (gate part `ledger`);
- every archived input against the 21/22 Nov pull manifests;
- the qwen3 relay and the pilot results archive against their recorded sha256, and the patembed relay through its
  evaluation being byte-identical to the pilot's;
- the pilot results record GO with m\*;
- relay unit order;
- corpus sha256;
- the P1-DEV query records;
- the VAL text rule on all P1-DEV records;
- the pilot sample;
- `apps-VAL.json` = the apps of the archived VAL F\* run.

Check of 24 Nov (inputs OK; Stage B incomplete at P1-DEV 5,248/25,626, VAL not started; pilot prefix intact).

### F-2. Stage the upload tree (after F-1 exits 0; about 1 min)

```bash
python -I scripts/research/g03_a3r1_full_inputs.py ../_private_artifacts . ../_private_artifacts/g03-a3r1-full-stage
```

It writes the following and stops on any failed check:
- `tree/` (about 2.7–2.8 GB: corpus 1.8 GB, relay runs 0.5 GB, VAL runs 0.06 GB, ledgers about 0.1 GB, references);
- `FILES-full.txt` (LF);
- `stage-report-full.json`;
- `MANIFEST-a3r1-full.sha256`, which the pod checks strictly, with no `--ignore-missing`.

Re-stage (delete the old stage directory first) whenever a script under `scripts/research/g03_*` changes.

### F-3. Pod

| Item | Value |
|---|---|
| GPU | 1 × ≥ 32 GB. Preferred: RTX PRO 4500 32 GB (about USD 0.72/h, community). Faster: A100 80 GB (about USD 2.19/h, Secure Cloud). Also fine: L40S, A40, RTX 6000 Ada |
| RAM / vCPU / disk | ≥ 64 GB (94 GB fine) / ≥ 12 (14 fine) / 100 GB (arms need about 15 GB, the re-encoded vectors 2 GB) |
| Image | as the pilot (torch 2.8.0+cu128; Blackwell works) |
| Data centre | US (upload about 1.5–3 MB/s per stream; EU-SE-1 gave 47 KB/s) |
| Volume | none |

| Stage | A100 80 GB | RTX PRO 4500 |
|---|---|---|
| Setup + upload (about 1.9 GB on the wire with `gzip -1`) | 0.4 h | 0.4 h |
| F0 ledger gate; F1 Arctic pins, `ser-arctic-v1`, BM25-C0 P1-DEV (CPU) | 0.4–0.6 h | 0.5–0.7 h |
| F2 six route evaluations, F3 v0 F\* × 2, gate part `cpu` | 0.2 h | 0.2 h |
| F4 `ser-patembed-v1` + PatEmbed re-encode and retrieval (pilot: 1:04 h on A100), gate part `enc` | 1.2 h | 2–2.5 h |
| F5 H (about 27.5k queries), K, 150 arms, 150 evaluations, decision | 1.2–1.5 h | 1.3–1.7 h |
| Pack + pull | 0.3 h | 0.3 h |
| **Total (with margin)** | **4–5.5 h, about USD 9–12** | **5.5–7.5 h, about USD 4–5.5** |

### F-4. Setup and upload

```bash
apt-get update -qq && apt-get install -y -qq time
pip install -q "transformers==4.55.2" "tokenizers==0.21.4" "numpy==2.2.6" "scikit-learn==1.7.2" "scipy==1.18.1" huggingface_hub
python3 -c 'import torch,transformers,tokenizers,numpy,sklearn,scipy;print(torch.__version__,transformers.__version__,tokenizers.__version__,numpy.__version__,sklearn.__version__,scipy.__version__)'
# must print 2.8.0+cu128 4.55.2 0.21.4 2.2.6 1.7.2 1.18.1 (role full refuses anything else)
```

```bash
# owner PC, Git Bash
ST=../_private_artifacts/g03-a3r1-full-stage
tar -C $ST/tree -cf - -T $ST/FILES-full.txt | gzip -1 | ssh -p $PX root@$HX 'tar -C / -xzf - --no-same-owner'
```

**Optional.** If a P2-T02 copy of `ser-arctic-v1/passages.jsonl` and `runs/bm25/run-P1-DEV.tsv.gz` still exists, put it
on the pod at the same paths and launch with `A3R1_COPIED_BM25=1`. The pod then checks both files against the recorded
sha256 instead of rebuilding them (saves about 0.5 h). Gate K0 and gate C apply either way.

### F-5. Launch and watch

```bash
ssh -p $PX root@$HX 'setsid nohup bash /data/ptp-paper2/g03-dev/code/g03_a3r1_runpod.sh full > /data/ptp-paper2/a3r1-full.log 2>&1 < /dev/null &'
ssh -p $PX root@$HX 'tail -3 /data/ptp-paper2/a3r1-full.log'
```

**Progress stamps:**
1. `GATE_FULL_ledger_PASSED`
2. `F1_L_ROUTE_READY`
3. `F2_ROUTE_EVALS_DONE`
4. `F3_V0_FSTAR_DONE`
5. `GATE_FULL_cpu_PASSED`
6. `F4_PATEMBED_REENCODED`
7. `GATE_FULL_enc_PASSED`
8. the decision lines of the queue
9. `G03_A3R1_RUNPOD_FULL_DONE`, then `G03_A3R1_RUNPOD_DONE`

**On failure.** The log ends with `G03_A3R1_RUNPOD_FAILED:<stage>`. If the failure is in a gate part, stop: report it,
apply no decision, and repair nothing silently. The run is resumable after a host failure **until**
`results-a3r1-full.json` exists.

### F-6. Pull, record, delete

```bash
L=../_private_artifacts/g03-a3r1-full-runpod; mkdir -p $L
for f in a3r1-full-results.tgz a3r1-full-evals.tgz a3r1-full.sha256; do
  ssh -p $PX root@$HX "cat /data/ptp-paper2/out/$f" > $L/$f; done      # about 1 GB + 0.2 GB
ssh -p $PX root@$HX 'cat /data/ptp-paper2/a3r1-full.log' > $L/a3r1-full.log
```

The results archive holds:
- `results-a3r1-full.json`;
- the three gate records (`bridgeret/logs/gate-full-*.json`);
- logs;
- the H/K routes of both blocks;
- the F\* and F3\* runs of both blocks;
- the arm traces;
- the v0 F\* evaluations;
- the rebuilt BM25 P1-DEV run.

The evaluations archive holds all 150 per-query evaluations.

Then:
1. Check the sha256s.
2. Write the gate table, F3\*, the VAL principal with its intervals, the decision, pod id, price and hours into the
   receipt.
3. Delete the pod; `list-pods` must be empty.
4. Read billing and record it against the envelope.
5. Report to the owner in Thai.
