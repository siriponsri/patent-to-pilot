"""G03 amendment 3: build the LLM routes H (HyDE with PatEmbed) and K (BM25 on the LLM text) for one model.

Protocol: docs/healthtech/research/g03-dev/G03-DEV-AMENDMENT-3-20261122.md §2. Runtime side only: reads the LLM ledger
(parsed priors and keywords), query texts and corpus vectors/passages, never labels. Refuses TEST blocks.

  sample  <runs_P1DEV_Fstar.tsv> <out_apps.json> [n]                 pilot sample (sha256('g03-a3-pilot-v1'+app_id))
  apps    <run_Fstar.tsv> <out_apps.json>                             every app of an F* run file
  dense   <name=ledger.jsonl,...> <model_dir> <ser_patembed_queries.jsonl> <passages.f16.npy> <units.json>
          <corpus-units.tsv> <tasks.tsv> <out_root> BLOCK [BLOCK...]   route H -> <out_root>/<name>/H (V100 only, GPU lock)
  bm25    <name=ledger.jsonl,...> <ser_dir> <corpus-units.tsv> <tasks.tsv> <out_root> BLOCK [BLOCK...]
                                                                       route K -> <out_root>/<name>/K (CPU, one index)

Settings are copied from dense_bridgeret_v3.py / queue_patembed.sh and bm25_bridgeret.py; masks: units first published on or
after the filing date, and the query's own unit.
"""
import csv, gzip, hashlib, json, os, sys, time
from pathlib import Path

PROTECTED = {'P1-TEST', 'P2-TEST', 'P3-TEST'}
LOCK = '/home/chaw/patent-to-pilot-jobs/research-product-o1-o4-20261031/models/.GPU-277ccc57-c3e5-0731-cd49-f4f8695f7089.lock'
QP = 'encode query for mixed document retrieval: '
DP = 'encode document for mixed retrieval: '
TOPK, BS, CHUNK = 1000, 16, 256
K1, B, QB = 1.5, 0.75, 64


def dint(s):
    return int(s.replace('-', '')[:8]) if s else 0


def check_blocks(blocks):
    if not blocks or set(blocks) & PROTECTED:
        raise SystemExit('refusing TEST blocks / no block given')


def apps_of(run_path):
    apps = set()
    with open(run_path, encoding='utf-8') as f:
        next(f)
        for line in f:
            apps.add(line.split('\t', 1)[0])
    return apps


def cmd_sample(argv):
    run_path, out = argv[0], argv[1]
    n = int(argv[2]) if len(argv) > 2 else 2000
    apps = sorted(apps_of(run_path), key=lambda a: hashlib.sha256(f'g03-a3-pilot-v1{a}'.encode()).hexdigest())[:n]
    Path(out).write_text(json.dumps(sorted(apps)))
    print('pilot sample', len(apps))


def cmd_apps(argv):
    apps = sorted(apps_of(argv[0]))
    Path(argv[1]).write_text(json.dumps(apps))
    print('apps', len(apps))


def load_ledger(path, blocks):
    """Latest usable parsed response per app (status ok)."""
    out = {}
    with open(path, encoding='utf-8') as f:
        for line in f:
            r = json.loads(line)
            if r.get('status') == 'ok' and r.get('block') in blocks:
                out[r['app_id']] = (r.get('priors') or [], r.get('keywords') or '')
    return out


def masks(units, units_p, tasks_p):
    import numpy as np
    pub = {}
    with open(units_p, encoding='utf-8') as f:
        for r in csv.DictReader(f, delimiter='\t'):
            pub[r['unit_id']] = dint(r['first_pub'])
    fd = {}
    with open(tasks_p, encoding='utf-8') as f:
        for r in csv.DictReader(f, delimiter='\t'):
            fd[r['app_id']] = dint(r['filing_date'])
    return np.array([pub[u] for u in units], dtype=np.int64), fd, {u: i for i, u in enumerate(units)}


def write_top(g, app, row, units, positive_only=False):
    import numpy as np
    top = np.argpartition(-row, TOPK)[:TOPK]
    top = top[np.lexsort((top, -row[top]))]
    g.write(''.join(f'{app}\t{k + 1}\t{units[j]}\t{row[j]:.5f}\n' for k, j in enumerate(top)
                    if np.isfinite(row[j]) and (not positive_only or row[j] > 0)))


def ledgers_of(spec):
    return [tuple(x.split('=', 1)) for x in spec.split(',') if x]


def cmd_dense(argv):
    spec, mdir, qpath, pfile, upath, units_p, tasks_p, out_root = argv[:8]
    blocks = argv[8:]
    check_blocks(blocks)
    for name, ledger in ledgers_of(spec):
        if (Path(out_root) / name / 'H' / f'run-{blocks[-1]}.tsv.gz').exists():
            print('skip H (exists)', name, flush=True)
            continue
        dense_one(mdir, ledger, qpath, pfile, upath, units_p, tasks_p, str(Path(out_root) / name / 'H'), blocks)
    print('G03_A3_H_DONE', flush=True)


def dense_one(mdir, ledger, qpath, pfile, upath, units_p, tasks_p, out, blocks):
    import fcntl
    import numpy as np, torch, torch.nn.functional as F
    from transformers import AutoModel, AutoTokenizer
    if torch.cuda.device_count() != 1 or 'V100' not in torch.cuda.get_device_name(0):
        raise SystemExit('refusing: set CUDA_VISIBLE_DEVICES to the approved V100 only')
    t0 = time.time()
    gen = load_ledger(ledger, set(blocks))
    qtext = {}
    with open(qpath, encoding='utf-8') as f:
        for line in f:
            r = json.loads(line)
            if r['block'] in blocks and r['app_id'] in gen:
                qtext[r['app_id']] = (r['block'], r['text'])
    vecs = {}
    lockf = open(LOCK, 'a'); fcntl.flock(lockf, fcntl.LOCK_EX)
    try:
        torch.cuda.set_per_process_memory_fraction(0.12, 0)
        tok = AutoTokenizer.from_pretrained(mdir, padding_side='right')
        model = AutoModel.from_pretrained(mdir, trust_remote_code=True, torch_dtype=torch.float16).cuda().eval()

        def enc(texts):
            outv = []
            for s in range(0, len(texts), BS):
                b = tok(texts[s:s + BS], padding=True, truncation=True, max_length=512, return_tensors='pt').to('cuda')
                with torch.inference_mode():
                    h = model(**b).last_hidden_state
                    m = b['attention_mask'].unsqueeze(-1).to(h.dtype)
                    outv.append(F.normalize(((h * m).sum(1) / m.sum(1)).float(), dim=-1).cpu().numpy())
            return np.concatenate(outv) if outv else np.zeros((0, 1), dtype=np.float32)
        for blk in blocks:
            apps = sorted(a for a, (b_, _) in qtext.items() if b_ == blk and gen[a][0])   # needs >= 1 prior
            eq = enc([QP + qtext[a][1] for a in apps])
            flat, owner = [], []
            for i, a in enumerate(apps):
                for p in gen[a][0]:
                    flat.append(DP + p); owner.append(i)
            ed = enc(flat)
            v = eq.copy()
            np.add.at(v, np.array(owner), ed)
            v /= np.linalg.norm(v, axis=1, keepdims=True)
            vecs[blk] = (apps, v.astype(np.float32))
            print(f'{time.time() - t0:7.1f}s encoded H {blk} {len(apps)} queries, {len(flat)} priors', flush=True)
    finally:
        fcntl.flock(lockf, fcntl.LOCK_UN)
        torch.cuda.empty_cache()
    units = json.loads(Path(upath).read_text())
    pubs, fd, uidx = masks(units, units_p, tasks_p)
    P = np.load(pfile).astype(np.float32)
    od = Path(out); od.mkdir(parents=True, exist_ok=True)
    for blk, (apps, Q) in vecs.items():
        tmp = od / f'run-{blk}.tsv.gz.tmp'
        with gzip.open(tmp, 'wt', encoding='utf-8') as g:
            g.write('app_id\trank\tunit\tscore\n')
            for s in range(0, len(apps), CHUNK):
                S = Q[s:s + CHUNK] @ P.T
                for i, row in enumerate(S):
                    a = apps[s + i]
                    row[pubs >= fd[a]] = -np.inf
                    own = uidx.get('A:' + a)
                    if own is not None:
                        row[own] = -np.inf
                    write_top(g, a, row, units)
        os.replace(tmp, od / f'run-{blk}.tsv.gz')
        print(f'{time.time() - t0:7.1f}s wrote H {blk} -> {out}', flush=True)


def cmd_bm25(argv):
    spec, sdir, units_p, tasks_p, out_root = argv[:5]
    blocks = argv[5:]
    check_blocks(blocks)
    import numpy as np
    from sklearn.feature_extraction.text import CountVectorizer
    t0 = time.time()
    todo = [(n, l) for n, l in ledgers_of(spec) if not (Path(out_root) / n / 'K' / f'run-{blocks[-1]}.tsv.gz').exists()]
    if not todo:
        print('G03_A3_K_DONE (nothing to do)', flush=True)
        return
    units, texts = [], []
    for line in open(Path(sdir) / 'passages.jsonl', encoding='utf-8'):
        r = json.loads(line)
        units.append(r['unit']); texts.append(r['text'])
    pubs, fd, uidx = masks(units, units_p, tasks_p)
    cv = CountVectorizer(token_pattern=r'[a-z0-9]+', lowercase=True, dtype=np.float32)
    tf = cv.fit_transform(texts).tocsr()
    del texts
    n = tf.shape[0]
    dl = np.asarray(tf.sum(axis=1)).ravel()
    df = np.bincount(tf.indices, minlength=tf.shape[1])
    idf = np.log1p((n - df + 0.5) / (df + 0.5)).astype(np.float32)
    norm = K1 * (1 - B + B * dl / dl.mean())
    rows = np.repeat(np.arange(n), np.diff(tf.indptr))
    tf.data = (tf.data * (K1 + 1) / (tf.data + norm[rows]) * idf[tf.indices]).astype(np.float32)
    W = tf.T.tocsr()
    print('index built', n, tf.shape[1], round(time.time() - t0, 1), flush=True)
    for name, ledger in todo:
      od = Path(out_root) / name / 'K'; od.mkdir(parents=True, exist_ok=True)
      for blk in blocks:                      # block membership comes from the ledger records
        gen = load_ledger(ledger, {blk})
        sel = sorted(a for a in gen if (gen[a][1] or gen[a][0]))
        tmp = od / f'run-{blk}.tsv.gz.tmp'
        with gzip.open(tmp, 'wt', encoding='utf-8') as g:
            g.write('app_id\trank\tunit\tscore\n')
            for s in range(0, len(sel), QB):
                chunk = sel[s:s + QB]
                Q = cv.transform([gen[a][1] + '\n' + '\n'.join(gen[a][0]) for a in chunk]).astype(np.float32)
                S = (Q @ W).toarray()
                for i, a in enumerate(chunk):
                    row = S[i]
                    row[pubs >= fd[a]] = -np.inf
                    own = uidx.get('A:' + a)
                    if own is not None:
                        row[own] = -np.inf
                    write_top(g, a, row, units, positive_only=True)
        os.replace(tmp, od / f'run-{blk}.tsv.gz')
        print(f'{time.time() - t0:7.1f}s wrote K {name} {blk} {len(sel)}', flush=True)
    print('G03_A3_K_DONE', flush=True)


if __name__ == '__main__':
    cmd, rest = sys.argv[1], sys.argv[2:]
    {'sample': cmd_sample, 'apps': cmd_apps, 'dense': cmd_dense, 'bm25': cmd_bm25}[cmd](rest)
