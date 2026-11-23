#!/usr/bin/env bash
# P2-T02 on a dedicated RunPod pod (amendment A1, docs/healthtech/research/p2-coverage/P2-T02-AMENDMENT-A1-RUNPOD.md).
# The pod mirrors the dr-train paths, so every frozen script runs unchanged:
#   /data/ptp-paper2/{patentsview, challenge1m/out-v1, splits/private/tasks.tsv (P1-DEV rows only), manifest-v1/out-v2,
#   bridgeret/{code, am7/prep-v1/meta.pkl, archived-c0}, models/arctic-embed-m-v2.0, p2-coverage/code}
# Stages: R1 texts-v1 | R2 ser-arctic-v1 | R3 Arctic C0 (GPU) || R4 BM25 C0 (CPU) | R5 evaluate + rebuild gate | then the
# frozen p2t02_queue.sh with P2T02_GPU_DEVICE=0 P2T02_NO_G03=1. P1-DEV only; no TEST block exists on the pod.
# Ends with P2T02_RUNPOD_DONE or P2T02_RUNPOD_FAILED:<stage>. Resumable.
# Launch: setsid nohup bash /data/ptp-paper2/p2-coverage/code/p2t02_runpod.sh > /data/ptp-paper2/runpod.log 2>&1 < /dev/null &
set -uo pipefail
D=/data/ptp-paper2
BR=$D/bridgeret
C=$D/challenge1m/out-v1
T=$D/splits/private/tasks.tsv
M=$D/models/arctic-embed-m-v2.0
NPROC=$(nproc)
# a container sees the host cores; use the cgroup CPU quota when there is one (amendment A1)
Q=$(cat /sys/fs/cgroup/cpu/cpu.cfs_quota_us 2>/dev/null || echo -1); PER=$(cat /sys/fs/cgroup/cpu/cpu.cfs_period_us 2>/dev/null || echo 100000)
if [ "$Q" -gt 0 ] 2>/dev/null; then NPROC=$(( (Q + PER - 1) / PER )); fi
export TOKENIZERS_PARALLELISM=false PYTHONNOUSERSITE=1
stamp() { echo "$1 $(date -Is)"; }
fail() { echo "P2T02_RUNPOD_FAILED:$1 $(date -Is)"; exit 1; }
stamp "P2T02_RUNPOD_START host=$(hostname) nproc=$NPROC mem=$(free -g | awk '/Mem/{print $2}')G"
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader
python3 -c 'import torch, transformers, numpy, sklearn, scipy; print("versions", torch.__version__, transformers.__version__, numpy.__version__, sklearn.__version__, scipy.__version__)'
cd "$BR" || exit 1
mkdir -p logs runs

# R1 texts (CPU; P1-DEV-only manifest built locally from meta.pkl, corpus side identical)
if [ ! -s texts-v1/report.json ]; then
  rm -rf texts-v1
  /usr/bin/time -v -o logs/texts.time python3 code/build_bridgeret_texts.py "$D/patentsview" \
    "$D/manifest-v1/out-v2/manifest-p1dev.json" "$C/corpus-units.tsv" texts-v1 $NPROC > logs/texts.log 2>&1 || fail texts
fi
stamp R1_TEXTS_DONE
# early check of gate A (fail fast before any GPU time)
python3 -I -c "
import hashlib,json,sys
h=hashlib.sha256(); f=open('texts-v1/corpus.jsonl','rb')
for b in iter(lambda: f.read(1<<22), b''): h.update(b)
w=json.load(open('archived-c0/texts-report.json'))['outputs_sha256']['corpus.jsonl']
print('corpus.jsonl', h.hexdigest(), 'archived', w); sys.exit(0 if h.hexdigest()==w else 1)" || fail gateA-corpus-text

# R2 serialised Arctic texts
if [ ! -s ser-arctic-v1/queries.jsonl ]; then
  rm -rf ser-arctic-v1
  /usr/bin/time -v -o logs/ser.time python3 code/serialise_bridgeret_texts.py texts-v1 "$M" 'query: ' ser-arctic-v1 \
    $(( NPROC < 24 ? NPROC : 24 )) > logs/ser.log 2>&1 || fail ser
fi
stamp R2_SER_DONE

# R3 Arctic C0 (GPU) and R4 BM25 C0 (CPU) in parallel
( if [ ! -s runs/z-arctic/run-P1-DEV.tsv.gz ]; then
    CUDA_VISIBLE_DEVICES=0 /usr/bin/time -v -o logs/zarctic.time python3 code/dense_bridgeret.py "$M" cls 'query: ' \
      ser-arctic-v1 "$C/corpus-units.tsv" "$T" runs/z-arctic 0.11 P1-DEV > logs/zarctic.log 2>&1 &&
    gzip -f runs/z-arctic/run-P1-DEV.tsv
  fi ) & A=$!
( if [ ! -s runs/bm25/run-P1-DEV.tsv.gz ]; then
    CUDA_VISIBLE_DEVICES= /usr/bin/time -v -o logs/bm25.time python3 code/bm25_bridgeret.py ser-arctic-v1 \
      "$C/corpus-units.tsv" "$T" runs/bm25 P1-DEV > logs/bm25.log 2>&1 && gzip -f runs/bm25/run-P1-DEV.tsv
  fi ) & B=$!
wait $A || fail arctic-c0; wait $B || fail bm25-c0
stamp R4_C0_RUNS_DONE

# R5 evaluate the rebuilt C0 runs and apply the rebuild gate (A-E, amendment A1 section 3)
mkdir -p evals-c0
for n in z-arctic bm25; do
  [ -s evals-c0/$n.json ] || python3 -I code/eval_bridgeret_dev.py <(zcat runs/$n/run-P1-DEV.tsv.gz) "$C/pairs-dev.tsv" \
    "$C/corpus-units.tsv" "$T" P1-DEV evals-c0/$n.json > evals-c0/$n.log 2>&1 || fail eval-$n
done
python3 -I "$D/p2-coverage/code/p2t02_rebuild_gate.py" archived-c0 . evals-c0/z-arctic.json evals-c0/bm25.json \
  rebuild-gate.json > logs/rebuild-gate.log 2>&1 || { tail -5 logs/rebuild-gate.log; fail rebuild-gate; }
stamp R5_REBUILD_GATE_PASSED
# summary-P1-DEV.json for the queue's stage-0 evaluator-path check (= evaluator output without per_query, as on dr-train)
for n in z-arctic bm25; do
  python3 -I -c "import json,sys; d=json.load(open(sys.argv[1])); d.pop('per_query'); d['run']='runs/$n/run-P1-DEV.tsv'; json.dump(d, open(sys.argv[2],'w'))" \
    evals-c0/$n.json runs/$n/summary-P1-DEV.json || fail summary-$n
done

# frozen P2-T02 queue (unchanged stages; single dedicated GPU = device 0; G03-dependent descriptive checks deferred)
THREADS=$(( NPROC < 16 ? NPROC : 16 )); WORKERS=$(( NPROC < 32 ? NPROC : 32 ))
P2T02_PY=$(command -v python3) P2T02_GPU_DEVICE=0 P2T02_NO_G03=1 P2T02_THREADS=$THREADS P2T02_WORKERS=$WORKERS \
  P2T02_TOK_WORKERS=$THREADS P2T02_MIN_FREE_GIB=${P2T02_MIN_FREE_GIB:-6} \
  bash "$D/p2-coverage/code/p2t02_queue.sh" > "$D/p2-coverage/logs-queue.log" 2>&1
tail -3 "$D/p2-coverage/logs-queue.log"
grep -q '^P2T02_DONE' "$D/p2-coverage/logs-queue.log" || fail queue
stamp P2T02_RUNPOD_DONE
