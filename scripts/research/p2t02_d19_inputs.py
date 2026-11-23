"""P2-T02 amendment A2 (owner D19): stage the RunPod upload tree on the owner PC. P1-DEV only; never opens TEST.

Amendment: docs/healthtech/research/p2-coverage/P2-T02-AMENDMENT-A2-D19-FOLLOWUP.md. Writes, under <out_dir>/tree, the
dr-train paths the pods mirror (extract the tars at / on a pod):
  data/ptp-paper2/splits/private/tasks.tsv              26,575 P1-DEV tasks           } from the A3r1 stage tree, each
  data/ptp-paper2/challenge1m/out-v1/corpus-units.tsv   copied                        } file checked against its
  data/ptp-paper2/challenge1m/out-v1/pairs-dev.tsv      P1-DEV rows only              } MANIFEST-a3r1.sha256 entry
  data/ptp-paper2/bridgeret/texts-v1/{corpus,queries}.jsonl  corpus 287ef7e0...; P1-DEV queries
  data/ptp-paper2/bridgeret/code/                       archived C0 scripts (serialisers, bridgeret_query, evaluator)
  data/ptp-paper2/bridgeret/am7/prep-v1/meta-p1dev.pkl  {'queries': {'P1-DEV': [{'app', 'au'}]}}: the cluster ids of the
                                                        frozen bootstrap only (meta.pkl also holds VAL labels; not staged)
  data/ptp-paper2/bridgeret/runs/z-arctic/units.json    corpus unit order (the content build asserts it)
  data/ptp-paper2/bridgeret/runs/z-<m>/{run-P1-DEV.tsv.gz,units.json}, evals-a3r1/z-<m>.json, logs/{gate,models}-<m>.json
                                                        the gated A3r1 C0 relay of model m (the C0 reference)
  data/ptp-paper2/bridgeret/archived-d19/               P2-T02 content manifest (Arctic reproduction gate), P2-T02
                                                        results.json (side-by-side only)
  data/ptp-paper2/patentsview/claims/*_claims_*.tsv.zip the 54 PatentsView claims files FILTERED to the rows of the 1M
                                                        corpus documents (same member name, header, row order and field
                                                        values; the content build keeps only these rows anyway, so its
                                                        outputs are unchanged; the pod proves it, gate C-A)
  data/ptp-paper2/p2-coverage/code/                     repository scripts (CRLF -> LF)
  data/ptp-paper2/MANIFEST-d19-<m>.sha256               sha256 of every file of pod m (absolute pod paths)
and <out_dir>/FILES-claims.txt (shared by both pods), FILES-<m>.txt (the rest of pod m), stage-report.json.
The frozen dr-train manifest (which lists TEST tasks) is never read. No TEST block, sealed file or TEST label is staged.

Usage: python -I p2t02_d19_inputs.py <private_artifacts_dir> <repo_dir> <out_dir> [--workers 8] [--claims-dir DIR]
       (--claims-dir defaults to <private_artifacts_dir>/pv-links/claims)
"""
import argparse
import csv
import hashlib
import io
import json
import os
import pickle
import shutil
import sys
import tarfile
import time
import zipfile
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

csv.field_size_limit(1 << 30)
CORPUS_SHA = '287ef7e0b823b31330a6b3ad804f4e0f99dceec0300f45ffb7d6345adc8d7a86'
UNITS_SHA = 'e2ab2d4a97c20fed483f6c89ff9d6d128676da14ba4c791c8b415d695f904d6a'
MODELS = ('qwen3', 'patembed')
COMMON_A3R1 = ('splits/private/tasks.tsv', 'challenge1m/out-v1/corpus-units.tsv', 'challenge1m/out-v1/pairs-dev.tsv',
               'bridgeret/texts-v1/corpus.jsonl', 'bridgeret/texts-v1/queries.jsonl',
               'bridgeret/code/serialise_bridgeret_texts.py', 'bridgeret/code/serialise_bridgeret_texts_v2.py',
               'bridgeret/code/bridgeret_query.py', 'bridgeret/code/eval_bridgeret_dev.py')
CODE = ('p2t02_build_content.py', 'p2t02_retrieve.py', 'p2t02_analyse.py', 'p2t02_d19_encode.py', 'p2t02_d19_gate.py',
        'p2t02_d19_decide.py', 'p2t02_d19_runpod.sh', 'g03_a3r1_runpod_models.py')
RELAY = ('bridgeret/runs/z-{m}/run-P1-DEV.tsv.gz', 'bridgeret/runs/z-{m}/units.json', 'bridgeret/evals-a3r1/z-{m}.json',
         'bridgeret/logs/gate-{m}.json', 'bridgeret/logs/models-{m}.json')
REPORT = {'format': 'ptp-p2t02-d19-stage-v1', 'checks': {}}
NEED = None


def fsha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 22), b''):
            h.update(b)
    return h.hexdigest()


def stop(msg):
    REPORT['status'] = 'FAILED: ' + msg
    raise SystemExit('staging stopped: ' + msg)


def place(src, dst):
    dst.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.link(src, dst)
    except OSError:
        shutil.copy2(src, dst)


# ------------------------------------------------------------------ claims filter (output-neutral for the content build)
def doc_key(pid, pg, pat_key):
    return ('PG' + pid) if pg else pat_key(pid)


def filter_zip(src, dst, need, pat_key):
    """Copy the rows of the documents in `need` (the build's own doc key) with their header, in file order. Fields are
    parsed and re-written with csv (tab, minimal quoting), which reads back to the identical field values."""
    src, dst = Path(src), Path(dst)
    pg = src.name.startswith('pg_')
    n_in = n_out = 0
    with zipfile.ZipFile(src) as zi:
        member = zi.namelist()[0]
        with zipfile.ZipFile(dst, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zo:
            with zi.open(member) as fi, zo.open(member, 'w', force_zip64=True) as fo:
                rd = csv.reader(io.TextIOWrapper(fi, encoding='utf-8', newline=''), delimiter='\t')
                tw = io.TextIOWrapper(fo, encoding='utf-8', newline='')
                wr = csv.writer(tw, delimiter='\t', lineterminator='\n')
                h = next(rd)
                wr.writerow(h)
                idc = h.index('pgpub_id' if pg else 'patent_id')
                for r in rd:
                    n_in += 1
                    if doc_key(r[idc], pg, pat_key) in need:
                        wr.writerow(r)
                        n_out += 1
                tw.flush()
                tw.detach()
    return {'file': src.name, 'member': member, 'rows_in': n_in, 'rows_kept': n_out, 'bytes_in': src.stat().st_size,
            'bytes_out': dst.stat().st_size}


def _init(need_path, repo):
    global NEED, PATKEY
    sys.path.insert(0, str(Path(repo) / 'scripts' / 'research'))
    import p2t02_build_content as bc                      # the build's own key function, so the filter cannot drift
    PATKEY = bc.pat_key
    NEED = set(json.loads(Path(need_path).read_text()))


def _job(args):
    src, dst = args
    return filter_zip(src, dst, NEED, PATKEY)
# ------------------------------------------------------------------


def a3r1_manifest(a3):
    out = {}
    for line in (a3 / 'MANIFEST-a3r1.sha256').read_text(encoding='utf-8').splitlines():
        h, p = line.split(None, 1)
        out[p.strip().lstrip('*').replace('/data/ptp-paper2/', '', 1)] = h
    return out


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument('private')
    ap.add_argument('repo')
    ap.add_argument('out')
    ap.add_argument('--workers', type=int, default=8)
    ap.add_argument('--claims-dir')
    a = ap.parse_args(argv)
    t0 = time.time()
    pa, repo, out = Path(a.private), Path(a.repo), Path(a.out)
    tree = out / 'tree'
    D = tree / 'data/ptp-paper2'
    if out.exists():
        stop(f'{out} exists')
    D.mkdir(parents=True)
    a3 = pa / 'g03-a3r1-runpod-stage/tree/data/ptp-paper2'
    man = a3r1_manifest(a3)
    files = {m: [] for m in MODELS}
    common = []

    # 1. common inputs from the A3r1 stage tree, each against its recorded sha256
    for rel in COMMON_A3R1:
        got = fsha(a3 / rel)
        if got != man.get(rel):
            stop(f'{rel}: sha256 {got} differs from MANIFEST-a3r1')
        place(a3 / rel, D / rel)
        common.append(rel)
    if fsha(D / 'bridgeret/texts-v1/corpus.jsonl') != CORPUS_SHA:
        stop('corpus.jsonl is not the archived 287ef7e0... text')
    with open(D / 'splits/private/tasks.tsv', encoding='utf-8') as f:
        blocks = {r['block'] for r in csv.DictReader(f, delimiter='\t')}
    with open(D / 'challenge1m/out-v1/pairs-dev.tsv', encoding='utf-8') as f:
        pblocks = {r['block'] for r in csv.DictReader(f, delimiter='\t')}
    qblocks, nq = set(), 0
    for l in open(D / 'bridgeret/texts-v1/queries.jsonl', encoding='utf-8'):
        qblocks.add(json.loads(l)['block'])
        nq += 1
    if blocks != {'P1-DEV'} or pblocks != {'P1-DEV'} or qblocks != {'P1-DEV'}:
        stop(f'not P1-DEV only: tasks {blocks}, pairs {pblocks}, queries {qblocks}')
    REPORT['checks']['p1dev_only'] = {'tasks': sorted(blocks), 'pairs': sorted(pblocks), 'queries': sorted(qblocks),
                                      'query_records': nq}

    # 2. P1-DEV cluster ids only (the frozen bootstrap clusters by examiner art unit)
    if fsha(a3 / 'bridgeret/am7/prep-v1/meta.pkl') != man['bridgeret/am7/prep-v1/meta.pkl']:
        stop('meta.pkl sha256')
    meta = pickle.load(open(a3 / 'bridgeret/am7/prep-v1/meta.pkl', 'rb'))
    small = {'queries': {'P1-DEV': [{'app': q['app'], 'au': q.get('au')} for q in meta['queries']['P1-DEV']]},
             'note': 'amendment A2: P1-DEV app and art-unit only, from am7/prep-v1/meta.pkl sha256 '
                     + man['bridgeret/am7/prep-v1/meta.pkl']}
    rel = 'bridgeret/am7/prep-v1/meta-p1dev.pkl'
    (D / rel).parent.mkdir(parents=True, exist_ok=True)
    with open(D / rel, 'wb') as f:
        pickle.dump(small, f, protocol=4)
    c_full = {q['app']: str(q.get('au') or 'q:' + q['app']) for q in meta['queries']['P1-DEV']}
    c_small = {q['app']: str(q.get('au') or 'q:' + q['app']) for q in pickle.load(open(D / rel, 'rb'))['queries']['P1-DEV']}
    if c_full != c_small or len(c_small) != 26575:
        stop('P1-DEV cluster map differs from meta.pkl')
    REPORT['checks']['clusters_p1dev'] = {'apps': len(c_small), 'art_units': len(set(c_small.values()))}
    del meta
    common.append(rel)

    # 3. corpus unit order (content build asserts it) and P2-T02 references for the gates
    p2 = pa / 'p2t02-runpod'
    for src, rel in ((p2 / 'bridgeret/runs/z-arctic/units.json', 'bridgeret/runs/z-arctic/units.json'),
                     (p2 / 'p2-coverage/content/manifest.json', 'bridgeret/archived-d19/p2t02-content-manifest.json'),
                     (p2 / 'p2-coverage/results.json', 'bridgeret/archived-d19/p2t02-results.json')):
        place(src, D / rel)
        common.append(rel)
    if fsha(D / 'bridgeret/runs/z-arctic/units.json') != UNITS_SHA:
        stop('z-arctic units.json is not the corpus order e2ab2d4a...')
    p2man = json.loads((D / 'bridgeret/archived-d19/p2t02-content-manifest.json').read_text())
    if p2man['outputs_sha256']['units.json'] != UNITS_SHA or p2man['inputs']['texts-v1/corpus.jsonl'] != CORPUS_SHA:
        stop('P2-T02 content manifest does not match the corpus')

    # 4. A3r1 relays (the gated C0 reference of each model)
    relays = pa / 'g03-a3r1-runpod'
    REPORT['relays'] = {}
    for m in MODELS:
        tp = relays / f'a3r1-{m}-relay.tar'
        rec = {'tar': tp.name, 'tar_sha256': fsha(tp)}
        sp = tp.with_name(tp.name + '.sha256')
        if sp.exists():
            want = sp.read_text().split()[0]
            rec['tar_sha256_recorded'] = want
            if want != rec['tar_sha256']:
                stop(f'{tp.name} sha256 differs from its .sha256')
        with tarfile.open(tp) as t:
            for pat in RELAY:
                rel = pat.format(m=m)
                ti = t.getmember('data/ptp-paper2/' + rel)
                (D / rel).parent.mkdir(parents=True, exist_ok=True)
                with t.extractfile(ti) as fi, open(D / rel, 'wb') as fo:
                    shutil.copyfileobj(fi, fo)
                files[m].append(rel)
        g = json.loads((D / f'bridgeret/logs/gate-{m}.json').read_text())
        ev = json.loads((D / f'bridgeret/evals-a3r1/z-{m}.json').read_text())
        if not g.get('gate_passed') or ev['block'] != 'P1-DEV' or ev['n_queries_run'] != 25626:
            stop(f'{m} relay: gate {g.get("gate_passed")}, block {ev["block"]}, n {ev["n_queries_run"]}')
        if fsha(D / f'bridgeret/runs/z-{m}/units.json') != UNITS_SHA:
            stop(f'{m} relay units.json is not the corpus order')
        rec.update({'gate_passed': True, 'ALL_R@200': ev['metrics']['ALL_R@200']['mean'],
                    'n_queries_run': ev['n_queries_run'], 'per_query': len(ev['per_query'])})
        REPORT['relays'][m] = rec

    # 5. code (repository, CRLF -> LF)
    for s in CODE:
        rel = 'p2-coverage/code/' + s
        (D / rel).parent.mkdir(parents=True, exist_ok=True)
        (D / rel).write_bytes((repo / 'scripts/research' / s).read_bytes().replace(b'\r\n', b'\n'))
        common.append(rel)

    # 6. claims filtered to the corpus documents
    need = sorted({json.loads(l)['doc'] for l in open(D / 'bridgeret/texts-v1/corpus.jsonl', encoding='utf-8')})
    need_p = out / 'need-docs.json'
    need_p.write_text(json.dumps(need))
    cdir = Path(a.claims_dir) if a.claims_dir else pa / 'pv-links/claims'
    srcs = sorted(cdir.glob('*_claims_*.tsv.zip'))
    if len(srcs) != 54:
        stop(f'{len(srcs)} claims files, expected 54')
    (D / 'patentsview/claims').mkdir(parents=True)
    jobs = [(str(s), str(D / 'patentsview/claims' / s.name)) for s in sorted(srcs, key=lambda p: -p.stat().st_size)]
    with ProcessPoolExecutor(a.workers, initializer=_init, initargs=(str(need_p), str(repo))) as ex:
        res = list(ex.map(_job, jobs))
    need_p.unlink()
    claims = []
    for r in sorted(res, key=lambda r: r['file']):
        claims.append('patentsview/claims/' + r['file'])
    REPORT['claims'] = {'files': len(res), 'docs_needed': len(need), 'rows_in': sum(r['rows_in'] for r in res),
                        'rows_kept': sum(r['rows_kept'] for r in res), 'bytes_in': sum(r['bytes_in'] for r in res),
                        'bytes_out': sum(r['bytes_out'] for r in res), 'per_file': sorted(res, key=lambda r: r['file'])}

    # 7. manifests and tar lists (LF)
    sha = {}
    for rel in common + claims + files['qwen3'] + files['patembed']:
        sha[rel] = fsha(D / rel)
    sizes = {}
    for m in MODELS:
        mrel = f'MANIFEST-d19-{m}.sha256'
        with open(D / mrel, 'w', encoding='utf-8', newline='\n') as f:
            for rel in sorted(common + claims + files[m]):
                f.write(f'{sha[rel]}  /data/ptp-paper2/{rel}\n')
        lst = sorted(common + files[m]) + [mrel]
        with open(out / f'FILES-{m}.txt', 'w', encoding='utf-8', newline='\n') as f:
            f.write(''.join(f'data/ptp-paper2/{rel}\n' for rel in lst))
        sizes[m] = sum((D / rel).stat().st_size for rel in lst)
    with open(out / 'FILES-claims.txt', 'w', encoding='utf-8', newline='\n') as f:
        f.write(''.join(f'data/ptp-paper2/{rel}\n' for rel in claims))
    REPORT['upload_bytes'] = {'claims_shared': sum((D / rel).stat().st_size for rel in claims), **sizes}
    REPORT['sha256'] = {rel: sha[rel] for rel in sorted(sha) if not rel.startswith('patentsview/')}
    REPORT['status'] = 'OK'
    REPORT['seconds'] = round(time.time() - t0, 1)
    (out / 'stage-report.json').write_text(json.dumps(REPORT, indent=1))
    print(json.dumps({k: REPORT[k] for k in ('status', 'upload_bytes', 'seconds')} |
                     {'claims': {k: v for k, v in REPORT['claims'].items() if k != 'per_file'}}, indent=1))


if __name__ == '__main__':
    try:
        main(sys.argv[1:])
    finally:
        if len(sys.argv) > 3 and Path(sys.argv[3]).is_dir() and REPORT.get('status', '').startswith('FAILED'):
            (Path(sys.argv[3]) / 'stage-report.json').write_text(json.dumps(REPORT, indent=1))
