"""P2-T02 amendment A2 (owner D19): complete-content C1 encodings for Qwen3 and PatEmbed with each model's own C0 settings.

Amendment: docs/healthtech/research/p2-coverage/P2-T02-AMENDMENT-A2-D19-FOLLOWUP.md. P1-DEV only; never reads VAL or TEST.

C0 settings copied from the archived dr-train scripts and the archived commands (*.time), as rebuilt and gated on RunPod
for A3r1 (A3R1-AMENDMENT-RUNPOD-REBUILD.md):
  qwen3     dense_bridgeret_v2.py, Qwen/Qwen3-Embedding-0.6B @97b0c614, last-token pooling, LEFT padding, fp16,
            trust_remote_code, query prompt "Instruct: Given a patent application, retrieve prior art cited against it\\n
            Query: ", no document prompt, max 512 positions (special tokens counted), L2-normalised, stored fp16.
  patembed  dense_bridgeret_v3.py, datalyes/patembed-large @2d5c0f92, mean pooling over the attention mask (in the model
            dtype, as C0), RIGHT padding, fp16, trust_remote_code, query prompt "encode query for mixed document
            retrieval: ", document prompt "encode document for mixed retrieval: " (counted inside the 512 cap).
The text path enc_text() is the C0 enc() verbatim. The id path enc_ids() feeds C1 windows from token ids and builds the
same tensors the text path would build for (document prompt + window text): head = the tokenizer's own leading special
tokens + document-prompt ids, tail = its trailing special tokens, both derived from the tokenizer itself (special_wrap).
`validate` proves on the pod that head + ids + tail equals the text-path tokens (100% required) and that the id path gives
the text-path vectors.

Subcommands
  window   (CPU) head/tail/prompt ids and the content window W = 512 - |head| - |tail| -> window.json. The content build
           runs with P2T02_WIN=W, so a window never exceeds the model's 512 positions.
  validate (GPU) first N C0 serialised passages: text path vs id path (tokens identical for 100%; vectors min cos > 0.9999).
  c0check  (GPU) score reproduction against the gated C0 run (A3r1 relay): first --nq P1-DEV queries of the run, their top
           --k units; this pod's text-path query and C0-passage vectors must reproduce the recorded scores
           (median |d| <= 0.001 and share(|d| <= 0.005) >= 0.99). Proves weights, prompts, pooling and padding on this pod.
  queries  (GPU) P1-DEV queries of ser-<model>-v1/queries.jsonl in file order, text path -> P1-DEV.f16.npy + apps.json
  passages (GPU) a content arm (c1) from token ids, length-sorted batches, checkpointed shards -> passages.f16.npy
Batch size P2T02_D19_BS (default the C0 value: qwen3 8, patembed 16) and the memory fraction (--frac) change speed only.
Usage: python p2t02_d19_encode.py <cmd> --model qwen3|patembed [--model-dir DIR] --out OUT [...]
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import time
from pathlib import Path

JOBS = '/home/chaw/patent-to-pilot-jobs/research-product-o1-o4-20261031'
LOCK = JOBS + '/models/.GPU-277ccc57-c3e5-0731-cd49-f4f8695f7089.lock'
MODELS = {
    'qwen3': {'dir': '/data/ptp-paper2/models/qwen3-embedding-0.6b', 'pooling': 'last',
              'qprompt': 'Instruct: Given a patent application, retrieve prior art cited against it\nQuery: ',
              'dprompt': '', 'ser': 'ser-qwen3-v1', 'c0_script': 'dense_bridgeret_v2.py', 'c0_bs': 8,
              'revision': 'Qwen/Qwen3-Embedding-0.6B@97b0c614be4d77ee51c0cef4e5f07c00f9eb65b3'},
    'patembed': {'dir': JOBS + '/models/patembed-large', 'pooling': 'mean',
                 'qprompt': 'encode query for mixed document retrieval: ',
                 'dprompt': 'encode document for mixed retrieval: ', 'ser': 'ser-patembed-v1',
                 'c0_script': 'dense_bridgeret_v3.py', 'c0_bs': 16,
                 'revision': 'datalyes/patembed-large@2d5c0f92a3e5dc3d5415c08e612c57543c0e03ad'},
}
MAXLEN = 512
SHARD = 262144
ALLOWED = {'P1-DEV'}
PROTECTED = {'P1-TEST', 'P2-TEST', 'P3-TEST'}
PROBES = ('patent claim probe text', 'A method of making a widget, comprising: heating the widget.')


def fsha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 22), b''):
            h.update(b)
    return h.hexdigest()


# ------------------------------------------------------------------ pure helpers (tested without a GPU)
def special_wrap(tok):
    """(prefix, suffix): the special tokens the tokenizer itself adds around a text (add_special_tokens=True)."""
    found = None
    for p in PROBES:
        w = list(tok(p, add_special_tokens=True)['input_ids'])
        wo = list(tok(p, add_special_tokens=False)['input_ids'])
        hit = [i for i in range(len(w) - len(wo) + 1) if w[i:i + len(wo)] == wo]
        assert hit, f'tokenizer wraps the probe in a way that is not prefix + text + suffix: {w} vs {wo}'
        cur = (w[:hit[0]], w[hit[0] + len(wo):])
        assert found is None or cur == found, f'special tokens depend on the text: {cur} vs {found}'
        found = cur
    return found


def wrap_spec(tok, dprompt):
    prefix, suffix = special_wrap(tok)
    prompt = list(tok(dprompt, add_special_tokens=False)['input_ids']) if dprompt else []
    head = prefix + prompt
    return {'prefix_ids': prefix, 'prompt_ids': prompt, 'suffix_ids': suffix, 'head_ids': head, 'tail_ids': suffix,
            'window': MAXLEN - len(head) - len(suffix), 'max_positions': MAXLEN}


def pack_batch(seqs, head, tail, pad_id, left):
    """input_ids / attention_mask (numpy int64) for head + seq + tail, padded to the batch maximum on the C0 side."""
    import numpy as np
    full = [list(head) + [int(x) for x in s] + list(tail) for s in seqs]
    L = max(len(x) for x in full)
    assert L <= MAXLEN, L
    ids = np.full((len(full), L), pad_id, dtype=np.int64)
    am = np.zeros((len(full), L), dtype=np.int64)
    for i, x in enumerate(full):
        n = len(x)
        if left:
            ids[i, L - n:] = x
            am[i, L - n:] = 1
        else:
            ids[i, :n] = x
            am[i, :n] = 1
    return ids, am


def score_check(new, rec):
    """c0check comparison: new and recorded scores (same pairs)."""
    import numpy as np
    d = np.abs(np.asarray(new, dtype=np.float64) - np.asarray(rec, dtype=np.float64))
    res = {'pairs': int(d.size), 'abs_diff_median': float(np.median(d)), 'abs_diff_p99': float(np.percentile(d, 99)),
           'abs_diff_max': float(d.max()), 'share_abs_diff_le_0.002': float(np.mean(d <= 0.002)),
           'share_abs_diff_le_0.005': float(np.mean(d <= 0.005))}
    res['passed'] = bool(res['abs_diff_median'] <= 0.001 and res['share_abs_diff_le_0.005'] >= 0.99)
    return res


def row_cosines(a, b):
    import numpy as np
    a, b = a.astype(np.float64), b.astype(np.float64)
    norms = np.linalg.norm(a, axis=1) * np.linalg.norm(b, axis=1)
    if not np.all(np.isfinite(norms) & (norms > 0)):
        raise ValueError('cosine validation requires finite nonzero vectors')
    return (a * b).sum(axis=1) / norms
# ------------------------------------------------------------------


def cfg(a):
    c = dict(MODELS[a.model])
    if a.model_dir:
        c['dir'] = a.model_dir
    c['bs'] = int(os.environ.get('P2T02_D19_BS') or c['c0_bs'])
    return c


def tokenizer(c):
    from transformers import AutoTokenizer
    return AutoTokenizer.from_pretrained(c['dir'], padding_side='left' if c['pooling'] == 'last' else 'right')


def unlock(lockf):
    import fcntl
    fcntl.flock(lockf, fcntl.LOCK_UN)


def setup(c, frac):
    # dr-train: the V100 is device 1. A dedicated single-GPU RunPod pod sets P2T02_EXPECT_GPU=0 (as amendment A1).
    want = os.environ.get('P2T02_EXPECT_GPU', '1')
    assert os.environ.get('CUDA_VISIBLE_DEVICES') == want, f'expected CUDA_VISIBLE_DEVICES={want}'
    assert 0 < float(frac) <= 0.9
    import fcntl
    import torch
    Path(LOCK).parent.mkdir(parents=True, exist_ok=True)
    lockf = open(LOCK, 'a')
    t = time.time()
    fcntl.flock(lockf, fcntl.LOCK_EX)
    print(f'GPU lock acquired after {time.time() - t:.1f}s', flush=True)
    torch.cuda.set_per_process_memory_fraction(float(frac), 0)
    print(f'memory fraction {frac} set on {torch.cuda.get_device_name(0)}; batch size {c["bs"]}', flush=True)
    from transformers import AutoModel
    tok = tokenizer(c)
    kw = dict(trust_remote_code=True, torch_dtype=torch.float16)          # the C0 kwargs for pooling last / mean
    model = AutoModel.from_pretrained(c['dir'], **kw).cuda().eval()
    return lockf, tok, model


def make_enc(c, tok, model, spec):
    import torch
    import torch.nn.functional as F
    pooling = c['pooling']

    def pool(h, am):
        if pooling == 'mean':                                             # dense_bridgeret_v3.py, verbatim
            m = am.unsqueeze(-1).to(h.dtype)
            return (h * m).sum(1) / m.sum(1)
        return h[:, 0] if pooling == 'cls' else h[:, -1]

    def enc_text(texts):   # C0 enc(): caller adds the prompt
        b = tok(texts, padding=True, truncation=True, max_length=MAXLEN, return_tensors='pt').to('cuda')
        with torch.inference_mode():
            h = model(**b).last_hidden_state
            return F.normalize(pool(h, b['attention_mask']).float(), dim=-1).half().cpu().numpy()

    def enc_ids(seqs):
        ids, am = pack_batch(seqs, spec['head_ids'], spec['tail_ids'], tok.pad_token_id, pooling == 'last')
        ids, am = torch.from_numpy(ids).cuda(), torch.from_numpy(am).cuda()
        with torch.inference_mode():
            h = model(input_ids=ids, attention_mask=am).last_hidden_state
            return F.normalize(pool(h, am).float(), dim=-1).half().cpu().numpy()

    return enc_text, enc_ids


def p1dev_queries(ser):
    sel = []
    for l in open(Path(ser) / 'queries.jsonl', encoding='utf-8'):
        r = json.loads(l)
        if r['block'] in PROTECTED:
            raise SystemExit('TEST block present in queries.jsonl: refused')
        if r['block'] in ALLOWED:
            sel.append(r)
    return sel


def cmd_window(a):
    c = cfg(a)
    tok = tokenizer(c)
    spec = wrap_spec(tok, c['dprompt'])
    spec.update({'model': a.model, 'revision': c['revision'], 'model_dir': c['dir'], 'pooling': c['pooling'],
                 'padding_side': tok.padding_side, 'document_prompt': c['dprompt'], 'query_prompt': c['qprompt'],
                 'segment_separator': '\n', 'segment_separator_ids': list(tok('\n', add_special_tokens=False)['input_ids']),
                 'tokenizer_json_sha256': fsha(Path(c['dir']) / 'tokenizer.json')})
    Path(a.out).write_text(json.dumps(spec, indent=1))
    print(json.dumps(spec))
    print(f"WINDOW={spec['window']}", flush=True)


def load_spec(a, c, tok):
    spec = wrap_spec(tok, c['dprompt'])
    if a.window_json:
        w = json.loads(Path(a.window_json).read_text())
        assert all(w[k] == spec[k] for k in ('head_ids', 'tail_ids', 'window')), 'window.json differs from the tokenizer'
    return spec


def cmd_validate(a):
    import numpy as np
    c = cfg(a)
    t0 = time.time()
    texts = []
    with open(Path(a.ser) / 'passages.jsonl', encoding='utf-8') as f:
        for i, l in enumerate(f):
            if i >= a.n:
                break
            texts.append(json.loads(l)['text'])
    lockf, tok, model = setup(c, a.frac)
    spec = load_spec(a, c, tok)
    enc_text, enc_ids = make_enc(c, tok, model, spec)
    dp = c['dprompt']
    txt_tok = tok([dp + t for t in texts], truncation=True, max_length=MAXLEN)['input_ids']
    seqs = [np.asarray(x, dtype=np.uint32) for x in tok(texts, add_special_tokens=False)['input_ids']]
    same_tok = [list(t) == spec['head_ids'] + [int(v) for v in s] + spec['tail_ids'] for t, s in zip(txt_tok, seqs)]
    order = np.argsort([len(s) for s in seqs], kind='stable')
    V = np.zeros((len(texts), model.config.hidden_size), dtype=np.float16)
    T = np.zeros_like(V)
    bs = c['bs']
    for s in range(0, len(order), bs):
        b = order[s:s + bs]
        V[b] = enc_ids([seqs[i] for i in b])
        T[b] = enc_text([dp + texts[i] for i in b])
    unlock(lockf)
    cos = row_cosines(V, T)
    res = {'model': a.model, 'n': len(texts), 'bs': bs, 'max_len_tokens': int(max(len(s) for s in seqs)),
           'token_identity_share': float(np.mean(same_tok)), 'first_token_mismatch': next(
               (i for i, x in enumerate(same_tok) if not x), None),
           'cos_idpath_vs_textpath': {'min': float(cos.min()), 'mean': float(cos.mean())},
           'idpath_equals_textpath_bitwise_share': float(np.mean(np.all(V == T, axis=1))),
           'seconds': round(time.time() - t0, 1)}
    res['passed'] = bool(len(texts) == a.n and res['token_identity_share'] == 1.0
                         and res['cos_idpath_vs_textpath']['min'] > 0.9999)
    Path(a.out).write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))
    print('VALIDATE_DONE' if res['passed'] else 'VALIDATE_FAILED', flush=True)
    if not res['passed']:
        raise SystemExit(1)


def cmd_c0check(a):
    import numpy as np
    c = cfg(a)
    t0 = time.time()
    qs = {r['app_id']: r['text'] for r in p1dev_queries(a.ser)}
    units = json.loads(Path(a.units).read_text())
    uidx = {u: i for i, u in enumerate(units)}
    sel, top = [], {}
    with gzip.open(a.run, 'rt', encoding='utf-8') as f:
        assert f.readline().rstrip('\n').split('\t') == ['app_id', 'rank', 'unit', 'score']
        for line in f:
            app, rank, unit, score = line.rstrip('\n').split('\t')
            if app not in top:
                if len(sel) >= a.nq:
                    break
                if app not in qs:
                    continue
                sel.append(app)
                top[app] = []
            if int(rank) <= a.k:
                top[app].append((uidx[unit], float(score)))
    need = sorted({i for v in top.values() for i, _ in v})
    want = set(need)
    texts = {}
    with open(Path(a.ser) / 'passages.jsonl', encoding='utf-8') as f:
        for i, l in enumerate(f):
            if i in want:
                r = json.loads(l)
                assert r['unit'] == units[i], 'ser passages are not in the C0 unit order'
                texts[i] = r['text']
    lockf, tok, model = setup(c, a.frac)
    spec = load_spec(a, c, tok)
    enc_text, _ = make_enc(c, tok, model, spec)
    bs = c['bs']
    Q = np.concatenate([enc_text([c['qprompt'] + qs[x] for x in sel[s:s + bs]]) for s in range(0, len(sel), bs)])
    order = sorted(need, key=lambda i: len(texts[i]))                      # C0: length-sorted passage batches
    P = {}
    for s in range(0, len(order), bs):
        b = order[s:s + bs]
        for i, v in zip(b, enc_text([c['dprompt'] + texts[i] for i in b])):
            P[i] = v
    unlock(lockf)
    new, rec = [], []
    topk_same = 0
    for qi, app in enumerate(sel):
        q = Q[qi].astype(np.float32)
        pairs = [(i, r, round(float(q @ P[i].astype(np.float32)), 5)) for i, r in top[app]]
        new += [x[2] for x in pairs]
        rec += [x[1] for x in pairs]
        topk_same += [x[0] for x in sorted(pairs, key=lambda x: -x[1])][:10] == \
            [x[0] for x in sorted(pairs, key=lambda x: -x[2])][:10]
    res = {'model': a.model, 'reference_run': a.run, 'queries': len(sel), 'k': a.k, 'passages_encoded': len(need),
           'bs': bs, **score_check(new, rec), 'queries_with_identical_top10_order': topk_same,
           'seconds': round(time.time() - t0, 1)}
    res['passed'] = res['passed'] and len(sel) == a.nq and all(len(v) == a.k for v in top.values())
    Path(a.out).write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))
    print('C0CHECK_DONE' if res['passed'] else 'C0CHECK_FAILED', flush=True)
    if not res['passed']:
        raise SystemExit(1)


def cmd_queries(a):
    import numpy as np, torch
    c = cfg(a)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    sel = p1dev_queries(a.ser)
    if a.limit:
        sel = sel[:a.limit]
    lockf, tok, model = setup(c, a.frac)
    spec = load_spec(a, c, tok)
    enc_text, _ = make_enc(c, tok, model, spec)
    bs = c['bs']
    Q = np.concatenate([enc_text([c['qprompt'] + r['text'] for r in sel[s:s + bs]]) for s in range(0, len(sel), bs)])
    np.save(out / 'P1-DEV.f16.npy', Q)
    (out / 'P1-DEV.apps.json').write_text(json.dumps([r['app_id'] for r in sel]))
    print(f'queries encoded {len(sel)} in {time.time() - t0:.1f}s; peak GPU mem '
          f'{torch.cuda.max_memory_allocated(0) / 2**30:.2f} GiB', flush=True)
    unlock(lockf)
    (out / 'DONE').write_text('ok')
    print('QUERIES_DONE', flush=True)


def cmd_passages(a):
    import numpy as np, torch
    c = cfg(a)
    arm, out = Path(a.arm), Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    st = json.loads((arm / 'stats.json').read_text())
    ln = np.load(arm / f'{a.name}.len.npy').astype(np.int64)
    off = np.zeros(ln.size + 1, dtype=np.int64)
    np.cumsum(ln, out=off[1:])
    ids = np.memmap(arm / f'{a.name}.ids.u32', dtype=np.uint32, mode='r')
    assert ids.size == off[-1]
    n = ln.size
    order = np.argsort(ln, kind='stable')
    nsh = (n + SHARD - 1) // SHARD
    print(f'{a.name}: {n} passages, {int(off[-1])} tokens, {nsh} shards', flush=True)
    lockf, tok, model = setup(c, a.frac)
    spec = load_spec(a, c, tok)
    assert st['window_content_tokens'] == spec['window'], (st['window_content_tokens'], spec['window'])
    assert int(ln.max()) <= spec['window']
    _, enc_ids = make_enc(c, tok, model, spec)
    dim, bs = model.config.hidden_size, c['bs']
    t1 = time.time()
    done = 0
    for k in range(nsh):
        sp = out / f'shard-{k:03d}.npy'
        idx = order[k * SHARD:(k + 1) * SHARD]
        if sp.exists():
            done += idx.size
            continue
        V = np.zeros((idx.size, dim), dtype=np.float16)
        for s in range(0, idx.size, bs):
            b = idx[s:s + bs]
            V[s:s + b.size] = enc_ids([np.asarray(ids[off[i]:off[i + 1]]) for i in b])
        np.save(out / f'shard-{k:03d}.tmp.npy', V)
        os.replace(out / f'shard-{k:03d}.tmp.npy', sp)
        done += idx.size
        el = time.time() - t1
        print(f'{a.name} shard {k + 1}/{nsh} done: {done}/{n} passages, {el:.0f}s, {done / max(el, 1e-9):.1f} passages/s, '
              f'peak GPU mem {torch.cuda.max_memory_allocated(0) / 2**30:.2f} GiB', flush=True)
    unlock(lockf)
    print(f'GPU lock released; encode seconds {time.time() - t1:.1f}', flush=True)
    P = np.zeros((n, dim), dtype=np.float16)
    for k in range(nsh):
        P[order[k * SHARD:(k + 1) * SHARD]] = np.load(out / f'shard-{k:03d}.npy')
    assert np.all(np.isfinite(P.astype(np.float32).sum(1)))
    np.save(out / 'passages.tmp.npy', P)
    os.replace(out / 'passages.tmp.npy', out / 'passages.f16.npy')
    for k in range(nsh):
        (out / f'shard-{k:03d}.npy').unlink()
    (out / 'encode.json').write_text(json.dumps({
        'model': a.model, 'arm': a.name, 'passages': int(n), 'tokens': int(off[-1]), 'dim': int(dim),
        'encode_seconds': round(time.time() - t1, 1), 'total_seconds': round(time.time() - t0, 1),
        'peak_gpu_mem_gib': round(torch.cuda.max_memory_allocated(0) / 2**30, 3), 'bs': bs,
        'mem_fraction': float(a.frac), 'window': spec, 'gpu': torch.cuda.get_device_name(0)}, indent=1))
    (out / 'DONE').write_text('ok')
    print(f'ENCODE_{a.model.upper()}_{a.name.upper()}_DONE', round(time.time() - t0, 1), flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', choices=('window', 'validate', 'c0check', 'queries', 'passages'))
    ap.add_argument('--model', required=True, choices=sorted(MODELS))
    ap.add_argument('--model-dir')
    ap.add_argument('--out', required=True)
    ap.add_argument('--ser')
    ap.add_argument('--arm')
    ap.add_argument('--name', default='c1')
    ap.add_argument('--run')
    ap.add_argument('--units')
    ap.add_argument('--window-json')
    ap.add_argument('--n', type=int, default=2048)
    ap.add_argument('--nq', type=int, default=256)
    ap.add_argument('--k', type=int, default=50)
    ap.add_argument('--limit', type=int, default=0)
    ap.add_argument('--frac', default='0.15')
    a = ap.parse_args()
    {'window': cmd_window, 'validate': cmd_validate, 'c0check': cmd_c0check, 'queries': cmd_queries,
     'passages': cmd_passages}[a.cmd](a)


if __name__ == '__main__':
    main()
