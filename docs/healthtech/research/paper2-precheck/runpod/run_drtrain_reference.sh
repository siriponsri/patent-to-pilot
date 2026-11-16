#!/usr/bin/env bash
# V100 reference run on dr-train for the RunPod pilot (first 1,000 sample documents).
# Runs beside the Paper 1 S8 job under the owner's parallel-GPU approval, with hard guards:
#  - the S8 supervisor refuses to launch a batch while ANY compute process is on the V100, so this script
#    only starts when an S8 batch container is running, started >= 10 min ago and <= 80 min ago
#    (SACR batches take about 2.1 h), and each mode is time-limited to 900 s;
#  - free V100 memory must be >= 9 GiB; the CUDA allocator is capped at 8 GiB; batch size <= 32;
#  - container: no network, read-only inputs, 8 CPUs, 16 GiB RAM.
# Usage on dr-train: bash run_drtrain_reference.sh <out-root>   (refuses to reuse an existing out dir)
set -euo pipefail
ROOT=/data/ptp-paper2/runpod-pilot
OUT=${1:?out root}
GPU=GPU-277ccc57-c3e5-0731-cd49-f4f8695f7089   # Tesla V100-SXM2-32GB (the S8 GPU)
MODEL=/home/chaw/patent-to-pilot-jobs/research-product-o1-o4-20261031/models/patembed-large
DEPS=/home/chaw/patent-to-pilot-jobs/research-product-o1-o4-20261031/venv/lib/python3.12/site-packages
IMAGE=sha256:cb33f7f771ecec2ef1225cf39b159591a040391bd73e4c01f00fdfc4c47611d2   # python:3.12-slim
[ -e "$OUT" ] && { echo "refusing to reuse $OUT"; exit 2; }

s8=$(docker ps --filter name=ptp-auto- --format '{{.Names}}' | head -1)
[ -n "$s8" ] || { echo "ABORT: no running S8 batch container (could be at a freeze boundary)"; exit 3; }
started=$(date -d "$(docker inspect -f '{{.State.StartedAt}}' "$s8")" +%s)
age=$(( $(date +%s) - started ))
if [ "$age" -lt 600 ] || [ "$age" -gt 4800 ]; then
  echo "ABORT: S8 batch $s8 age ${age}s outside the safe window [600, 4800]"; exit 3
fi
free=$(nvidia-smi --id=$GPU --query-gpu=memory.free --format=csv,noheader,nounits)
[ "$free" -ge 9216 ] || { echo "ABORT: V100 free memory ${free} MiB < 9216"; exit 3; }
echo "S8 batch $s8 age ${age}s; V100 free ${free} MiB; starting"

mkdir -p "$OUT"
for mode in fp32 fp16; do
  name=ptp-runpod-pilot-v100-ref-$mode-$(date +%Y%m%d%H%M%S)
  mkdir "$OUT/$mode"
  docker run --rm --name "$name" --gpus "device=$GPU" --network none --cpus 8 --memory 16g --pids-limit 256 \
    --read-only --tmpfs /tmp:rw,nosuid,size=268435456 \
    --mount type=bind,src=$ROOT/code,dst=/code,readonly \
    --mount type=bind,src=$ROOT/sample.jsonl,dst=/data/sample.jsonl,readonly \
    --mount type=bind,src=$MODEL,dst=/model,readonly \
    --mount type=bind,src=$DEPS,dst=/deps,readonly \
    --mount type=bind,src=$OUT/$mode,dst=/out \
    -e PYTHONPATH=/deps -e HF_HUB_OFFLINE=1 -e TRANSFORMERS_OFFLINE=1 -e HOME=/tmp \
    -e OMP_NUM_THREADS=8 -e CUDA_VISIBLE_DEVICES=0 \
    --user "$(id -u):$(id -g)" --entrypoint python "$IMAGE" -s /code/encode_pilot.py \
      --sample /data/sample.jsonl --out-dir /out --mode $mode --model-dir /model --max-docs 1000 \
      --sweep 8,16,32 --sweep-passages 512 --max-batch-size 32 --max-gpu-mem-gb 8 --time-limit-seconds 900 \
    2>&1 | tee "$OUT/$mode.log"
done
# Parity (CPU only, no GPU, same image and numpy as the encoder).
docker run --rm --network none --cpus 2 --memory 4g --read-only --tmpfs /tmp:rw,nosuid,size=67108864   --mount type=bind,src=$ROOT/code,dst=/code,readonly --mount type=bind,src=$DEPS,dst=/deps,readonly   --mount type=bind,src=$OUT,dst=/out -e PYTHONPATH=/deps --user "$(id -u):$(id -g)" --entrypoint python "$IMAGE" -s   /code/parity_check.py --run-a /out/fp32 --run-b /out/fp16 --n-docs 1000 --out /out/parity-v100-fp32-vs-fp16.json
