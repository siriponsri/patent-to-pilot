#!/bin/bash
# dr-train watcher for one parallel FT pod (AM-5, envelope USD 25): waits for results/<CFG>/DONE on the pod, pulls the
# config's results (train logs + gzipped P1-DEV/VAL runs encoded ON the pod), evaluates with eval_bridgeret_dev.py,
# writes PULLED on the pod and exits. The pod itself must be deleted via RunPod MCP afterwards.
# usage: ft_watch_pod.sh NAME HOST PORT CFG
N=$1; H=$2; PT=$3; CFG=$4
cd /data/ptp-paper2/bridgeret
C=/data/ptp-paper2/challenge1m/out-v1; T=/data/ptp-paper2/splits/private/tasks.tsv
K=/home/chaw/.ssh/ptp_runpod_ed25519
P="ssh -i $K -p $PT -o ConnectTimeout=30 -o BatchMode=yes -o StrictHostKeyChecking=accept-new root@$H"
mkdir -p ft-grid runs/ft-$CFG
while true; do
  st=$($P "test -f /workspace/results/$CFG/DONE && echo DONE; test -f /workspace/results/$CFG/FAILED && echo FAILED" 2>/dev/null)
  if [ "$st" = "FAILED" ]; then scp -q -r -i $K -P $PT root@$H:/workspace/results/$CFG ft-grid/$CFG-failed; echo "$(date -u) $N FAILED $CFG"; exit 1; fi
  if [ "$st" = "DONE" ]; then
    scp -q -r -i $K -P $PT -o StrictHostKeyChecking=accept-new root@$H:/workspace/results/$CFG ft-grid/ || { sleep 60; continue; }
    for b in P1-DEV VAL; do
      gunzip -c ft-grid/$CFG/run-$b.tsv.gz > runs/ft-$CFG/run-$b.tsv
      python3 -I code/eval_bridgeret_dev.py runs/ft-$CFG/run-$b.tsv $C/pairs-dev.tsv $C/corpus-units.tsv $T $b runs/ft-$CFG/eval-$b.json > runs/ft-$CFG/eval-$b.log 2>&1
    done
    touch ft-grid/$CFG.pulled ft-grid/$CFG.evaluated
    $P "touch /workspace/results/PULLED"
    echo "$(date -u) $N EVALUATED $CFG $(python3 -c "import json;print(json.load(open('runs/ft-$CFG/eval-P1-DEV.json'))['metrics']['OUT_R@200'])")"
    exit 0
  fi
  sleep 300
done
