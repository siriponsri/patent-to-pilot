#!/usr/bin/env bash
# G03 A3r1 Stage B evaluation queue: A3r0 §4 as kept by G03-DEV-AMENDMENT-3R1-PROPOSED.md §7 (frozen by
# P1-T03_freeze_receipt.json), for m* = deepseek/deepseek-v4-flash-0731 (frozen pilot decision, results-a3r1-pilot.json).
# Host and inputs: docs/healthtech/research/g03-dev/A3R1-FULL-EVAL-RUNPOD.md (declared before any Stage B number).
# Needs: the gated L, Q, P route runs of P1-DEV and VAL under $BR/runs/{bm25,z-qwen3,z-patembed}; the v0 F* evaluations of
# both blocks in evals/<block>/ (the integrity reference); PatEmbed corpus vectors ($G03_A3R1_PASSAGES_DIR); ser-arctic-v1;
# the Stage B ledgers a3r1/ledger/<m*>/{P1-DEV,VAL}.jsonl (P1-DEV includes the 2,000 pilot records); a3/apps-<block>.json.
#   1 H_m* (PatEmbed HyDE, GPU lock) and 2 K_m* (BM25 on the LLM text, CPU) for every app of both blocks with a usable
#     response, filing-date and own-unit masks (A3r0 §2, unchanged code)
#   3 arms: the 70 fixed allocations at B = 4 plus the 5 at B = 1 over (L, Q, P, H, K), on each block, over the F* apps
#   4 the unchanged evaluator, both blocks
#   5 g03_a3_decide.py full (unchanged): F* integrity on both blocks; F3* on P1-DEV with the frozen tie rule; VAL
#     principal F3* - F* (art-unit cluster bootstrap, B = 10,000, seed 20261119); frozen CONTINUE / REVISE / PARK
# P1-DEV and VAL only; every script refuses TEST blocks. Resumable (finished routes, arms and evaluations are skipped).
# Env overrides only (dr-train defaults unchanged): G03_PY, G03_GPU_DEVICE, G03_WORKERS, G03_EVAL_PAR,
# G03_A3R1_PASSAGES_DIR (pod: the re-encoded vectors), G03_A3_GPU_MATCH (read by g03_a3_routes.py).
set -euo pipefail
PY=${G03_PY:-/home/chaw/patent-to-pilot-jobs/research-product-o1-o4-20261031/venv/bin/python}
GDEV=${G03_GPU_DEVICE:-1}; WK=${G03_WORKERS:-36}; EP=${G03_EVAL_PAR:-18}
G=/data/ptp-paper2/g03-dev
BR=/data/ptp-paper2/bridgeret
C=/data/ptp-paper2/challenge1m/out-v1
T=/data/ptp-paper2/splits/private/tasks.tsv
EV=$BR/code/eval_bridgeret_dev.py
PE=/home/chaw/patent-to-pilot-jobs/research-product-o1-o4-20261031/models/patembed-large
PV=${G03_A3R1_PASSAGES_DIR:-$BR/runs/z-patembed}
M=deepseek__deepseek-v4-flash-0731
BLOCKS="P1-DEV VAL"
cd "$G"
# one ledger file per model for the route builder (it filters records by block); P1-DEV then VAL, bytes unchanged
LF=a3r1/ledger-full/$M/P1-DEV+VAL.jsonl
WANT=$(( $(stat -c%s "a3r1/ledger/$M/P1-DEV.jsonl") + $(stat -c%s "a3r1/ledger/$M/VAL.jsonl") ))
if [ ! -s "$LF" ] || [ "$(stat -c%s "$LF")" != "$WANT" ]; then
  mkdir -p "a3r1/ledger-full/$M"
  cat "a3r1/ledger/$M/P1-DEV.jsonl" "a3r1/ledger/$M/VAL.jsonl" > "$LF.tmp"
  mv "$LF.tmp" "$LF"
fi
SPEC="$M=$LF,"
CUDA_VISIBLE_DEVICES=$GDEV $PY -I code/g03_a3_routes.py dense "$SPEC" "$PE" $BR/ser-patembed-v1/queries.jsonl \
  "$PV/passages.f16.npy" "$PV/units.json" "$C/corpus-units.tsv" "$T" a3r1/routes-full P1-DEV VAL
export CUDA_VISIBLE_DEVICES=""
$PY -I code/g03_a3_routes.py bm25 "$SPEC" $BR/ser-arctic-v1 "$C/corpus-units.tsv" "$T" a3r1/routes-full P1-DEV VAL
ROUTES="L=$BR/runs/bm25,Q=$BR/runs/z-qwen3,P=$BR/runs/z-patembed,H=$G/a3r1/routes-full/$M/H,K=$G/a3r1/routes-full/$M/K"
for b in $BLOCKS; do
  $PY -I code/g03_route_acquisition.py --runs-root / --routes "$ROUTES" --block "$b" --apps-file "a3/apps-$b.json" \
    --out runs-a3r1-full --budgets 1,4 --workers "$WK"
  mkdir -p "evals-a3r1-full/$b"
  ls runs-a3r1-full/$b/*.tsv | while read -r f; do n=$(basename "$f" .tsv); [ -s "evals-a3r1-full/$b/$n.json" ] || echo "$f"; done | \
    xargs -r -P "$EP" -I{} sh -c 'n=$(basename {} .tsv); python3 -I '"$EV"' {} '"$C"'/pairs-dev.tsv '"$C"'/corpus-units.tsv '"$T"' '"$b"' evals-a3r1-full/'"$b"'/$n.json > evals-a3r1-full/'"$b"'/$n.log 2>&1'
  n_runs=$(ls runs-a3r1-full/$b/*.tsv | wc -l); n_ev=$(ls evals-a3r1-full/$b/*.json | wc -l)
  [ "$n_runs" = 75 ] && [ "$n_ev" = 75 ] || { echo "G03_A3R1_FULL_INCOMPLETE $b runs=$n_runs evals=$n_ev"; exit 1; }
done
$PY -I code/g03_a3_decide.py full --evals evals-a3r1-full --v0-evals evals --meta $BR/am7/prep-v1/meta.pkl \
  --out results-a3r1-full.json
echo G03_A3R1_FULL_DONE
