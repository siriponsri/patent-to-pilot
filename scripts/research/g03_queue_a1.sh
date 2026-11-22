#!/usr/bin/env bash
# G03 amendment 1 queue (docs/healthtech/research/g03-dev/G03-DEV-AMENDMENT-1-20261122.md).
# 1) encode field obligations on the approved V100 (GPU lock) + CPU retrieval; 2) arms; 3) evaluation; 4) decision.
set -euo pipefail
PY=/home/chaw/patent-to-pilot-jobs/research-product-o1-o4-20261031/venv/bin/python
G=/data/ptp-paper2/g03-dev
BR=/data/ptp-paper2/bridgeret
C=/data/ptp-paper2/challenge1m/out-v1
T=/data/ptp-paper2/splits/private/tasks.tsv
EV=$BR/code/eval_bridgeret_dev.py
cd "$G"
if [ ! -s routes/z-patembed-claim/run-VAL.tsv.gz ]; then
  CUDA_VISIBLE_DEVICES=1 $PY -I code/g03_field_routes.py /home/chaw/patent-to-pilot-jobs/research-product-o1-o4-20261031/models/patembed-large \
    $BR/texts-v1/queries.jsonl $BR/runs/z-patembed/passages.f16.npy $BR/runs/z-patembed/units.json routes P1-DEV VAL
fi
export CUDA_VISIBLE_DEVICES=""
ROUTES="L=$BR/runs/bm25,Q=$BR/runs/z-qwen3,P=$BR/runs/z-patembed,T=$G/routes/z-patembed-ta,C=$G/routes/z-patembed-claim"
for b in P1-DEV VAL; do
  $PY -I code/g03_route_acquisition.py --runs-root / --routes "$ROUTES" --anchor P --policy --policy-modes consensus \
    --block "$b" --out runs-a1 --budgets 4 --workers 48
  mkdir -p "evals-a1/$b"
  ls runs-a1/$b/*.tsv | while read -r f; do n=$(basename "$f" .tsv); [ -s "evals-a1/$b/$n.json" ] || echo "$f"; done | \
    xargs -P 24 -I{} sh -c 'n=$(basename {} .tsv); python3 -I '"$EV"' {} '"$C"'/pairs-dev.tsv '"$C"'/corpus-units.tsv '"$T"' '"$b"' evals-a1/'"$b"'/$n.json > evals-a1/'"$b"'/$n.log 2>&1'
done
$PY -I code/g03_decide_v1.py --evals evals-a1 --v0-evals evals --meta $BR/am7/prep-v1/meta.pkl --out results-a1.json
echo G03_A1_DONE
