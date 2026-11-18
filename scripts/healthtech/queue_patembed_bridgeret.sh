#!/bin/bash
# Z-PatEmbed-large (optional C3), prompts per clarification CL-1 (retrieval_MIXED). Runs after Z-Qwen3 on the V100.
cd /data/ptp-paper2/bridgeret
export PYTHONPATH=/home/chaw/patent-to-pilot-jobs/research-product-o1-o4-20261031/venv/lib/python3.12/site-packages TOKENIZERS_PARALLELISM=false
PE=/home/chaw/patent-to-pilot-jobs/research-product-o1-o4-20261031/models/patembed-large
QP='encode query for mixed document retrieval: '
DP='encode document for mixed retrieval: '
C=/data/ptp-paper2/challenge1m/out-v1
T=/data/ptp-paper2/splits/private/tasks.tsv
/usr/bin/time -v nice -n 15 python3 code/serialise_bridgeret_texts_v2.py texts-v1 "$PE" "$QP" ser-patembed-v1 24 "$DP" > serp.log 2> serp.time
grep -q "Exit status: 0" serp.time || { echo SER_FAILED; exit 1; }
echo SER_DONE
until grep -qE "ZQWEN3_DONE|ZQWEN3_FAILED|EVAL_FAILED" queue_qwen3.log; do sleep 30; done
export CUDA_VISIBLE_DEVICES=1 BS=16 PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True DOC_PROMPT="$DP"
/usr/bin/time -v nice -n 10 python3 code/dense_bridgeret_v3.py "$PE" mean "$QP" ser-patembed-v1 "$C/corpus-units.tsv" "$T" runs/z-patembed 0.15 P1-DEV VAL > zpe.log 2> zpe.time
grep -q "Exit status: 0" zpe.time || { echo ZPE_FAILED; exit 1; }
for b in P1-DEV VAL; do
  python3 -I code/eval_bridgeret_dev.py runs/z-patembed/run-$b.tsv "$C/pairs-dev.tsv" "$C/corpus-units.tsv" "$T" $b runs/z-patembed/eval-$b.json > runs/z-patembed/eval-$b.log 2>&1
done
echo ZPE_DONE
