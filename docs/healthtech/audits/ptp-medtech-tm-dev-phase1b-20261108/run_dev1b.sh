#!/bin/bash
# MTM dev phase 1b (methods log V1b-V3b, query prefix stripped), code = git archive 14263c9 in $D/code. One GPU job at a time, in sequence.
# Dev only; no retries; the scripts refuse to overwrite. A failed step does not stop independent later steps.
set -u
J=/home/chaw/patent-to-pilot-jobs/mtm-20261107
D=$J/dev1b
M=/home/chaw/patent-to-pilot-jobs/research-product-o1-o4-20261031/models
PY=/home/chaw/patent-to-pilot-jobs/research-product-o1-o4-20261031/venv/bin/python
export CUDA_VISIBLE_DEVICES=GPU-277ccc57-c3e5-0731-cd49-f4f8695f7089
S=$D/logs/status.log
mkdir -p $D/private $D/logs $D/analysis; cd $D/code || exit 1
step() { name=$1; shift; echo "$(date -u +%FT%TZ) start $name" >> $S; "$@" > $D/logs/$name.log 2>&1; rc=$?; echo "$(date -u +%FT%TZ) end $name exit=$rc" >> $S; return $rc; }
for qv in P-dev T-dev; do
  step hybrid-$qv $PY scripts/healthtech/run_mtm_hybrid.py --corpus $J/inputs/corpus.jsonl --queries $J/inputs/queries-$qv.jsonl \
    --queries-meta $J/inputs/queries-meta.jsonl --model-dir $M/patembed-large --vectors $J/out/passage-vectors-f32.npy \
    --output-dir $D/out --name $qv
done
for qv in P-dev T-dev; do
  step ce-$qv $PY scripts/healthtech/run_mtm_rerank_ce.py --corpus $J/inputs/corpus.jsonl --queries $J/inputs/queries-$qv.jsonl \
    --baseline-dir $J/out --model-dir $M/bge-reranker-v2-m3 --revision 953dc6f6f85a1b2dbfca4c34a2796e7dde08d41e \
    --output-dir $D/out/ce --name $qv --views main --scores-out $D/private/ce-scores-$qv.jsonl
done
step analysis nice $PY scripts/healthtech/analyze_mtm_methods.py --queries-meta $J/inputs/queries-meta.jsonl --baseline-dir $J/out \
  --methods-dir $D/out --methods bm25,hyb-0.5,hyb-0.6,hyb-0.7,hyb-0.8,hyb-0.9,hyb-1.0,ce --cv-prefix hyb- \
  --query-views P,T --output $D/analysis/dev-phase1b.json
echo "$(date -u +%FT%TZ) all done" >> $S
