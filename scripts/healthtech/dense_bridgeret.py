"""Zero-shot (or checkpoint) dense retrieval over Challenge-1M for DEV/VAL blocks (never TEST).

Encodes serialised passages once (fp16, CLS or last-token pooling, L2-normalised) into <out>/passages.f16.npy,
encodes queries of the named blocks with the model's query prompt, retrieves on CPU by exact inner product with the
RPD mask (first_pub < filing date) and self-unit exclusion, writes run-<block>.tsv (top 1000).
GPU etiquette on the shared V100: per-process memory fraction cap, small batches, flock on the shared GPU lock.
Usage: python3 dense_bridgeret.py <model_dir> <pooling cls|last> <query_prompt> <serialised_dir> <corpus-units.tsv>
       <tasks.tsv> <out_dir> <mem_fraction> BLOCK [BLOCK...]
"""
import csv, fcntl, json, sys, time
from pathlib import Path

PROTECTED = {'P1-TEST', 'P2-TEST', 'P3-TEST'}
LOCK = '/home/chaw/patent-to-pilot-jobs/research-product-o1-o4-20261031/models/.GPU-277ccc57-c3e5-0731-cd49-f4f8695f7089.lock'
TOPK, BS = 1000, 64


def main(argv):
    mdir, pooling, qprompt, sdir, units_p, tasks_p, out, frac = argv[:8]
    blocks = set(argv[8:])
    if blocks & PROTECTED:
        raise SystemExit('dense dev script refuses TEST blocks')
    import numpy as np, torch, torch.nn.functional as F
    from transformers import AutoModel, AutoTokenizer
    out = Path(out); out.mkdir(parents=True, exist_ok=True); sdir = Path(sdir)
    t0 = time.time()
    lockf = open(LOCK, 'a'); fcntl.flock(lockf, fcntl.LOCK_EX)
    torch.cuda.set_per_process_memory_fraction(float(frac), 0)
    tok = AutoTokenizer.from_pretrained(mdir, padding_side='left' if pooling == 'last' else 'right')
    kw = dict(trust_remote_code=True, torch_dtype=torch.float16)
    if pooling == 'cls':
        kw.update(use_memory_efficient_attention=False, unpad_inputs=False)
    model = AutoModel.from_pretrained(mdir, **kw).cuda().eval()

    def enc(texts):
        b = tok(texts, padding=True, truncation=True, max_length=512, return_tensors='pt').to('cuda')
        with torch.inference_mode():
            h = model(**b).last_hidden_state
            v = h[:, 0] if pooling == 'cls' else h[:, -1]
            return F.normalize(v.float(), dim=-1).half().cpu().numpy()

    units = []
    pfile = out / 'passages.f16.npy'
    if not pfile.exists():
        texts = []
        for l in open(sdir / 'passages.jsonl', encoding='utf-8'):
            r = json.loads(l); units.append(r['unit']); texts.append(r['text'])
        order = sorted(range(len(texts)), key=lambda i: len(texts[i]))          # length-sorted batches
        P = np.zeros((len(texts), model.config.hidden_size), dtype=np.float16)
        for s in range(0, len(order), BS):
            idx = order[s:s + BS]; P[idx] = enc([texts[i] for i in idx])
            if s % (BS * 2000) == 0:
                print('passages', s, round(time.time() - t0, 1), flush=True)
        np.save(pfile, P); (out / 'units.json').write_text(json.dumps(units))
        print('passages done', round(time.time() - t0, 1), flush=True)
    else:
        units = json.loads((out / 'units.json').read_text()); P = np.load(pfile)
    pub = {}
    with open(units_p, encoding='utf-8') as f:
        for r in csv.DictReader(f, delimiter='\t'):
            pub[r['unit_id']] = int(r['first_pub'].replace('-', ''))
    pubs = np.array([pub[u] for u in units]); uidx = {u: i for i, u in enumerate(units)}
    fd = {}
    with open(tasks_p, encoding='utf-8') as f:
        for r in csv.DictReader(f, delimiter='\t'):
            fd[r['app_id']] = int(r['filing_date'].replace('-', ''))
    qs = [json.loads(l) for l in open(sdir / 'queries.jsonl', encoding='utf-8')]
    Pf = P.astype(np.float32)
    for blk in sorted(blocks):
        sel = [r for r in qs if r['block'] == blk]
        Q = np.concatenate([enc([qprompt + r['text'] for r in sel[s:s + BS]]) for s in range(0, len(sel), BS)]).astype(np.float32)
        print(blk, 'queries encoded', len(sel), round(time.time() - t0, 1), flush=True)
        with open(out / f'run-{blk}.tsv', 'w', encoding='utf-8') as g:
            g.write('app_id\trank\tunit\tscore\n')
            for s in range(0, len(sel), 512):
                S = Q[s:s + 512] @ Pf.T
                for i, r in enumerate(sel[s:s + 512]):
                    row = S[i]; row[pubs >= fd[r['app_id']]] = -np.inf
                    own = uidx.get('A:' + r['app_id'])
                    if own is not None: row[own] = -np.inf
                    top = np.argpartition(-row, TOPK)[:TOPK]; top = top[np.lexsort((top, -row[top]))]
                    g.write(''.join(f"{r['app_id']}\t{k + 1}\t{units[j]}\t{row[j]:.5f}\n" for k, j in enumerate(top) if np.isfinite(row[j])))
        print(blk, 'retrieved', round(time.time() - t0, 1), flush=True)
    fcntl.flock(lockf, fcntl.LOCK_UN)
    print('done', round(time.time() - t0, 1))


if __name__ == '__main__':
    main(sys.argv[1:])
