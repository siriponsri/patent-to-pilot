"""Render AM-7 stage-2a results (am7_stage2a.py + optional am7_sensitivity.py JSON) as Markdown tables. Descriptive.
Usage: python render_am7_stage2a.py <stage2a-results.json> [<sensitivity.json>] > out.md
"""
import json, sys


def f(x, nd=4):
    return '—' if x is None else f'{x:.{nd}f}'


def render(res, sens=None):
    sel = res['selection']
    out = ['## Selection on P1-DEV (frozen rules AM-7.1 §1, §2, §4, §6)', '',
           f"- A1 beta = {sel['A1_beta']}; A2 gamma = {sel['A2_gamma']}; Abar = {sel['Abar']}",
           f"- N4-E2 gamma = {sel['N4E2_gamma']}; N4-E1 gamma = {sel['N4E1_gamma']}; MMR lambda = {sel['MMR_lambda']}",
           f"- **A\\* = {sel['A_star']}**; N\\* = {sel['N_star']}; L\\* = {sel['L_star']}", '',
           '| Incumbent | Challenger | Δ MR@200 | 95% CI (art unit) | Replaced |', '|---|---|---|---|---|']
    for s in sel['selection_log']:
        out.append(f"| {s['incumbent']} | {s['challenger']} | {s['delta']:+.4f} | [{s['ci95'][0]:+.4f}, {s['ci95'][1]:+.4f}] | {s['replaced']} |")
    for b, blk in res['blocks'].items():
        out += ['', f'## {b}', '',
                f"queries {blk['n_queries']} (with vector {blk['n_queries_with_vector']}); E2 cohort {blk['n_cohort']} "
                f"(with vector {blk['n_cohort_with_vector']}); clean {blk['n_clean']}; N5 coverage {blk['n5_coverage']}; "
                f"N5 source actions median {blk['n5_source_actions_median']}; decoy missing {blk['decoy_missing']}", '',
                '### E1 (OUT R@200 = registered endpoint)', '',
                '| System | OUT R@200 | OUT R@1000 | IN R@200 | ALL R@200 |', '|---|---|---|---|---|']
        for name, m in blk['E1'].items():
            out.append(f"| {name} | {f(m['OUT_R@200'][0])} | {f(m['OUT_R@1000'][0])} | {f(m['IN_R@200'][0])} | {f(m['ALL_R@200'][0])} |")
        out += ['', '### E2 (missing-reference recall)', '',
                '| System | MR@50 | MR@200 | MR@1000 | MRR | MR@200 strict | MR@200 unseen | MR@200 clean | all co-ref R@200 |',
                '|---|---|---|---|---|---|---|---|---|']
        for name, m in blk['E2'].items():
            out.append(f"| {name} | {f(m['MR@50'][0])} | {f(m['MR@200'][0])} | {f(m['MR@1000'][0])} | {f(m['MRR'][0])} | "
                       f"{f(m['MR@200_strict'][0])} | {f(m['MR@200_unseen'][0])} | {f(blk['E2_clean'][name][0])} | {f(m['allcoref_R@200'][0])} |")
        out += ['', '### Contrasts (descriptive on DEV/VAL; confirmatory only on P1-TEST)', '',
                '| Label | Contrast | Δ | 95% CI (art unit) |', '|---|---|---|---|']
        for lab, c in blk['contrasts_descriptive'].items():
            out.append(f"| {lab} | {c['contrast']} | {c['delta']:+.4f} | [{c['ci95_artunit'][0]:+.4f}, {c['ci95_artunit'][1]:+.4f}] |")
    out += ['', '## Owner gate (AM-7 §6.4)', '', f"{res['owner_gate_AM7_6_4']['rule']}: {res['owner_gate_AM7_6_4']['passes']}",
            '', '## Power (TEST, 80 %, alpha 0.025, design effect from DEV)', '']
    for lab, v in res['power'].items():
        out.append(f'- {lab}: ' + ', '.join(f'{k} = {x}' for k, x in v.items()))
    if sens:
        out += ['', '## Sensitivity (AM-7.1 §7, descriptive)', '']
        for b, blk in sens['blocks'].items():
            out.append(f'- {b}: ' + json.dumps(blk))
    return '\n'.join(out) + '\n'


if __name__ == '__main__':
    r = json.load(open(sys.argv[1]))
    s = json.load(open(sys.argv[2])) if len(sys.argv) > 2 else None
    sys.stdout.write(render(r, s))
