"""P1 BridgeRet: apply the frozen S* rule (pre-declaration section 2 + AM-5) and write the DEV results table.

Rule (frozen before any fine-tuned number): S* = the registered configuration with the highest P1-DEV OUT Recall@200
(conditional); configurations within 0.001 of the best are tied and the tie goes to the simpler recipe (lower S index:
S1 < S2 < S3 < S4), then the smaller grid value (tau, then w_OUT). Only P1-DEV is used to choose; VAL is reported.
Baselines (zero-shot / BM25 / E0) are reported for context and are never candidates.
Usage: python3 bridgeret_select_sstar.py <runs_dir> <out.json> <out.md> CFG [CFG...]
  CFG names follow the grid: S2-t0.02, S3-t0.02-w1.5, S4rule-t0.02, ... (eval files runs/ft-<CFG>/eval-<BLOCK>.json)
"""
import json, re, sys
from pathlib import Path

TIE = 0.001
BASELINES = ('bm25', 'z-arctic', 'z-patembed', 'z-qwen3', 'e0-qwen3')
COLS = ('OUT_R@200', 'IN_R@200', 'ALL_R@200', 'OUT_R@1000', 'OUT_nDCG@10', 'OUT_MRR')
RECIPE_ORDER = {'S1': 1, 'S2': 2, 'S3': 3, 'S4rule': 4, 'S4': 4}


def parse_cfg(name):
    m = re.fullmatch(r'(S1|S2|S3|S4rule|S4)-t([0-9.]+)(?:-w([0-9.]+))?', name)
    if not m:
        raise SystemExit(f'unknown config name {name}')
    return {'recipe': m.group(1), 'tau': float(m.group(2)), 'w_out': float(m.group(3) or 1.0)}


def simplicity(name):
    c = parse_cfg(name)
    return (RECIPE_ORDER[c['recipe']], c['tau'], c['w_out'])


def metrics(path):
    d = json.load(open(path, encoding='utf-8'))
    if d.get('block') in ('P1-TEST', 'P2-TEST', 'P3-TEST'):
        raise SystemExit('refusing a TEST eval file')
    return {k: v['mean'] for k, v in d['metrics'].items()}


def select(dev_scores):
    best = max(dev_scores.values())
    tied = sorted((n for n, v in dev_scores.items() if round(best - v, 9) <= TIE), key=simplicity)   # 0.001 apart = tied
    return tied[0], tied, best


def main(argv):
    runs, out_json, out_md, cfgs = Path(argv[0]), argv[1], argv[2], argv[3:]
    rows = {}
    for c in cfgs:
        parse_cfg(c)
        rows[c] = {b: metrics(runs / f'ft-{c}' / f'eval-{b}.json') for b in ('P1-DEV', 'VAL')}
    base = {}
    for b in BASELINES:
        p = runs / b / 'eval-P1-DEV.json'
        if p.exists():
            base[b] = {'P1-DEV': metrics(p), 'VAL': metrics(runs / b / 'eval-VAL.json') if (runs / b / 'eval-VAL.json').exists() else {}}
    sstar, tied, best = select({c: rows[c]['P1-DEV']['OUT_R@200'] for c in cfgs})
    ref = base.get('z-qwen3', {}).get('P1-DEV', {}).get('OUT_R@200')
    res = {'format': 'ptp-bridgeret-sstar-v1', 'rule': 'max P1-DEV OUT_R@200; ties within 0.001 -> simpler recipe, then smaller grid value',
           'candidates': cfgs, 'S_star': sstar, 'tied_within_0.001': tied, 'best_OUT_R@200': best,
           'S_star_minus_z_qwen3_DEV_OUT_R@200': round(best_of(rows, sstar) - ref, 5) if ref is not None else None,
           'rows': rows, 'baselines': base}
    json.dump(res, open(out_json, 'w', encoding='utf-8'), indent=1)
    lines = ['| System | ' + ' | '.join(f'DEV {c}' for c in COLS) + ' | VAL OUT_R@200 |', '|' + '---|' * (len(COLS) + 2)]
    for name, r in [(b, base[b]) for b in base] + [(c, rows[c]) for c in cfgs]:
        tag = ' **(S\\*)**' if name == sstar else ''
        lines.append(f'| {name}{tag} | ' + ' | '.join(f"{r['P1-DEV'].get(c, float('nan')):.4f}" for c in COLS)
                     + f" | {r['VAL'].get('OUT_R@200', float('nan')):.4f} |")
    lines.append('')
    lines.append(f'S* = {sstar} (tied within 0.001: {", ".join(tied)}). DEV is descriptive; no significance claim.')
    Path(out_md).write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print('S*', sstar, 'tied', tied, 'best', best)


def best_of(rows, c):
    return rows[c]['P1-DEV']['OUT_R@200']


if __name__ == '__main__':
    main(sys.argv[1:])
