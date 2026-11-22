#!/usr/bin/env bash
# G03 DEV queue (protocol docs/healthtech/research/g03-dev/G03-DEV-PROTOCOL.md, frozen ec720914). CPU only, no GPU.
# Stage 1: E01 single routes (B=1) + evaluation + reproduction gate. Stage 2: all arms B=2,3,4 + policy, evaluation.
set -euo pipefail
PY=/home/chaw/patent-to-pilot-jobs/research-product-o1-o4-20261031/venv/bin/python
G=/data/ptp-paper2/g03-dev
R=/data/ptp-paper2/bridgeret/runs
C=/data/ptp-paper2/challenge1m/out-v1
T=/data/ptp-paper2/splits/private/tasks.tsv
EV=/data/ptp-paper2/bridgeret/code/eval_bridgeret_dev.py
cd "$G"
export CUDA_VISIBLE_DEVICES=""

evaluate() {   # $1 block; evaluates every arm run without an eval file, 24 in parallel, with the unchanged evaluator
  mkdir -p "evals/$1"
  ls "runs/$1"/*.tsv | while read -r f; do
    n=$(basename "$f" .tsv); [ -s "evals/$1/$n.json" ] || echo "$f"
  done | xargs -P 24 -I{} sh -c 'n=$(basename {} .tsv); python3 -I '"$EV"' {} '"$C"'/pairs-dev.tsv '"$C"'/corpus-units.tsv '"$T"' '"$1"' evals/'"$1"'/$n.json > evals/'"$1"'/$n.log 2>&1'
}

if [ "${1:-}" = "stage1" ]; then
  for b in P1-DEV VAL; do
    $PY -I code/g03_route_acquisition.py --runs-root "$R" --block "$b" --out runs --budgets 1 --workers 4
    evaluate "$b"
  done
  $PY -I code/g03_decide.py gate --evals evals --summaries "$R" > gate.json
  echo G03_STAGE1_DONE
fi

if [ "${1:-}" = "stage2" ]; then
  ANCHOR=$($PY -c 'import json;print(json.load(open("gate.json"))["anchor_dense"])')
  for b in P1-DEV VAL; do
    $PY -I code/g03_route_acquisition.py --runs-root "$R" --block "$b" --out runs --budgets 2,3,4 --policy --anchor-dense "$ANCHOR" --workers 48
    evaluate "$b"
  done
  $PY -I code/g03_decide.py decide --evals evals --meta /data/ptp-paper2/bridgeret/am7/prep-v1/meta.pkl --out results.json
  echo G03_STAGE2_DONE
fi
