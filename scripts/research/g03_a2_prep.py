"""G03 amendment 2 prep: TRAIN sample (30,000) and the PatEmbed whole-query TRAIN route for it.

Sample (amendment 2 §1): TRAIN tasks with >= 1 ALL positive under the evaluator rules (cited unit first published before the
filing date, own unit excluded, unit in the corpus) and output from L, Q and A; the 30,000 smallest sha256('g03-a2-train-v1'
+ app_id). Labels are read here only to define eligibility (TRAIN block, developer-visible).
P route: exactly the z-patembed settings on ser-patembed-v1/queries.jsonl (approved V100 under the GPU lock; CPU retrieval).

Usage: python g03_a2_prep.py <bridgeret_dir> <c1m_out> <tasks.tsv> <model_dir> <out_dir>
"""
import csv, fcntl, gzip, hashlib, json, os, sys, time
from pathlib import Path

LOCK = '/home/chaw/patent-to-pilot-jobs/research-product-o1-o4-20261031/models/.GPU-277ccc57-c3e5-0731-cd49-f4f8695f7089.lock'
PROMPT, TOPK, BS, CHUNK, N = 'encode query for mixed document retrieval: ', 1000, 16, 256, 30000


def run_apps(p):
    apps = set()
    with gzip.open(p, 'rt', encoding='utf-8') as f:
        next(f)
        for line in f:
            apps.add(line.split('\t', 1)[0])
    return apps


def main(br, c1m, tasks_p, mdir, out):
    br, c1m, out = Path(br), Path(c1m), Path(out)
    out.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    corpus = set()
    with open(c1m / 'corpus-units.tsv', encoding='utf-8') as f:
        for r in csv.DictReader(f, delimiter='\t'):
            corpus.add(r['unit_id'])
    fd = {}
    with open(tasks_p, encoding='utf-8') as f:
        for r in csv.DictReader(f, delimiter='\t'):
            fd[r['app_id']] = r['filing_date']
    pos = set()
    with open(c1m / 'pairs-dev.tsv', encoding='utf-8') as f:
        for r in csv.DictReader(f, delimiter='\t'):
            if r['block'] != 'TRAIN' or not r['unit'] or not r['unit_first_pub']:
                continue
            a, u = r['app_id'], r['unit']
            if r['unit_first_pub'] < fd[a] and u != 'A:' + a and u in corpus:
                pos.add(a)
    have = run_apps(br / 'runs/bm25-train/run-TRAIN.tsv.gz') & run_apps(br / 'runs/z-qwen3/run-TRAIN.tsv.gz') \
        & run_apps(br / 'runs/z-arctic/run-TRAIN.tsv.gz')
    elig = sorted(pos & have, key=lambda a: hashlib.sha256(('g03-a2-train-v1' + a).encode()).hexdigest())[:N]
    (out / 'train-sample.json').write_text(json.dumps(sorted(elig)))
    print(f'{time.time() - t0:7.1f}s eligible {len(pos & have)} sample {len(elig)}', flush=True)
    want = set(elig)
    qs = [r for r in map(json.loads, open(br / 'ser-patembed-v1/queries.jsonl', encoding='utf-8'))
          if r['block'] == 'TRAIN' and r['app_id'] in want and r.get('text')]
    import numpy as np, torch, torch.nn.functional as F
    from transformers import AutoModel, AutoTokenizer
    if torch.cuda.device_count() != 1 or 'V100' not in torch.cuda.get_device_name(0):
        raise SystemExit('refusing: set CUDA_VISIBLE_DEVICES to the approved V100 only')
    lockf = open(LOCK, 'a'); fcntl.flock(lockf, fcntl.LOCK_EX)
    try:
        torch.cuda.set_per_process_memory_fraction(0.12, 0)
        tok = AutoTokenizer.from_pretrained(mdir, padding_side='right')
        model = AutoModel.from_pretrained(mdir, trust_remote_code=True, torch_dtype=torch.float16).cuda().eval()

        def enc(texts):
            b = tok(texts, padding=True, truncation=True, max_length=512, return_tensors='pt').to('cuda')
            with torch.inference_mode():
                h = model(**b).last_hidden_state
                m = b['attention_mask'].unsqueeze(-1).to(h.dtype)
                return F.normalize(((h * m).sum(1) / m.sum(1)).float(), dim=-1).cpu().numpy()
        Q = np.concatenate([enc([PROMPT + r['text'] for r in qs[s:s + BS]]) for s in range(0, len(qs), BS)])
    finally:
        fcntl.flock(lockf, fcntl.LOCK_UN)
    print(f'{time.time() - t0:7.1f}s encoded {len(qs)}', flush=True)
    units = json.loads((br / 'runs/z-patembed/units.json').read_text())
    P = np.load(br / 'runs/z-patembed/passages.f16.npy').astype(np.float32)
    d = out / 'z-patembed-train'
    d.mkdir(exist_ok=True)
    tmp = d / 'run-TRAIN.tsv.gz.tmp'
    with gzip.open(tmp, 'wt', encoding='utf-8') as f:
        f.write('app_id\trank\tunit\tscore\n')
        for s in range(0, len(qs), CHUNK):
            S = Q[s:s + CHUNK] @ P.T
            for i, row in enumerate(S):
                top = np.argpartition(-row, TOPK)[:TOPK]
                top = top[np.lexsort((top, -row[top]))]
                a = qs[s + i]['app_id']
                f.write(''.join(f'{a}\t{k + 1}\t{units[j]}\t{row[j]:.6f}\n' for k, j in enumerate(top)))
    os.replace(tmp, d / 'run-TRAIN.tsv.gz')
    print(f'{time.time() - t0:7.1f}s G03_A2_PREP_DONE', flush=True)


if __name__ == '__main__':
    main(*sys.argv[1:])
