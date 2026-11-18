"""RunPod pilot for P1-BridgeRet (owner-approved, hard cap USD 10). Engineering measurement only.

Measures on the rented GPU, with Arctic-embed-m-v2.0 @95c27414 (Apache-2.0):
  1. encode throughput (passages/s) and peak memory at max_len 512 for fp16 and fp32, batch sweep;
  2. full fine-tuning step time and peak memory (InfoNCE, 1 positive + in-batch + 7 extra negatives per query),
     per batch size, with and without gradient checkpointing;
  3. projections: hours to encode 1M passages and to run 1 epoch over the TRAIN pairs (count passed in).
Input: pilot-data.jsonl.gz with TRAIN-block query texts and passages only (public USPTO text; no DEV/TEST
labels, no DAPFAM). Output: /workspace/pilot-result.json. No retrieval quality is measured.
"""
import gzip, json, os, sys, time

import torch
import torch.nn.functional as F
from transformers import AutoModel, AutoTokenizer

MODEL = '/workspace/arctic'
DATA = '/workspace/pilot-data.jsonl.gz'
OUT = '/workspace/pilot-result.json'
TRAIN_PAIRS = int(os.environ.get('TRAIN_PAIRS', '432961'))
CORPUS = 1_000_000


def load_model(dtype):
    m = AutoModel.from_pretrained(MODEL, trust_remote_code=True, use_memory_efficient_attention=False,
                                  unpad_inputs=False, torch_dtype=dtype).cuda()
    return m


def embed(model, batch):
    out = model(**batch)
    return F.normalize(out.last_hidden_state[:, 0], dim=-1)   # Arctic m v2.0 uses CLS pooling


def main():
    rows = [json.loads(l) for l in gzip.open(DATA, 'rt', encoding='utf-8')]
    queries = [r['q'] for r in rows]
    passages = [r['p'] for r in rows] + [n for r in rows for n in r['n']]
    tok = AutoTokenizer.from_pretrained(MODEL)
    res = {'gpu': torch.cuda.get_device_name(0), 'torch': torch.__version__, 'cuda': torch.version.cuda,
           'bf16_supported': torch.cuda.is_bf16_supported(), 'n_queries': len(queries), 'n_passages': len(passages),
           'encode': [], 'train': []}
    enc_texts = passages[:4096]
    for dtype, name in ((torch.float16, 'fp16'), (torch.float32, 'fp32')):
        model = load_model(dtype).eval()
        for bs in (32, 64, 128, 256):
            torch.cuda.reset_peak_memory_stats(); torch.cuda.synchronize(); t = time.time(); n = 0
            try:
                with torch.inference_mode():
                    for i in range(0, len(enc_texts), bs):
                        b = tok(enc_texts[i:i + bs], padding=True, truncation=True, max_length=512, return_tensors='pt').to('cuda')
                        embed(model, b); n += b['input_ids'].shape[0]
                torch.cuda.synchronize(); dt = time.time() - t
                res['encode'].append({'dtype': name, 'batch': bs, 'passages_per_s': round(n / dt, 1),
                                      'peak_gb': round(torch.cuda.max_memory_allocated() / 2 ** 30, 2),
                                      'hours_1M': round(CORPUS / (n / dt) / 3600, 2)})
            except torch.cuda.OutOfMemoryError:
                res['encode'].append({'dtype': name, 'batch': bs, 'oom': True}); torch.cuda.empty_cache()
            print(res['encode'][-1], flush=True)
        del model; torch.cuda.empty_cache()
    amp = torch.bfloat16 if res['bf16_supported'] else torch.float16
    for gc in (False, True):
        for bs in (16, 32, 64):
            model = load_model(torch.float32).train()
            if gc:
                model.gradient_checkpointing_enable()
            opt = torch.optim.AdamW(model.parameters(), lr=2e-5)
            scaler = torch.amp.GradScaler(enabled=amp == torch.float16)
            torch.cuda.reset_peak_memory_stats(); times = []
            try:
                for step in range(12):
                    i = (step * bs) % max(1, len(rows) - bs)
                    grp = rows[i:i + bs]
                    qb = tok([QP + r['q'] for r in grp], padding=True, truncation=True, max_length=512, return_tensors='pt').to('cuda')
                    docs = [r['p'] for r in grp] + [n for r in grp for n in r['n'][:7]]
                    db = tok(docs, padding=True, truncation=True, max_length=512, return_tensors='pt').to('cuda')
                    torch.cuda.synchronize(); t = time.time()
                    with torch.autocast('cuda', dtype=amp):
                        qe, de = embed(model, qb), embed(model, db)
                        loss = F.cross_entropy(qe @ de.T / 0.02, torch.arange(len(grp), device='cuda'))
                    opt.zero_grad(); scaler.scale(loss).backward(); scaler.step(opt); scaler.update()
                    torch.cuda.synchronize()
                    if step >= 2:
                        times.append(time.time() - t)
                s = sum(times) / len(times)
                res['train'].append({'grad_ckpt': gc, 'batch_queries': bs, 'docs_per_step': bs * 8, 'amp': str(amp),
                                     'step_s': round(s, 3), 'peak_gb': round(torch.cuda.max_memory_allocated() / 2 ** 30, 2),
                                     'hours_per_epoch': round(TRAIN_PAIRS / bs * s / 3600, 2)})
            except torch.cuda.OutOfMemoryError:
                res['train'].append({'grad_ckpt': gc, 'batch_queries': bs, 'oom': True})
            print(res['train'][-1], flush=True)
            del model, opt; torch.cuda.empty_cache()
    json.dump(res, open(OUT, 'w'), indent=1)
    print('DONE', flush=True)


QP = 'query: '
if __name__ == '__main__':
    main()
