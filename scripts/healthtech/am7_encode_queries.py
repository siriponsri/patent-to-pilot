"""AM-7 stage 2a: encode P1-DEV / VAL queries with the identical zero-shot settings of dense_bridgeret_v3.py and save
the vectors (fp16, L2-normalised) as Q-<BLOCK>.f16.npy + Q-<BLOCK>.ids.json. Refuses TEST blocks and any GPU other
than the approved V100 (CUDA_VISIBLE_DEVICES must expose it alone); takes the shared GPU lock.
Usage: python3 am7_encode_queries.py <model_dir> <pooling cls|last|mean> <query_prompt> <serialised_dir> <out_dir>
       <mem_fraction> BLOCK [BLOCK...]
"""
import fcntl, json, os, sys, time
from pathlib import Path

PROTECTED = {'P1-TEST', 'P2-TEST', 'P3-TEST'}
LOCK = '/home/chaw/patent-to-pilot-jobs/research-product-o1-o4-20261031/models/.GPU-277ccc57-c3e5-0731-cd49-f4f8695f7089.lock'
BS = int(os.environ.get('BS', '16'))


def main(argv):
    mdir, pooling, qprompt, sdir, out, frac = argv[:6]
    blocks = argv[6:]
    if set(blocks) & PROTECTED:
        raise SystemExit('refusing TEST blocks')
    import numpy as np, torch, torch.nn.functional as F
    from transformers import AutoModel, AutoTokenizer
    if torch.cuda.device_count() != 1 or 'V100' not in torch.cuda.get_device_name(0):
        raise SystemExit('refusing: set CUDA_VISIBLE_DEVICES to the approved V100 only')
    out = Path(out); out.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    lockf = open(LOCK, 'a'); fcntl.flock(lockf, fcntl.LOCK_EX)
    try:
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
                if pooling == 'mean':
                    m = b['attention_mask'].unsqueeze(-1).to(h.dtype); v = (h * m).sum(1) / m.sum(1)
                else:
                    v = h[:, 0] if pooling == 'cls' else h[:, -1]
                return F.normalize(v.float(), dim=-1).half().cpu().numpy()
        qs = [json.loads(l) for l in open(Path(sdir) / 'queries.jsonl', encoding='utf-8')]
        for blk in blocks:
            sel = [r for r in qs if r['block'] == blk]
            Q = np.concatenate([enc([qprompt + r['text'] for r in sel[s:s + BS]]) for s in range(0, len(sel), BS)])
            np.save(out / f'Q-{blk}.f16.npy', Q)
            (out / f'Q-{blk}.ids.json').write_text(json.dumps([r['app_id'] for r in sel]))
            print(blk, len(sel), round(time.time() - t0, 1), flush=True)
    finally:
        fcntl.flock(lockf, fcntl.LOCK_UN)
    print('done', round(time.time() - t0, 1))


if __name__ == '__main__':
    main(sys.argv[1:])
