"""P2-T02 amendment A1: C0 rebuild gate (RunPod). Stdlib only. P1-DEV only; never reads TEST.

The C0 inputs that existed only on dr-train are rebuilt on a dedicated RunPod pod from the local PatentsView copy. Before any
C1/C2 number may be interpreted, the rebuilt C0 must match the archived C0 records (copied from dr-train on 21 Nov 2026):

  A  texts-v1/corpus.jsonl sha256 equals the archived texts-v1/report.json value (byte-identical corpus text);
  B  the rebuilt runs/z-arctic/units.json equals the archived units.json (identical unit order);
  C  BM25-C0 (CPU): every reported P1-DEV mean (ALL/IN/OUT R@200, R@1000) within 0.0005 of the archived evaluation, and
     ALL_R@200 identical per query for >= 99% of the archived queries;
  D  Arctic-C0 (different GPU than the V100): every reported mean within 0.002, and ALL_R@200 identical per query for
     >= 90% of the archived queries;
  E  the rebuilt runs cover the same number of queries as the archived runs (n_queries_run).

Usage: python3 -I p2t02_rebuild_gate.py <archived_dir> <bridgeret_dir> <eval-arctic.json> <eval-bm25.json> <out.json>
archived_dir holds texts-report.json, z-arctic/{units.json,eval-P1-DEV.json}, bm25/eval-P1-DEV.json.
Exit 0 and "gate_passed": true only if A-E all hold.
"""
import hashlib
import json
import sys
from pathlib import Path

KEYS = ('ALL_R@200', 'IN_R@200', 'OUT_R@200', 'ALL_R@1000', 'IN_R@1000', 'OUT_R@1000')
TOL = {'bm25': (0.0005, 0.99), 'arctic': (0.002, 0.90)}


def fsha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 22), b''):
            h.update(b)
    return h.hexdigest()


def compare(new_p, old_p, tol_mean, min_agree):
    new, old = json.load(open(new_p)), json.load(open(old_p))
    assert new['block'] == old['block'] == 'P1-DEV'
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
            'n_queries_run': {'rebuilt': new['n_queries_run'], 'archived': old['n_queries_run']}}


def main(argv):
    arch, br, ev_arctic, ev_bm25, out = Path(argv[0]), Path(argv[1]), argv[2], argv[3], argv[4]
    rep = json.load(open(arch / 'texts-report.json'))
    want = rep['outputs_sha256']['corpus.jsonl']
    got = fsha(br / 'texts-v1/corpus.jsonl')
    a = {'passed': got == want, 'archived': want, 'rebuilt': got}
    b_ok = json.loads((br / 'runs/z-arctic/units.json').read_text()) == json.loads((arch / 'z-arctic/units.json').read_text())
    res = {'format': 'ptp-p2t02-rebuild-gate-v1', 'amendment': 'A1', 'block': 'P1-DEV',
           'A_corpus_text_sha256': a, 'B_unit_order_identical': {'passed': b_ok},
           'C_bm25_c0': compare(ev_bm25, arch / 'bm25/eval-P1-DEV.json', *TOL['bm25']),
           'D_arctic_c0': compare(ev_arctic, arch / 'z-arctic/eval-P1-DEV.json', *TOL['arctic'])}
    res['gate_passed'] = all(res[k]['passed'] for k in ('A_corpus_text_sha256', 'B_unit_order_identical',
                                                          'C_bm25_c0', 'D_arctic_c0'))
    Path(out).write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))
    print('REBUILD_GATE_PASSED' if res['gate_passed'] else 'REBUILD_GATE_FAILED', flush=True)
    sys.exit(0 if res['gate_passed'] else 1)


if __name__ == '__main__':
    main(sys.argv[1:])
