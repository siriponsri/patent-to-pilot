#!/usr/bin/env bash
# P2-T02 coverage control, whole pipeline as ONE detached queue on dr-train
# (protocol docs/healthtech/research/p2-coverage/P2-T02-COVERAGE-CONTROL-PROTOCOL.md, frozen bd30d3f7). P1-DEV only.
# Stages: 0 C0 evaluator gate | 1 content build (CPU) | 2 BM25-full (CPU, background) | 3 encoder validation + query
# encoding (V100) | 4 C0 retrieval reproduction (CPU, background) | 5 encode C1 (V100) | 6 retrieve C1 (CPU, after BM25-full)
# | 7 encode C2 (V100) | 8 retrieve C2 | 9 evaluate | 10 contrasts + decision | 11 fusion check (only if an arm qualifies)
# Ends with the sentinel line P2T02_DONE, or P2T02_FAILED:<stage>. Resumable: finished stages are skipped.
# Launch: setsid nohup bash code/p2t02_queue.sh > logs/queue.log 2>&1 < /dev/null & disown
# Smoke:  SMOKE=1 P2T02_ROOT=/data/ptp-paper2/p2-coverage/smoke bash code/p2t02_queue.sh
set -uo pipefail
PY=/home/chaw/patent-to-pilot-jobs/research-product-o1-o4-20261031/venv/bin/python
R=${P2T02_ROOT:-/data/ptp-paper2/p2-coverage}
CODE=/data/ptp-paper2/p2-coverage/code
BR=/data/ptp-paper2/bridgeret
C=/data/ptp-paper2/challenge1m/out-v1
T=/data/ptp-paper2/splits/private/tasks.tsv
EV=$BR/code/eval_bridgeret_dev.py
BM25=$BR/code/bm25_bridgeret.py
G03=/data/ptp-paper2/g03-dev
META=$BR/am7/prep-v1/meta.pkl
SMOKE=${SMOKE:-0}
if [ "$SMOKE" = 1 ]; then LIMIT=2000; LIMIT_Q=128; VALN=256; FORCE_FUSION=1; else LIMIT=0; LIMIT_Q=0; VALN=2048; FORCE_FUSION=0; fi
mkdir -p "$R"/{logs,runs,evals,enc}
cd "$R" || exit 1
export TOKENIZERS_PARALLELISM=false PYTHONNOUSERSITE=1
CPU="env CUDA_VISIBLE_DEVICES= OMP_NUM_THREADS=16 OPENBLAS_NUM_THREADS=16 MKL_NUM_THREADS=16"
GPU="env CUDA_VISIBLE_DEVICES=1 PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True"
stamp() { echo "$1 $(date -Is)"; }
fail() { echo "P2T02_FAILED:$1 $(date -Is)"; exit 1; }
ev() {   # unchanged evaluator on a gzip run: $1 run.tsv.gz  $2 out.json
  python3 -I "$EV" <(zcat "$1") "$C/pairs-dev.tsv" "$C/corpus-units.tsv" "$T" P1-DEV "$2" > "${2%.json}.log" 2>&1
}
stamp "P2T02_START root=$R smoke=$SMOKE host=$(hostname)"
sha256sum "$CODE"/p2t02_*.py "$CODE"/p2t02_queue.sh "$EV" "$BM25" "$G03/code/g03_route_acquisition.py" > logs/code.sha256

# ---- 0. C0 reproduction gate (existing runs through this evaluator path must equal summary-P1-DEV.json)
if ! grep -q '"gate_passed": true' gate.json 2>/dev/null; then
  stamp STAGE0_GATE_START
  ev "$BR/runs/z-arctic/run-P1-DEV.tsv.gz" evals/arctic-c0.json & p1=$!
  ev "$BR/runs/bm25/run-P1-DEV.tsv.gz" evals/bm25-c0.json & p2=$!
  wait $p1 || fail gate-eval-arctic; wait $p2 || fail gate-eval-bm25
  $PY "$CODE/p2t02_analyse.py" gate --eval-arctic evals/arctic-c0.json --eval-bm25 evals/bm25-c0.json \
    --summary-arctic "$BR/runs/z-arctic/summary-P1-DEV.json" --summary-bm25 "$BR/runs/bm25/summary-P1-DEV.json" \
    --out gate.json > logs/gate.log 2>&1 || fail gate
fi
stamp STAGE0_GATE_PASSED

# ---- 1. content build
if [ ! -f content/manifest.json ]; then
  stamp STAGE1_BUILD_START
  rm -rf content
  $CPU /usr/bin/time -v -o logs/build.time nice -n 10 $PY "$CODE/p2t02_build_content.py" "$BR" \
    /data/ptp-paper2/patentsview/claims content --workers 32 --tok-workers 16 --min-free-gib 24 --limit $LIMIT \
    > logs/build.log 2>&1 || fail build
fi
if [ "$SMOKE" = 1 ]; then
  grep '"block": "P1-DEV"' "$BR/ser-arctic-v1/queries.jsonl" | head -n $LIMIT_Q > content/ser-full/queries.jsonl
else
  ln -sfn "$BR/ser-arctic-v1/queries.jsonl" content/ser-full/queries.jsonl
fi
stamp STAGE1_BUILD_DONE

# ---- 2. BM25 full text (unchanged bm25_bridgeret.py over the untruncated C1 content; queries = ser-arctic-v1)
( if [ ! -f runs/bm25-full/run-P1-DEV.tsv.gz ]; then
    mkdir -p runs/bm25-full
    $CPU /usr/bin/time -v -o logs/bm25-full.time nice -n 15 $PY "$BM25" content/ser-full "$C/corpus-units.tsv" "$T" \
      runs/bm25-full P1-DEV > logs/bm25-full.log 2>&1 && gzip -f runs/bm25-full/run-P1-DEV.tsv
  fi ) & BMPID=$!
stamp STAGE2_BM25_FULL_LAUNCHED

# ---- 3. encoder validation (id path vs stored C0 vectors) + P1-DEV query encoding (V100, under the lock)
if ! grep -q '"passed": true' validate-c0.json 2>/dev/null; then
  $GPU nice -n 10 $PY "$CODE/p2t02_encode.py" validate --ser "$BR/ser-arctic-v1" --c0 "$BR/runs/z-arctic" --n $VALN \
    --out validate-c0.json > logs/validate.log 2>&1 || fail validate
fi
if [ ! -f enc/q/DONE ]; then
  $GPU /usr/bin/time -v -o logs/encode-queries.time nice -n 10 $PY "$CODE/p2t02_encode.py" queries \
    --ser "$BR/ser-arctic-v1" --out enc/q --limit $LIMIT_Q > logs/encode-queries.log 2>&1 || fail encode-queries
fi
stamp STAGE3_QUERIES_DONE

# ---- 4. C0 retrieval reproduction with this retriever (identity aggregation) vs the existing z-arctic run
( if [ ! -f samerun.json ]; then
    mkdir -p runs/arctic-c0repro
    $CPU nice -n 15 $PY "$CODE/p2t02_retrieve.py" --passages "$BR/runs/z-arctic/passages.f16.npy" --identity \
      --units "$BR/runs/z-arctic/units.json" --queries enc/q --units-tsv "$C/corpus-units.tsv" --tasks "$T" \
      --out runs/arctic-c0repro/run-P1-DEV.tsv.gz --chunk 512 > logs/retrieve-c0repro.log 2>&1 &&
    $PY "$CODE/p2t02_analyse.py" samerun --new runs/arctic-c0repro/run-P1-DEV.tsv.gz \
      --ref "$BR/runs/z-arctic/run-P1-DEV.tsv.gz" --out samerun.json > logs/samerun.log 2>&1
  fi ) & C0PID=$!

retrieve() {   # $1 arm name (c1|c2)
  mkdir -p "runs/arctic-$1"
  $CPU /usr/bin/time -v -o "logs/retrieve-$1.time" nice -n 15 $PY "$CODE/p2t02_retrieve.py" \
    --passages "enc/$1/passages.f16.npy" --punit "content/$1.unit.npy" --units content/units.json --queries enc/q \
    --units-tsv "$C/corpus-units.tsv" --tasks "$T" --out "runs/arctic-$1/run-P1-DEV.tsv.gz" --chunk 256 \
    > "logs/retrieve-$1.log" 2>&1
}

# ---- 5-8. encode C1, encode C2 (V100); then, once BM25-full has finished, retrieve C1 and C2 one after the other.
# Large CPU stages never overlap (dr-train is shared; the first launch exhausted host memory in the content build).
for arm in c1 c2; do
  if [ ! -f "enc/$arm/DONE" ]; then
    stamp "STAGE_ENCODE_${arm}_START"
    $GPU /usr/bin/time -v -o "logs/encode-$arm.time" nice -n 10 $PY "$CODE/p2t02_encode.py" passages --arm content \
      --name $arm --out "enc/$arm" > "logs/encode-$arm.log" 2>&1 || fail "encode-$arm"
  fi
  stamp "STAGE_ENCODE_${arm}_DONE"
done
wait $C0PID || fail c0-reproduction
wait $BMPID || fail bm25-full
[ -f runs/bm25-full/run-P1-DEV.tsv.gz ] || fail bm25-full-output
stamp STAGE_BM25_FULL_DONE
for arm in c1 c2; do
  [ -f "runs/arctic-$arm/run-P1-DEV.tsv.gz" ] || retrieve $arm || fail "retrieve-$arm"
  stamp "STAGE_RETRIEVE_${arm}_DONE"
done
stamp STAGE8_ALL_RUNS_DONE

# ---- 9. evaluate every arm with the unchanged evaluator (P1-DEV only)
pids=()
for n in arctic-c1 arctic-c2 bm25-full arctic-c0repro; do
  [ -s "evals/$n.json" ] || { ev "runs/$n/run-P1-DEV.tsv.gz" "evals/$n.json" & pids+=($!); }
done
for p in "${pids[@]}"; do wait "$p" || fail evaluate; done
stamp STAGE9_EVAL_DONE

# ---- 10. frozen contrasts, decision rule, descriptives
$CPU /usr/bin/time -v -o logs/decide.time $PY "$CODE/p2t02_analyse.py" decide --root "$R" --meta "$META" \
  --g03-evals "$G03/evals/P1-DEV" --pairs "$C/pairs-dev.tsv" --units-tsv "$C/corpus-units.tsv" --tasks "$T" \
  --run-arctic-c0 "$BR/runs/z-arctic/run-P1-DEV.tsv.gz" --run-bm25-c0 "$BR/runs/bm25/run-P1-DEV.tsv.gz" \
  --out results.json > logs/decide.log 2>&1 || fail decide
stamp STAGE10_DECIDE_DONE

# ---- 11. descriptive fusion check (G03 action model, B = 4) with the qualifying arm(s) substituted
SUB=$($PY -c 'import json,sys;d=json.load(open("results.json"))["decision"]["substitute_for_fusion"];print(json.dumps(d))')
if [ "$FORCE_FUSION" = 1 ] && [ "$SUB" = "{}" ]; then SUB='{"A": "arctic-c1", "L": "bm25-full"}'; fi
if [ "$SUB" != "{}" ]; then
  ROUTES=$($PY -c '
import json,sys
s=json.loads(sys.argv[1]); r=sys.argv[2]
d={"L":"bm25","Q":"z-qwen3","P":"z-patembed","A":"z-arctic"}
d.update({k: r+"/runs/"+v for k,v in s.items()})
print(",".join(k+"="+d[k] for k in "LQPA"))' "$SUB" "$R")
  APPS=""; [ "$SMOKE" = 1 ] && APPS="--apps-file enc/q/P1-DEV.apps.json"
  $CPU $PY "$G03/code/g03_route_acquisition.py" --runs-root "$BR/runs" --block P1-DEV --out fusion/runs --budgets 4 \
    --routes "$ROUTES" --workers 24 $APPS > logs/fusion-arms.log 2>&1 || fail fusion-arms
  mkdir -p fusion/evals
  ls fusion/runs/P1-DEV/alloc-*.tsv | xargs -P 16 -I{} sh -c 'n=$(basename {} .tsv); [ -s fusion/evals/$n.json ] || python3 -I '"$EV"' {} '"$C"'/pairs-dev.tsv '"$C"'/corpus-units.tsv '"$T"' P1-DEV fusion/evals/$n.json > fusion/evals/$n.log 2>&1' \
    || fail fusion-eval
  $PY "$CODE/p2t02_analyse.py" fusion --sub-evals fusion/evals --g03-evals "$G03/evals/P1-DEV" --meta "$META" \
    --substituted "$SUB" --out fusion/fusion.json > logs/fusion.log 2>&1 || fail fusion-analyse
  gzip -f fusion/runs/P1-DEV/alloc-*.tsv
  stamp "STAGE11_FUSION_DONE routes=$ROUTES"
else
  echo '{"fusion": "not run: no complete-content arm qualified (protocol §5: substitution needs a qualifying arm)"}' > fusion-not-run.json
  stamp STAGE11_FUSION_NOT_APPLICABLE
fi
du -sb content enc runs evals > logs/disk.txt 2>/dev/null
sha256sum results.json gate.json samerun.json validate-c0.json content/manifest.json > logs/outputs.sha256 2>/dev/null
stamp P2T02_DONE
