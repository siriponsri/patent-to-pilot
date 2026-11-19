#!/bin/bash
# dr-train watcher for the P1 FT grid on RunPod pod ndxgcuza0qg17m (AM-5). Autonomous; survives the owner's notebook shutdown.
# Pulls each finished config (train logs + fp16 checkpoint), encodes P1-DEV/VAL on the V100 with dense_bridgeret_v3.py
# (same code as the zero-shot baselines) and evaluates. After MAXCFG configs are pulled, stops the pod runner and writes PULLED.
cd /data/ptp-paper2/bridgeret
export PYTHONPATH=/home/chaw/patent-to-pilot-jobs/research-product-o1-o4-20261031/venv/lib/python3.12/site-packages TOKENIZERS_PARALLELISM=false CUDA_VISIBLE_DEVICES=1 BS=8 PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
MAXCFG=${MAXCFG:-3}
P="ssh -i /home/chaw/.ssh/ptp_runpod_ed25519 -p 22089 -o ConnectTimeout=30 -o BatchMode=yes root@194.68.245.232"
C=/data/ptp-paper2/challenge1m/out-v1; T=/data/ptp-paper2/splits/private/tasks.tsv
QP="Instruct: Given a patent application, retrieve prior art cited against it
Query: "
mkdir -p ft-grid
while true; do
  done_list=$($P 'cd /workspace/results 2>/dev/null && for d in */; do d=${d%/}; [ -f $d/DONE ] && echo $d; [ -f $d/FAILED ] && echo FAILED:$d; done' 2>/dev/null)
  for d in $done_list; do
    case $d in FAILED:*) n=${d#FAILED:}; [ -e ft-grid/$n.failed ] || { scp -q -r -i /home/chaw/.ssh/ptp_runpod_ed25519 -P 22089 root@194.68.245.232:/workspace/results/$n ft-grid/$n-failed; touch ft-grid/$n.failed; echo "$(date -u) FAILED $n"; }; continue;; esac
    [ -e ft-grid/$d.pulled ] && continue
    if scp -q -r -i /home/chaw/.ssh/ptp_runpod_ed25519 -P 22089 root@194.68.245.232:/workspace/results/$d ft-grid/; then
      touch ft-grid/$d.pulled; echo "$(date -u) PULLED $d"
    fi
  done
  # encode/eval the oldest pulled-but-not-evaluated config (one at a time; GPU lock inside dense_bridgeret_v3.py)
  for f in $(ls -tr ft-grid/*.pulled 2>/dev/null); do
    n=$(basename $f .pulled); [ -e ft-grid/$n.evaluated ] && continue
    echo "$(date -u) ENCODE $n"
    /usr/bin/time -v nice -n 10 python3 code/dense_bridgeret_v3.py ft-grid/$n/ckpt-fp16 last "$QP" ser-qwen3-v1 $C/corpus-units.tsv $T runs/ft-$n 0.15 P1-DEV VAL > ft-grid/$n.encode.log 2> ft-grid/$n.encode.time
    if grep -q "Exit status: 0" ft-grid/$n.encode.time; then
      for b in P1-DEV VAL; do python3 -I code/eval_bridgeret_dev.py runs/ft-$n/run-$b.tsv $C/pairs-dev.tsv $C/corpus-units.tsv $T $b runs/ft-$n/eval-$b.json > runs/ft-$n/eval-$b.log 2>&1; done
      rm -f runs/ft-$n/passages.f16.npy
      touch ft-grid/$n.evaluated; echo "$(date -u) EVALUATED $n $(python3 -c "import json;print(json.load(open('runs/ft-$n/eval-P1-DEV.json'))['metrics']['OUT_R@200'])")"
    else
      touch ft-grid/$n.evaluated; echo "$(date -u) ENCODE_FAILED $n"
    fi
    break
  done
  npulled=$(ls ft-grid/*.pulled 2>/dev/null | wc -l)
  if [ "$npulled" -ge "$MAXCFG" ] && [ ! -e ft-grid/RUNNER_STOPPED ]; then
    $P 'pkill -f ft_runpod_runner.py; touch /workspace/results/PULLED' && touch ft-grid/RUNNER_STOPPED && echo "$(date -u) RUNNER_STOPPED after $npulled configs; PULLED written"
  fi
  nev=$(ls ft-grid/*.evaluated 2>/dev/null | wc -l)
  if [ -e ft-grid/RUNNER_STOPPED ] && [ "$nev" -ge "$npulled" ]; then echo "$(date -u) WATCH_DONE"; break; fi
  sleep 300
done
