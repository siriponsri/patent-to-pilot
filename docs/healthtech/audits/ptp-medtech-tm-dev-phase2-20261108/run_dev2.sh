#!/bin/bash
# MTM dev phase 2 (methods log V4-V6), code = git archive 2691931 in $D/code. One GPU job at a time, in sequence.
# PROMPTS is set from the V4 smoke test by the 8-hour rule (N,C or C). Dev only; no retries; scripts refuse to overwrite.
# Needs phase 1b: the V3b raw scores in $J/dev1b/private.
set -u
PROMPTS=${PROMPTS:?set PROMPTS to N,C or C}
J=/home/chaw/patent-to-pilot-jobs/mtm-20261107
D=$J/dev2
M=/home/chaw/patent-to-pilot-jobs/research-product-o1-o4-20261031/models
PY=/home/chaw/patent-to-pilot-jobs/research-product-o1-o4-20261031/venv/bin/python
export CUDA_VISIBLE_DEVICES=GPU-277ccc57-c3e5-0731-cd49-f4f8695f7089
S=$D/logs/status.log
mkdir -p $D/private $D/logs $D/analysis $D/out; cd $D/code || exit 1
step() { name=$1; shift; echo "$(date -u +%FT%TZ) start $name" >> $S; "$@" > $D/logs/$name.log 2>&1; rc=$?; echo "$(date -u +%FT%TZ) end $name exit=$rc" >> $S; return $rc; }
DENSE="--corpus $J/inputs/corpus.jsonl --baseline-dir $J/out --model-dir $M/patembed-large --vectors $J/out/passage-vectors-f32.npy"
LAM=0.0,0.5,0.6,0.7,0.8,0.9,1.0
# V5: V3b reranker scores fused with dense over the X top 100 (P and T)
for qv in P-dev T-dev; do
  step fusion-cef-$qv $PY scripts/healthtech/run_mtm_fusion.py $DENSE --queries $J/inputs/queries-$qv.jsonl \
    --scores cef=$J/dev1b/private/ce-scores-$qv.jsonl --top 100 --lambdas $LAM --output-dir $D/out --name $qv
done
# V4: Qwen3-8B yes/no scores on the X top 30 (P), then fusion
step llm-P-dev $PY scripts/healthtech/run_mtm_rerank_llm.py --corpus $J/inputs/corpus.jsonl --queries $J/inputs/queries-P-dev.jsonl \
  --baseline-dir $J/out --model-dir $M/qwen3-8b --output-dir $D/private --name P-dev --prompts $PROMPTS --top 30
SC=$(echo $PROMPTS | tr ',' '\n' | sed "s#.*#llm&=$D/private/llm&-scores-P-dev.jsonl#" | paste -sd,)
step fusion-llm-P-dev $PY scripts/healthtech/run_mtm_fusion.py $DENSE --queries $J/inputs/queries-P-dev.jsonl \
  --scores $SC --top 30 --lambdas $LAM --output-dir $D/out --name P-dev
# V6: function text from each P brief, then a second dense channel fused with P
step gen-F-dev $PY scripts/healthtech/run_qwen_scout_actions.py generate --input $J/inputs/brief-inputs-dev.jsonl \
  --model-dir $M/qwen3-8b --output $D/private/briefs-F-dev.out.jsonl --actions F --briefs $J/out/briefs-P-dev.out.jsonl
step build-F-dev $PY scripts/healthtech/build_mtm_p_queries.py --generated $D/private/briefs-F-dev.out.jsonl --key F_P \
  --output $D/private/queries-F-dev.jsonl
step channel-F-P-dev $PY scripts/healthtech/run_mtm_hybrid.py --corpus $J/inputs/corpus.jsonl --queries $J/inputs/queries-P-dev.jsonl \
  --queries-meta $J/inputs/queries-meta.jsonl --model-dir $M/patembed-large --vectors $J/out/passage-vectors-f32.npy \
  --channel-queries $D/private/queries-F-dev.jsonl --method-prefix fch --lambdas $LAM --output-dir $D/out --name P-dev
METHODS=$(for g in llmN llmC cef fch; do for l in 0.0 0.5 0.6 0.7 0.8 0.9 1.0; do printf "%s-%s," $g $l; done; done)
step analysis nice $PY scripts/healthtech/analyze_mtm_methods.py --queries-meta $J/inputs/queries-meta.jsonl --baseline-dir $J/out \
  --methods-dir $D/out --methods ${METHODS%,} --cv-prefix llm,cef,fch --query-views P,T --output $D/analysis/dev-phase2.json
echo "$(date -u +%FT%TZ) all done" >> $S
