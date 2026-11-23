"""P2-T02 amendment A2 (owner D19): frozen coverage contrast and decision for one follow-up model. P1-DEV only.

Amendment: docs/healthtech/research/p2-coverage/P2-T02-AMENDMENT-A2-D19-FOLLOWUP.md, section 5. The functions are the
frozen P2-T02 ones (p2t02_analyse.py, protocol bd30d3f7): paired per-query deltas with the G03 cluster bootstrap by
examiner art unit (B = 10,000, seed 20261119), 95% CIs for ALL, IN and OUT R@200, and the frozen rule:
  <model>-C1 becomes that model's representation baseline if, against <model>-C0, the ALL lower bound is > 0 and the IN
  and OUT lower bounds are > -0.005; otherwise NO_GAIN for that model and C0 stays.
Reported regardless: R@200/R@1000/OUT MRR/OUT nDCG@10 of both arms, new candidates vs C0, new judged-positive recovery
|G n (P1 minus P0)| and displaced positives (evaluator side), per-query wins/losses, build and encode cost, content stats.
The Arctic P2-T02 row is shown next to it for reading only; it plays no part in the rule.
Refuses to run unless the final A2 gate passed.
Usage: python p2t02_d19_decide.py --model qwen3|patembed --gate gate-final.json --c0-eval E0 --c1-eval E1 --c0-run R0
         --c1-run R1 --meta meta-p1dev.pkl --pairs pairs-dev.tsv --units-tsv corpus-units.tsv --tasks tasks.tsv
         --root <model root> [--arctic-results p2t02-results.json] --out results-<model>.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import p2t02_analyse as an  # noqa: E402  (frozen P2-T02 analysis functions)

METRICS = ('ALL_R@200', 'IN_R@200', 'OUT_R@200', 'ALL_R@1000', 'IN_R@1000', 'OUT_R@1000', 'OUT_MRR', 'OUT_nDCG@10')


def decide_rule(model, contrast):
    ok = an.qualifies(contrast)
    text = (f'{model}-C1 (flat complete content) becomes the {model} representation baseline' if ok else
            f'NO_GAIN for {model} coverage: keep {model}-C0')
    return {'rule': 'baseline if vs C0 of the same model ALL lo > 0 and IN, OUT lo > -0.005 (P2-T02 §5, unchanged)',
            'qualifies': ok, 'baseline': f'{model}-c1' if ok else f'{model}-c0', 'text': text}


def table_row(ev):
    return {k: ev['metrics'][k]['mean'] for k in METRICS if k in ev['metrics']} | {'n_queries_run': ev['n_queries_run']}


def main(argv=None):
    ap = argparse.ArgumentParser()
    for x in ('model', 'gate', 'c0-eval', 'c1-eval', 'c0-run', 'c1-run', 'meta', 'pairs', 'units-tsv', 'tasks', 'root',
              'arctic-results', 'out'):
        ap.add_argument('--' + x)
    a = ap.parse_args(argv)
    gate = json.loads(Path(a.gate).read_text())
    if not gate.get('gate_passed'):
        sys.exit('A2 gate not passed: no contrast is computed')
    root = Path(a.root)
    e0, e1 = an.load_eval(a.c0_eval), an.load_eval(a.c1_eval)
    assert e0['metrics']['ALL_R@200']['n'] == e1['metrics']['ALL_R@200']['n']
    assert e0['n_queries_run'] == e1['n_queries_run'] == 25626, (e0['n_queries_run'], e1['n_queries_run'])
    clusters = an.clusters_from_meta(a.meta)
    contrast = an.paired_pq(e1['per_query'], e0['per_query'], clusters)
    decision = decide_rule(a.model, contrast)
    rel = an.positives(a.pairs, a.units_tsv, a.tasks)
    cand = an.overlap_stats(an.read_run(a.c1_run), an.read_run(a.c0_run), rel)
    enc = root / 'enc/c1/encode.json'
    cost = {k: an.parse_time(root / f'logs/{k}.time') for k in
            ('ser', 'build', 'arctic-repro-build', 'validate', 'c0check', 'encode-queries', 'encode-c1', 'retrieve-c1')}
    cost['encode_json'] = json.loads(enc.read_text()) if enc.exists() else None
    cost['disk_bytes'] = {'content_dir': an.du(root / 'content'), 'c1_ids': an.du(root / 'content/c1.ids.u32'),
                          'c1_vectors': an.du(root / 'enc/c1/passages.f16.npy')}
    res = {'format': 'ptp-p2t02-d19-v1', 'model': a.model,
           'protocol': 'docs/healthtech/research/p2-coverage/P2-T02-COVERAGE-CONTROL-PROTOCOL.md@bd30d3f7',
           'amendment': 'docs/healthtech/research/p2-coverage/P2-T02-AMENDMENT-A2-D19-FOLLOWUP.md',
           'block': an.BLOCK,
           'c0_reference': {'eval': a.c0_eval, 'run': a.c0_run, 'note': 'gated A3r1 RunPod C0 rebuild (relay)'},
           'arm_table': {f'{a.model}-c0': table_row(e0), f'{a.model}-c1': table_row(e1)},
           'contrasts': {f'coverage_{a.model}_C1_minus_C0': contrast}, 'decision': decision,
           'candidates_and_recovery': {f'{a.model}-c1_vs_{a.model}-c0': cand}, 'cost': cost,
           'content_stats': json.loads((root / 'content/stats.json').read_text()),
           'window': json.loads((root / 'window.json').read_text()),
           'gate': {k: v for k, v in gate.items() if k != 'records'},
           'bootstrap': {'B': an.B, 'seed': an.SEED, 'cluster': 'examiner art unit (am7/prep-v1/meta.pkl, P1-DEV)'}}
    if a.arctic_results and Path(a.arctic_results).exists():
        ar = json.loads(Path(a.arctic_results).read_text())
        res['arctic_p2t02_for_reading_only'] = {
            'arm_table': {k: ar['arm_table'][k] for k in ('arctic-c0', 'arctic-c1')},
            'coverage_arctic_C1_minus_C0': ar['contrasts']['coverage_arctic_C1_minus_C0'],
            'decision': ar['decision']['arctic']}
    Path(a.out).write_text(json.dumps(res, indent=1))
    print(json.dumps({'arm_table': res['arm_table'], 'decision': decision,
                      'contrast': {m: {'delta': round(v['delta'], 5), 'ci95': [round(x, 5) for x in v['ci95']]}
                                   for m, v in contrast.items()}}, indent=1))
    print('D19_DECIDE_DONE', flush=True)


if __name__ == '__main__':
    main()
