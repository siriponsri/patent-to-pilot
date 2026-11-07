#!/bin/bash
# E3 generations of the frozen Solution Scout protocol: three greedy Qwen3-8B runs in sequence on the approved V100.
# No retries. An existing output file is never overwritten.
set -u
J=/home/chaw/patent-to-pilot-jobs/scout-public-demo
C=/home/chaw/patent-to-pilot-jobs/org-adaptive-20261105/code-v3
PY=/home/chaw/patent-to-pilot-jobs/research-product-o1-o4-20261031/venv/bin/python
M=/home/chaw/patent-to-pilot-jobs/research-product-o1-o4-20261031/models/qwen3-8b
export CUDA_VISIBLE_DEVICES=GPU-277ccc57-c3e5-0731-cd49-f4f8695f7089
S=$J/logs/e3-status.log
mkdir -p $J/logs
cd $C || exit 1
run() {
  name=$1; ver=$2; in=$3; out=$4
  if [ -e "$out" ]; then echo "$(date -u +%FT%TZ) skip $name: output exists" >> $S; return; fi
  echo "$(date -u +%FT%TZ) start $name" >> $S
  $PY scripts/healthtech/run_qwen_scout_rationales.py generate --model-dir $M --prompt-version $ver \
    --input $in --output $out > $J/logs/e3-$name.log 2>&1
  rc=$?
  echo "$(date -u +%FT%TZ) end $name exit=$rc lines=$(wc -l < $out)" >> $S
}
run dapfam-v0 v0 $J/e3-dapfam-dev-inputs.jsonl $J/e3-dapfam-v0.out.jsonl
run dapfam-v1 v1 $J/e3-dapfam-dev-inputs.jsonl $J/e3-dapfam-v1.out.jsonl
run hupd-v1   v1 $J/rationale-inputs.jsonl     $J/e3-hupd-v1.out.jsonl
echo "$(date -u +%FT%TZ) all done" >> $S
