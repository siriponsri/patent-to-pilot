"""G03 amendment 1: field-obligation routes T (title+abstract) and C (first independent claim) with PatEmbed-large.

Settings identical to z-patembed (mean pooling, prompt 'encode query for mixed document retrieval: ', 512 tokens, fp16,
L2-normalised). Encoding on the approved V100 only (CUDA_VISIBLE_DEVICES must expose it alone) under the shared GPU lock;
exact inner-product retrieval on CPU against the existing z-patembed passages (top 1000; ties score desc then unit order).
Refuses TEST blocks. Runtime side: reads query texts and corpus vectors only, never labels.

Usage: python g03_field_routes.py <model_dir> <texts_queries.jsonl> <passages.f16.npy> <units.json> <out_root> BLOCK [BLOCK...]
"""
import fcntl, gzip, json, os, sys, time
from pathlib import Path

PROTECTED = {'P1-TEST', 'P2-TEST', 'P3-TEST'}
LOCK = '/home/chaw/patent-to-pilot-jobs/research-product-o1-o4-20261031/models/.GPU-277ccc57-c3e5-0731-cd49-f4f8695f7089.lock'
PROMPT = 'encode query for mixed document retrieval: '
TOPK, BS, CHUNK = 1000, 16, 256
FIELDS = {'z-patembed-ta': lambda r: f"{r.get('title') or ''}\n{r.get('abstract') or ''}".strip(),
          'z-patembed-claim': lambda r: r.get('claim') or ''}   # missing fields (no pgpub) stay empty, never invented


def main(argv):
    mdir, qpath, pfile, upath, out_root = argv[:5]
    blocks = argv[5:]
    if set(blocks) & PROTECTED or not blocks:
        raise SystemExit('refusing TEST blocks / no block given')
    import numpy as np, torch, torch.nn.functional as F
    from transformers import AutoModel, AutoTokenizer
    if torch.cuda.device_count() != 1 or 'V100' not in torch.cuda.get_device_name(0):
        raise SystemExit('refusing: set CUDA_VISIBLE_DEVICES to the approved V100 only')
    t0 = time.time()
    rows = [r for r in map(json.loads, open(qpath, encoding='utf-8')) if r['block'] in blocks]
    vecs = {}
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
                v = (h * m).sum(1) / m.sum(1)
                return F.normalize(v.float(), dim=-1).cpu().numpy()
        for route, field in FIELDS.items():
            for blk in blocks:
                # a query without text for this field gets no output (scores 0), like the whole-query routes
                sel = [r for r in rows if r['block'] == blk and field(r)]
                texts = [PROMPT + field(r) for r in sel]
                vecs[(route, blk)] = ([r['app_id'] for r in sel],
                                      np.concatenate([enc(texts[s:s + BS]) for s in range(0, len(texts), BS)]))
                print(f'{time.time() - t0:7.1f}s encoded {route} {blk} {len(sel)}', flush=True)
    finally:
        fcntl.flock(lockf, fcntl.LOCK_UN)
        del model
        torch.cuda.empty_cache()
    units = json.loads(Path(upath).read_text())
    P = np.load(pfile).astype(np.float32)
    print(f'{time.time() - t0:7.1f}s loaded passages {P.shape}', flush=True)
    for (route, blk), (apps, Q) in vecs.items():
        d = Path(out_root) / route
        d.mkdir(parents=True, exist_ok=True)
        tmp = d / f'run-{blk}.tsv.gz.tmp'
        with gzip.open(tmp, 'wt', encoding='utf-8') as f:
            f.write('app_id\trank\tunit\tscore\n')
            for s in range(0, len(apps), CHUNK):
                S = Q[s:s + CHUNK] @ P.T
                for i, row in enumerate(S):
                    top = np.argpartition(-row, TOPK)[:TOPK]
                    top = top[np.lexsort((top, -row[top]))]
                    a = apps[s + i]
                    f.write(''.join(f'{a}\t{k + 1}\t{units[j]}\t{row[j]:.6f}\n' for k, j in enumerate(top)))
        os.replace(tmp, d / f'run-{blk}.tsv.gz')
        print(f'{time.time() - t0:7.1f}s wrote {route} {blk}', flush=True)
    print('G03_FIELD_ROUTES_DONE', flush=True)


if __name__ == '__main__':
    main(sys.argv[1:])
