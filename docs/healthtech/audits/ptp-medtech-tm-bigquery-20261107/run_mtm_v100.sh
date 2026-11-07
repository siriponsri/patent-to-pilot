#!/bin/bash
# MTM V100 job (frozen rules, commit 7d317e7). One GPU job at a time, in sequence. No retries.
# An existing output is never overwritten (the scripts refuse); a failed step stops the steps that depend on it.
set -u
J=/home/chaw/patent-to-pilot-jobs/mtm-20261107
M=/home/chaw/patent-to-pilot-jobs/research-product-o1-o4-20261031/models
PY=/home/chaw/patent-to-pilot-jobs/research-product-o1-o4-20261031/venv/bin/python
export CUDA_VISIBLE_DEVICES=GPU-277ccc57-c3e5-0731-cd49-f4f8695f7089
S=$J/logs/status.log
cd $J/code || exit 1
step() { name=$1; shift; echo "$(date -u +%FT%TZ) start $name" >> $S; "$@" > $J/logs/$name.log 2>&1; rc=$?; echo "$(date -u +%FT%TZ) end $name exit=$rc" >> $S; return $rc; }
dense() { view=$1; extra=${2:-}; step dense-$view $PY scripts/healthtech/run_mtm_dense_pool.py --corpus $J/inputs/corpus.jsonl --queries $J/inputs/queries-$view.jsonl --queries-meta $J/inputs/queries-meta.jsonl --model-dir $M/patembed-large --output-dir $J/out --name $view $extra; }
briefs() { split=$1; step briefs-P-$split $PY scripts/healthtech/run_qwen_scout_actions.py generate --actions P --model-dir $M/qwen3-8b --input $J/inputs/brief-inputs-$split.jsonl --output $J/out/briefs-P-$split.out.jsonl && step pq-$split $PY scripts/healthtech/build_mtm_p_queries.py --generated $J/out/briefs-P-$split.out.jsonl --output $J/inputs/queries-P-$split.jsonl; }
R="--reuse-vectors $J/out/passage-vectors-f32.npy"
dense T-dev || { echo "$(date -u +%FT%TZ) stop: corpus encoding failed" >> $S; exit 1; }
dense A-dev "$R"
briefs dev && dense P-dev "$R"
briefs test && dense P-test "$R"
dense T-test "$R"
dense A-test "$R"
echo "$(date -u +%FT%TZ) all done" >> $S
