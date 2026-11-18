"""Pilot data for the RunPod BridgeRet pilot: TRAIN-block only (public USPTO text, no DEV/TEST/DAPFAM).

2,000 TRAIN tasks by salted hash; per task: serialised query text, one positive passage (a TRAIN K(q) unit present
in the texts), 7 random passages from TRAIN positives of OTHER tasks (stand-ins for hard negatives; timing only).
Usage: python3 -I build_runpod_pilot_data.py <texts_dir> <pairs-dev.tsv> <out.jsonl.gz>
"""
import csv, gzip, hashlib, json, sys
from pathlib import Path

SALT = 'ptp-runpod-pilot-v1'
N = 2000


def h(x):
    return hashlib.sha256(f'{SALT}|{x}'.encode()).hexdigest()


def text(r):
    return '\n'.join(v for v in (r.get('title'), r.get('abstract'), r.get('claim')) if v)


def main(argv):
    d, pairs_p, out = Path(argv[0]), argv[1], argv[2]
    q = {}
    for l in open(d / 'queries.jsonl', encoding='utf-8'):
        r = json.loads(l)
        if r['block'] == 'TRAIN' and r.get('doc'):
            q[r['app_id']] = text(r)
    pos = {}
    with open(pairs_p, encoding='utf-8') as f:
        for r in csv.DictReader(f, delimiter='\t'):
            if r['block'] == 'TRAIN' and r['unit']:
                pos.setdefault(r['app_id'], []).append(r['unit'])
    need = {u for v in pos.values() for u in v}
    ptxt = {}
    for l in open(d / 'corpus.jsonl', encoding='utf-8'):
        r = json.loads(l)
        if r['unit'] in need:
            ptxt[r['unit']] = text(r)
    tasks = sorted((a for a in q if any(u in ptxt for u in pos.get(a, ()))), key=h)[:N]
    pool = sorted(ptxt, key=h)
    with gzip.open(out, 'wt', encoding='utf-8') as f:
        for i, a in enumerate(tasks):
            mine = set(pos[a])
            p = next(u for u in sorted(mine, key=h) if u in ptxt)
            negs = [u for u in pool[i * 13:i * 13 + 40] if u not in mine][:7]
            f.write(json.dumps({'q': q[a], 'p': ptxt[p], 'n': [ptxt[u] for u in negs]}) + '\n')
    print(json.dumps({'tasks': len(tasks), 'train_tasks_with_text': len(q), 'train_pairs': sum(len(v) for v in pos.values())}))


if __name__ == '__main__':
    main(sys.argv[1:])
