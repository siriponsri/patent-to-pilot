#!/usr/bin/env bash
# G03 amendment 3, Stage A pilot queue (docs/healthtech/research/g03-dev/G03-DEV-AMENDMENT-3-20261122.md §3).
# Needs the four pilot ledgers in a3/ledger/<model_dir>/P1-DEV.jsonl (uploaded from the owner PC, where the OpenRouter
# caller runs). 1) H routes on the V100 (GPU lock); 2) K routes on CPU (one BM25 index); 3) 70 + 5 arms per model on the
# pilot apps; 4) evaluation; 5) pilot decision. Resumable.
set -euo pipefail
PY=/home/chaw/patent-to-pilot-jobs/research-product-o1-o4-20261031/venv/bin/python
G=/data/ptp-paper2/g03-dev
BR=/data/ptp-paper2/bridgeret
C=/data/ptp-paper2/challenge1m/out-v1
T=/data/ptp-paper2/splits/private/tasks.tsv
EV=$BR/code/eval_bridgeret_dev.py
PE=/home/chaw/patent-to-pilot-jobs/research-product-o1-o4-20261031/models/patembed-large
MODELS="qwen__qwen3.7-flash deepseek__deepseek-v4-flash-0731 qwen__qwen3-32b anthropic__claude-haiku-5.5"
cd "$G"
SPEC=$(for m in $MODELS; do printf '%s=a3/ledger/%s/P1-DEV.jsonl,' "$m" "$m"; done)
CUDA_VISIBLE_DEVICES=1 $PY -I code/g03_a3_routes.py dense "$SPEC" "$PE" $BR/ser-patembed-v1/queries.jsonl \
  $BR/runs/z-patembed/passages.f16.npy $BR/runs/z-patembed/units.json "$C/corpus-units.tsv" "$T" a3/routes P1-DEV
export CUDA_VISIBLE_DEVICES=""
$PY -I code/g03_a3_routes.py bm25 "$SPEC" $BR/ser-arctic-v1 "$C/corpus-units.tsv" "$T" a3/routes P1-DEV
for m in $MODELS; do
  ROUTES="L=$BR/runs/bm25,Q=$BR/runs/z-qwen3,P=$BR/runs/z-patembed,H=$G/a3/routes/$m/H,K=$G/a3/routes/$m/K"
  $PY -I code/g03_route_acquisition.py --runs-root / --routes "$ROUTES" --block P1-DEV --apps-file a3/apps-pilot.json \
    --out "runs-a3-pilot/$m" --budgets 1,4 --workers 36
  mkdir -p "evals-a3-pilot/$m/P1-DEV"
  ls runs-a3-pilot/$m/P1-DEV/*.tsv | while read -r f; do n=$(basename "$f" .tsv); [ -s "evals-a3-pilot/$m/P1-DEV/$n.json" ] || echo "$f"; done | \
    xargs -P 18 -I{} sh -c 'n=$(basename {} .tsv); python3 -I '"$EV"' {} '"$C"'/pairs-dev.tsv '"$C"'/corpus-units.tsv '"$T"' P1-DEV evals-a3-pilot/'"$m"'/P1-DEV/$n.json > evals-a3-pilot/'"$m"'/P1-DEV/$n.log 2>&1'
done
$PY -I code/g03_a3_decide.py pilot --evals-root evals-a3-pilot \
  --models qwen/qwen3.7-flash,deepseek/deepseek-v4-flash-0731,qwen/qwen3-32b,anthropic/claude-haiku-5.5 \
  --apps a3/apps-pilot.json --v0-evals evals --meta $BR/am7/prep-v1/meta.pkl --costs a3/pilot-costs.json \
  --out results-a3-pilot.json
echo G03_A3_PILOT_DONE
