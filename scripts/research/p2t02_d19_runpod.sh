#!/usr/bin/env bash
# P2-T02 amendment A2 (owner D19): complete-content C1 follow-up for ONE model on a dedicated RunPod pod.
# Amendment docs/healthtech/research/p2-coverage/P2-T02-AMENDMENT-A2-D19-FOLLOWUP.md; runbook P2-T02-D19-RUNPOD-RUNBOOK.md.
# The pod mirrors the dr-train paths (upload tree from p2t02_d19_inputs.py, extracted at /):
#   /data/ptp-paper2/{splits/private/tasks.tsv (P1-DEV only), challenge1m/out-v1, patentsview/claims (filtered),
#   bridgeret/{code, texts-v1, am7/prep-v1/meta-p1dev.pkl, runs/z-arctic/units.json, runs/z-<m>, evals-a3r1, logs,
#   archived-d19}, p2-coverage/code}
# Stages (resumable; finished stages are skipped):
#   S0 preflight | S1 weights at their pinned revisions | S2 gate relay (C0 reference) | S3 ser-<m>-v1 (archived command)
#   | S4 window | S5 C1 content (model tokenizer, model window) | S6 Arctic content reproduction in the background (gate
#   C-A) || S7 GPU validate (id path = text path) + c0check (scores of the gated C0 run) + P1-DEV queries | wait S6, gate
#   content | S8 GPU encode C1 | S9 retrieve C1 (CPU, max-p, C0 masks) | S10 evaluate (unchanged evaluator, P1-DEV)
#   | S11 final gate | S12 frozen contrast + decision | S13 pack
# P1-DEV only. No TEST block, sealed file, frozen manifest or VAL label exists on the pod; the preflight refuses otherwise.
# Ends with P2T02_D19_<MODEL>_DONE or P2T02_D19_FAILED:<stage>.
# Launch: setsid nohup bash /data/ptp-paper2/p2-coverage/code/p2t02_d19_runpod.sh <qwen3|patembed> \
#           > /data/ptp-paper2/d19-<model>.log 2>&1 < /dev/null &
# Speed knobs (outputs unchanged, amendment A2 section 3): P2T02_D19_BS (pod default 32), P2T02_D19_FRAC (pod default 0.5),
# P2T02_GPU_DEVICE (pod 0). Not for dr-train as written: its tree holds TEST rows and meta.pkl, which the preflight refuses.
set -uo pipefail
M=${1:?usage: p2t02_d19_runpod.sh qwen3|patembed}
case "$M" in qwen3|patembed) ;; *) echo "P2T02_D19_FAILED:unknown-model-$M"; exit 1 ;; esac
D=/data/ptp-paper2
BR=$D/bridgeret
C=$D/challenge1m/out-v1
T=$D/splits/private/tasks.tsv
P=$D/p2-coverage
CODE=$P/code
R=$P/d19/$M
EV=$BR/code/eval_bridgeret_dev.py
JOBS=/home/chaw/patent-to-pilot-jobs/research-product-o1-o4-20261031
MA=$D/models/arctic-embed-m-v2.0
if [ "$M" = qwen3 ]; then MD=$D/models/qwen3-embedding-0.6b; SER=ser-qwen3-v1
else MD=$JOBS/models/patembed-large; SER=ser-patembed-v1; fi
QWEN_PROMPT=$'Instruct: Given a patent application, retrieve prior art cited against it\nQuery: '
QP='encode query for mixed document retrieval: '
DP='encode document for mixed retrieval: '
GDEV=${P2T02_GPU_DEVICE:-0}
export P2T02_D19_BS=${P2T02_D19_BS:-32}
FRAC=${P2T02_D19_FRAC:-0.5}
export TOKENIZERS_PARALLELISM=false PYTHONNOUSERSITE=1
stamp() { echo "$1 $(date -Is)"; }
fail() { echo "P2T02_D19_FAILED:$1 $(date -Is)"; exit 1; }

# ---- host facts (container CPU quota and memory limit)
NPROC=$(nproc)
if [ -r /sys/fs/cgroup/cpu.max ]; then read -r Q PER < /sys/fs/cgroup/cpu.max
else Q=$(cat /sys/fs/cgroup/cpu/cpu.cfs_quota_us 2>/dev/null || echo -1); PER=$(cat /sys/fs/cgroup/cpu/cpu.cfs_period_us 2>/dev/null || echo 100000); fi
if [ "$Q" != max ] && [ "$Q" -gt 0 ] 2>/dev/null; then NPROC=$(( (Q + PER - 1) / PER )); fi
MEMG=$(free -g | awk '/Mem/{print $2}')
if [ -r /sys/fs/cgroup/memory.max ] && [ "$(cat /sys/fs/cgroup/memory.max)" != max ]; then MEMG=$(( $(cat /sys/fs/cgroup/memory.max) / 1073741824 )); fi
SW=$(( NPROC < 24 ? NPROC : 24 )); TH=$(( NPROC < 16 ? NPROC : 16 )); WK=$(( NPROC < 32 ? NPROC : 32 ))
CPU="env CUDA_VISIBLE_DEVICES= OMP_NUM_THREADS=$TH OPENBLAS_NUM_THREADS=$TH MKL_NUM_THREADS=$TH"
GPU="env CUDA_VISIBLE_DEVICES=$GDEV P2T02_EXPECT_GPU=$GDEV PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True"
ENC="python3 -I $CODE/p2t02_d19_encode.py"
mkdir -p "$R"/{logs,gates,runs,evals,enc} "$D/out" "$BR/logs" "$JOBS/models"
cd "$R" || fail cd
stamp "P2T02_D19_START model=$M host=$(hostname) nproc=$NPROC mem=${MEMG}G bs=$P2T02_D19_BS frac=$FRAC"

# ---- S0 preflight
[ -x /usr/bin/time ] || fail "preflight-no-GNU-time (apt-get install -y time)"
python3 -c 'import torch, transformers, tokenizers, numpy; print("versions", torch.__version__, transformers.__version__, tokenizers.__version__, numpy.__version__)' \
  | tee logs/versions.txt || fail preflight-python
if [ "${P2T02_D19_ALLOW_VERSIONS:-0}" != 1 ]; then
  grep -q '^versions 2\.8\.0[+ ].* 4\.55\.2 0\.21\.4 2\.2\.6$' logs/versions.txt \
    || fail "preflight-library-pins (torch 2.8.0, transformers 4.55.2, tokenizers 0.21.4, numpy 2.2.6)"
fi
[ "$(awk -F'\t' 'NR>1 && $2 != "P1-DEV"' "$T" | wc -l)" = 0 ] || fail preflight-tasks-not-P1DEV-only
[ "$(awk -F'\t' 'NR>1 && $2 != "P1-DEV"' "$C/pairs-dev.tsv" | wc -l)" = 0 ] || fail preflight-pairs-not-P1DEV-only
! grep -qvE '"block": ?"P1-DEV"' "$BR/texts-v1/queries.jsonl" || fail preflight-queries-not-P1DEV-only
[ -z "$(find "$D/splits" "$C" "$BR" "$P" -path '*TEST*' 2>/dev/null | head -1)" ] || fail preflight-TEST-path-present
[ ! -e "$D/manifest-v1/out-v2/manifest-frozen.json" ] || fail preflight-frozen-manifest-present
[ ! -e "$BR/am7/prep-v1/meta.pkl" ] || fail "preflight-meta.pkl-present (holds VAL labels; A2 uses meta-p1dev.pkl)"
( cd / && sha256sum -c --quiet "$D/MANIFEST-d19-$M.sha256" ) || fail preflight-upload-sha256
GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | head -1)
GPU_MIB=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits 2>/dev/null | head -1)
echo "gpu: ${GPU_NAME:-none} ${GPU_MIB:-0} MiB; disk free $(df -BG --output=avail "$D" | tail -1)"
[ -n "$GPU_NAME" ] || fail preflight-no-gpu
[ "${GPU_MIB:-0}" -ge 31000 ] || [ "${P2T02_D19_ALLOW_SMALL_GPU:-0}" = 1 ] || fail preflight-gpu-below-32GB
[ "$MEMG" -ge 60 ] || [ "${P2T02_D19_ALLOW_SMALL_RAM:-0}" = 1 ] || fail "preflight-ram-below-60GB (${MEMG}G)"
stamp S0_PREFLIGHT_PASSED

# ---- S1 weights at their recorded revisions (sha256 per file), Arctic for the reproduction gate
python3 -I "$CODE/g03_a3r1_runpod_models.py" "$M" "$MD" > logs/models-$M.json 2>&1 || fail models-$M-pins
python3 -I "$CODE/g03_a3r1_runpod_models.py" arctic "$MA" > logs/models-arctic.json 2>&1 || fail models-arctic-pins
stamp S1_WEIGHTS_VERIFIED

# ---- S2 the C0 reference (gated A3r1 relay)
python3 -I "$CODE/p2t02_d19_gate.py" relay "$M" "$BR" gates/relay.json > logs/gate-relay.log 2>&1 \
  || { tail -3 logs/gate-relay.log; fail gate-relay; }
stamp S2_RELAY_GATE_PASSED

# ---- S3 serialised C0 texts with the archived command (C0 query text; C0 passages for validate/c0check)
if [ ! -f "$BR/logs/ser-$M.done" ]; then
  rm -rf "$BR/$SER"
  cd "$BR" || fail cd
  if [ "$M" = qwen3 ]; then
    /usr/bin/time -v -o "$R/logs/ser.time" python3 code/serialise_bridgeret_texts.py texts-v1 "$MD" "$QWEN_PROMPT" "$SER" "$SW" \
      > "$R/logs/ser.log" 2>&1 || fail ser-$M
  else
    /usr/bin/time -v -o "$R/logs/ser.time" python3 code/serialise_bridgeret_texts_v2.py texts-v1 "$MD" "$QP" "$SER" "$SW" "$DP" \
      > "$R/logs/ser.log" 2>&1 || fail ser-$M
  fi
  touch "$BR/logs/ser-$M.done"
  cd "$R" || fail cd
fi
stamp S3_SER_DONE

# ---- S4 window of this model (512 positions minus its own special tokens and document prompt)
$CPU $ENC window --model "$M" --model-dir "$MD" --out window.json > logs/window.log 2>&1 || fail window
WIN=$(python3 -c 'import json; print(json.load(open("window.json"))["window"])') || fail window-read
stamp "S4_WINDOW=$WIN"

# ---- S5 C1 content with the model tokenizer and window (A2 overrides; separator = the C0 join "\n")
if [ ! -f content/manifest.json ]; then
  rm -rf content
  $CPU P2T02_TOKDIR="$MD" P2T02_WIN="$WIN" P2T02_SEG_SEP=$'\n' /usr/bin/time -v -o logs/build.time \
    python3 "$CODE/p2t02_build_content.py" "$BR" "$D/patentsview/claims" content --workers "$WK" --tok-workers "$TH" \
    --min-free-gib "${P2T02_MIN_FREE_GIB:-6}" > logs/build.log 2>&1 || fail build-content
fi
stamp S5_CONTENT_DONE

# ---- S6 (background, CPU) Arctic content reproduction with NO override: gate C-A
AR=$P/d19/arctic-repro
( if [ ! -s gates/content-arctic.json ]; then
    if [ ! -f "$AR/manifest.json" ]; then
      rm -rf "$AR"
      $CPU /usr/bin/time -v -o logs/arctic-repro-build.time python3 "$CODE/p2t02_build_content.py" "$BR" \
        "$D/patentsview/claims" "$AR" --workers "$WK" --tok-workers "$TH" --min-free-gib "${P2T02_MIN_FREE_GIB:-6}" \
        > logs/arctic-repro-build.log 2>&1 || exit 1
    fi
    python3 -I "$CODE/p2t02_d19_gate.py" content "$BR/archived-d19/p2t02-content-manifest.json" "$AR/manifest.json" \
      gates/content-arctic.json > logs/gate-content.log 2>&1 || exit 1
  fi
  cp "$AR/stats.json" gates/arctic-repro-stats.json 2>/dev/null
  rm -rf "$AR"/c1.* "$AR"/c2.* "$AR"/ser-full ) & ARPID=$!

# ---- S7 GPU checks and P1-DEV queries (text path = the C0 path)
if ! grep -q '"passed": true' gates/validate.json 2>/dev/null; then
  $GPU /usr/bin/time -v -o logs/validate.time $ENC validate --model "$M" --model-dir "$MD" --ser "$BR/$SER" --n 2048 \
    --window-json window.json --frac "$FRAC" --out gates/validate.json > logs/validate.log 2>&1 || fail validate
fi
if ! grep -q '"passed": true' gates/c0check.json 2>/dev/null; then
  $GPU /usr/bin/time -v -o logs/c0check.time $ENC c0check --model "$M" --model-dir "$MD" --ser "$BR/$SER" \
    --run "$BR/runs/z-$M/run-P1-DEV.tsv.gz" --units "$BR/runs/z-$M/units.json" --nq 256 --k 50 \
    --window-json window.json --frac "$FRAC" --out gates/c0check.json > logs/c0check.log 2>&1 || fail c0check
fi
if [ ! -f enc/q/DONE ]; then
  $GPU /usr/bin/time -v -o logs/encode-queries.time $ENC queries --model "$M" --model-dir "$MD" --ser "$BR/$SER" \
    --window-json window.json --frac "$FRAC" --out enc/q > logs/encode-queries.log 2>&1 || fail encode-queries
fi
stamp S7_GPU_CHECKS_AND_QUERIES_DONE
wait $ARPID || { tail -3 logs/arctic-repro-build.log logs/gate-content.log 2>/dev/null; fail gate-content-arctic-reproduction; }
grep -q '"passed": true' gates/content-arctic.json || fail gate-content-arctic-reproduction
stamp S6_CONTENT_GATE_PASSED

# ---- S8 encode C1 (GPU, id path, length-sorted, checkpointed shards)
if [ ! -f enc/c1/DONE ]; then
  stamp S8_ENCODE_C1_START
  $GPU /usr/bin/time -v -o logs/encode-c1.time $ENC passages --model "$M" --model-dir "$MD" --arm content --name c1 \
    --window-json window.json --frac "$FRAC" --out enc/c1 > logs/encode-c1.log 2>&1 || fail encode-c1
fi
stamp S8_ENCODE_C1_DONE

# ---- S9 retrieve C1 (frozen P2-T02 retriever: max-p, C0 masks, top 1000)
if [ ! -f runs/$M-c1/run-P1-DEV.tsv.gz ]; then
  mkdir -p runs/$M-c1
  $CPU /usr/bin/time -v -o logs/retrieve-c1.time python3 "$CODE/p2t02_retrieve.py" --passages enc/c1/passages.f16.npy \
    --punit content/c1.unit.npy --units content/units.json --queries enc/q --units-tsv "$C/corpus-units.tsv" --tasks "$T" \
    --out runs/$M-c1/run-P1-DEV.tsv.gz --chunk 256 > logs/retrieve-c1.log 2>&1 || fail retrieve-c1
fi
stamp S9_RETRIEVE_C1_DONE

# ---- S10 evaluate (unchanged evaluator, P1-DEV)
if [ ! -s evals/$M-c1.json ]; then
  python3 -I "$EV" <(zcat runs/$M-c1/run-P1-DEV.tsv.gz) "$C/pairs-dev.tsv" "$C/corpus-units.tsv" "$T" P1-DEV \
    evals/$M-c1.json > evals/$M-c1.log 2>&1 || fail evaluate-c1
fi
stamp S10_EVAL_DONE

# ---- S11 final gate (every part passed; the content was built with this model's window)
python3 -I "$CODE/p2t02_d19_gate.py" final "$M" gates/gate-final.json gates/relay.json gates/content-arctic.json \
  gates/validate.json gates/c0check.json window.json content/stats.json > logs/gate-final.log 2>&1 \
  || { tail -5 logs/gate-final.log; fail gate-final; }
stamp S11_FINAL_GATE_PASSED

# ---- S12 frozen contrast and decision (cluster bootstrap B = 10,000, seed 20261119)
$CPU /usr/bin/time -v -o logs/decide.time python3 "$CODE/p2t02_d19_decide.py" --model "$M" --gate gates/gate-final.json \
  --c0-eval "$BR/evals-a3r1/z-$M.json" --c1-eval evals/$M-c1.json --c0-run "$BR/runs/z-$M/run-P1-DEV.tsv.gz" \
  --c1-run runs/$M-c1/run-P1-DEV.tsv.gz --meta "$BR/am7/prep-v1/meta-p1dev.pkl" --pairs "$C/pairs-dev.tsv" \
  --units-tsv "$C/corpus-units.tsv" --tasks "$T" --root "$R" --arctic-results "$BR/archived-d19/p2t02-results.json" \
  --out results-$M.json > logs/decide.log 2>&1 || fail decide
stamp S12_DECIDE_DONE

# ---- S13 pack (results, gates, per-query evaluation, run, logs, content stats; vectors and content stay on the pod)
du -sb content enc runs evals > logs/disk.txt 2>/dev/null
sha256sum results-$M.json gates/*.json window.json content/manifest.json content/stats.json > logs/outputs.sha256
( cd / && tar -czf "$D/out/p2t02-d19-$M-results.tgz" "${R#/}/results-$M.json" "${R#/}/gates" "${R#/}/window.json" \
    "${R#/}/content/manifest.json" "${R#/}/content/stats.json" "${R#/}/enc/c1/encode.json" "${R#/}/evals" \
    "${R#/}/runs" "${R#/}/logs" && sha256sum "$D/out/p2t02-d19-$M-results.tgz" > "$D/out/p2t02-d19-$M-results.tgz.sha256" ) \
  || fail pack
stamp "P2T02_D19_${M^^}_DONE"
