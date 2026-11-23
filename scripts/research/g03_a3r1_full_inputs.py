"""A3r1 full evaluation on RunPod: stage the private upload tree on the owner PC. P1-DEV and VAL only; never opens TEST.

Addendum docs/healthtech/research/g03-dev/A3R1-FULL-EVAL-RUNPOD.md (declared before any Stage B number). Writes, under
<out_dir>/tree, the dr-train paths the pod mirrors (extract the tar at / on the pod):
  data/ptp-paper2/splits/private/tasks.tsv            app_id, block, filing_date: 26,575 P1-DEV + 2,000 VAL (meta.pkl)
  data/ptp-paper2/challenge1m/out-v1/corpus-units.tsv copied; pairs-dev.tsv with its P1-DEV and VAL rows only
  data/ptp-paper2/bridgeret/texts-v1/corpus.jsonl     the local LF build (sha256 287ef7e0..., hard link when possible)
  data/ptp-paper2/bridgeret/texts-v1/queries.jsonl    the local P1-DEV records (bytes unchanged) + the VAL records derived
                                                      from the dr-train extract, sorted by app_id as the builder does
  data/ptp-paper2/bridgeret/code/                     archived C0 scripts (unchanged bytes)
  data/ptp-paper2/bridgeret/am7/prep-v1/meta.pkl      copied (VAL filing dates; art units of the frozen bootstrap)
  data/ptp-paper2/bridgeret/runs/{bm25,z-qwen3,z-patembed}/run-VAL.tsv.gz   archived dr-train VAL runs (routes L, Q, P)
  data/ptp-paper2/bridgeret/runs/{z-qwen3,z-patembed}/{run-P1-DEV.tsv.gz,units.json}   the gated pilot rebuilds (relays)
  data/ptp-paper2/bridgeret/archived-a3r1/            gate references (g03_a3r1_full_gate.py docstring)
  data/ptp-paper2/g03-dev/code/                       repository scripts (CRLF -> LF)
  data/ptp-paper2/g03-dev/a3/apps-{pilot,P1-DEV,VAL}.json, a3r1/ledger/<m*>/{P1-DEV,VAL}.jsonl (Stage B, m* only)
  data/ptp-paper2/MANIFEST-a3r1-full.sha256           sha256 of every staged file (absolute pod paths)
and <out_dir>/FILES-full.txt (tar file list, LF) and <out_dir>/stage-report-full.json.

VAL query records: texts-v1/queries.jsonl was built locally for P1-DEV only. The VAL records are derived from the dr-train
extract (g03-a3/inputs/queries-dev-val.jsonl: app_id, block, title, abstract, claim): a record whose title is non-empty
gets a `doc` marker (the serialiser only tests that `doc` is truthy), one with an empty title is `no_pgpub`. The rule is
first checked on all 26,575 P1-DEV records against the local builder output (same app, block, doc presence, title,
abstract, claim) and staging stops if any record differs. The pod gate (A2v, E-VAL, n_queries_run) checks it again.

Local pre-checks (any failure stops before the tree is complete):
  H-full  Stage B ledgers of m* complete and clean (g03_a3r1_full_gate.check_ledgers), run FIRST: an incomplete Stage B
          stops here with per-block counts
  every archived input against the dr-train pull manifests; the qwen3 relay and the pilot results archive against
  their recorded sha256; the patembed relay through its evaluation being byte-identical to the pilot assembly's
  B (relay units.json = archived units.json), A (corpus sha256), A2 (P1-DEV records = extract), the VAL rule, the pilot
  sample regenerated from apps-P1-DEV.json, apps-VAL.json = the apps of the archived v0 F* VAL run
The frozen dr-train manifest (which lists TEST tasks) is never read. No TEST block, sealed file or TEST label is staged.

Usage: python -I g03_a3r1_full_inputs.py <private_artifacts_dir> <repo_dir> <out_dir> [--check-only]
  --check-only  run every pre-check, continue past an incomplete Stage B, and write only <out_dir>/stage-report-full.json;
                exit 0 = inputs verified and Stage B complete, 2 = inputs verified but Stage B incomplete, 1 = a check failed
"""
import csv
import hashlib
import io
import json
import pickle
import shutil
import sys
import tarfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import g03_a3r1_full_gate as fg          # noqa: E402
import g03_a3r1_runpod_inputs as pin      # noqa: E402  (pure helpers: pulled, link_or_copy, lf_copy)

CORPUS_SHA = '287ef7e0b823b31330a6b3ad804f4e0f99dceec0300f45ffb7d6345adc8d7a86'
PILOT_SHA = 'c6653b6f299c5bfe8bd90617391ec62235171558d4d5afca660085b9e165c2bf'
MSTAR, MSTAR_DIR = fg.MSTAR, fg.MSTAR_DIR
BLOCKS = fg.BLOCKS
N_TASKS = {'P1-DEV': 26575, 'VAL': 2000}
C0_CODE = ('serialise_bridgeret_texts.py', 'serialise_bridgeret_texts_v2.py', 'dense_bridgeret_v3.py', 'bm25_bridgeret.py',
           'bridgeret_query.py', 'eval_bridgeret_dev.py')
G03_CODE = ('g03_a3_routes.py', 'g03_a3_decide.py', 'g03_route_acquisition.py', 'g03_queue_a3r1_full.sh',
            'g03_a3r1_runpod.sh', 'g03_a3r1_runpod_gate.py', 'g03_a3r1_full_gate.py', 'g03_a3r1_runpod_v0.py',
            'g03_a3r1_runpod_models.py')
QFIELDS = ('app_id', 'block', 'title', 'abstract', 'claim')
VAL_DOC_MARKER = 'drtrain-extract'
P = 'data/ptp-paper2/'
REPORT = {}


def fsha(p):
    return fg.pg.fsha(p)


def bsha(b):
    return hashlib.sha256(b).hexdigest()


def stop(msg):
    REPORT['status'] = 'FAILED: ' + msg
    raise SystemExit('staging stopped: ' + msg)


def no_test(block, where):
    if 'TEST' in str(block):
        stop(f'TEST block in {where}')


class Stager:
    """Writes into the tree (or, with --check-only, only verifies)."""

    def __init__(self, out, write, man):
        self.out, self.write, self.man = out, write, man

    def verified(self, src, rel, remote_path):
        """Copy an archived file after checking it against the dr-train pull manifest (remote sha256)."""
        got = fsha(src)
        if self.man.get(remote_path) != got:
            stop(f'archived file differs from its pull manifest: {remote_path}')
        REPORT.setdefault('archived_refs_verified', {})[remote_path] = got
        if self.write:
            dst = self.out / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)

    def put_bytes(self, rel, data):
        if self.write:
            dst = self.out / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(data)

    def put_file(self, rel, src, link=False):
        if not self.write:
            return
        dst = self.out / rel
        if link:
            pin.link_or_copy(src, dst)
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)


def tar_members(path, mode, wanted):
    """{member name: bytes} for the wanted members (exact names); a missing member stops staging."""
    got = {}
    with tarfile.open(path, mode) as tf:
        for m in tf:
            if m.name in wanted and m.isfile():
                got[m.name] = tf.extractfile(m).read()
    missing = sorted(set(wanted) - set(got))
    if missing:
        stop(f'{Path(path).name} lacks {missing}')
    return got


def derive_val_record(r):
    """VAL texts record from a dr-train extract row (the rule checked on P1-DEV first)."""
    if r.get('title'):
        return {'app_id': r['app_id'], 'block': r['block'], 'doc': VAL_DOC_MARKER, 'title': r['title'],
                'abstract': r.get('abstract') or '', 'claim': r.get('claim') or ''}
    return {'app_id': r['app_id'], 'block': r['block'], 'doc': None, 'variant': 'no_pgpub'}


def ser_key(r):
    """The fields the serialisers read: app, block, whether a document exists, title, abstract, claim."""
    has = bool(r.get('doc'))
    return (r['app_id'], r['block'], has) + (tuple(r.get(k) or '' for k in QFIELDS[2:]) if has else ('', '', ''))


def ledger_message(led):
    parts = []
    for b in BLOCKS:
        x = led.get(b, {})
        if not x.get('present'):
            parts.append(f'{b}: ledger file absent ({x.get("population")} apps expected)')
        else:
            done = x['apps_terminal'] + x['apps_transport_failed']
            parts.append(f'{b}: {done}/{x["population"]} apps finished, {x["apps_missing"]} missing, '
                         f'{x["apps_unknown_cost_unreconciled"]} unknown-cost, clean={x["clean"]}')
    parts.append(f'pilot prefix ok={led["pilot_prefix"]["passed"]}')
    return '; '.join(parts)


def main(argv):
    check_only = '--check-only' in argv
    args = [a for a in argv if not a.startswith('--')]
    if len(args) != 3:
        raise SystemExit(__doc__)
    priv, repo, outd = Path(args[0]), Path(args[1]), Path(args[2])
    tree = outd / 'tree'
    if not check_only and tree.exists():
        sys.exit(f'{tree} exists')
    a21, a22 = priv / 'dr-train-archive/20261121', priv / 'dr-train-archive/20261122-g03'
    src, src22 = a21 / 'files/data/ptp-paper2', a22 / 'files/data/ptp-paper2'
    rp = priv / 'g03-a3r1-runpod'
    inp = priv / 'g03-a3/inputs'
    man = {**pin.pulled(a21 / 'pull-manifest.tsv'), **pin.pulled(a22 / 'pull-manifest.tsv')}
    st = Stager(tree, not check_only, man)
    REPORT.update({'format': 'ptp-g03-a3r1-full-stage-v1', 'addendum': 'A3R1-FULL-EVAL-RUNPOD.md',
                   'blocks': list(BLOCKS), 'm_star': MSTAR, 'mode': 'check-only' if check_only else 'stage'})

    # 1 Stage B ledgers first (gate part ledger): fail fast and say how far Stage B is
    apps = {b: json.loads((inp / f'apps-{b}.json').read_text(encoding='utf-8')) for b in BLOCKS}
    pstage = priv / 'g03-a3r1-runpod-stage'
    pilot_ledger = pstage / 'tree' / P / 'g03-dev/a3r1/ledger' / MSTAR_DIR / 'P1-DEV.jsonl'
    pilot_sha = json.loads((pstage / 'stage-report.json').read_text(encoding='utf-8'))['H_local_ledgers'][MSTAR_DIR]['sha256']
    if fsha(pilot_ledger) != pilot_sha:
        stop('the staged pilot ledger differs from the pilot stage report')
    prefix = {'bytes': pilot_ledger.stat().st_size, 'sha256': pilot_sha, 'source': 'g03-a3r1-runpod-stage (pilot upload)'}
    ldir = priv / 'g03-a3r1/ledger/A3r1' / MSTAR_DIR
    led = fg.check_ledgers(ldir, apps, prefix)
    REPORT['H_full_ledgers'] = led
    REPORT['stage_b_complete'] = led['passed']
    print('H-full (Stage B ledgers):', 'PASS' if led['passed'] else 'FAIL', '-', ledger_message(led), flush=True)
    if not led['passed'] and not check_only:
        stop('Stage B is incomplete or a ledger is not clean: ' + ledger_message(led))

    # 2 pilot results archive and relays (recorded sha256), pilot decision names m*
    sums = {}
    for line in (rp / 'a3r1-pilot.sha256').read_text(encoding='utf-8').splitlines():
        h, _, name = line.partition('  ')
        sums[Path(name.strip()).name] = h.strip()
    res_tgz = rp / 'a3r1-pilot-results.tgz'
    if fsha(res_tgz) != sums.get('a3r1-pilot-results.tgz'):
        stop('a3r1-pilot-results.tgz differs from a3r1-pilot.sha256')
    pm = {P + 'bridgeret/evals-a3r1/bm25.json': 'pilot/bm25.json',
          P + 'bridgeret/evals-a3r1/z-qwen3.json': 'pilot/z-qwen3.json',
          P + 'bridgeret/evals-a3r1/z-patembed.json': 'pilot/z-patembed.json',
          P + 'g03-dev/evals/P1-DEV/alloc-L0-Q2-P2-A0.json': 'pilot/fstar-P1-DEV.json',
          P + 'g03-dev/rebuild-gate-a3r1.json': 'pilot/gate-full.json',
          P + 'g03-dev/results-a3r1-pilot.json': None}
    pilot = tar_members(res_tgz, 'r:gz', pm)
    pres = json.loads(pilot[P + 'g03-dev/results-a3r1-pilot.json'])
    pgate = json.loads(pilot[P + 'g03-dev/rebuild-gate-a3r1.json'])
    if pres.get('m_star') != MSTAR or not str(pres.get('decision', '')).startswith('GO') or not pgate.get('gate_passed'):
        stop('the pilot results do not record GO with m* = ' + MSTAR + ' after a passed gate')
    REPORT['pilot'] = {'results_tgz_sha256': sums['a3r1-pilot-results.tgz'], 'm_star': pres['m_star'],
                       'decision_is_GO': True, 'pilot_gate_passed': True}
    q_sha = (rp / 'a3r1-qwen3-relay.tar.sha256').read_text(encoding='utf-8').split()[0]
    if fsha(rp / 'a3r1-qwen3-relay.tar') != q_sha:
        stop('a3r1-qwen3-relay.tar differs from its recorded sha256')
    p_sha = fsha(rp / 'a3r1-patembed-relay.tar')
    REPORT['relays'] = {'qwen3_sha256': q_sha, 'patembed_sha256': p_sha,
                        'patembed_note': 'no sha256 was recorded at relay time; its evaluation must equal the pilot one'}
    for name, rel_tar in (('z-qwen3', 'a3r1-qwen3-relay.tar'), ('z-patembed', 'a3r1-patembed-relay.tar')):
        want = [P + f'bridgeret/runs/{name}/run-P1-DEV.tsv.gz', P + f'bridgeret/runs/{name}/units.json',
                P + f'bridgeret/evals-a3r1/{name}.json']
        mem = tar_members(rp / rel_tar, 'r:', want)
        if mem[want[2]] != pilot[P + f'bridgeret/evals-a3r1/{name}.json']:
            stop(f'{rel_tar}: its evaluation differs from the pilot assembly evaluation')
        arch_units = (src / f'bridgeret/runs/{name}/units.json').read_bytes()
        if bsha(arch_units) != man.get(f'/data/ptp-paper2/bridgeret/runs/{name}/units.json') or mem[want[1]] != arch_units:
            stop(f'{rel_tar}: units.json differs from the archived unit order')
        REPORT['relays'][f'{name}_run_P1DEV_sha256'] = bsha(mem[want[0]])
        st.put_bytes(f'{P}bridgeret/runs/{name}/run-P1-DEV.tsv.gz', mem[want[0]])
        st.put_bytes(f'{P}bridgeret/runs/{name}/units.json', mem[want[1]])
    arch = f'{P}bridgeret/archived-a3r1/'
    for k, v in pm.items():
        if v:
            st.put_bytes(arch + v, pilot[k])
    st.put_bytes(arch + 'pilot/ledger-prefix.json', json.dumps(prefix, indent=1).encode())
    p2 = (rp / 'bm25copy.sha256').read_bytes().replace(b'\r\n', b'\n')
    if not any(l.endswith(b'ser-arctic-v1/passages.jsonl') for l in p2.splitlines()):
        stop('bm25copy.sha256 does not record ser-arctic-v1/passages.jsonl')
    st.put_bytes(arch + 'p2t02-copy.sha256', p2)

    # 3 tasks (P1-DEV + VAL from meta.pkl), pairs (P1-DEV + VAL rows), corpus units, meta
    st.verified(src / 'bridgeret/am7/prep-v1/meta.pkl', f'{P}bridgeret/am7/prep-v1/meta.pkl',
                '/data/ptp-paper2/bridgeret/am7/prep-v1/meta.pkl')
    meta = pickle.load(open(src / 'bridgeret/am7/prep-v1/meta.pkl', 'rb'))
    for b in meta['queries']:
        no_test(b, 'meta.pkl')
    tasks, fd = {}, {}
    for b in BLOCKS:
        q = meta['queries'][b]
        tasks[b] = sorted({r['app'] for r in q})
        fd.update({r['app']: str(r['fd']) for r in q})
        if len(tasks[b]) != N_TASKS[b]:
            stop(f'{b} tasks {len(tasks[b])} != {N_TASKS[b]}')
    if set(tasks['P1-DEV']) & set(tasks['VAL']):
        stop('P1-DEV and VAL tasks overlap')
    lines = ['app_id\tblock\tfiling_date\n'] + [f'{a}\t{b}\t{fd[a][:4]}-{fd[a][4:6]}-{fd[a][6:]}\n'
                                                for b in BLOCKS for a in tasks[b]]
    st.put_bytes(f'{P}splits/private/tasks.tsv', ''.join(lines).encode('utf-8'))
    st.verified(src / 'challenge1m/out-v1/corpus-units.tsv', f'{P}challenge1m/out-v1/corpus-units.tsv',
                '/data/ptp-paper2/challenge1m/out-v1/corpus-units.tsv')
    if fsha(src / 'challenge1m/out-v1/pairs-dev.tsv') != man.get('/data/ptp-paper2/challenge1m/out-v1/pairs-dev.tsv'):
        stop('archived pairs-dev.tsv differs from its pull manifest')
    buf, npairs = io.StringIO(), {b: 0 for b in BLOCKS}
    with open(src / 'challenge1m/out-v1/pairs-dev.tsv', encoding='utf-8', newline='') as f:
        rd, wr = csv.reader(f, delimiter='\t'), csv.writer(buf, delimiter='\t', lineterminator='\n')
        head = next(rd)
        wr.writerow(head)
        bi = head.index('block')
        for r in rd:
            if r[bi] in BLOCKS:
                wr.writerow(r)
                npairs[r[bi]] += 1
    st.put_bytes(f'{P}challenge1m/out-v1/pairs-dev.tsv', buf.getvalue().encode('utf-8'))
    REPORT['tasks'] = {b: len(tasks[b]) for b in BLOCKS}
    REPORT['pairs_rows'] = npairs

    # 4 texts: corpus (A), P1-DEV records (A2), the VAL rule checked on P1-DEV, VAL records derived (A2v)
    loc = priv / 'p2t02-local-check/texts-v1'
    got = fsha(loc / 'corpus.jsonl')
    REPORT['A_corpus_sha256'] = {'local': got, 'archived': CORPUS_SHA, 'passed': got == CORPUS_SHA}
    if got != CORPUS_SHA:
        stop('corpus.jsonl is not byte-identical to the dr-train text')
    st.put_file(f'{P}bridgeret/texts-v1/corpus.jsonl', loc / 'corpus.jsonl', link=True)
    local_lines, local_recs = [], {}
    for raw in (loc / 'queries.jsonl').read_bytes().replace(b'\r\n', b'\n').decode('utf-8').splitlines():
        r = json.loads(raw)
        no_test(r.get('block'), 'local queries.jsonl')
        if r.get('block') != 'P1-DEV':
            stop('the local texts-v1/queries.jsonl holds a non-P1-DEV record')
        local_lines.append((r['app_id'], raw))
        local_recs[r['app_id']] = r
    ext = {b: {} for b in BLOCKS}
    ext_lines = {b: [] for b in BLOCKS}
    with open(inp / 'queries-dev-val.jsonl', encoding='utf-8') as f:
        for line in f:
            r = json.loads(line)
            no_test(r.get('block'), 'queries-dev-val.jsonl')
            if r.get('block') in BLOCKS:
                ext[r['block']][r['app_id']] = r
                ext_lines[r['block']].append(line.rstrip('\r\n') + '\n')
    a2 = sorted(a for a in set(local_recs) | set(ext['P1-DEV'])
                if (a not in local_recs or a not in ext['P1-DEV'] or
                    tuple(local_recs[a].get(k) or '' for k in QFIELDS) != tuple(ext['P1-DEV'][a].get(k) or '' for k in QFIELDS)))
    REPORT['A2_query_records_P1DEV'] = {'n_local': len(local_recs), 'n_drtrain': len(ext['P1-DEV']),
                                        'records_differing': len(a2), 'passed': not a2 and len(local_recs) == N_TASKS['P1-DEV']}
    if a2 or len(local_recs) != N_TASKS['P1-DEV']:
        stop(f'P1-DEV query records differ from the dr-train extract ({len(a2)} differ)')
    rule = sorted(a for a in local_recs if ser_key(local_recs[a]) != ser_key(derive_val_record(ext['P1-DEV'][a])))
    REPORT['VAL_rule_checked_on_P1DEV'] = {'records': len(local_recs), 'records_differing': len(rule),
                                           'with_doc': sum(bool(r.get('doc')) for r in local_recs.values()),
                                           'passed': not rule}
    if rule:
        stop(f'the VAL derivation rule does not reproduce {len(rule)} P1-DEV records of the local builder')
    val = [derive_val_record(ext['VAL'][a]) for a in sorted(ext['VAL'])]
    if len(val) != N_TASKS['VAL'] or set(ext['VAL']) != set(tasks['VAL']):
        stop('the VAL extract does not hold exactly the 2,000 VAL tasks')
    n_doc = sum(bool(r['doc']) for r in val)
    REPORT['A2v_VAL_records'] = {'n': len(val), 'with_doc': n_doc, 'no_pgpub': len(val) - n_doc,
                                 'passed': n_doc == fg.N_VAL_WITH_DOC}
    if n_doc != fg.N_VAL_WITH_DOC:
        stop(f'VAL records with a document {n_doc} != {fg.N_VAL_WITH_DOC}')
    merged = sorted(local_lines + [(r['app_id'], json.dumps(r, ensure_ascii=False)) for r in val])
    REPORT['local_P1DEV_order_sorted'] = [a for a, _ in local_lines] == sorted(a for a, _ in local_lines)
    st.put_bytes(f'{P}bridgeret/texts-v1/queries.jsonl', ''.join(l + '\n' for _, l in merged).encode('utf-8'))
    st.put_bytes(arch + 'queries-p1dev-drtrain.jsonl', ''.join(ext_lines['P1-DEV']).encode('utf-8'))
    st.put_bytes(arch + 'queries-val-drtrain.jsonl', ''.join(ext_lines['VAL']).encode('utf-8'))

    # 5 archived references, archived VAL runs, C0 code (all against the pull manifests)
    for s in C0_CODE:
        st.verified(src / 'bridgeret/code' / s, f'{P}bridgeret/code/{s}', f'/data/ptp-paper2/bridgeret/code/{s}')
    st.verified(src / 'bridgeret/texts-v1/report.json', arch + 'texts-report.json',
                '/data/ptp-paper2/bridgeret/texts-v1/report.json')
    for r, files in (('z-qwen3', ('units.json', 'eval-P1-DEV.json', 'eval-VAL.json')),
                     ('z-patembed', ('units.json', 'eval-P1-DEV.json', 'eval-VAL.json')),
                     ('bm25', ('eval-P1-DEV.json', 'eval-VAL.json'))):
        for f in files:
            st.verified(src / 'bridgeret/runs' / r / f, f'{arch}{r}/{f}', f'/data/ptp-paper2/bridgeret/runs/{r}/{f}')
        st.verified(src / 'bridgeret/runs' / r / 'run-VAL.tsv.gz', f'{P}bridgeret/runs/{r}/run-VAL.tsv.gz',
                    f'/data/ptp-paper2/bridgeret/runs/{r}/run-VAL.tsv.gz')
    st.verified(src22 / 'g03-dev/evals/P1-DEV/alloc-L0-Q2-P2-A0.json', arch + 'g03-v0/alloc-L0-Q2-P2-A0.json',
                '/data/ptp-paper2/g03-dev/evals/P1-DEV/alloc-L0-Q2-P2-A0.json')
    st.verified(src22 / 'g03-dev/evals/VAL/alloc-L0-Q2-P2-A0.json', arch + 'g03-v0/VAL/alloc-L0-Q2-P2-A0.json',
                '/data/ptp-paper2/g03-dev/evals/VAL/alloc-L0-Q2-P2-A0.json')

    # 6 populations: pilot sample from apps-P1-DEV.json; apps-VAL.json = the apps of the archived v0 F* VAL run
    pilot_p = inp / 'apps-pilot.json'
    if fsha(pilot_p) != PILOT_SHA:
        stop('apps-pilot.json sha256 differs')
    regen = sorted(sorted(apps['P1-DEV'], key=lambda a: hashlib.sha256(f'g03-a3-pilot-v1{a}'.encode()).hexdigest())[:2000])
    vrun = src22 / 'g03-dev/runs/VAL/alloc-L0-Q2-P2-A0.tsv'
    if fsha(vrun) != man.get('/data/ptp-paper2/g03-dev/runs/VAL/alloc-L0-Q2-P2-A0.tsv'):
        stop('archived v0 F* VAL run differs from its pull manifest')
    vapps = sorted(fg.pg.apps_of(vrun))
    REPORT['G_local'] = {'n_apps_P1_DEV': len(apps['P1-DEV']), 'pilot_regenerated_equal':
                         regen == json.loads(pilot_p.read_text(encoding='utf-8')),
                         'n_apps_VAL': len(apps['VAL']), 'apps_VAL_equal_archived_v0_fstar_VAL_run': vapps == apps['VAL']}
    if not (REPORT['G_local']['pilot_regenerated_equal'] and len(apps['P1-DEV']) == fg.N_APPS['P1-DEV']
            and vapps == apps['VAL'] and len(vapps) == fg.N_APPS['VAL']):
        stop('populations: pilot sample or VAL F* apps do not match')
    st.put_file(f'{P}g03-dev/a3/apps-pilot.json', pilot_p)
    for b in BLOCKS:
        st.put_file(f'{P}g03-dev/a3/apps-{b}.json', inp / f'apps-{b}.json')

    # 7 code and ledgers (the ledger copies are re-checked after copying: the upload is what was checked)
    for s in G03_CODE:
        if st.write:
            pin.lf_copy(repo / 'scripts/research' / s, tree / f'{P}g03-dev/code/{s}')
    REPORT['ledgers'] = {}
    for b in BLOCKS:
        lp = ldir / f'{b}.jsonl'
        if lp.is_file():
            REPORT['ledgers'][b] = {'sha256': fsha(lp), 'bytes': lp.stat().st_size}
            st.put_file(f'{P}g03-dev/a3r1/ledger/{MSTAR_DIR}/{b}.jsonl', lp)
    if st.write:
        led2 = fg.check_ledgers(tree / f'{P}g03-dev/a3r1/ledger/{MSTAR_DIR}', apps, prefix)
        if not led2['passed'] or any(fsha(tree / f'{P}g03-dev/a3r1/ledger/{MSTAR_DIR}/{b}.jsonl') != REPORT['ledgers'][b]['sha256']
                                     for b in BLOCKS):
            stop('the copied ledgers changed or no longer pass (was the generator still writing?)')

    if not st.write:
        REPORT['status'] = 'CHECKED' if led['passed'] else 'CHECKED: inputs OK, Stage B NOT complete'
        if not led['passed']:
            raise SystemExit(2)   # inputs verified, but the pod must not start yet
        return
    # 8 TEST guard over the staged tree, manifest, file list
    files = sorted(p for p in tree.rglob('*') if p.is_file())
    if any('TEST' in str(p.relative_to(tree)) for p in files):
        stop('a staged path names TEST')
    rel = [p.relative_to(tree).as_posix() for p in files]
    with open(tree / P / 'MANIFEST-a3r1-full.sha256', 'w', encoding='utf-8', newline='\n') as f:
        for p, r in zip(files, rel):
            f.write(f'{fsha(p)}  /{r}\n')
    rel.append(P + 'MANIFEST-a3r1-full.sha256')
    with open(outd / 'FILES-full.txt', 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(rel) + '\n')
    size = sum((tree / r).stat().st_size for r in rel)
    REPORT.update({'status': 'OK', 'files': len(rel), 'bytes_upload': size, 'tree': str(tree)})


if __name__ == '__main__':
    try:
        main(sys.argv[1:])
    finally:
        argv = [a for a in sys.argv[1:] if not a.startswith('--')]
        if len(argv) == 3 and REPORT:
            Path(argv[2]).mkdir(parents=True, exist_ok=True)
            (Path(argv[2]) / 'stage-report-full.json').write_text(json.dumps(REPORT, indent=1), encoding='utf-8')
            print(json.dumps({k: REPORT.get(k) for k in ('status', 'mode', 'stage_b_complete', 'files', 'bytes_upload',
                                                           'tree')}), flush=True)
