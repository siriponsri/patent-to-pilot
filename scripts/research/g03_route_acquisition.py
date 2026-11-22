"""G03 DEV route-acquisition arms (protocol docs/healthtech/research/g03-dev/G03-DEV-PROTOCOL.md, frozen at ec720914).

Runtime side only: reads the precomputed depth-1000 route rankings (no labels, no TEST) and writes, per arm, a run file
with the final top-200 ranking produced by the common final scorer (RRF over acquired windows), plus a trace summary.

Arms (protocol §4): every fixed allocation (nL, nQ, nP, nA) with sum = B, and the policy support_frontier_v0 in two variants
(novelty, consensus) anchored on L window 1 + the declared dense route window 1.

Usage (dr-train, research venv):
  python g03_route_acquisition.py --runs-root /data/ptp-paper2/bridgeret/runs --block P1-DEV --out /data/ptp-paper2/g03-dev/runs \
      --budgets 1 [--policy --anchor-dense P] [--workers 48]
"""
from __future__ import annotations

import argparse
import gzip
import itertools
import json
import os
from collections import Counter
from multiprocessing import Pool
from pathlib import Path
import time

ROUTES = ('L', 'Q', 'P', 'A')
RDIR = {'L': 'bm25', 'Q': 'z-qwen3', 'P': 'z-patembed', 'A': 'z-arctic'}
WINDOW, RRF_K, FINAL_DEPTH = 200, 60, 200
NEUTRAL_DUP = 0.5
PROTECTED = ('P1-TEST', 'P2-TEST', 'P3-TEST')

DATA: dict[str, dict[str, list[str]]] = {}   # route -> app -> ranked units (filled before forking)
APPS: list[str] = []


def load_route(path: Path) -> dict[str, list[str]]:
    intern: dict[str, str] = {}
    out: dict[str, list[tuple[int, str]]] = {}
    with gzip.open(path, 'rt', encoding='utf-8') as f:
        header = f.readline().rstrip('\n').split('\t')
        assert header[:3] == ['app_id', 'rank', 'unit'], header
        for line in f:
            a, r, u, _ = line.rstrip('\n').split('\t')
            u = intern.setdefault(u, u)
            out.setdefault(a, []).append((int(r), u))
    return {a: [u for _, u in sorted(v)] for a, v in out.items()}


def final_ranking(acquired: dict[str, int], lists: dict[str, list[str]]) -> list[tuple[str, float]]:
    """Common final scorer (protocol §3): RRF over acquired windows; ties by best acquired rank, then unit id."""
    score: dict[str, float] = {}
    best: dict[str, int] = {}
    for r, depth in acquired.items():
        for i, u in enumerate(lists[r][:depth]):
            score[u] = score.get(u, 0.0) + 1.0 / (RRF_K + i + 1)
            if i < best.get(u, 10 ** 9):
                best[u] = i
    ranked = sorted(score, key=lambda u: (-score[u], best[u], u))[:FINAL_DEPTH]
    return [(u, score[u]) for u in ranked]


def allocation_arm(lists, alloc):
    acquired = {r: WINDOW * n for r, n in zip(ROUTES, alloc) if n and lists[r]}
    pool = set()
    for r, d in acquired.items():
        pool.update(lists[r][:d])
    trace = ','.join(f'{r}{n}' for r, n in zip(ROUTES, alloc) if n)
    return final_ranking(acquired, lists), trace, len(pool)


def policy_arm(lists, budget, mode, anchor_dense):
    """support_frontier_v0, single whole-query obligation (protocol §5). Labels are never read."""
    depth = {r: 0 for r in ROUTES}
    attempts = {r: 0 for r in ROUTES}
    useful = {r: 0 for r in ROUTES}
    dup: dict[str, float | None] = {r: None for r in ROUTES}
    pool: set[str] = set()
    actions: list[str] = []

    def take(r):
        win = lists[r][depth[r]:depth[r] + WINDOW]
        new = [u for u in win if u not in pool]
        dup[r] = 1.0 - len(new) / len(win)
        useful[r] += int(len(new) > 0)
        attempts[r] += 1
        depth[r] += len(win)
        pool.update(win)
        actions.append(f'{r}{attempts[r]}')

    for r in ('L', anchor_dense)[:budget]:
        if lists[r]:
            take(r)
    while len(actions) < budget:
        feasible = [r for r in ROUTES if depth[r] < len(lists[r])]
        if not feasible:
            break

        def score(r):
            y = (1 + useful[r]) / (2 + attempts[r])
            d = dup[r] if attempts[r] else NEUTRAL_DUP
            return y * (1 - d) if mode == 'novelty' else y * d

        take(min(feasible, key=lambda r: (-score(r), attempts[r], ROUTES.index(r))))
    acquired = {r: d for r, d in depth.items() if d}
    return final_ranking(acquired, lists), ','.join(actions), len(pool)


def run_arm(job):
    name, kind, param, budget, out_path = job
    t0 = time.time()
    traces: Counter = Counter()
    pools = []
    tmp = out_path.with_suffix('.tmp')
    with open(tmp, 'w', encoding='utf-8') as f:
        f.write('app_id\trank\tunit\tscore\n')
        for a in APPS:
            lists = {r: DATA[r].get(a, []) for r in ROUTES}
            if kind == 'alloc':
                ranked, trace, npool = allocation_arm(lists, param)
            else:
                ranked, trace, npool = policy_arm(lists, budget, param[0], param[1])
            traces[trace] += 1
            pools.append(npool)
            for i, (u, s) in enumerate(ranked, start=1):
                f.write(f'{a}\t{i}\t{u}\t{s:.8f}\n')
    os.replace(tmp, out_path)
    return {'arm': name, 'kind': kind, 'budget': budget, 'param': list(param) if kind == 'alloc' else list(param),
            'queries': len(APPS), 'mean_pool': sum(pools) / max(1, len(pools)),
            'top_traces': traces.most_common(12), 'n_distinct_traces': len(traces),
            'cpu_seconds': round(time.time() - t0, 1)}


def allocations(budget):
    return [c for c in itertools.product(range(budget + 1), repeat=4) if sum(c) == budget]


def arm_name(alloc):
    return 'alloc-' + '-'.join(f'{r}{n}' for r, n in zip(ROUTES, alloc))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--runs-root', required=True)
    ap.add_argument('--block', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--budgets', default='1')
    ap.add_argument('--policy', action='store_true', help='also build the two SF-v0 variants for each budget')
    ap.add_argument('--anchor-dense', choices=('Q', 'P', 'A'))
    ap.add_argument('--workers', type=int, default=48)
    a = ap.parse_args()
    if a.block in PROTECTED:
        raise SystemExit('G03 DEV never reads TEST blocks')
    if a.policy and not a.anchor_dense:
        raise SystemExit('--policy needs --anchor-dense (selected from the E01 gate on P1-DEV)')
    t0 = time.time()
    for r in ROUTES:
        DATA[r] = load_route(Path(a.runs_root) / RDIR[r] / f'run-{a.block}.tsv.gz')
        print(f'{time.time() - t0:7.1f}s loaded {r} ({RDIR[r]}): {len(DATA[r])} queries', flush=True)
    APPS.extend(sorted(set().union(*(DATA[r].keys() for r in ROUTES))))
    out = Path(a.out) / a.block
    out.mkdir(parents=True, exist_ok=True)
    jobs = []
    for b in (int(x) for x in a.budgets.split(',')):
        for alloc in allocations(b):
            jobs.append((arm_name(alloc), 'alloc', alloc, b, out / f'{arm_name(alloc)}.tsv'))
        if a.policy and b >= 1:
            for mode in ('novelty', 'consensus'):
                name = f'sf-v0{mode[0]}-B{b}'
                jobs.append((name, 'policy', (mode, a.anchor_dense), b, out / f'{name}.tsv'))
    jobs = [j for j in jobs if not j[4].exists()]   # resumable
    print(f'{len(jobs)} arms to build for {a.block} over {len(APPS)} queries', flush=True)
    with Pool(min(a.workers, max(1, len(jobs)))) as pool:
        for res in pool.imap_unordered(run_arm, jobs):
            with open(out / 'arms-trace.jsonl', 'a', encoding='utf-8') as f:
                f.write(json.dumps(res) + '\n')
            print(f"{time.time() - t0:7.1f}s built {res['arm']} ({res['cpu_seconds']}s)", flush=True)
    print('G03_ARMS_DONE', a.block, a.budgets, flush=True)


if __name__ == '__main__':
    main()
