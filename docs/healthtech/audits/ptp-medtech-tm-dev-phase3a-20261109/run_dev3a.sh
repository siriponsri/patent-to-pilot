#!/bin/bash
# MTM dev phase 3a (methods log: dense vector PRF), code = git archive a29610b in $D/code. Dev only; no retries.
set -u
J=/home/chaw/patent-to-pilot-jobs/mtm-20261107
D=$J/dev3a
M=/home/chaw/patent-to-pilot-jobs/research-product-o1-o4-20261031/models
PY=/home/chaw/patent-to-pilot-jobs/research-product-o1-o4-20261031/venv/bin/python
export CUDA_VISIBLE_DEVICES=GPU-277ccc57-c3e5-0731-cd49-f4f8695f7089
S=$D/logs/status.log
mkdir -p $D/logs $D/analysis $D/out; cd $D/code || exit 1
step() { name=$1; shift; echo "$(date -u +%FT%TZ) start $name" >> $S; "$@" > $D/logs/$name.log 2>&1; rc=$?; echo "$(date -u +%FT%TZ) end $name exit=$rc" >> $S; return $rc; }
for qv in P-dev T-dev; do
  step prf-$qv $PY scripts/healthtech/run_mtm_prf.py --corpus $J/inputs/corpus.jsonl --queries $J/inputs/queries-$qv.jsonl \
    --queries-meta $J/inputs/queries-meta.jsonl --model-dir $M/patembed-large --vectors $J/out/passage-vectors-f32.npy \
    --output-dir $D/out --name $qv
done
METHODS=prfK0-1.0,prfK3-0.7,prfK5-0.7,prfK10-0.7,prfK3-0.8,prfK5-0.8,prfK10-0.8,prfK3-0.9,prfK5-0.9,prfK10-0.9
step analysis nice $PY scripts/healthtech/analyze_mtm_methods.py --queries-meta $J/inputs/queries-meta.jsonl --baseline-dir $J/out \
  --methods-dir $D/out --methods $METHODS --cv-prefix prf --query-views P,T --output $D/analysis/dev-phase3a.json
echo "$(date -u +%FT%TZ) all done" >> $S
