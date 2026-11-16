#!/usr/bin/env bash
# Run INSIDE a RunPod pod after unpacking the bundle into /workspace:
#   cd /workspace && tar xzf runpod-pilot-bundle.tar.gz && bash runpod-pilot/pod_run.sh rtx4090 40
# Args: <label> [watchdog_minutes, default 40]. The watchdog removes (terminates) the pod after that many
# minutes no matter what, so the per-pod spend can never exceed watchdog_minutes x hourly rate.
# Produces /workspace/results-<label>.tar.gz (receipts, parity JSON, vectors). Fetch it, then terminate.
set -euo pipefail
LABEL=${1:?label, e.g. rtx4090 or a100sxm}
WATCH_MIN=${2:-40}
cd /workspace/runpod-pilot

if [ -n "${RUNPOD_POD_ID:-}" ] && command -v runpodctl >/dev/null; then
  nohup bash -c "sleep $((WATCH_MIN * 60)); runpodctl remove pod $RUNPOD_POD_ID" > /workspace/watchdog.log 2>&1 &
  echo "WATCHDOG: pod $RUNPOD_POD_ID will be terminated in $WATCH_MIN min (pid $!)"
  runpodctl get pod "$RUNPOD_POD_ID" >/dev/null 2>&1 || echo "WARNING: runpodctl cannot see this pod; terminate it manually in the console when done"
else
  echo "WARNING: no RUNPOD_POD_ID/runpodctl -> no self-terminate watchdog; terminate the pod manually"
fi

sha256sum -c SHA256SUMS
python - <<'EOF'
import torch
print("torch", torch.__version__, "cuda", torch.version.cuda, torch.cuda.get_device_name(0))
if not torch.__version__.startswith("2.8.0"):
    print("NOTE: reference used torch 2.8.0+cu128; the receipt records this difference")
EOF
pip install --no-cache-dir -q "transformers==4.55.2" "tokenizers==0.21.4" "safetensors==0.6.2" "numpy==2.2.6"
pip freeze > pip-freeze-$LABEL.txt
nvidia-smi | tee nvidia-smi-$LABEL.txt

# 1) throughput: whole sample (6,261 docs, 26,972 passages), fp16, batch sweep.
python encode_pilot.py --sample sample.jsonl --out-dir out-$LABEL-fp16 --mode fp16 \
  --sweep 32,64,128,256,512 --sweep-passages 2048 --time-limit-seconds 1200 --model-cache /workspace/patembed-large
# 2) fp32 on the first 1,000 docs (cross-GPU same-precision parity with the V100 reference).
python encode_pilot.py --sample sample.jsonl --out-dir out-$LABEL-fp32-1k --mode fp32 --max-docs 1000 \
  --sweep 32,64,128 --sweep-passages 1024 --time-limit-seconds 600 --model-dir /workspace/patembed-large
# 3) parity against the V100 fp32 reference (first 1,000 docs).
python parity_check.py --run-a ref-v100-fp32-1k --run-b out-$LABEL-fp32-1k --n-docs 1000 --out parity-$LABEL-fp32-vs-v100fp32.json
python parity_check.py --run-a ref-v100-fp32-1k --run-b out-$LABEL-fp16 --n-docs 1000 --out parity-$LABEL-fp16-vs-v100fp32.json
python decision_table.py "V100 fp16 (dr-train, shared)=0=ref-v100-fp16-1k/receipt-fp16.json" \
  "$LABEL fp16=${PRICE_PER_HOUR:-0}=out-$LABEL-fp16/receipt-fp16.json" | tee decision-$LABEL.md

tar czf /workspace/results-$LABEL.tar.gz out-$LABEL-fp16 out-$LABEL-fp32-1k parity-$LABEL-*.json \
  decision-$LABEL.md pip-freeze-$LABEL.txt nvidia-smi-$LABEL.txt
sha256sum /workspace/results-$LABEL.tar.gz | tee /workspace/results-$LABEL.tar.gz.sha256
echo "DONE. Fetch /workspace/results-$LABEL.tar.gz now, then terminate the pod (runpodctl remove pod \$RUNPOD_POD_ID)."
