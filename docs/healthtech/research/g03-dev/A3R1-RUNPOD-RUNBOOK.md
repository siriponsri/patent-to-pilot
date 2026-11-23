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
