"""P2-T02 amendment A1: stage the RunPod upload tree from local copies (owner PC). P1-DEV only; never opens TEST.

Writes <out>/data/ptp-paper2/... mirroring the dr-train paths (the pod runs the frozen scripts unchanged):
  splits/private/tasks.tsv                  app_id, block, filing_date for the 26,575 P1-DEV tasks (from am7 meta.pkl)
  manifest-v1/out-v2/manifest-p1dev.json    {"frozen": true, blocks: P1-DEV only; TRAIN/VAL/P2-DEV empty}
  challenge1m/out-v1/pairs-dev.tsv          P1-DEV rows only (the evaluator filters by block, so results are identical)
  challenge1m/out-v1/corpus-units.tsv       copied
  bridgeret/am7/prep-v1/meta.pkl            copied
  bridgeret/code/*.py                       the archived bridgeret scripts used for C0 + bridgeret_query.py (unchanged)
  bridgeret/archived-c0/                    texts-report.json, z-arctic/{units.json,eval-P1-DEV.json},
                                            bm25/eval-P1-DEV.json (P1-DEV evaluator records, for the rebuild gate)
  p2-coverage/code/                         p2t02_*.py, p2t02_queue.sh, p2t02_runpod.sh
PatentsView zips are not copied here; they are uploaded straight from data/raw/uspto (4 text files + 54 claims files).
The frozen dr-train manifest (which lists TEST tasks) is never read.

Usage: python -I p2t02_runpod_inputs.py <archive_ptp_paper2_dir> <repo_dir> <out_dir>
"""
import csv
import json
import pickle
import shutil
import sys
from pathlib import Path


def main(argv):
    src, repo, out = Path(argv[0]), Path(argv[1]), Path(argv[2]) / 'data/ptp-paper2'
    if out.exists():
        sys.exit(f'{out} exists')
    meta = pickle.load(open(src / 'bridgeret/am7/prep-v1/meta.pkl', 'rb'))
    q = meta['queries']['P1-DEV']
    apps = sorted({r['app'] for r in q})
    assert len(apps) == 26575, len(apps)
    fd = {r['app']: str(r['fd']) for r in q}
    (out / 'splits/private').mkdir(parents=True)
    with open(out / 'splits/private/tasks.tsv', 'w', encoding='utf-8', newline='\n') as f:
        f.write('app_id\tblock\tfiling_date\n')
        for a in apps:
            d = fd[a]
            f.write(f'{a}\tP1-DEV\t{d[:4]}-{d[4:6]}-{d[6:]}\n')
    (out / 'manifest-v1/out-v2').mkdir(parents=True)
    (out / 'manifest-v1/out-v2/manifest-p1dev.json').write_text(json.dumps({
        'frozen': True, 'note': 'amendment A1: P1-DEV subset rebuilt from am7/prep-v1/meta.pkl; TEST never included',
        'manifest_sha256': 'P1-DEV subset of c8443600d74fed015213237e070882efd1ddeefef7e66b6f3d6f7bb2f31e8039',
        'blocks': {'TRAIN': [], 'VAL': [], 'P1-DEV': apps, 'P2-DEV': []}}))
    c = out / 'challenge1m/out-v1'
    c.mkdir(parents=True)
    shutil.copy2(src / 'challenge1m/out-v1/corpus-units.tsv', c)
    n = 0
    with open(src / 'challenge1m/out-v1/pairs-dev.tsv', encoding='utf-8', newline='') as f, \
            open(c / 'pairs-dev.tsv', 'w', encoding='utf-8', newline='') as g:
        rd = csv.reader(f, delimiter='\t')
        wr = csv.writer(g, delimiter='\t', lineterminator='\n')
        head = next(rd)
        wr.writerow(head)
        bi = head.index('block')
        for r in rd:
            if r[bi] == 'P1-DEV':
                wr.writerow(r)
                n += 1
    b = out / 'bridgeret'
    (b / 'am7/prep-v1').mkdir(parents=True)
    shutil.copy2(src / 'bridgeret/am7/prep-v1/meta.pkl', b / 'am7/prep-v1')
    (b / 'code').mkdir()
    for s in ('build_bridgeret_texts.py', 'serialise_bridgeret_texts.py', 'dense_bridgeret.py', 'bm25_bridgeret.py', 'bridgeret_query.py',
              'eval_bridgeret_dev.py'):
        shutil.copy2(src / 'bridgeret/code' / s, b / 'code')
    a = b / 'archived-c0'
    (a / 'z-arctic').mkdir(parents=True)
    (a / 'bm25').mkdir()
    shutil.copy2(src / 'bridgeret/texts-v1/report.json', a / 'texts-report.json')
    for f in ('units.json', 'eval-P1-DEV.json'):
        shutil.copy2(src / 'bridgeret/runs/z-arctic' / f, a / 'z-arctic')
    shutil.copy2(src / 'bridgeret/runs/bm25/eval-P1-DEV.json', a / 'bm25')
    pc = out / 'p2-coverage/code'
    pc.mkdir(parents=True)
    for s in sorted((repo / 'scripts/research').glob('p2t02_*')):
        if s.suffix in ('.py', '.sh'):
            shutil.copy2(s, pc)
    print(json.dumps({'tasks_P1_DEV': len(apps), 'pairs_P1_DEV_rows': n, 'out': str(out)}))


if __name__ == '__main__':
    main(sys.argv[1:])
