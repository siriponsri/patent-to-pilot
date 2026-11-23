"""A3r1 RunPod rebuild gate (docs/healthtech/research/g03-dev/A3R1-AMENDMENT-RUNPOD-REBUILD.md §3). Stdlib only.

P1-DEV only; never reads TEST. Declared before any A3r1 retrieval number exists. The dr-train-only inputs of the frozen
A3r1 pilot queue are rebuilt on RunPod pods; before the frozen GO/STOP rule may be applied, they must match the archived
dr-train records (pulled 21 and 22 Nov 2026):

  A   texts-v1/corpus.jsonl sha256 = archived texts-v1/report.json value (byte-identical corpus text)
  A2  texts-v1/queries.jsonl P1-DEV records (app_id, block, title, abstract, claim) = the dr-train extract of the same
      records (g03-dev/a3/queries-dev-val.jsonl, P1-DEV rows): same set, no record differs (order reported only)
  B   rebuilt runs/z-qwen3/units.json and runs/z-patembed/units.json = archived units.json (identical unit order)
  C   BM25-C0 (if present): every P1-DEV mean (ALL/IN/OUT R@200, R@1000) within 0.0005, ALL_R@200 identical per query
      for >= 99% of queries, same n_queries_run
  D   Qwen3-C0: every mean within 0.002, ALL_R@200 identical per query for >= 90%, same n_queries_run
  E   PatEmbed-C0: as D
  F   G03 v0 F* (alloc-L0-Q2-P2-A0) regenerated from the rebuilt runs: as D against the archived evaluation; in addition
      the pilot-subset means of ALL/IN/OUT R@200 within 0.002 of the archived ones, and the archived means equal the
      repository record (g03-dev-tables.md: 0.4230 / 0.4940 / 0.3334 at 4 dp)
  G   pilot population: apps of the regenerated F* run = uploaded apps-P1-DEV.json (25,626); the regenerated sha256
      sample (g03_a3_routes.py sample, n = 2,000) = uploaded apps-pilot.json, whose sha256 is c6653b6f...
  H   ledgers: every record is block P1-DEV and every usable app is a pilot app

Usage: python3 -I g03_a3r1_runpod_gate.py <qwen3|patembed|full> <archived_dir> <bridgeret_dir> <g03_dir> <out.json>
archived_dir: texts-report.json, queries-p1dev-drtrain.jsonl, z-qwen3/{units.json,eval-P1-DEV.json},
              z-patembed/{units.json,eval-P1-DEV.json}, bm25/eval-P1-DEV.json, g03-v0/alloc-L0-Q2-P2-A0.json
Rebuilt evaluations: <bridgeret_dir>/evals-a3r1/{z-qwen3,z-patembed,bm25}.json, <g03_dir>/evals/P1-DEV/alloc-L0-Q2-P2-A0.json
Exit 0 and "gate_passed": true only if every check of the part holds.
"""
import hashlib
import json
import sys
from pathlib import Path

KEYS = ('ALL_R@200', 'IN_R@200', 'OUT_R@200', 'ALL_R@1000', 'IN_R@1000', 'OUT_R@1000')
TOL_BM25, TOL_DENSE = (0.0005, 0.99), (0.002, 0.90)
PILOT_SHA256 = 'c6653b6f299c5bfe8bd90617391ec62235171558d4d5afca660085b9e165c2bf'
FSTAR_RECORDED = {'ALL_R@200': 0.4230, 'IN_R@200': 0.4940, 'OUT_R@200': 0.3334}   # g03-dev-tables.md, P1-DEV, 4 dp
N_APPS_FSTAR, N_PILOT = 25626, 2000
MODELS = ('qwen__qwen3-32b', 'deepseek__deepseek-v4-flash-0731', 'google__gemini-2.5-flash-lite',
          'typhoon-v2.5-30b-a3b-instruct')
QFIELDS = ('app_id', 'block', 'title', 'abstract', 'claim')


def fsha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 22), b''):
            h.update(b)
    return h.hexdigest()


def compare(new_p, old_p, tol_mean, min_agree):
    new, old = json.load(open(new_p)), json.load(open(old_p))
    if not (new['block'] == old['block'] == 'P1-DEV'):
        raise SystemExit('gate compares P1-DEV evaluations only')
    means = {k: {'rebuilt': new['metrics'][k]['mean'], 'archived': old['metrics'][k]['mean'],
                 'abs_diff': round(abs(new['metrics'][k]['mean'] - old['metrics'][k]['mean']), 6)} for k in KEYS}
    qs = list(old['per_query'])
    same = sum(1 for q in qs if abs(new['per_query'].get(q, {}).get('ALL_R@200', -1)
                                    - old['per_query'][q].get('ALL_R@200', 0)) < 1e-12)
    agree = same / len(qs)
    ok = (all(v['abs_diff'] <= tol_mean for v in means.values()) and agree >= min_agree
          and new['n_queries_run'] == old['n_queries_run'])
    return {'passed': ok, 'tolerance_mean': tol_mean, 'min_per_query_agreement': min_agree, 'means': means,
            'per_query_ALL_R@200_identical': round(agree, 5), 'queries_compared': len(qs),
            'n_queries_run': {'rebuilt': new['n_queries_run'], 'archived': old['n_queries_run']}}, new, old


def qrecords(path):
    out = {}
    order = []
    with open(path, encoding='utf-8') as f:
        for line in f:
            r = json.loads(line)
            if r.get('block') != 'P1-DEV':
                if 'TEST' in str(r.get('block')):
                    raise SystemExit('TEST record found: stop')
                continue
            out[r['app_id']] = tuple(r.get(k) or '' for k in QFIELDS)
            order.append(r['app_id'])
    return out, order


def check_a(arch, br):
    want = json.load(open(arch / 'texts-report.json'))['outputs_sha256']['corpus.jsonl']
    got = fsha(br / 'texts-v1/corpus.jsonl')
    return {'passed': got == want, 'archived': want, 'rebuilt': got}


def check_a2(arch, br):
    new, no = qrecords(br / 'texts-v1/queries.jsonl')
    old, oo = qrecords(arch / 'queries-p1dev-drtrain.jsonl')
    diff = sorted(a for a in set(new) | set(old) if new.get(a) != old.get(a))
    return {'passed': not diff and len(new) == 26575, 'n_rebuilt': len(new), 'n_drtrain': len(old),
            'records_differing': len(diff), 'first_differing': diff[:5], 'same_order': no == oo}


def check_b(arch, br, name):
    a = json.loads((br / 'runs' / name / 'units.json').read_text())
    b = json.loads((arch / name / 'units.json').read_text())
    return {'passed': a == b, 'n_rebuilt': len(a), 'n_archived': len(b)}


def apps_of(run_path):
    apps = set()
    with open(run_path, encoding='utf-8') as f:
        next(f)
        for line in f:
            apps.add(line.split('\t', 1)[0])
    return apps


def check_g(g):
    up_all = json.loads((g / 'a3/apps-P1-DEV.json').read_text())
    up_pilot = json.loads((g / 'a3/apps-pilot.json').read_text())
    regen_all = json.loads((g / 'a3/apps-P1-DEV.regen.json').read_text())
    regen_pilot = json.loads((g / 'a3/apps-pilot.regen.json').read_text())
    run_apps = sorted(apps_of(g / 'runs/P1-DEV/alloc-L0-Q2-P2-A0.tsv'))
    sha = fsha(g / 'a3/apps-pilot.json')
    ok = (regen_all == up_all == run_apps and len(up_all) == N_APPS_FSTAR and regen_pilot == up_pilot
          and len(up_pilot) == N_PILOT and sha == PILOT_SHA256)
    return {'passed': ok, 'n_fstar_apps': {'regenerated': len(regen_all), 'uploaded': len(up_all)},
            'fstar_apps_identical': regen_all == up_all == run_apps, 'pilot_identical': regen_pilot == up_pilot,
            'apps_pilot_sha256': sha, 'apps_pilot_sha256_expected': PILOT_SHA256}


def check_h(g):
    pilot = set(json.loads((g / 'a3/apps-pilot.json').read_text()))
    res, ok = {}, True
    for m in MODELS:
        n = bad_block = outside = usable = 0
        with open(g / 'a3r1/ledger' / m / 'P1-DEV.jsonl', encoding='utf-8') as f:
            for line in f:
                r = json.loads(line)
                n += 1
                bad_block += r.get('block') != 'P1-DEV'
                if r.get('status') == 'ok':
                    usable += 1
                    outside += r['app_id'] not in pilot
        res[m] = {'records': n, 'usable': usable, 'non_P1DEV_records': bad_block, 'usable_outside_pilot': outside}
        ok &= bad_block == 0 and outside == 0 and n > 0
    res['passed'] = bool(ok)
    return res


def check_f(arch, g):
    res, new, old = compare(g / 'evals/P1-DEV/alloc-L0-Q2-P2-A0.json', arch / 'g03-v0/alloc-L0-Q2-P2-A0.json', *TOL_DENSE)
    pilot = json.loads((g / 'a3/apps-pilot.json').read_text())
    sub = {}
    for k in FSTAR_RECORDED:
        mn = [new['per_query'][a][k] for a in pilot if a in new['per_query'] and k in new['per_query'][a]]
        mo = [old['per_query'][a][k] for a in pilot if a in old['per_query'] and k in old['per_query'][a]]
        a_, b_ = sum(mn) / max(1, len(mn)), sum(mo) / max(1, len(mo))
        sub[k] = {'rebuilt': round(a_, 6), 'archived': round(b_, 6), 'abs_diff': round(abs(a_ - b_), 6),
                  'n': [len(mn), len(mo)]}
    recorded = {k: {'archived_4dp': round(old['metrics'][k]['mean'], 4), 'recorded': v,
                    'equal': round(old['metrics'][k]['mean'], 4) == v} for k, v in FSTAR_RECORDED.items()}
    res['pilot_subset'] = sub
    res['archived_vs_repo_record'] = recorded
    res['passed'] = bool(res['passed'] and all(v['abs_diff'] <= TOL_DENSE[0] and v['n'][0] == v['n'][1]
                                               for v in sub.values()) and all(v['equal'] for v in recorded.values()))
    return res


def main(argv):
    part, arch, br, g, out = argv[0], Path(argv[1]), Path(argv[2]), Path(argv[3]), Path(argv[4])
    if part not in ('qwen3', 'patembed', 'full'):
        raise SystemExit(__doc__)
    ev = br / 'evals-a3r1'
    res = {'format': 'ptp-g03-a3r1-runpod-rebuild-gate-v1', 'amendment': 'A3R1-AMENDMENT-RUNPOD-REBUILD.md',
           'part': part, 'block': 'P1-DEV', 'A_corpus_text_sha256': check_a(arch, br),
           'A2_query_records': check_a2(arch, br)}
    if part in ('qwen3', 'full'):
        res['B_unit_order_z-qwen3'] = check_b(arch, br, 'z-qwen3')
        res['D_qwen3_c0'] = compare(ev / 'z-qwen3.json', arch / 'z-qwen3/eval-P1-DEV.json', *TOL_DENSE)[0]
    if part in ('patembed', 'full'):
        res['B_unit_order_z-patembed'] = check_b(arch, br, 'z-patembed')
        res['E_patembed_c0'] = compare(ev / 'z-patembed.json', arch / 'z-patembed/eval-P1-DEV.json', *TOL_DENSE)[0]
    if part == 'full':
        res['C_bm25_c0'] = compare(ev / 'bm25.json', arch / 'bm25/eval-P1-DEV.json', *TOL_BM25)[0]
        res['F_g03_v0_fstar'] = check_f(arch, g)
        res['G_pilot_population'] = check_g(g)
        res['H_ledgers'] = check_h(g)
    res['gate_passed'] = all(v['passed'] for k, v in res.items() if isinstance(v, dict) and 'passed' in v)
    out.write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))
    print('A3R1_REBUILD_GATE_PASSED' if res['gate_passed'] else 'A3R1_REBUILD_GATE_FAILED', part, flush=True)
    sys.exit(0 if res['gate_passed'] else 1)


if __name__ == '__main__':
    main(sys.argv[1:])
