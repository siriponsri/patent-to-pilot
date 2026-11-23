"""A3r1 RunPod rebuild: stage the private upload tree on the owner PC. P1-DEV only; never opens TEST.

Amendment docs/healthtech/research/g03-dev/A3R1-AMENDMENT-RUNPOD-REBUILD.md. Writes, under <out_dir>/tree, the dr-train
paths the pods mirror (extract the tars at / on a pod):
  data/ptp-paper2/splits/private/tasks.tsv            app_id, block, filing_date, the 26,575 P1-DEV tasks (from meta.pkl)
  data/ptp-paper2/challenge1m/out-v1/corpus-units.tsv copied; pairs-dev.tsv with its P1-DEV rows only
  data/ptp-paper2/bridgeret/texts-v1/corpus.jsonl     the local LF build (sha256 must equal the archived 287ef7e0...)
  data/ptp-paper2/bridgeret/texts-v1/queries.jsonl    the local P1-DEV build, CRLF -> LF
  data/ptp-paper2/bridgeret/code/                     archived C0 scripts (unchanged bytes)
  data/ptp-paper2/bridgeret/am7/prep-v1/meta.pkl      copied (cluster ids for the frozen decision; P1-DEV and VAL only)
  data/ptp-paper2/bridgeret/archived-a3r1/            gate references: texts-report.json, queries-p1dev-drtrain.jsonl,
                                                      z-qwen3|z-patembed/{units,eval-P1-DEV,summary-P1-DEV}.json,
                                                      bm25/{eval,summary}-P1-DEV.json, g03-v0/alloc-L0-Q2-P2-A0.json
  data/ptp-paper2/g03-dev/code/                       repository scripts (CRLF -> LF)
  data/ptp-paper2/g03-dev/a3/{apps-pilot,apps-P1-DEV}.json, a3r1/ledger/<model>/P1-DEV.jsonl, a3r1/pilot-costs.json
  data/ptp-paper2/MANIFEST-a3r1.sha256                sha256 of every staged file (absolute pod paths)
and <out_dir>/FILES-qwen3.txt, FILES-patembed.txt (tar file lists per pod role; the assemble role uses the patembed pod)
and <out_dir>/stage-report.json (local pre-checks A, A2, G-local, H-local and every archived reference against the
dr-train pull manifests). Any failed pre-check aborts before the tree is complete.
The frozen dr-train manifest (which lists TEST tasks) is never read. No TEST block, sealed file or TEST label is staged.

Usage: python -I g03_a3r1_runpod_inputs.py <private_artifacts_dir> <repo_dir> <out_dir>
"""
import csv
import hashlib
import json
import os
import pickle
import shutil
import sys
from pathlib import Path

CORPUS_SHA = '287ef7e0b823b31330a6b3ad804f4e0f99dceec0300f45ffb7d6345adc8d7a86'
PILOT_SHA = 'c6653b6f299c5bfe8bd90617391ec62235171558d4d5afca660085b9e165c2bf'
MODELS = ('qwen__qwen3-32b', 'deepseek__deepseek-v4-flash-0731', 'google__gemini-2.5-flash-lite',
          'typhoon-v2.5-30b-a3b-instruct')
C0_CODE = ('serialise_bridgeret_texts.py', 'serialise_bridgeret_texts_v2.py', 'dense_bridgeret_v2.py',
           'dense_bridgeret_v3.py', 'bm25_bridgeret.py', 'bridgeret_query.py', 'eval_bridgeret_dev.py')
G03_CODE = ('g03_a3_routes.py', 'g03_a3_decide.py', 'g03_queue_a3r1_pilot.sh', 'g03_route_acquisition.py',
            'g03_a3r1_runpod.sh', 'g03_a3r1_runpod_gate.py', 'g03_a3r1_runpod_v0.py', 'g03_a3r1_runpod_models.py')
QFIELDS = ('app_id', 'block', 'title', 'abstract', 'claim')
REPORT = {}


def fsha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 22), b''):
            h.update(b)
    return h.hexdigest()


def stop(msg):
    REPORT['status'] = 'FAILED: ' + msg
    raise SystemExit('staging stopped: ' + msg)


def pulled(manifest_tsv):
    out = {}
    with open(manifest_tsv, encoding='utf-8') as f:
        next(f)
        for line in f:
            p = line.rstrip('\n').split('\t')
            if len(p) >= 5 and p[4] == 'OK':
                out[p[0]] = p[2]
    return out


def copy_verified(src, dst, remote_path, man):
    """Copy an archived file after checking it against the dr-train pull manifest (remote sha256)."""
    want = man.get(remote_path)
    got = fsha(src)
    if want != got:
        stop(f'archived file differs from its pull manifest: {remote_path}')
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    REPORT.setdefault('archived_refs_verified', {})[remote_path] = got


def link_or_copy(src, dst):
    dst.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.link(src, dst)
    except OSError:
        shutil.copy2(src, dst)


def lf_copy(src, dst):
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(Path(src).read_bytes().replace(b'\r\n', b'\n'))


def qrec(path):
    recs, order = {}, []
    with open(path, encoding='utf-8') as f:
        for line in f:
            r = json.loads(line)
            if 'TEST' in str(r.get('block')):
                stop(f'TEST record in {path}')
            if r.get('block') == 'P1-DEV':
                recs[r['app_id']] = tuple(r.get(k) or '' for k in QFIELDS)
                order.append(r['app_id'])
    return recs, order


def main(argv):
    priv, repo, outd = Path(argv[0]), Path(argv[1]), Path(argv[2])
    tree = outd / 'tree'
    if tree.exists():
        sys.exit(f'{tree} exists')
    out = tree / 'data/ptp-paper2'
    a21 = priv / 'dr-train-archive/20261121'
    a22 = priv / 'dr-train-archive/20261122-g03'
    src = a21 / 'files/data/ptp-paper2'
    man = {**pulled(a21 / 'pull-manifest.tsv'), **pulled(a22 / 'pull-manifest.tsv')}
    REPORT.update({'format': 'ptp-g03-a3r1-runpod-stage-v1', 'block': 'P1-DEV'})

    # tasks.tsv: P1-DEV only, from meta.pkl (as P2-T02 amendment A1)
    meta = pickle.load(open(src / 'bridgeret/am7/prep-v1/meta.pkl', 'rb'))
    if any('TEST' in b for b in meta['queries']):
        stop('meta.pkl holds a TEST block')
    q = meta['queries']['P1-DEV']
    apps = sorted({r['app'] for r in q})
    if len(apps) != 26575:
        stop(f'P1-DEV tasks {len(apps)} != 26575')
    fd = {r['app']: str(r['fd']) for r in q}
    (out / 'splits/private').mkdir(parents=True)
    with open(out / 'splits/private/tasks.tsv', 'w', encoding='utf-8', newline='\n') as f:
        f.write('app_id\tblock\tfiling_date\n')
        for a in apps:
            d = fd[a]
            f.write(f'{a}\tP1-DEV\t{d[:4]}-{d[4:6]}-{d[6:]}\n')
    c = out / 'challenge1m/out-v1'
    copy_verified(src / 'challenge1m/out-v1/corpus-units.tsv', c / 'corpus-units.tsv',
                  '/data/ptp-paper2/challenge1m/out-v1/corpus-units.tsv', man)
    n = 0
    if fsha(src / 'challenge1m/out-v1/pairs-dev.tsv') != man.get('/data/ptp-paper2/challenge1m/out-v1/pairs-dev.tsv'):
        stop('archived pairs-dev.tsv differs from its pull manifest')
    with open(src / 'challenge1m/out-v1/pairs-dev.tsv', encoding='utf-8', newline='') as f, \
            open(c / 'pairs-dev.tsv', 'w', encoding='utf-8', newline='') as g:
        rd, wr = csv.reader(f, delimiter='\t'), csv.writer(g, delimiter='\t', lineterminator='\n')
        head = next(rd)
        wr.writerow(head)
        bi = head.index('block')
        for r in rd:
            if r[bi] == 'P1-DEV':
                wr.writerow(r)
                n += 1
    REPORT['tasks_P1_DEV'], REPORT['pairs_P1_DEV_rows'] = len(apps), n

    b = out / 'bridgeret'
    # texts-v1 (local build, verified): gate A and A2 checked here, before any upload
    loc = priv / 'p2t02-local-check/texts-v1'
    got = fsha(loc / 'corpus.jsonl')
    REPORT['A_corpus_sha256'] = {'local': got, 'archived': CORPUS_SHA, 'passed': got == CORPUS_SHA}
    if got != CORPUS_SHA:
        stop('corpus.jsonl is not byte-identical to the dr-train text')
    link_or_copy(loc / 'corpus.jsonl', b / 'texts-v1/corpus.jsonl')
    lf_copy(loc / 'queries.jsonl', b / 'texts-v1/queries.jsonl')
    new, no = qrec(b / 'texts-v1/queries.jsonl')
    arch = b / 'archived-a3r1'
    arch.mkdir(parents=True)
    with open(priv / 'g03-a3/inputs/queries-dev-val.jsonl', encoding='utf-8') as f, \
            open(arch / 'queries-p1dev-drtrain.jsonl', 'w', encoding='utf-8', newline='\n') as g:
        for line in f:
            if json.loads(line).get('block') == 'P1-DEV':
                g.write(line.rstrip('\r\n') + '\n')
    old, oo = qrec(arch / 'queries-p1dev-drtrain.jsonl')
    diff = sorted(a for a in set(new) | set(old) if new.get(a) != old.get(a))
    REPORT['A2_query_records'] = {'n_local': len(new), 'n_drtrain': len(old), 'records_differing': len(diff),
                                  'same_order': no == oo, 'passed': not diff and len(new) == 26575}
    if diff or len(new) != 26575:
        stop(f'P1-DEV query records differ from the dr-train extract ({len(diff)} differ)')

    for s in C0_CODE:   # byte-identical to dr-train (some of these Python files have CRLF there too; Python reads both)
        copy_verified(src / 'bridgeret/code' / s, b / 'code' / s, f'/data/ptp-paper2/bridgeret/code/{s}', man)
    copy_verified(src / 'bridgeret/am7/prep-v1/meta.pkl', b / 'am7/prep-v1/meta.pkl',
                  '/data/ptp-paper2/bridgeret/am7/prep-v1/meta.pkl', man)
    copy_verified(src / 'bridgeret/texts-v1/report.json', arch / 'texts-report.json',
                  '/data/ptp-paper2/bridgeret/texts-v1/report.json', man)
    for r, files in (('z-qwen3', ('units.json', 'eval-P1-DEV.json', 'summary-P1-DEV.json')),
                     ('z-patembed', ('units.json', 'eval-P1-DEV.json', 'summary-P1-DEV.json')),
                     ('bm25', ('eval-P1-DEV.json', 'summary-P1-DEV.json'))):
        for f in files:
            copy_verified(src / 'bridgeret/runs' / r / f, arch / r / f, f'/data/ptp-paper2/bridgeret/runs/{r}/{f}', man)
    copy_verified(a22 / 'files/data/ptp-paper2/g03-dev/evals/P1-DEV/alloc-L0-Q2-P2-A0.json',
                  arch / 'g03-v0/alloc-L0-Q2-P2-A0.json', '/data/ptp-paper2/g03-dev/evals/P1-DEV/alloc-L0-Q2-P2-A0.json', man)

    g = out / 'g03-dev'
    for s in G03_CODE:
        lf_copy(repo / 'scripts/research' / s, g / 'code' / s)
    pilot_p, all_p = priv / 'g03-a3/inputs/apps-pilot.json', priv / 'g03-a3/inputs/apps-P1-DEV.json'
    if fsha(pilot_p) != PILOT_SHA:
        stop('apps-pilot.json sha256 differs')
    pilot, allf = json.loads(pilot_p.read_text()), json.loads(all_p.read_text())
    regen = sorted(sorted(allf, key=lambda a: hashlib.sha256(f'g03-a3-pilot-v1{a}'.encode()).hexdigest())[:2000])
    REPORT['G_local_pilot_from_apps_P1_DEV'] = {'n_apps_P1_DEV': len(allf), 'n_pilot': len(pilot),
                                                'regenerated_equal': regen == pilot, 'sha256': PILOT_SHA}
    if regen != pilot or len(allf) != 25626:
        stop('apps-pilot.json is not the sha256 sample of apps-P1-DEV.json')
    (g / 'a3').mkdir(parents=True)
    shutil.copy2(pilot_p, g / 'a3/apps-pilot.json')
    shutil.copy2(all_p, g / 'a3/apps-P1-DEV.json')
    ps, hl = set(pilot), {}
    for m in MODELS:
        lp = priv / 'g03-a3r1/ledger/A3r1' / m / 'P1-DEV.jsonl'
        nrec = bad = outside = 0
        with open(lp, encoding='utf-8') as f:
            for line in f:
                r = json.loads(line)
                nrec += 1
                bad += r.get('block') != 'P1-DEV'
                outside += r.get('status') == 'ok' and r['app_id'] not in ps
        hl[m] = {'records': nrec, 'non_P1DEV': bad, 'usable_outside_pilot': outside, 'sha256': fsha(lp)}
        if bad or outside:
            stop(f'ledger {m} has non-P1-DEV or out-of-pilot records')
        (g / 'a3r1/ledger' / m).mkdir(parents=True)
        shutil.copy2(lp, g / 'a3r1/ledger' / m / 'P1-DEV.jsonl')
    shutil.copy2(priv / 'g03-a3r1/pilot-costs.json', g / 'a3r1/pilot-costs.json')
    REPORT['H_local_ledgers'] = hl

    # TEST guard over the staged tree, manifest, per-role file lists
    files = sorted(p for p in tree.rglob('*') if p.is_file())
    if any('TEST' in str(p.relative_to(tree)) for p in files):
        stop('a staged path names TEST')
    rel = [p.relative_to(tree).as_posix() for p in files]
    with open(out / 'MANIFEST-a3r1.sha256', 'w', encoding='utf-8', newline='\n') as f:
        for p, r in zip(files, rel):
            f.write(f'{fsha(p)}  /{r}\n')
    rel.append('data/ptp-paper2/MANIFEST-a3r1.sha256')
    not_qwen = ('bridgeret/am7/', 'bridgeret/archived-a3r1/z-patembed/', 'bridgeret/archived-a3r1/bm25/',
                'bridgeret/archived-a3r1/g03-v0/', 'g03-dev/a3/', 'g03-dev/a3r1/', 'code/serialise_bridgeret_texts_v2.py',
                'code/dense_bridgeret_v3.py', 'code/bm25_bridgeret.py')
    qwen = [r for r in rel if not any(x in r for x in not_qwen)]
    (outd / 'FILES-qwen3.txt').write_text('\n'.join(qwen) + '\n', encoding='utf-8')
    (outd / 'FILES-patembed.txt').write_text('\n'.join(rel) + '\n', encoding='utf-8')
    extra = [r for r in rel if r not in qwen or r.endswith('MANIFEST-a3r1.sha256')]   # to assemble on the Qwen3 pod
    (outd / 'FILES-assemble-extra.txt').write_text('\n'.join(extra) + '\n', encoding='utf-8')
    size = lambda rs: sum((tree / r).stat().st_size for r in rs)
    REPORT.update({'status': 'OK', 'files': len(rel), 'bytes_qwen3_pod': size(qwen), 'bytes_patembed_pod': size(rel),
                   'tree': str(tree)})
    (outd / 'stage-report.json').write_text(json.dumps(REPORT, indent=1), encoding='utf-8')
    print(json.dumps({k: REPORT[k] for k in ('status', 'files', 'bytes_qwen3_pod', 'bytes_patembed_pod', 'tree')}))


if __name__ == '__main__':
    try:
        main(sys.argv[1:])
    finally:
        if REPORT.get('status', '').startswith('FAILED') and len(sys.argv) > 3:
            Path(sys.argv[3]).mkdir(parents=True, exist_ok=True)
            (Path(sys.argv[3]) / 'stage-report.json').write_text(json.dumps(REPORT, indent=1), encoding='utf-8')
