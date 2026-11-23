#!/usr/bin/env bash
# G03 A3r1 Stage A pilot queue (amendment G03-DEV-AMENDMENT-3R1-PROPOSED.md, frozen by P1-T03_freeze_receipt.json).
# Same pipeline as A3r0 (g03_queue_a3_pilot.sh) with the A3r1 panel. Needs the four pilot ledgers in
# a3r1/ledger/<model_dir>/P1-DEV.jsonl (generated on the owner PC by the budgeted caller). Resumable.
set -euo pipefail
# RunPod rebuild amendment (docs/healthtech/research/g03-dev/A3R1-AMENDMENT-RUNPOD-REBUILD.md): env overrides only; the
# dr-train defaults are unchanged. G03_PY, G03_GPU_DEVICE (pod: 0), G03_WORKERS, G03_EVAL_PAR change host and speed only.
PY=${G03_PY:-/home/chaw/patent-to-pilot-jobs/research-product-o1-o4-20261031/venv/bin/python}
GDEV=${G03_GPU_DEVICE:-1}; WK=${G03_WORKERS:-36}; EP=${G03_EVAL_PAR:-18}
G=/data/ptp-paper2/g03-dev
BR=/data/ptp-paper2/bridgeret
C=/data/ptp-paper2/challenge1m/out-v1
T=/data/ptp-paper2/splits/private/tasks.tsv
EV=$BR/code/eval_bridgeret_dev.py
PE=/home/chaw/patent-to-pilot-jobs/research-product-o1-o4-20261031/models/patembed-large
MODELS="qwen__qwen3-32b deepseek__deepseek-v4-flash-0731 google__gemini-2.5-flash-lite typhoon-v2.5-30b-a3b-instruct"
cd "$G"
SPEC=$(for m in $MODELS; do printf '%s=a3r1/ledger/%s/P1-DEV.jsonl,' "$m" "$m"; done)
CUDA_VISIBLE_DEVICES=$GDEV $PY -I code/g03_a3_routes.py dense "$SPEC" "$PE" $BR/ser-patembed-v1/queries.jsonl \
  $BR/runs/z-patembed/passages.f16.npy $BR/runs/z-patembed/units.json "$C/corpus-units.tsv" "$T" a3r1/routes P1-DEV
export CUDA_VISIBLE_DEVICES=""
$PY -I code/g03_a3_routes.py bm25 "$SPEC" $BR/ser-arctic-v1 "$C/corpus-units.tsv" "$T" a3r1/routes P1-DEV
for m in $MODELS; do
  ROUTES="L=$BR/runs/bm25,Q=$BR/runs/z-qwen3,P=$BR/runs/z-patembed,H=$G/a3r1/routes/$m/H,K=$G/a3r1/routes/$m/K"
  $PY -I code/g03_route_acquisition.py --runs-root / --routes "$ROUTES" --block P1-DEV --apps-file a3/apps-pilot.json \
    --out "runs-a3r1-pilot/$m" --budgets 1,4 --workers "$WK"
  mkdir -p "evals-a3r1-pilot/$m/P1-DEV"
  ls runs-a3r1-pilot/$m/P1-DEV/*.tsv | while read -r f; do n=$(basename "$f" .tsv); [ -s "evals-a3r1-pilot/$m/P1-DEV/$n.json" ] || echo "$f"; done | \
    xargs -P "$EP" -I{} sh -c 'n=$(basename {} .tsv); python3 -I '"$EV"' {} '"$C"'/pairs-dev.tsv '"$C"'/corpus-units.tsv '"$T"' P1-DEV evals-a3r1-pilot/'"$m"'/P1-DEV/$n.json > evals-a3r1-pilot/'"$m"'/P1-DEV/$n.log 2>&1'
done
$PY -I code/g03_a3_decide.py pilot --evals-root evals-a3r1-pilot \
  --models qwen/qwen3-32b,deepseek/deepseek-v4-flash-0731,google/gemini-2.5-flash-lite,typhoon-v2.5-30b-a3b-instruct \
  --eligible qwen/qwen3-32b,deepseek/deepseek-v4-flash-0731,google/gemini-2.5-flash-lite \
  --apps a3/apps-pilot.json --v0-evals evals --meta $BR/am7/prep-v1/meta.pkl --costs a3r1/pilot-costs.json \
  --out results-a3r1-pilot.json
echo G03_A3R1_PILOT_DONE
