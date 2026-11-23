# P2-T02 D19 follow-up (PatEmbed and Qwen3 complete content) on RunPod: runbook

Executes [P2-T02-AMENDMENT-A2-D19-FOLLOWUP.md](P2-T02-AMENDMENT-A2-D19-FOLLOWUP.md) (owner D19, envelope R2 under D22).
**Sub-cap:** USD 15 for this follow-up, with stop and report at USD 12. R2 itself is USD 60, notify at USD 45.

Before creating any pod:
- State each pod's hourly price.
- Use A100 pods only after the owner approves (the worst case is about USD 35; amendment §6).
- Record the pod id, price and start and stop times in the receipt (§9).

No TEST data, sealed file, VAL label, `meta.pkl` or credential goes to any pod.

## 0. Local staging (owner PC, USD 0, about 6 min)

From the repository root (Git Bash):

```bash
python -I scripts/research/p2t02_d19_inputs.py ../_private_artifacts . ../_private_artifacts/p2t02-d19-stage --workers 8
```

It writes:
- `tree/`;
- `FILES-claims.txt`, shared by both pods: 54 filtered claims zips, 1.40 GB;
- `FILES-qwen3.txt` and `FILES-patembed.txt`: about 2.16 GB each, including `MANIFEST-d19-<m>.sha256`;
- `stage-report.json`.

It stops on any failed local check:
- every A3r1-stage input matches `MANIFEST-a3r1.sha256`, and the corpus is `287ef7e0…`;
- tasks, pairs and queries are P1-DEV only;
- the P1-DEV cluster map in `meta-p1dev.pkl` equals the one in `meta.pkl`;
- relay tar sha256 (Qwen3 against its `.sha256`);
- relay gates passed, each relay evaluation is P1-DEV with 25,626 queries, and relay unit order is `e2ab2d4a…`;
- the P2-T02 content manifest matches the corpus.

Re-run it (after deleting the old stage directory) whenever a script under `scripts/research/p2t02_*` or
`g03_a3r1_runpod_models.py` changes, because the pod checks every file against the manifest. A dry run on 24 Nov
(`p2t02-d19-stage-try1`, made before the final commit) passed:
- 21,609,708 of 167,971,637 claims rows kept;
- 11.28 GB → 1.40 GB;
- 351 s.

## 1. Pods (two in parallel, one per model)

| Pod | Model | GPU | RAM | vCPU | Container disk | Hours (central / worst) |
|---|---|---|---|---|---|---|
| Q | `qwen3` | 1 × ≥ 32 GB: RTX PRO 4500 32 GB (preferred), L40S, RTX 6000 Ada, A40 | ≥ 64 GB | ≥ 12 | 150 GB | 6.3 h / 10.8 h |
| P | `patembed` | same class | ≥ 64 GB | ≥ 12 | 150 GB | 3.9 h / 5.3 h |

- **Expected spend:** about USD 7.3 at USD 0.72/h (range 6.2–8.7; worst case 11.6).
- **Stop a pod at twice its planned hours:** pod Q at 14 h, pod P at 9 h.
- **Image:** the one used for P2-T02 pod `jd41r4cvv171q6` (torch 2.8.0+cu128; works on Blackwell, compute capability
  12.0).
- **Data centre:** a US one. The owner PC uploads at about 1.5–3 MB/s per stream to the US; EU-SE-1 gave 47 KB/s.
- **Network volume:** none (§8 for the optional D21 copy).

## 2. Setup on each new pod

```bash
apt-get update -qq && apt-get install -y -qq time            # GNU time is not in the image
pip install -q "transformers==4.55.2" "tokenizers==0.21.4" "numpy==2.2.6" huggingface_hub
python3 -c 'import torch,transformers,tokenizers,numpy;print(torch.__version__,transformers.__version__,tokenizers.__version__,numpy.__version__)'
# must print 2.8.0+cu128 4.55.2 0.21.4 2.2.6 (the pod script refuses anything else)
```

## 3. Upload (owner PC, Git Bash; `ST=../_private_artifacts/p2t02-d19-stage`)

Use two streams per pod. The claims zips are already compressed. The main list carries the 1.8 GB corpus, which
`gzip -1` roughly halves. Every list has LF line ends: they are written with `newline='\n'`. Check with
`file $ST/FILES-*.txt`, which must not say CRLF.

```bash
# pod Q (host $HQ, port $PQ)
tar -C $ST/tree -cf - -T $ST/FILES-claims.txt | ssh -p $PQ root@$HQ 'tar -C / -xf - --no-same-owner' &
tar -C $ST/tree -cf - -T $ST/FILES-qwen3.txt | gzip -1 | ssh -p $PQ root@$HQ 'tar -C / -xzf - --no-same-owner' &
wait
# pod P (host $HP, port $PP)
tar -C $ST/tree -cf - -T $ST/FILES-claims.txt | ssh -p $PP root@$HP 'tar -C / -xf - --no-same-owner' &
tar -C $ST/tree -cf - -T $ST/FILES-patembed.txt | gzip -1 | ssh -p $PP root@$HP 'tar -C / -xzf - --no-same-owner' &
wait
```

About 2.6 GB goes on the wire per pod: about 6–10 min per pod at 4–8 MB/s. Pod P may start uploading while pod Q runs.
The pod script checks every uploaded file against `MANIFEST-d19-<m>.sha256` (`sha256sum -c`, no missing file allowed)
before it starts. The weights are fetched on the pod at the pinned revisions and checked file by file
(`g03_a3r1_runpod_models.py`).

## 4. Launch (Q and P in parallel)

```bash
ssh -p $PQ root@$HQ 'setsid nohup bash /data/ptp-paper2/p2-coverage/code/p2t02_d19_runpod.sh qwen3 > /data/ptp-paper2/d19-qwen3.log 2>&1 < /dev/null &'
ssh -p $PP root@$HP 'setsid nohup bash /data/ptp-paper2/p2-coverage/code/p2t02_d19_runpod.sh patembed > /data/ptp-paper2/d19-patembed.log 2>&1 < /dev/null &'
```

The pod defaults are `P2T02_GPU_DEVICE=0`, `P2T02_D19_BS=32` and `P2T02_D19_FRAC=0.5` (speed only; amendment §3). If
`encode-c1` fails with an out-of-memory error, relaunch with `P2T02_D19_BS=16`: finished shards are kept. Record the
retry in the receipt.

## 5. Watch

```bash
ssh -p $PQ root@$HQ 'grep -E "^(S[0-9]|P2T02_D19)" /data/ptp-paper2/d19-qwen3.log; tail -2 /data/ptp-paper2/p2-coverage/d19/qwen3/logs/encode-c1.log'
```

The stage lines are:
1. `S0_PREFLIGHT_PASSED`;
2. `S1_WEIGHTS_VERIFIED`;
3. `S2_RELAY_GATE_PASSED`;
4. `S3_SER_DONE`;
5. `S4_WINDOW=<W>`;
6. `S5_CONTENT_DONE`;
7. `S7_GPU_CHECKS_AND_QUERIES_DONE`;
8. `S6_CONTENT_GATE_PASSED`;
9. `S8_ENCODE_C1_DONE`;
10. `S9_RETRIEVE_C1_DONE`;
11. `S10_EVAL_DONE`;
12. `S11_FINAL_GATE_PASSED`;
13. `S12_DECIDE_DONE`;
14. `P2T02_D19_<MODEL>_DONE`.

The encode log prints passages per second per shard. Extrapolate the remaining hours after the first two shards. If the
projection passes twice the planned hours (§1), stop and ask the owner.

`P2T02_D19_FAILED:<stage>` ends the run:
- **A gate stage** (`gate-relay`, `gate-content-arctic-reproduction`, `validate`, `c0check`, `gate-final`): report it as
  it is and do not continue.
- **Anything else** (for example `encode-c1` out of memory): fix the host cause and relaunch. The script resumes.

## 6. Pull and verify (each pod, as soon as it finishes)

```bash
L=../_private_artifacts/p2t02-d19-runpod; mkdir -p $L
for m in qwen3; do   # on pod P: m=patembed, $PP/$HP
  ssh -p $PQ root@$HQ "cat /data/ptp-paper2/out/p2t02-d19-$m-results.tgz" > $L/p2t02-d19-$m-results.tgz
  ssh -p $PQ root@$HQ "cat /data/ptp-paper2/out/p2t02-d19-$m-results.tgz.sha256"
  sha256sum $L/p2t02-d19-$m-results.tgz      # must equal the pod's value
  ssh -p $PQ root@$HQ "cat /data/ptp-paper2/d19-$m.log" > $L/d19-$m.log
done
```

Each archive is about 0.27 GB. It holds:
- `results-<m>.json`;
- `gates/` (every gate record);
- `window.json`;
- the content `manifest.json` and `stats.json`;
- `encode.json`;
- the per-query C1 evaluation;
- the C1 run;
- all logs.

The content, the vectors and `ser-<m>-v1` stay on the pod and are deleted with it, unless §8 applies.

## 7. Delete and record

1. Delete each pod right after its pull is verified. `list-pods` must be empty at the end.
2. Read billing (`list-billing` / pod billing) and record the actual spend per pod against R2.
3. Fill in the receipt (§9). Update the tracker through `python scripts/tracking/ptp_tracker.py`, and update HANDOFF.
4. Report to the owner in Thai.

## 8. Optional: keep reusable outputs on a D21 volume (owner choice; about USD 2.2/month)

Before deleting a pod, copy `p2-coverage/d19/<m>/enc/c1/passages.f16.npy` (about 8.6 GB), `content/c1.*` (about 7 GB) and
`content/units.json` to a network volume in a data centre that offers one, through a cheap CPU pod, as D21 describes.
Nothing else goes there. Record the volume id and size in the receipt and HANDOFF.

## 9. Receipt template (`docs/tracking/owner-note-22112026/receipts/P2-T02_D19_followup_results.md`)

```markdown
# P2-T02 D19 follow-up — PatEmbed and Qwen3 complete content (P1-DEV only)

**Protocol:** P2-T02-COVERAGE-CONTROL-PROTOCOL.md (frozen bd30d3f7) with amendment A2 (declared <commit>).
**Pods:** Q `<id>` <GPU>, <DC>, USD <price>/h, <start>–<end> UTC (<h> h); P `<id>` …; both deleted (list-pods empty).
**Spend:** USD <x> (billing read <date>); R2 used so far USD <y> of 60. Retries: <none | stage, cause>.
**Outputs (private):** ../_private_artifacts/p2t02-d19-runpod/ (tgz sha256: <…>, <…>).

## Gates
| Gate | Qwen3 | PatEmbed |
|---|---|---|
| P preflight, W weights | | |
| C-R C0 reference (relay ALL R@200) | 0.34736 | 0.41806 |
| C-A Arctic content reproduction (8 outputs identical) | | |
| Window W (head / tail ids) | | |
| V id path = text path (token identity, min cos) | | |
| Q C0 score reproduction (median / share ≤ 0.005) | | |
| F final | | |

## Arm table (P1-DEV, query-macro; 25,626 queries run, population 26,547)
| Arm | ALL R@200 | IN R@200 | OUT R@200 | ALL R@1000 | OUT MRR |
|---|---|---|---|---|---|
| Qwen3 C0 (A3r1 rebuild) | | | | | |
| Qwen3 C1 | | | | | |
| PatEmbed C0 (A3r1 rebuild) | | | | | |
| PatEmbed C1 | | | | | |
| Arctic C0 / C1 (P2-T02, reading only) | 0.2980 / 0.3145 | | | | |

## Frozen contrasts (cluster bootstrap by art unit, B = 10,000, seed 20261119)
| Contrast | ALL R@200 Δ [95% CI] | IN | OUT | wins / losses |
|---|---|---|---|---|
| Qwen3 C1 − C0 | | | | |
| PatEmbed C1 − C0 | | | | |

## Decision (frozen rule, `p2t02_d19_decide.py`)
- Qwen3: <C1 becomes the Qwen3 representation baseline | NO_GAIN, keep C0>.
- PatEmbed: <…>.
- Engineering controls only: "more eligible text was indexed". Not evidence for the acquisition method.

## Descriptives and cost
New candidates, recovery and displacement @200/@1000; content stats (passages, tokens, separator ids, join-difference
sample); wall time and peak memory per stage (ser, build, gates, queries, encode, retrieve, decide).

## Incidents
<none | as they happened>
```
