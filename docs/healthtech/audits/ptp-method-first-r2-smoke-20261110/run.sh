#!/usr/bin/env bash
set -u
J=$1
PY=/home/chaw/patent-to-pilot-jobs/research-product-o1-o4-20261031/venv/bin/python
MODEL=/home/chaw/patent-to-pilot-jobs/research-product-o1-o4-20261031/models/qwen3-8b
export CUDA_VISIBLE_DEVICES=GPU-277ccc57-c3e5-0731-cd49-f4f8695f7089
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
printf '%s START SYNTHETIC_SMOKE_SUPERVISOR\n' "$(date -u +%FT%TZ)" > "$J/logs/status.log"
timeout --signal=TERM --kill-after=30s 1200 "$PY" "$J/code/scripts/healthtech/smoke_sacr_qwen.py" \
  --model-root "$MODEL" \
  --identity "$J/code/docs/healthtech/audits/ptp-method-first-r2-weights-20261110/identity.json" \
  --identity-sha256 5b4f4a7317919979affc88df9837a6741ffa6715bf39d9516fe6cd4816ac9ac2 \
  --output "$J/out"
rc=$?
printf '%s EXIT %s\n' "$(date -u +%FT%TZ)" "$rc" >> "$J/logs/status.log"
exit "$rc"
