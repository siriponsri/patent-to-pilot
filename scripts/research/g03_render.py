"""Render G03 DEV results.json (g03_decide.py) into Markdown tables for the decision memo.
Usage: python g03_render.py <results.json> <out.md>
"""
import json, sys

KINDS = ('ALL', 'IN', 'OUT')


def f(x, s=True):
    return (f'{x:+.4f}' if s else f'{x:.4f}').replace('-', '−')


def ci(d):
    return f"{f(d['delta'])} [{f(d['ci95'][0])}, {f(d['ci95'][1])}]"


def main(src, dst):
    r = json.load(open(src))
    sel, g = r['selection_on_P1-DEV'], r['gate']
    out = [f"Gate: {sum(c['equal_4dp'] for c in g['checks'])}/{len(g['checks'])} single-route cells equal the existing summaries; "
           f"anchor dense = {g['anchor_dense']}; best single route = {g['best_single']}.", '',
           f"Selection on P1-DEV: F* = `{sel['F_star']}`, SF* = `{sel['SF_star']}`, D = `{sel['D']}`, RR = `{sel['RR']}`, "
           f"anchor-only = `{sel['anchor_only_B2']}`.", '',
           '**Principal contrast on VAL (SF* − F*, B = 4, cluster bootstrap by art unit):**', '',
           '| Metric | Δ [95% CI] | n | wins / losses |', '|---|---|---|---|']
    for k in KINDS:
        d = r['principal_VAL_SFstar_minus_Fstar'][f'{k}_R@200']
        out.append(f"| {k} R@200 | {ci(d)} | {d['n']} | {d['wins']} / {d['losses']} |")
    out += ['', f"**Decision (frozen rule, δ = {r['delta_margin']}):** {r['decision']}", '',
            '**Mechanism contrasts (descriptive):**', '', '| Block | Contrast | ALL | IN | OUT |', '|---|---|---|---|---|']
    for key, v in r['mechanism_descriptive'].items():
        b, lab = key.split('|')
        out.append(f"| {b} | {lab} | " + ' | '.join(ci(v[f'{k}_R@200']) for k in KINDS) + ' |')
    out += ['', '**Budget sweep (R@200 ALL / IN / OUT; F = best fixed allocation per budget chosen on P1-DEV):**', '',
            '| Block | B | F (allocation) | F | SF-v0n | SF-v0c |', '|---|---|---|---|---|---|']
    for key, v in r['budget_sweep'].items():
        b, bud = key.split('|')
        cell = lambda m: ' / '.join(f'{m[k]:.4f}' for k in KINDS)
        out.append(f"| {b} | {bud[1:]} | `{v['F_best_on_dev']}` | {cell(v['F'])} | {cell(v['SF-v0n'])} | {cell(v['SF-v0c'])} |")
    out += ['', '**All arms (R@200 ALL / IN / OUT, OUT MRR):**', '']
    for b, tab in r['arm_table'].items():
        out += [f'*{b}*', '', '| Arm | ALL | IN | OUT | OUT MRR |', '|---|---|---|---|---|']
        for arm, m in sorted(tab.items(), key=lambda kv: -kv[1]['ALL']):
            out.append(f"| `{arm}` | {m['ALL']:.4f} | {m['IN']:.4f} | {m['OUT']:.4f} | {m['OUT_MRR']:.4f} |")
        out.append('')
    open(dst, 'w', encoding='utf-8').write('\n'.join(out) + '\n')
    print('\n'.join(out[:40]))


if __name__ == '__main__':
    main(*sys.argv[1:])
