#!/usr/bin/env bash
# OWNER ONLY: reads mixed metadata. Do not execute in the development-agent session.
set -euo pipefail
if [[ "${1:-}" != "--owner-curator" ]]; then
  echo 'Run personally as owner-curator; this reads mixed source only to prepare dev bundles.' >&2
  exit 2
fi
HERE=$(cd -- "$(dirname -- "$0")" && pwd)
CODE="$HERE/code"
PY=/home/chaw/patent-to-pilot-jobs/research-product-o1-o4-20261031/venv/bin/python
J=/home/chaw/patent-to-pilot-jobs/mtm-20261107
STAGE="$HERE/staged"
LOCK=/home/chaw/patent-to-pilot-jobs/research-product-o1-o4-20261031/models/.GPU-277ccc57-c3e5-0731-cd49-f4f8695f7089.lock
[[ ! -e "$STAGE" ]] || { echo 'Staging already exists; preserve it, do not restart.' >&2; exit 3; }
exec 9>>"$LOCK"
flock -n 9 || { echo 'Project slot busy; no staging started.' >&2; exit 4; }
export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8
export CUDA_VISIBLE_DEVICES='' HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
ulimit -v 33554432
mkdir -- "$STAGE"
# Completion is written only after both existing validated tools exit successfully.
timeout --signal=TERM --kill-after=5s 1800 bash -s -- "$PY" "$CODE" "$J" "$STAGE" <<'STEPS'
set -euo pipefail
PY=$1 CODE=$2 J=$3 STAGE=$4
"$PY" "$CODE/scripts/healthtech/stage_mtm_metadata.py" \
  --source "$J/inputs/queries-meta.jsonl" \
  --runtime-root "$STAGE/runtime" --dev-eval-root "$STAGE/dev-evaluation" \
  --protected-root "$STAGE/protected" --trusted-curator
"$PY" "$CODE/scripts/healthtech/prepare_mtm_dev_assets.py" \
  --source-corpus "$J/inputs/corpus.jsonl" \
  --dev-queries "$J/inputs/queries-P-dev.jsonl" \
  --metadata-root "$STAGE/runtime/dev" \
  --identity-report "$CODE/docs/healthtech/audits/ptp-method-first-r1-vectors-20261110/vector-identity.json" \
  --identity-report-sha256 935d9b6c677b6df3abba405efe88097811cd1cea907bee42d4292131a8c7d945 \
  --view P --expected-missing-count 0 --output-root "$STAGE/assets-P" --trusted-curator
printf 'OWNER_CURATOR_MTM_PREPARED\n' > "$STAGE/owner-complete.txt"
STEPS
echo 'Owner staging complete. Return only this success message; do not paste source/labels/IDs.'
