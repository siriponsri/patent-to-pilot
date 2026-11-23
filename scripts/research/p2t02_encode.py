"""P2-T02 step 2 (GPU): Arctic encodings with the z-arctic settings (protocol §4, frozen bd30d3f7).

Settings copied from bridgeret/code/dense_bridgeret.py as run for runs/z-arctic (zarctic.time): model
/data/ptp-paper2/models/arctic-embed-m-v2.0, fp16, trust_remote_code, use_memory_efficient_attention=False,
unpad_inputs=False, CLS pooling, L2-normalised, stored fp16, padding right, max 512 positions, batch 64, query prompt
"query: ", no document prompt. Shared V100 etiquette: CUDA_VISIBLE_DEVICES=1 (the V100), fcntl lock on the shared GPU
lock file, torch.cuda.set_per_process_memory_fraction(<= 0.12, 0).

Subcommands (each takes the lock for its whole run):
  queries   : encode the P1-DEV queries of ser-arctic-v1/queries.jsonl in file order, batches of 64 in that order,
              text path tok(prompt + text) exactly as dense_bridgeret.py -> <out>/P1-DEV.f16.npy + P1-DEV.apps.json
  passages  : encode a C1/C2 arm from token ids: input = CLS + window ids + SEP (the identical tokens the text path
              would give; see validate). Length-sorted batches, checkpointed in shards -> <out>/passages.f16.npy
  validate  : id path vs the stored C0 vectors (runs/z-arctic/passages.f16.npy) on the first N C0 passages: the C0
              serialised text is tokenised without special tokens and encoded through the id path; reports cosine.
Never reads TEST (only the P1-DEV block is accepted).
Usage: python p2t02_encode.py queries  --ser <ser-arctic-v1> --out <qdir> [--limit N]
       python p2t02_encode.py passages --arm <content_dir> --name c1|c2 --out <encdir>
       python p2t02_encode.py validate --ser <ser-arctic-v1> --c0 <runs/z-arctic> --n 2048 --out <json>
"""
from __future__ import annotations

import argparse
import fcntl
import json
import os
import time
from pathlib import Path

MODEL = '/data/ptp-paper2/models/arctic-embed-m-v2.0'
LOCK = '/home/chaw/patent-to-pilot-jobs/research-product-o1-o4-20261031/models/.GPU-277ccc57-c3e5-0731-cd49-f4f8695f7089.lock'
QPROMPT = 'query: '
BS = 64
SHARD = 262144
ALLOWED = {'P1-DEV'}
PROTECTED = {'P1-TEST', 'P2-TEST', 'P3-TEST'}


def setup(frac):
    # dr-train: the V100 is device 1. A dedicated single-GPU RunPod pod (amendment A1) sets P2T02_EXPECT_GPU=0.
    want = os.environ.get('P2T02_EXPECT_GPU', '1')
    assert os.environ.get('CUDA_VISIBLE_DEVICES') == want, f'expected CUDA_VISIBLE_DEVICES={want}'
    assert float(frac) <= 0.12
    import torch
    lockf = open(LOCK, 'a')
    t = time.time()
    fcntl.flock(lockf, fcntl.LOCK_EX)
    print(f'GPU lock acquired after {time.time() - t:.1f}s', flush=True)
    torch.cuda.set_per_process_memory_fraction(float(frac), 0)
    print(f'memory fraction {frac} set on {torch.cuda.get_device_name(0)}', flush=True)
    from transformers import AutoModel, AutoTokenizer
    tok = AutoTokenizer.from_pretrained(MODEL, padding_side='right')
    model = AutoModel.from_pretrained(MODEL, trust_remote_code=True, torch_dtype=torch.float16,
                                      use_memory_efficient_attention=False, unpad_inputs=False).cuda().eval()
    return lockf, tok, model


def make_enc(tok, model):
    import torch
    import torch.nn.functional as F

    def enc_text(texts):   # identical to dense_bridgeret.py enc() with pooling 'cls'
        b = tok(texts, padding=True, truncation=True, max_length=512, return_tensors='pt').to('cuda')
        with torch.inference_mode():
            h = model(**b).last_hidden_state
            v = h[:, 0]
            return F.normalize(v.float(), dim=-1).half().cpu().numpy()

    cls_id, sep_id, pad_id = tok.cls_token_id, tok.sep_token_id, tok.pad_token_id

    def enc_ids(seqs):     # same tensors the text path builds: [CLS] ids [SEP], right padding, attention mask
        L = max(len(s) for s in seqs) + 2
        assert L <= 512
        ids = torch.full((len(seqs), L), pad_id, dtype=torch.long)
        am = torch.zeros((len(seqs), L), dtype=torch.long)
        for i, s in enumerate(seqs):
            n = len(s)
            ids[i, 0] = cls_id
            ids[i, 1:n + 1] = torch.as_tensor(s.astype('int64'))
            ids[i, n + 1] = sep_id
            am[i, :n + 2] = 1
        with torch.inference_mode():
            h = model(input_ids=ids.cuda(), attention_mask=am.cuda()).last_hidden_state
            v = h[:, 0]
            return F.normalize(v.float(), dim=-1).half().cpu().numpy()

    return enc_text, enc_ids


def cmd_queries(a):
    import numpy as np, torch
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    sel = []
    for l in open(Path(a.ser) / 'queries.jsonl', encoding='utf-8'):
        r = json.loads(l)
        assert r['block'] not in PROTECTED
        if r['block'] in ALLOWED:
            sel.append(r)
    if a.limit:
        sel = sel[:a.limit]
    lockf, tok, model = setup(a.frac)
    enc_text, _ = make_enc(tok, model)
    Q = np.concatenate([enc_text([QPROMPT + r['text'] for r in sel[s:s + BS]]) for s in range(0, len(sel), BS)])
    np.save(out / 'P1-DEV.f16.npy', Q)
    (out / 'P1-DEV.apps.json').write_text(json.dumps([r['app_id'] for r in sel]))
    print(f'queries encoded {len(sel)} in {time.time() - t0:.1f}s; peak GPU mem '
          f'{torch.cuda.max_memory_allocated(0) / 2**30:.2f} GiB', flush=True)
    fcntl.flock(lockf, fcntl.LOCK_UN)
    (out / 'DONE').write_text('ok')
    print('QUERIES_DONE', flush=True)


def cmd_passages(a):
    import numpy as np, torch
    arm, out = Path(a.arm), Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    ln = np.load(arm / f'{a.name}.len.npy').astype(np.int64)
    off = np.zeros(ln.size + 1, dtype=np.int64); np.cumsum(ln, out=off[1:])
    ids = np.memmap(arm / f'{a.name}.ids.u32', dtype=np.uint32, mode='r')
    assert ids.size == off[-1]
    n = ln.size
    order = np.argsort(ln, kind='stable')                 # length-sorted batches
    nsh = (n + SHARD - 1) // SHARD
    print(f'{a.name}: {n} passages, {int(off[-1])} tokens, {nsh} shards', flush=True)
    lockf, tok, model = setup(a.frac)
    _, enc_ids = make_enc(tok, model)
    t1 = time.time()
    done = 0
    for k in range(nsh):
        sp = out / f'shard-{k:03d}.npy'
        idx = order[k * SHARD:(k + 1) * SHARD]
        if sp.exists():
            done += idx.size
            continue
        V = np.zeros((idx.size, model.config.hidden_size), dtype=np.float16)
        for s in range(0, idx.size, BS):
            b = idx[s:s + BS]
            V[s:s + b.size] = enc_ids([np.asarray(ids[off[i]:off[i + 1]]) for i in b])
        np.save(out / f'shard-{k:03d}.tmp.npy', V)
        os.replace(out / f'shard-{k:03d}.tmp.npy', sp)
        done += idx.size
        el = time.time() - t1
        print(f'{a.name} shard {k + 1}/{nsh} done: {done}/{n} passages, {el:.0f}s, '
              f'{done / max(el, 1e-9):.1f} passages/s, peak GPU mem {torch.cuda.max_memory_allocated(0) / 2**30:.2f} GiB',
              flush=True)
    fcntl.flock(lockf, fcntl.LOCK_UN)
    print(f'GPU lock released; encode seconds {time.time() - t1:.1f}', flush=True)
    P = np.zeros((n, 768), dtype=np.float16)
    for k in range(nsh):
        P[order[k * SHARD:(k + 1) * SHARD]] = np.load(out / f'shard-{k:03d}.npy')
    assert np.all(np.isfinite(P.astype(np.float32).sum(1)))
    np.save(out / 'passages.tmp.npy', P)
    os.replace(out / 'passages.tmp.npy', out / 'passages.f16.npy')
    for k in range(nsh):
        (out / f'shard-{k:03d}.npy').unlink()
    (out / 'encode.json').write_text(json.dumps({'arm': a.name, 'passages': int(n), 'tokens': int(off[-1]),
                                                 'encode_seconds': round(time.time() - t1, 1),
                                                 'total_seconds': round(time.time() - t0, 1),
                                                 'peak_gpu_mem_gib': round(torch.cuda.max_memory_allocated(0) / 2**30, 3),
                                                 'bs': BS, 'mem_fraction': float(a.frac)}, indent=1))
    (out / 'DONE').write_text('ok')
    print(f'ENCODE_{a.name.upper()}_DONE', round(time.time() - t0, 1), flush=True)


def cmd_validate(a):
    import numpy as np
    t0 = time.time()
    texts = []
    with open(Path(a.ser) / 'passages.jsonl', encoding='utf-8') as f:
        for i, l in enumerate(f):
            if i >= a.n:
                break
            texts.append(json.loads(l)['text'])
    ref = np.load(Path(a.c0) / 'passages.f16.npy', mmap_mode='r')[:len(texts)].astype(np.float32)
    lockf, tok, model = setup(a.frac)
    enc_text, enc_ids = make_enc(tok, model)
    seqs = [np.asarray(x, dtype=np.uint32) for x in tok(texts, add_special_tokens=False)['input_ids']]
    order = np.argsort([len(s) for s in seqs], kind='stable')
    V = np.zeros((len(texts), 768), dtype=np.float16)
    T = np.zeros((len(texts), 768), dtype=np.float16)
    for s in range(0, len(order), BS):
        b = order[s:s + BS]
        V[b] = enc_ids([seqs[i] for i in b])
        T[b] = enc_text([texts[i] for i in b])
    fcntl.flock(lockf, fcntl.LOCK_UN)
    cos_ids = (V.astype(np.float32) * ref).sum(1)
    cos_txt = (T.astype(np.float32) * ref).sum(1)
    res = {'n': len(texts), 'max_len_tokens': int(max(len(s) for s in seqs)),
           'cos_idpath_vs_stored_c0': {'min': float(cos_ids.min()), 'mean': float(cos_ids.mean())},
           'cos_textpath_vs_stored_c0': {'min': float(cos_txt.min()), 'mean': float(cos_txt.mean())},
           'idpath_equals_textpath_bitwise_share': float(np.mean(np.all(V == T, axis=1))),
           'seconds': round(time.time() - t0, 1)}
    res['passed'] = bool(res['cos_idpath_vs_stored_c0']['min'] > 0.999)
    Path(a.out).write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))
    print('VALIDATE_DONE' if res['passed'] else 'VALIDATE_FAILED', flush=True)
    if not res['passed']:
        raise SystemExit(1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', choices=('queries', 'passages', 'validate'))
    ap.add_argument('--ser'); ap.add_argument('--arm'); ap.add_argument('--name'); ap.add_argument('--c0')
    ap.add_argument('--out', required=True)
    ap.add_argument('--limit', type=int, default=0)
    ap.add_argument('--n', type=int, default=2048)
    ap.add_argument('--frac', default='0.12')
    a = ap.parse_args()
    {'queries': cmd_queries, 'passages': cmd_passages, 'validate': cmd_validate}[a.cmd](a)


if __name__ == '__main__':
    main()
