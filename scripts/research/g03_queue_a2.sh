#!/usr/bin/env bash
# G03 amendment 2 queue (docs/healthtech/research/g03-dev/G03-DEV-AMENDMENT-2-20261122.md).
set -euo pipefail
PY=/home/chaw/patent-to-pilot-jobs/research-product-o1-o4-20261031/venv/bin/python
G=/data/ptp-paper2/g03-dev
BR=/data/ptp-paper2/bridgeret
C=/data/ptp-paper2/challenge1m/out-v1
T=/data/ptp-paper2/splits/private/tasks.tsv
EV=$BR/code/eval_bridgeret_dev.py
cd "$G"
# wait for amendment 1 to release the V100 and the CPU-heavy steps
while ! grep -q -E "G03_A1_DONE|Traceback" a1.log 2>/dev/null; do sleep 30; done
if [ ! -s a2/z-patembed-train/run-TRAIN.tsv.gz ]; then
  CUDA_VISIBLE_DEVICES=1 $PY -I code/g03_a2_prep.py $BR $C $T \
    /home/chaw/patent-to-pilot-jobs/research-product-o1-o4-20261031/models/patembed-large a2
fi
export CUDA_VISIBLE_DEVICES=""
ROUTES="L=$BR/runs/bm25-train,Q=$BR/runs/z-qwen3,P=$G/a2/z-patembed-train,A=$BR/runs/z-arctic"
$PY -I code/g03_route_acquisition.py --runs-root / --routes "$ROUTES" --block TRAIN --apps-file a2/train-sample.json \
  --out runs-a2 --budgets 4 --workers 36
mkdir -p evals-a2/TRAIN
ls runs-a2/TRAIN/*.tsv | while read -r f; do n=$(basename "$f" .tsv); [ -s "evals-a2/TRAIN/$n.json" ] || echo "$f"; done | \
  xargs -P 18 -I{} sh -c 'n=$(basename {} .tsv); python3 -I '"$EV"' {} '"$C"'/pairs-dev.tsv '"$C"'/corpus-units.tsv '"$T"' TRAIN evals-a2/TRAIN/$n.json > evals-a2/TRAIN/$n.log 2>&1'
$PY -I code/g03_a2_selector.py --g03 "$G" --bridgeret "$BR" --out results-a2.json
echo G03_A2_DONE
