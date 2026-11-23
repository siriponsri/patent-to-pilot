"""A3r1 RunPod rebuild: regenerate the protocol-v1 F* run (alloc-L0-Q2-P2-A0) from the rebuilt route runs.

Amendment: docs/healthtech/research/g03-dev/A3R1-AMENDMENT-RUNPOD-REBUILD.md §2.4. The G03 v0 directory on dr-train holds
evals/P1-DEV/alloc-L0-Q2-P2-A0.json, which the frozen pilot decision reads (--v0-evals evals) and requires to equal the A3r1
F* (alloc-L0-Q2-P2-H0-K0) per query. The A3r1 F* is built from the rebuilt Q and P runs, so the v0 F* is rebuilt from the
same runs here, with the unchanged harness (g03_route_acquisition.run_arm, allocation (L0, Q2, P2, A0), budget 4).
Full-evaluation addendum (A3R1-FULL-EVAL-RUNPOD.md §2): the same rebuild for block VAL from the archived dr-train VAL route
runs (`g03_a3_decide.py full` checks the integrity on P1-DEV and VAL). The default block is unchanged (P1-DEV).

Route A (z-arctic) has a zero allocation in F*. In the harness its only effect is to add apps that get no rows, so it is
loaded when runs/z-arctic/run-<block>.tsv.gz exists and is empty otherwise; the written run is identical either way.
Runtime side only: reads route rankings, never labels. Blocks P1-DEV (default) and VAL only; TEST is refused.

Usage: python3 -I g03_a3r1_runpod_v0.py <g03_code_dir> <bridgeret_runs_dir> <out_dir> [P1-DEV|VAL]
       writes <out_dir>/<block>/alloc-L0-Q2-P2-A0.tsv and <out_dir>/<block>/arms-trace-v0-rebuild.jsonl
"""
import json
import sys
import time
from pathlib import Path

ALLOWED = ('P1-DEV', 'VAL')
ARM, ALLOC, BUDGET = 'alloc-L0-Q2-P2-A0', (0, 2, 2, 0), 4


def main(argv):
    block = argv[3] if len(argv) > 3 else 'P1-DEV'
    if block not in ALLOWED:
        raise SystemExit(f'refusing block {block!r}: P1-DEV or VAL only (never TEST)')
    code, runs, out = Path(argv[0]), Path(argv[1]), Path(argv[2]) / block
    sys.path.insert(0, str(code))
    import g03_route_acquisition as ra
    ra.ROUTES = ('L', 'Q', 'P', 'A')
    ra.RDIR = {'L': 'bm25', 'Q': 'z-qwen3', 'P': 'z-patembed', 'A': 'z-arctic'}
    t0 = time.time()
    for r in ra.ROUTES:
        p = runs / ra.RDIR[r] / f'run-{block}.tsv.gz'
        if r == 'A' and not p.exists():
            ra.DATA[r] = {}
            print('route A absent (zero allocation in F*): empty', flush=True)
            continue
        ra.DATA[r] = ra.load_route(p)
        print(f'{time.time() - t0:7.1f}s loaded {r}: {len(ra.DATA[r])} queries', flush=True)
    ra.APPS.extend(sorted(set().union(*(ra.DATA[r].keys() for r in ra.ROUTES))))
    out.mkdir(parents=True, exist_ok=True)
    res = ra.run_arm((ARM, 'alloc', ALLOC, BUDGET, out / f'{ARM}.tsv'))
    res['note'] = f'A3r1 RunPod rebuild of the protocol-v1 F* run from rebuilt route runs ({block})'
    with open(out / 'arms-trace-v0-rebuild.jsonl', 'a', encoding='utf-8') as f:
        f.write(json.dumps(res) + '\n')
    print(json.dumps({k: res[k] for k in ('arm', 'queries', 'mean_pool', 'cpu_seconds')}), flush=True)
    print('G03_V0_FSTAR_REBUILT', block, flush=True)


if __name__ == '__main__':
    main(sys.argv[1:])
