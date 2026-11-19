#!/bin/bash
# B53 Stage 1 (plans/B53-PREDECLARATION.md, frozen 274af5de). CPU BM25 then V100 dense arms one at a time, then RRF + eval.
cd /data/ptp-paper2/b53
export PYTHONPATH=/home/chaw/patent-to-pilot-jobs/research-product-o1-o4-20261031/venv/lib/python3.12/site-packages TOKENIZERS_PARALLELISM=false CUDA_VISIBLE_DEVICES=1 PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
M=/home/chaw/patent-to-pilot-jobs/research-product-o1-o4-20261031/models
run() { name=$1; shift; /usr/bin/time -v nice -n 10 python3 code/b53_first_stage.py "$@" > logs/$name.log 2> logs/$name.time; grep -q "Exit status: 0" logs/$name.time && echo "$name OK" || echo "$name FAILED"; }
mkdir -p logs
run F1 bm25 inputs runs
BS=16 run F0 dense inputs runs F0 $M/patembed-base st-mixed 0.15
BS=16 run F0-OUT dense inputs runs F0-OUT $M/patembed-base st-out 0.15
BS=16 run F3 dense inputs runs F3 /data/ptp-paper2/models/arctic-embed-m-v2.0 arctic 0.15
BS=8 run F6 dense inputs runs F6 $M/patembed-large st-mixed 0.15
BS=8 run F7 dense inputs runs F7 /data/ptp-paper2/models/qwen3-embedding-0.6b qwen3 0.15
run F2 rrf runs F2 F1 F0
run F4 rrf runs F4 F1 F3
run EVAL eval inputs runs stage1-results.json
echo B53_STAGE1_DONE
