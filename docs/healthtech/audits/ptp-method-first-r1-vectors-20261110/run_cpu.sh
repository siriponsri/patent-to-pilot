#!/usr/bin/env bash
set -eu
J=/home/chaw/patent-to-pilot-jobs/mtm-20261107/r1-vector-identity-20261110-v2
M=/home/chaw/patent-to-pilot-jobs/mtm-20261107
B=/home/chaw/patent-to-pilot-jobs/research-product-o1-o4-20261031
cd "$J/code"
printf '%s start vector-identity CPU-only\n' "$(date -u +%FT%TZ)" >> "$J/logs/status.log"
set +e
"$B/venv/bin/python" scripts/healthtech/inspect_mtm_vector_identity.py \
  --corpus "$M/inputs/corpus.jsonl" \
  --vectors "$M/out/passage-vectors-f32.npy" \
  --model-root "$B/models/patembed-large" \
  --encoding-receipt "$M/out/receipt-T-dev.json" \
  --reuse-receipt "$M/out/receipt-P-dev.json" \
  --output "$J/vector-identity.json" > "$J/logs/inspection.log" 2>&1
result=$?
printf '%s end vector-identity exit=%s\n' "$(date -u +%FT%TZ)" "$result" >> "$J/logs/status.log"
exit "$result"
