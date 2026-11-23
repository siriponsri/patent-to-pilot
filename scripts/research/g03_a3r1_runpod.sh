#!/usr/bin/env bash
# G03 A3r1 pilot evaluation on RunPod pods (amendment docs/healthtech/research/g03-dev/A3R1-AMENDMENT-RUNPOD-REBUILD.md,
# owner D22/D23). The pods mirror the dr-train paths, so the frozen A3r1 queue and the archived C0 scripts run unchanged:
#   /data/ptp-paper2/{splits/private/tasks.tsv (P1-DEV rows only), challenge1m/out-v1, bridgeret/{code, texts-v1,
#   am7/prep-v1/meta.pkl, archived-a3r1}, g03-dev/{code, a3, a3r1}, models/qwen3-embedding-0.6b}
#   /home/chaw/patent-to-pilot-jobs/research-product-o1-o4-20261031/models/{patembed-large, GPU lock file}
# Roles (one per pod, or "all" on one pod):
#   qwen3     Q1 ser-qwen3-v1 | Q2 Qwen3 C0 encode + retrieval (GPU) | Q3 evaluate | gate part qwen3 | pack for relay
#   patembed  P1 ser-patembed-v1 | P2 PatEmbed C0 (GPU) | P3 evaluate | gate part patembed | P4 H routes (label-free, GPU)
#   assemble  (after patembed, with the Qwen3 relay and the BM25/ser-arctic copy in place) evaluate BM25 | rebuild v0 F*
#             and the pilot population | FULL rebuild gate | then the frozen g03_queue_a3r1_pilot.sh (K routes,
#             arms, evaluation, frozen GO/STOP decision) | pack results
# P1-DEV only; no TEST block, sealed file or frozen manifest exists on the pod, and the preflight refuses to run if one does.
# Ends with G03_A3R1_RUNPOD_<ROLE>_DONE or G03_A3R1_RUNPOD_FAILED:<stage>. Resumable.
# Launch: setsid nohup bash /data/ptp-paper2/g03-dev/code/g03_a3r1_runpod.sh <role> > /data/ptp-paper2/a3r1-<role>.log 2>&1 < /dev/null &
set -uo pipefail
ROLE=${1:?usage: g03_a3r1_runpod.sh qwen3|patembed|assemble|all}
D=/data/ptp-paper2
BR=$D/bridgeret
G=$D/g03-dev
GC=$G/code
C=$D/challenge1m/out-v1
T=$D/splits/private/tasks.tsv
EV=$BR/code/eval_bridgeret_dev.py
ARCH=$BR/archived-a3r1
JOBS=/home/chaw/patent-to-pilot-jobs/research-product-o1-o4-20261031
MQ=$D/models/qwen3-embedding-0.6b
PE=$JOBS/models/patembed-large
MA=$D/models/arctic-embed-m-v2.0
QWEN_PROMPT=$'Instruct: Given a patent application, retrieve prior art cited against it\nQuery: '
QP='encode query for mixed document retrieval: '
DP='encode document for mixed retrieval: '
MODELS="qwen__qwen3-32b deepseek__deepseek-v4-flash-0731 google__gemini-2.5-flash-lite typhoon-v2.5-30b-a3b-instruct"
export TOKENIZERS_PARALLELISM=false PYTHONNOUSERSITE=1
stamp() { echo "$1 $(date -Is)"; }
fail() { echo "G03_A3R1_RUNPOD_FAILED:$1 $(date -Is)"; exit 1; }

# ---- host facts: CPU quota and memory limit of the container (cgroup v2, else v1), GPU
NPROC=$(nproc)
if [ -r /sys/fs/cgroup/cpu.max ]; then read -r Q PER < /sys/fs/cgroup/cpu.max
else Q=$(cat /sys/fs/cgroup/cpu/cpu.cfs_quota_us 2>/dev/null || echo -1); PER=$(cat /sys/fs/cgroup/cpu/cpu.cfs_period_us 2>/dev/null || echo 100000); fi
if [ "$Q" != max ] && [ "$Q" -gt 0 ] 2>/dev/null; then NPROC=$(( (Q + PER - 1) / PER )); fi
MEMG=$(free -g | awk '/Mem/{print $2}')
if [ -r /sys/fs/cgroup/memory.max ] && [ "$(cat /sys/fs/cgroup/memory.max)" != max ]; then MEMG=$(( $(cat /sys/fs/cgroup/memory.max) / 1073741824 )); fi
SW=$(( NPROC < 24 ? NPROC : 24 ))                         # serialisation workers (dr-train used 24; output order fixed)
WK=$(( NPROC < 36 ? NPROC : 36 ))                         # arm builders (dr-train 36)
EP=$(( NPROC < 18 ? NPROC : 18 )); EM=$(( MEMG / 4 )); [ "$EM" -lt 1 ] && EM=1; [ "$EP" -gt "$EM" ] && EP=$EM   # evaluators
stamp "G03_A3R1_RUNPOD_START role=$ROLE host=$(hostname) nproc=$NPROC mem=${MEMG}G"

# ---- preflight: tools, versions, P1-DEV-only inputs, uploaded files match the staging manifest
[ -x /usr/bin/time ] || fail "preflight-no-GNU-time (apt-get install -y time)"
python3 -c 'import torch, transformers, tokenizers, numpy; print("versions", torch.__version__, transformers.__version__, tokenizers.__version__, numpy.__version__)' | tee "$D/a3r1-versions-$ROLE.txt" || fail preflight-python
python3 -c 'import sklearn, scipy; print("versions-cpu", sklearn.__version__, scipy.__version__)' | tee -a "$D/a3r1-versions-$ROLE.txt"
if [ "${A3R1_ALLOW_VERSIONS:-0}" != 1 ]; then
  grep -q '^versions 2\.8\.0[+ ].* 4\.55\.2 0\.21\.4 2\.2\.6$' "$D/a3r1-versions-$ROLE.txt" || fail "preflight-library-pins (torch 2.8.0, transformers 4.55.2, tokenizers 0.21.4, numpy 2.2.6)"
fi
[ "$(awk -F'\t' 'NR>1 && $2!="P1-DEV"' "$T" | wc -l)" = 0 ] || fail preflight-tasks-not-P1DEV-only
[ "$(awk -F'\t' 'NR>1 && $2!="P1-DEV"' "$C/pairs-dev.tsv" | wc -l)" = 0 ] || fail preflight-pairs-not-P1DEV-only
[ -z "$(find "$D/splits" "$C" "$BR" "$G" -path '*TEST*' 2>/dev/null | head -1)" ] || fail preflight-TEST-path-present
[ ! -e "$D/manifest-v1/out-v2/manifest-frozen.json" ] || fail preflight-frozen-manifest-present
! grep -qE '"block": ?"P[0-9]-TEST"' "$BR/texts-v1/queries.jsonl" || fail preflight-TEST-query-present
( cd / && sha256sum -c --quiet --ignore-missing "$D/MANIFEST-a3r1.sha256" ) || fail preflight-upload-sha256
mkdir -p "$JOBS/models" "$BR/logs" "$BR/evals-a3r1" "$BR/runs" "$D/out"   # $JOBS/models holds the GPU lock file of the archived scripts
GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | head -1)
GPU_MIB=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits 2>/dev/null | head -1)
echo "gpu: ${GPU_NAME:-none} ${GPU_MIB:-0} MiB"
need_gpu() {   # the frozen memory fractions (0.15, 0.12) equal the V100 caps only on a >= 32 GB GPU
  [ -n "$GPU_NAME" ] || fail "$1-no-gpu"
  [ "${GPU_MIB:-0}" -ge 31000 ] || [ "${A3R1_ALLOW_SMALL_GPU:-0}" = 1 ] || fail "$1-gpu-below-32GB"
}
ev_run() {   # unchanged evaluator, P1-DEV: $1 run name under runs/
  local f=$BR/runs/$1/run-P1-DEV.tsv
  [ -s "$BR/evals-a3r1/$1.json" ] && return 0
  if [ -s "$f" ]; then python3 -I "$EV" "$f" "$C/pairs-dev.tsv" "$C/corpus-units.tsv" "$T" P1-DEV "$BR/evals-a3r1/$1.json" > "$BR/evals-a3r1/$1.log" 2>&1
  else python3 -I "$EV" <(zcat "$f.gz") "$C/pairs-dev.tsv" "$C/corpus-units.tsv" "$T" P1-DEV "$BR/evals-a3r1/$1.json" > "$BR/evals-a3r1/$1.log" 2>&1; fi
}
gate() {   # $1 part
  python3 -I "$GC/g03_a3r1_runpod_gate.py" "$1" "$ARCH" "$BR" "$G" "$BR/logs/gate-$1.json" > "$BR/logs/gate-$1.log" 2>&1 \
    || { tail -3 "$BR/logs/gate-$1.log"; fail "rebuild-gate-$1"; }
  stamp "GATE_${1}_PASSED"
}
# early gate A (byte-identical corpus text) before any GPU time
python3 -I -c "
import hashlib,json,sys
h=hashlib.sha256(); f=open('$BR/texts-v1/corpus.jsonl','rb')
for b in iter(lambda: f.read(1<<22), b''): h.update(b)
w=json.load(open('$ARCH/texts-report.json'))['outputs_sha256']['corpus.jsonl']
print('corpus.jsonl', h.hexdigest(), 'archived', w); sys.exit(0 if h.hexdigest()==w else 1)" || fail gateA-corpus-text

role_qwen3() {
  need_gpu qwen3
  cd "$BR" || fail cd
  python3 -I "$GC/g03_a3r1_runpod_models.py" qwen3 "$MQ" > logs/models-qwen3.json 2>&1 || fail models-qwen3-pins
  if [ ! -f logs/serq.done ]; then
    rm -rf ser-qwen3-v1
    /usr/bin/time -v -o logs/serq.time python3 code/serialise_bridgeret_texts.py texts-v1 "$MQ" "$QWEN_PROMPT" ser-qwen3-v1 "$SW" \
      > logs/serq.log 2>&1 && touch logs/serq.done || fail ser-qwen3
  fi
  stamp Q1_SER_QWEN3_DONE
  if [ ! -s runs/z-qwen3/run-P1-DEV.tsv.gz ]; then
    [ -s runs/z-qwen3/run-P1-DEV.tsv ] && [ -f logs/zqwen3.done ] || {
      CUDA_VISIBLE_DEVICES=0 BS=${A3R1_QWEN_BS:-8} PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True \
        /usr/bin/time -v -o logs/zqwen3.time python3 code/dense_bridgeret_v2.py "$MQ" last "$QWEN_PROMPT" ser-qwen3-v1 \
        "$C/corpus-units.tsv" "$T" runs/z-qwen3 0.15 P1-DEV > logs/zqwen3.log 2>&1 && touch logs/zqwen3.done || fail encode-qwen3; }
  fi
  stamp Q2_QWEN3_C0_DONE
  ev_run z-qwen3 || fail eval-qwen3
  [ -s runs/z-qwen3/run-P1-DEV.tsv ] && { gzip -f runs/z-qwen3/run-P1-DEV.tsv || fail gzip-qwen3; }
  gate qwen3
  ( cd / && tar -cf "$D/out/a3r1-qwen3-relay.tar" data/ptp-paper2/bridgeret/runs/z-qwen3/run-P1-DEV.tsv.gz \
      data/ptp-paper2/bridgeret/runs/z-qwen3/units.json data/ptp-paper2/bridgeret/evals-a3r1/z-qwen3.json \
      data/ptp-paper2/bridgeret/evals-a3r1/z-qwen3.log data/ptp-paper2/bridgeret/logs/gate-qwen3.json \
      data/ptp-paper2/bridgeret/logs/models-qwen3.json data/ptp-paper2/bridgeret/logs/serq.time data/ptp-paper2/bridgeret/logs/zqwen3.time \
      data/ptp-paper2/bridgeret/logs/zqwen3.log && sha256sum "$D/out/a3r1-qwen3-relay.tar" > "$D/out/a3r1-qwen3-relay.tar.sha256" ) || fail pack-qwen3
  stamp G03_A3R1_RUNPOD_QWEN3_DONE
}

role_patembed() {
  need_gpu patembed
  cd "$BR" || fail cd
  python3 -I "$GC/g03_a3r1_runpod_models.py" patembed "$PE" > logs/models-patembed.json 2>&1 || fail models-patembed-pins
  if [ ! -f logs/serp.done ]; then
    rm -rf ser-patembed-v1
    /usr/bin/time -v -o logs/serp.time python3 code/serialise_bridgeret_texts_v2.py texts-v1 "$PE" "$QP" ser-patembed-v1 "$SW" "$DP" \
      > logs/serp.log 2>&1 && touch logs/serp.done || fail ser-patembed
  fi
  stamp P1_SER_PATEMBED_DONE
  if [ ! -s runs/z-patembed/run-P1-DEV.tsv.gz ]; then
    [ -s runs/z-patembed/run-P1-DEV.tsv ] && [ -f logs/zpe.done ] || {
      CUDA_VISIBLE_DEVICES=0 BS=16 PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True DOC_PROMPT="$DP" \
        /usr/bin/time -v -o logs/zpe.time python3 code/dense_bridgeret_v3.py "$PE" mean "$QP" ser-patembed-v1 \
        "$C/corpus-units.tsv" "$T" runs/z-patembed 0.15 P1-DEV > logs/zpe.log 2>&1 && touch logs/zpe.done || fail encode-patembed; }
  fi
  stamp P2_PATEMBED_C0_DONE
  ev_run z-patembed || fail eval-patembed
  [ -s runs/z-patembed/run-P1-DEV.tsv ] && { gzip -f runs/z-patembed/run-P1-DEV.tsv || fail gzip-patembed; }
  gate patembed
  # P4 H routes: the frozen queue's own first command (label-free runtime side); the queue later skips them
  cd "$G" || fail cd
  SPEC=$(for m in $MODELS; do printf '%s=a3r1/ledger/%s/P1-DEV.jsonl,' "$m" "$m"; done)
  TORCH_GPU=$(CUDA_VISIBLE_DEVICES=0 python3 -c 'import torch; print(torch.cuda.get_device_name(0))') || fail torch-gpu-name
  CUDA_VISIBLE_DEVICES=0 G03_A3_GPU_MATCH="$TORCH_GPU" python3 -I code/g03_a3_routes.py dense "$SPEC" "$PE" \
    $BR/ser-patembed-v1/queries.jsonl $BR/runs/z-patembed/passages.f16.npy $BR/runs/z-patembed/units.json \
    "$C/corpus-units.tsv" "$T" a3r1/routes P1-DEV > logs-a3r1-H.log 2>&1 || fail h-routes
  # relay bundle, so the assembly may run on whichever pod finishes last (passages.f16.npy stays here: H is built)
  ( cd / && tar -cf "$D/out/a3r1-patembed-relay.tar" data/ptp-paper2/bridgeret/runs/z-patembed/run-P1-DEV.tsv.gz \
      data/ptp-paper2/bridgeret/runs/z-patembed/units.json data/ptp-paper2/bridgeret/evals-a3r1/z-patembed.json \
      data/ptp-paper2/bridgeret/evals-a3r1/z-patembed.log data/ptp-paper2/bridgeret/logs/gate-patembed.json \
      data/ptp-paper2/bridgeret/logs/models-patembed.json data/ptp-paper2/bridgeret/logs/serp.time data/ptp-paper2/bridgeret/logs/zpe.time \
      data/ptp-paper2/bridgeret/logs/zpe.log data/ptp-paper2/g03-dev/a3r1/routes data/ptp-paper2/g03-dev/logs-a3r1-H.log \
    && sha256sum "$D/out/a3r1-patembed-relay.tar" > "$D/out/a3r1-patembed-relay.tar.sha256" ) || fail pack-patembed
  stamp G03_A3R1_RUNPOD_PATEMBED_DONE
}

role_assemble() {
  cd "$BR" || fail cd
  for f in runs/z-qwen3/run-P1-DEV.tsv.gz runs/z-qwen3/units.json runs/z-patembed/run-P1-DEV.tsv.gz runs/z-patembed/units.json; do
    [ -s "$f" ] || fail "assemble-missing-$f"
  done
  for m in $MODELS; do [ -s "$G/a3r1/routes/$m/H/run-P1-DEV.tsv.gz" ] || fail "assemble-missing-H-$m (run role patembed first)"; done
  # L route and K-route passages: copied from the P2-T02 pod (default; its gate C passed) or rebuilt (A3R1_REBUILD_BM25=1)
  if [ ! -s runs/bm25/run-P1-DEV.tsv.gz ] || [ ! -s ser-arctic-v1/passages.jsonl ]; then
    [ "${A3R1_REBUILD_BM25:-0}" = 1 ] || fail "assemble-missing-bm25-or-ser-arctic (copy from the P2-T02 pod, or A3R1_REBUILD_BM25=1)"
    python3 -I "$GC/g03_a3r1_runpod_models.py" arctic "$MA" > logs/models-arctic.json 2>&1 || fail models-arctic-pins
    if [ ! -f logs/ser-arctic.done ]; then
      rm -rf ser-arctic-v1
      /usr/bin/time -v -o logs/ser.time python3 code/serialise_bridgeret_texts.py texts-v1 "$MA" 'query: ' ser-arctic-v1 "$SW" \
        > logs/ser.log 2>&1 && touch logs/ser-arctic.done || fail ser-arctic
    fi
    CUDA_VISIBLE_DEVICES= /usr/bin/time -v -o logs/bm25.time python3 code/bm25_bridgeret.py ser-arctic-v1 "$C/corpus-units.tsv" "$T" \
      runs/bm25 P1-DEV > logs/bm25.log 2>&1 && gzip -f runs/bm25/run-P1-DEV.tsv || fail bm25-c0
  elif [ -s runs/bm25/copied-from-p2t02.sha256 ]; then
    ( cd / && sha256sum -c --quiet "$BR/runs/bm25/copied-from-p2t02.sha256" ) || fail bm25-copy-sha256
  fi
  stamp A1_L_ROUTE_READY
  for n in bm25 z-qwen3 z-patembed; do ev_run $n || fail eval-$n; done
  # v0 F* from the rebuilt runs, its evaluation, and the pilot population regenerated from it
  cd "$G" || fail cd
  [ -s runs/P1-DEV/alloc-L0-Q2-P2-A0.tsv ] || python3 -I "$GC/g03_a3r1_runpod_v0.py" "$GC" "$BR/runs" runs > logs-a3r1-v0.log 2>&1 || fail v0-fstar
  mkdir -p evals/P1-DEV
  [ -s evals/P1-DEV/alloc-L0-Q2-P2-A0.json ] || python3 -I "$EV" runs/P1-DEV/alloc-L0-Q2-P2-A0.tsv "$C/pairs-dev.tsv" \
    "$C/corpus-units.tsv" "$T" P1-DEV evals/P1-DEV/alloc-L0-Q2-P2-A0.json > evals/P1-DEV/alloc-L0-Q2-P2-A0.log 2>&1 || fail eval-v0-fstar
  python3 -I code/g03_a3_routes.py apps runs/P1-DEV/alloc-L0-Q2-P2-A0.tsv a3/apps-P1-DEV.regen.json || fail regen-apps
  python3 -I code/g03_a3_routes.py sample runs/P1-DEV/alloc-L0-Q2-P2-A0.tsv a3/apps-pilot.regen.json 2000 || fail regen-pilot
  stamp A2_V0_FSTAR_DONE
  gate full
  cp "$BR/logs/gate-full.json" "$G/rebuild-gate-a3r1.json"
  # frozen A3r1 queue: H skipped (exists), K on CPU, arms, evaluation, frozen GO/STOP decision
  G03_PY=$(command -v python3) G03_GPU_DEVICE=0 G03_WORKERS=$WK G03_EVAL_PAR=$EP \
    bash "$GC/g03_queue_a3r1_pilot.sh" > "$G/logs-a3r1-pilot.log" 2>&1
  tail -3 "$G/logs-a3r1-pilot.log"
  grep -q '^G03_A3R1_PILOT_DONE' "$G/logs-a3r1-pilot.log" || fail queue
  PACK=""
  for p in data/ptp-paper2/g03-dev/results-a3r1-pilot.json data/ptp-paper2/g03-dev/rebuild-gate-a3r1.json \
      data/ptp-paper2/g03-dev/logs-a3r1-pilot.log data/ptp-paper2/g03-dev/logs-a3r1-H.log data/ptp-paper2/g03-dev/logs-a3r1-v0.log \
      data/ptp-paper2/g03-dev/a3r1/routes data/ptp-paper2/g03-dev/runs-a3r1-pilot data/ptp-paper2/g03-dev/evals/P1-DEV \
      data/ptp-paper2/g03-dev/a3/apps-P1-DEV.regen.json data/ptp-paper2/g03-dev/a3/apps-pilot.regen.json \
      data/ptp-paper2/bridgeret/logs data/ptp-paper2/bridgeret/evals-a3r1; do [ -e "/$p" ] && PACK="$PACK $p"; done
  ( cd / && tar -czf "$D/out/a3r1-pilot-results.tgz" $PACK data/ptp-paper2/a3r1-versions-*.txt \
    && tar -czf "$D/out/a3r1-pilot-evals.tgz" data/ptp-paper2/g03-dev/evals-a3r1-pilot \
    && sha256sum "$D"/out/a3r1-pilot-*.tgz > "$D/out/a3r1-pilot.sha256" ) || fail pack-results
  stamp G03_A3R1_RUNPOD_ASSEMBLE_DONE
}

case "$ROLE" in
  qwen3) role_qwen3 ;;
  patembed) role_patembed ;;
  assemble) role_assemble ;;
  all) role_qwen3; role_patembed; role_assemble ;;
  *) fail "unknown-role-$ROLE" ;;
esac
stamp G03_A3R1_RUNPOD_DONE
