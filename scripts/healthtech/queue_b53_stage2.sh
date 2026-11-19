#!/bin/bash
# B53 Stage 2 (plans/B53-PREDECLARATION.md, Stage 2 section): Qwen3-Reranker x 4 instructions, then BGE plain pair.
cd /data/ptp-paper2/b53
export PYTHONPATH=/home/chaw/patent-to-pilot-jobs/research-product-o1-o4-20261031/venv/lib/python3.12/site-packages TOKENIZERS_PARALLELISM=false CUDA_VISIBLE_DEVICES=1 PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True MEM_FRAC=0.15
run() { name=$1; shift; /usr/bin/time -v nice -n 10 python3 code/b53_rerank.py "$@" > logs/$name.log 2> logs/$name.time; grep -q "Exit status: 0" logs/$name.time && echo "$name OK" || echo "$name FAILED"; }
run RERANK rerank inputs runs /data/ptp-paper2/models/qwen3-reranker-0.6b stage2
run BGE rerank-bge inputs runs /home/chaw/patent-to-pilot-jobs/research-product-o1-o4-20261031/models/bge-reranker-v2-m3 stage2
echo B53_STAGE2_SCORES_DONE
