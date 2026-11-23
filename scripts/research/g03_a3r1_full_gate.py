"""A3r1 full evaluation on RunPod: Stage B ledger check and rebuild gate. Stdlib only.

Addendum docs/healthtech/research/g03-dev/A3R1-FULL-EVAL-RUNPOD.md §3, declared before any Stage B number. P1-DEV and
VAL only; never reads TEST. The frozen Stage B evaluation (A3r0 §4, kept by A3r1 §7) may run only after every check of
every part holds. Parts:

  ledger  H-full  Stage B ledgers of m* are complete and clean (also run on the owner PC by g03_a3r1_full_inputs.py):
                  every record of <ledger_dir>/P1-DEV.jsonl is block P1-DEV, model m*, protocol A3r1, max_tokens 800,
                  app in apps-P1-DEV.json; the same for VAL.jsonl with apps-VAL.json; the two app sets are disjoint;
                  every population app has a terminal record (ok or content_unusable), or failed transport on all
                  three attempts (A3r1 §5: counted as transport_failed, kept in the population without H/K output);
                  the P1-DEV ledger starts with the exact bytes of the pilot ledger the pilot evaluation used
  cpu     A       texts-v1/corpus.jsonl sha256 = archived (byte-identical corpus text)
          A2      the 26,575 P1-DEV query records equal the dr-train extract (as the pilot gate)
          A2v     VAL query records: the 1,919 with a pre-grant publication equal the dr-train extract; the 81 without
                  one are exactly the extract rows with an empty title (the rule checked on all P1-DEV records at staging)
          C       BM25-C0 P1-DEV (rebuilt or copied): every mean within 0.0005, ALL R@200 identical per query >= 99%,
                  same n_queries_run, against the archived dr-train evaluation
          D       Qwen3-C0 P1-DEV (the pilot rebuild, re-evaluated here): every mean within 0.002, >= 90%, same n
          E       PatEmbed-C0 P1-DEV (the pilot rebuild, re-evaluated here): as D
          V-L/Q/P archived dr-train VAL runs (byte-identical, pull manifest) re-evaluated here against the archived
                  eval-VAL.json: L as C, Q and P as D (exact agreement is expected and reported)
          F       v0 F* P1-DEV regenerated from these runs: as the pilot gate F (as D against the archived evaluation,
                  pilot-subset means within 0.002, archived means = repository record 0.4230 / 0.4940 / 0.3334)
          F-VAL   v0 F* VAL regenerated from the archived VAL runs: as D against the archived VAL evaluation, and the
                  archived means = repository record (g03-dev-tables.md: 0.4523 / 0.5306 / 0.3590 at 4 dp)
          G       F* populations: P1-DEV as the pilot gate G (25,626 apps; pilot sample sha256 c6653b6f...); the apps of
                  the regenerated VAL F* run = apps-VAL.json (1,919)
          K0      ser-arctic-v1/passages.jsonl sha256 = the P2-T02 record the pilot K routes used (e07122ce...)
          H-full  repeated on the uploaded ledgers
  enc     B-re    re-encoded PatEmbed units.json (runs/z-patembed-reenc) = archived units.json
          E-re    re-encoded PatEmbed-C0 P1-DEV against the archived evaluation: as D
          E-VAL   re-encoded PatEmbed-C0 VAL against the archived eval-VAL.json: as D (VAL query text, serialisation and
                  vectors end to end; these vectors feed route H)

Descriptive only (never a pass condition): per-query agreement with the pilot's own evaluations (BM25, Q, P, v0 F*) and
of the re-encoded P run with the pilot P run.

Usage: python3 -I g03_a3r1_full_gate.py <ledger|cpu|enc> <archived_dir> <bridgeret_dir> <g03_dir> <out.json>
archived_dir (bridgeret/archived-a3r1): texts-report.json, queries-{p1dev,val}-drtrain.jsonl, z-qwen3/ and z-patembed/
  {units.json, eval-P1-DEV.json, eval-VAL.json}, bm25/eval-{P1-DEV,VAL}.json, g03-v0/alloc-L0-Q2-P2-A0.json (P1-DEV),
  g03-v0/VAL/alloc-L0-Q2-P2-A0.json, pilot/{bm25,z-qwen3,z-patembed,fstar-P1-DEV}.json, pilot/ledger-prefix.json,
  p2t02-copy.sha256
Evaluations: <bridgeret_dir>/evals-a3r1-full/<run>-<block>.json, <g03_dir>/evals/<block>/alloc-L0-Q2-P2-A0.json
Exit 0 and "gate_passed": true only if every check of the part holds.
"""
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import g03_a3r1_runpod_gate as pg   # noqa: E402  (pilot gate: A, A2, F, G and the shared helpers)

MSTAR = 'deepseek/deepseek-v4-flash-0731'
MSTAR_DIR = 'deepseek__deepseek-v4-flash-0731'
BLOCKS = ('P1-DEV', 'VAL')
KEYS = pg.KEYS
TOL_BM25, TOL_DENSE = pg.TOL_BM25, pg.TOL_DENSE
N_APPS = {'P1-DEV': 25626, 'VAL': 1919}
N_VAL_QUERIES, N_VAL_WITH_DOC = 2000, 1919
FSTAR_VAL_RECORDED = {'ALL_R@200': 0.4523, 'IN_R@200': 0.5306, 'OUT_R@200': 0.3590}   # g03-dev-tables.md, VAL, B = 4
TERMINAL = ('ok', 'content_unusable')
TRANSPORT = ('transport_error', 'transport_error_unbilled')
ATTEMPTS_PER_APP = 3   # g03_a3_llm_expand.py: MAX_RETRIES = 2 retries after the first attempt (A3r1 §5)


def no_test(block):
    if 'TEST' in str(block):
        raise SystemExit('TEST record found: stop')


def compare(new_p, old_p, block, tol_mean, min_agree):
    """The pilot gate comparison (pg.compare) for one named block."""
    new, old = json.load(open(new_p)), json.load(open(old_p))
    if not (new['block'] == old['block'] == block) or block not in BLOCKS:
        raise SystemExit(f'gate compares {block} evaluations only (got {new["block"]} / {old["block"]})')
    means = {k: {'rebuilt': new['metrics'][k]['mean'], 'archived': old['metrics'][k]['mean'],
                 'abs_diff': round(abs(new['metrics'][k]['mean'] - old['metrics'][k]['mean']), 6)} for k in KEYS}
    qs = list(old['per_query'])
    same = sum(1 for q in qs if abs(new['per_query'].get(q, {}).get('ALL_R@200', -1)
                                    - old['per_query'][q].get('ALL_R@200', 0)) < 1e-12)
    agree = same / len(qs)
    ok = (all(v['abs_diff'] <= tol_mean for v in means.values()) and agree >= min_agree
          and new['n_queries_run'] == old['n_queries_run'])
    exact = new['per_query'] == old['per_query'] and new['n_queries_run'] == old['n_queries_run']
    return {'passed': ok, 'block': block, 'tolerance_mean': tol_mean, 'min_per_query_agreement': min_agree,
            'means': means, 'per_query_ALL_R@200_identical': round(agree, 5), 'queries_compared': len(qs),
            'n_queries_run': {'rebuilt': new['n_queries_run'], 'archived': old['n_queries_run']},
            'exact_per_query': exact}, new, old


def agreement(a_p, b_p):
    """Descriptive: share of queries whose per-query values are identical in two evaluations of one block."""
    a, b = json.load(open(a_p)), json.load(open(b_p))
    qs = sorted(set(a['per_query']) | set(b['per_query']))
    same = sum(1 for q in qs if a['per_query'].get(q) == b['per_query'].get(q))
    return {'block': a['block'], 'queries': len(qs), 'per_query_identical': round(same / max(1, len(qs)), 5),
            'ALL_R@200_mean': [round(a['metrics']['ALL_R@200']['mean'], 6), round(b['metrics']['ALL_R@200']['mean'], 6)]}


# ------------------------------------------------------------------ H-full: Stage B ledgers (shared with staging)
def prefix_sha256(path, nbytes):
    h, left = hashlib.sha256(), nbytes
    with open(path, 'rb') as f:
        while left > 0:
            b = f.read(min(1 << 22, left))
            if not b:
                break
            h.update(b)
            left -= len(b)
    return h.hexdigest() if left == 0 else None


def check_ledgers(ledger_dir, apps, pilot_prefix):
    """ledger_dir: <...>/<m* dir>/ with P1-DEV.jsonl and VAL.jsonl; apps: {'P1-DEV': [...], 'VAL': [...]};
    pilot_prefix: {'bytes': n, 'sha256': h} of the pilot ledger file. Returns the report; 'passed' and 'complete'."""
    ledger_dir = Path(ledger_dir)
    res, ok = {'model': MSTAR, 'terminal_statuses': list(TERMINAL)}, True
    for blk in BLOCKS:
        p = ledger_dir / f'{blk}.jsonl'
        pop = set(apps[blk])
        if not p.is_file():
            res[blk] = {'present': False, 'population': len(pop)}
            ok = False
            continue
        n = bad_block = outside = wrong_model = 0
        statuses, protocols, max_tokens = Counter(), Counter(), Counter()
        terminal, usable, transport_attempts, unknown_cost = set(), set(), Counter(), set()
        with open(p, encoding='utf-8') as f:
            for line in f:
                r = json.loads(line)
                n += 1
                no_test(r.get('block'))
                a = r.get('app_id')
                bad_block += r.get('block') != blk
                outside += a not in pop
                wrong_model += r.get('model') != MSTAR
                st = r.get('status')
                statuses[st] += 1
                protocols[r.get('protocol')] += 1
                max_tokens[r.get('max_tokens')] += 1
                if st in TERMINAL:
                    terminal.add(a)
                if st == 'ok':
                    usable.add(a)
                if st in TRANSPORT:
                    transport_attempts[a] += 1
                if r.get('cost_status') == 'unknown_paused':
                    unknown_cost.add(a)
        no_terminal = pop - terminal
        transport_failed = {a for a in no_terminal if transport_attempts[a] >= ATTEMPTS_PER_APP and a not in unknown_cost}
        missing = sorted(no_terminal - transport_failed)
        clean = (bad_block == 0 and outside == 0 and wrong_model == 0 and n > 0 and set(protocols) == {'A3r1'}
                 and set(max_tokens) == {800})
        res[blk] = {'present': True, 'records': n, 'population': len(pop), 'apps_terminal': len(terminal & pop),
                    'apps_usable': len(usable & pop), 'usable_share': round(len(usable & pop) / max(1, len(pop)), 5),
                    'apps_transport_failed': len(transport_failed), 'apps_missing': len(missing),
                    'first_missing': missing[:5], 'apps_unknown_cost_unreconciled': len(unknown_cost - terminal),
                    'statuses': dict(statuses), 'non_block_records': bad_block, 'records_outside_population': outside,
                    'records_other_model': wrong_model, 'protocols': dict(protocols),
                    'max_tokens': {str(k): v for k, v in max_tokens.items()}, 'clean': clean,
                    'complete': clean and not missing}
        ok &= clean and not missing
    disjoint = not (set(apps['P1-DEV']) & set(apps['VAL']))
    pp = ledger_dir / 'P1-DEV.jsonl'
    got = prefix_sha256(pp, pilot_prefix['bytes']) if pp.is_file() else None
    res['pilot_prefix'] = {'bytes': pilot_prefix['bytes'], 'expected_sha256': pilot_prefix['sha256'],
                           'got_sha256': got, 'passed': got == pilot_prefix['sha256']}
    res['populations_disjoint'] = disjoint
    res['populations'] = {b: len(apps[b]) for b in BLOCKS}
    res['complete'] = bool(ok)
    res['passed'] = bool(ok and disjoint and res['pilot_prefix']['passed']
                         and all(len(apps[b]) == N_APPS[b] for b in BLOCKS))
    return res


def ledger_part(g, arch):
    apps = {b: json.loads((g / f'a3/apps-{b}.json').read_text()) for b in BLOCKS}
    prefix = json.loads((arch / 'pilot/ledger-prefix.json').read_text())
    return check_ledgers(g / 'a3r1/ledger' / MSTAR_DIR, apps, prefix)


# ------------------------------------------------------------------ cpu part
def check_a2v(arch, br):
    new, nodoc = {}, set()
    with open(br / 'texts-v1/queries.jsonl', encoding='utf-8') as f:
        for line in f:
            r = json.loads(line)
            no_test(r.get('block'))
            if r.get('block') != 'VAL':
                continue
            if r.get('doc'):
                new[r['app_id']] = tuple(r.get(k) or '' for k in pg.QFIELDS)
            else:
                nodoc.add(r['app_id'])
    old, empty = {}, set()
    with open(arch / 'queries-val-drtrain.jsonl', encoding='utf-8') as f:
        for line in f:
            r = json.loads(line)
            no_test(r.get('block'))
            if r.get('block') != 'VAL':
                continue
            if r.get('title'):
                old[r['app_id']] = tuple(r.get(k) or '' for k in pg.QFIELDS)
            else:
                empty.add(r['app_id'])
    diff = sorted(a for a in set(new) | set(old) if new.get(a) != old.get(a))
    ok = (not diff and nodoc == empty and len(new) == N_VAL_WITH_DOC and len(new) + len(nodoc) == N_VAL_QUERIES)
    return {'passed': ok, 'n_with_doc': len(new), 'n_no_pgpub': len(nodoc), 'n_extract_with_title': len(old),
            'records_differing': len(diff), 'first_differing': diff[:5], 'no_pgpub_equal_empty_title': nodoc == empty}


def check_g_val(g):
    up = json.loads((g / 'a3/apps-VAL.json').read_text())
    run_apps = sorted(pg.apps_of(g / 'runs/VAL/alloc-L0-Q2-P2-A0.tsv'))
    return {'passed': up == run_apps and len(up) == N_APPS['VAL'], 'n_uploaded': len(up), 'n_regenerated': len(run_apps)}


def check_f_val(arch, g):
    res, new, old = compare(g / 'evals/VAL/alloc-L0-Q2-P2-A0.json', arch / 'g03-v0/VAL/alloc-L0-Q2-P2-A0.json', 'VAL',
                            *TOL_DENSE)
    rec = {k: {'archived_4dp': round(old['metrics'][k]['mean'], 4), 'recorded': v,
               'equal': round(old['metrics'][k]['mean'], 4) == v} for k, v in FSTAR_VAL_RECORDED.items()}
    res['archived_vs_repo_record'] = rec
    res['passed'] = bool(res['passed'] and all(v['equal'] for v in rec.values()))
    return res


def check_k0(arch, br):
    want = None
    for line in (arch / 'p2t02-copy.sha256').read_text().splitlines():
        h, _, p = line.partition('  ')
        if p.strip().endswith('ser-arctic-v1/passages.jsonl'):
            want = h.strip()
    got = pg.fsha(br / 'ser-arctic-v1/passages.jsonl')
    return {'passed': want is not None and got == want, 'expected': want, 'rebuilt_or_copied': got}


def cpu_part(arch, br, g):
    ev = br / 'evals-a3r1-full'
    res = {'A_corpus_text_sha256': pg.check_a(arch, br), 'A2_query_records_P1DEV': pg.check_a2(arch, br),
           'A2v_query_records_VAL': check_a2v(arch, br)}
    res['C_bm25_c0_P1DEV'] = compare(ev / 'bm25-P1-DEV.json', arch / 'bm25/eval-P1-DEV.json', 'P1-DEV', *TOL_BM25)[0]
    res['D_qwen3_c0_P1DEV'] = compare(ev / 'z-qwen3-P1-DEV.json', arch / 'z-qwen3/eval-P1-DEV.json', 'P1-DEV',
                                      *TOL_DENSE)[0]
    res['E_patembed_c0_P1DEV'] = compare(ev / 'z-patembed-P1-DEV.json', arch / 'z-patembed/eval-P1-DEV.json', 'P1-DEV',
                                         *TOL_DENSE)[0]
    res['V_L_bm25_VAL'] = compare(ev / 'bm25-VAL.json', arch / 'bm25/eval-VAL.json', 'VAL', *TOL_BM25)[0]
    res['V_Q_qwen3_VAL'] = compare(ev / 'z-qwen3-VAL.json', arch / 'z-qwen3/eval-VAL.json', 'VAL', *TOL_DENSE)[0]
    res['V_P_patembed_VAL'] = compare(ev / 'z-patembed-VAL.json', arch / 'z-patembed/eval-VAL.json', 'VAL', *TOL_DENSE)[0]
    res['F_g03_v0_fstar_P1DEV'] = pg.check_f(arch, g)
    res['F_VAL_g03_v0_fstar'] = check_f_val(arch, g)
    res['G_populations_P1DEV'] = pg.check_g(g)
    res['G_populations_VAL'] = check_g_val(g)
    res['K0_ser_arctic_passages'] = check_k0(arch, br)
    res['H_full_ledgers'] = ledger_part(g, arch)
    res['descriptive_vs_pilot'] = {
        'bm25_P1DEV': agreement(ev / 'bm25-P1-DEV.json', arch / 'pilot/bm25.json'),
        'z-qwen3_P1DEV': agreement(ev / 'z-qwen3-P1-DEV.json', arch / 'pilot/z-qwen3.json'),
        'z-patembed_P1DEV': agreement(ev / 'z-patembed-P1-DEV.json', arch / 'pilot/z-patembed.json'),
        'v0_fstar_P1DEV': agreement(g / 'evals/P1-DEV/alloc-L0-Q2-P2-A0.json', arch / 'pilot/fstar-P1-DEV.json')}
    return res


def enc_part(arch, br):
    ev = br / 'evals-a3r1-full'
    a = json.loads((br / 'runs/z-patembed-reenc/units.json').read_text())
    b = json.loads((arch / 'z-patembed/units.json').read_text())
    return {'B_unit_order_z-patembed-reenc': {'passed': a == b, 'n_rebuilt': len(a), 'n_archived': len(b)},
            'E_re_patembed_reenc_P1DEV': compare(ev / 'z-patembed-reenc-P1-DEV.json', arch / 'z-patembed/eval-P1-DEV.json',
                                                 'P1-DEV', *TOL_DENSE)[0],
            'E_VAL_patembed_reenc_VAL': compare(ev / 'z-patembed-reenc-VAL.json', arch / 'z-patembed/eval-VAL.json', 'VAL',
                                                *TOL_DENSE)[0],
            'descriptive_reenc_vs_pilot_P': agreement(ev / 'z-patembed-reenc-P1-DEV.json', ev / 'z-patembed-P1-DEV.json')}


def main(argv):
    if len(argv) != 5 or argv[0] not in ('ledger', 'cpu', 'enc'):
        raise SystemExit(__doc__)
    part, arch, br, g, out = argv[0], Path(argv[1]), Path(argv[2]), Path(argv[3]), Path(argv[4])
    res = {'format': 'ptp-g03-a3r1-full-rebuild-gate-v1', 'addendum': 'A3R1-FULL-EVAL-RUNPOD.md', 'part': part,
           'blocks': list(BLOCKS), 'm_star': MSTAR}
    if part == 'ledger':
        res['H_full_ledgers'] = ledger_part(g, arch)
    elif part == 'cpu':
        res.update(cpu_part(arch, br, g))
    else:
        res.update(enc_part(arch, br))
    res['gate_passed'] = all(v['passed'] for k, v in res.items() if isinstance(v, dict) and 'passed' in v)
    out.write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))
    print('A3R1_FULL_GATE_PASSED' if res['gate_passed'] else 'A3R1_FULL_GATE_FAILED', part, flush=True)
    sys.exit(0 if res['gate_passed'] else 1)


if __name__ == '__main__':
    main(sys.argv[1:])
