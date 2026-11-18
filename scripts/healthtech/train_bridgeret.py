"""P1-BridgeRet fine-tuning (pre-declaration section 4; amendment A1 parameters are arguments, not defaults applied).

Recipes over the mined pools (mine_negatives_bridgeret.py): per query 1 positive + k mined negatives + in-batch.
  S1: k from BM25 top-100.        S2: k/2 BM25 + k/2 dense ranks 20-200 (rounded toward dense).
  S3: S2 with dense negatives IN:OUT 1:1 and log(w_out) added to OUT-negative logits.
  S4: S2 + denoise; 'rule' drops dense negatives with score > 0.95 x the positive's dense score;
      'reranker' drops negatives whose precomputed reranker score >= the positive's 10th-percentile score
      (needs --rerank-scores jsonl {app_id, unit: score}).
Loss: InfoNCE with temperature tau; in-batch documents that are positives of the anchor query (other than its own
sampled positive) are masked (multi-positive guard). Full fine-tuning (fp32 master weights, bf16 autocast on Ampere,
fp16 + GradScaler otherwise), gradient checkpointing, AdamW lr 2e-5, 5% linear warm-up, 1 epoch over the chosen tasks.
Usage: python3 train_bridgeret.py --model DIR --mined mined-TRAIN.jsonl --ser SER_DIR --out OUT --recipe S2 [--k 3]
       [--tau 0.02] [--w-out 1.0] [--denoise rule|reranker] [--subset N --subset-salt S] [--bq 16] [--seed 1]
"""
import argparse, hashlib, json, math, os, random, time


def h(salt, x):
    return hashlib.sha256(f'{salt}|{x}'.encode()).hexdigest()


def build_examples(args):
    rows = [json.loads(l) for l in open(args.mined, encoding='utf-8')]
    if args.subset:
        rows = sorted(rows, key=lambda r: h(args.subset_salt, r['app_id']))[:args.subset]
    rer = {}
    if args.denoise == 'reranker':
        for l in open(args.rerank_scores, encoding='utf-8'):
            r = json.loads(l); rer[r['app_id']] = r['scores']
    rng = random.Random(args.seed)
    ex = []
    for r in rows:
        dense = r['dense']
        if args.recipe == 'S4' and args.denoise == 'rule' and r['pos_dense'] is not None:
            dense = [d for d in dense if d[2] <= 0.95 * r['pos_dense']]
        if args.recipe == 'S4' and args.denoise == 'reranker':
            sc = rer.get(r['app_id'], {})
            ps = sorted(sc[u] for u in r['pos'] if u in sc)
            if ps:
                thr = ps[max(0, int(0.1 * len(ps)) - 1)] if len(ps) > 1 else ps[0]
                dense = [d for d in dense if sc.get(d[0], -1e9) < thr]
        bm = [b[0] for b in r['bm25']]
        if args.recipe == 'S1':
            negs = rng.sample(bm, min(args.k, len(bm)))
        else:
            nd = args.k - args.k // 2
            if args.recipe == 'S3':
                outs = [d[0] for d in dense if d[3] == 'OUT']; ins = [d[0] for d in dense if d[3] == 'IN']
                half = nd // 2
                dn = rng.sample(outs, min(nd - half, len(outs))) + rng.sample(ins, min(half, len(ins)))
            else:
                dn = rng.sample([d[0] for d in dense], min(nd, len(dense)))
            negs = dn + rng.sample([b for b in bm if b not in dn], min(args.k - len(dn), len(bm)))
        ex.append({'app_id': r['app_id'], 'pos': r['pos'], 'negs': negs,
                   'out': {d[0] for d in r['dense'] if d[3] == 'OUT'}})
    rng.shuffle(ex)
    return ex


def main():
    ap = argparse.ArgumentParser()
    for a, d in (('--model', None), ('--mined', None), ('--ser', None), ('--out', None), ('--recipe', 'S2'),
                 ('--denoise', 'rule'), ('--rerank-scores', None), ('--subset-salt', 'ptp-2x2-30k-v1'), ('--query-prompt', 'query: ')):
        ap.add_argument(a, default=d)
    for a, d in (('--k', 3), ('--subset', 0), ('--bq', 16), ('--seed', 1), ('--max-len', 512)):
        ap.add_argument(a, type=int, default=d)
    for a, d in (('--tau', 0.02), ('--w-out', 1.0), ('--lr', 2e-5)):
        ap.add_argument(a, type=float, default=d)
    ap.add_argument('--max-steps', type=int, default=0)
    args = ap.parse_args()
    import torch, torch.nn.functional as F
    from transformers import AutoModel, AutoTokenizer
    torch.manual_seed(args.seed)
    os.makedirs(args.out, exist_ok=False)
    ex = build_examples(args)
    need = {u for e in ex for u in e['pos'] + e['negs']}
    ptxt = {}
    for l in open(os.path.join(args.ser, 'passages.jsonl'), encoding='utf-8'):
        r = json.loads(l)
        if r['unit'] in need:
            ptxt[r['unit']] = r['text']
    qtxt = {json.loads(l)['app_id']: json.loads(l)['text'] for l in open(os.path.join(args.ser, 'queries.jsonl'), encoding='utf-8')}
    ex = [e for e in ex if e['app_id'] in qtxt and any(u in ptxt for u in e['pos'])]
    cuda = torch.cuda.is_available()
    dev = 'cuda' if cuda else 'cpu'
    amp = torch.bfloat16 if (cuda and torch.cuda.is_bf16_supported()) else torch.float16
    tok = AutoTokenizer.from_pretrained(args.model)
    model = AutoModel.from_pretrained(args.model, trust_remote_code=True, use_memory_efficient_attention=False,
                                      unpad_inputs=False, torch_dtype=torch.float32).to(dev)
    model.gradient_checkpointing_enable(); model.train()
    steps = math.ceil(len(ex) / args.bq) if not args.max_steps else args.max_steps
    opt = torch.optim.AdamW(model.parameters(), lr=args.lr)
    warm = max(1, int(0.05 * steps))
    sched = torch.optim.lr_scheduler.LambdaLR(opt, lambda s: min(1.0, (s + 1) / warm) * max(0.0, (steps - s) / max(1, steps - warm)) if s >= warm else (s + 1) / warm)
    scaler = torch.amp.GradScaler(enabled=cuda and amp == torch.float16)
    rng = random.Random(args.seed)
    log = open(os.path.join(args.out, 'train-log.jsonl'), 'w')
    t0 = time.time()
    enc = lambda texts: tok(texts, padding=True, truncation=True, max_length=args.max_len, return_tensors='pt').to(dev)
    for s in range(steps):
        b = ex[s * args.bq:(s + 1) * args.bq]
        if not b:
            break
        docs, owner, pos_idx = [], [], []
        for i, e in enumerate(b):
            p = rng.choice([u for u in e['pos'] if u in ptxt])
            pos_idx.append(len(docs)); docs.append(p); owner.append(i)
            for n in e['negs']:
                if n in ptxt:
                    docs.append(n); owner.append(i)
        with torch.autocast(dev, dtype=amp, enabled=cuda):
            q = F.normalize(model(**enc([args.query_prompt + qtxt[e['app_id']] for e in b])).last_hidden_state[:, 0], dim=-1)
            d = F.normalize(model(**enc([ptxt[u] for u in docs])).last_hidden_state[:, 0], dim=-1)
            logits = (q @ d.T).float() / args.tau
        mask = torch.zeros_like(logits, dtype=torch.bool)
        for i, e in enumerate(b):
            P = set(e['pos'])
            for j, u in enumerate(docs):
                if j != pos_idx[i] and u in P:
                    mask[i, j] = True                      # multi-positive guard
            if args.recipe == 'S3' and args.w_out != 1.0:
                for j, u in enumerate(docs):
                    if owner[j] == i and j != pos_idx[i] and u in e['out']:
                        logits[i, j] = logits[i, j] + math.log(args.w_out)
        logits = logits.masked_fill(mask, float('-inf'))
        loss = F.cross_entropy(logits, torch.tensor(pos_idx, device=dev))
        opt.zero_grad(); scaler.scale(loss).backward(); scaler.step(opt); scaler.update(); sched.step()
        if s % 50 == 0 or s == steps - 1:
            log.write(json.dumps({'step': s, 'loss': round(loss.item(), 4), 'lr': sched.get_last_lr()[0], 'sec': round(time.time() - t0, 1)}) + '\n'); log.flush()
    ck = os.path.join(args.out, 'checkpoint')
    model.save_pretrained(ck); tok.save_pretrained(ck)
    import shutil
    for f in os.listdir(args.model):                      # remote-code modules + pooling config travel with the weights
        if f.endswith('.py') or f in ('modules.json', 'config_sentence_transformers.json'):
            shutil.copy(os.path.join(args.model, f), ck)
        if f == '1_Pooling':
            shutil.copytree(os.path.join(args.model, f), os.path.join(ck, f), dirs_exist_ok=True)
    json.dump({**vars(args), 'n_examples': len(ex), 'steps': steps, 'seconds': round(time.time() - t0, 1), 'amp': str(amp)},
              open(os.path.join(args.out, 'train-config.json'), 'w'), indent=1)
    print('TRAIN_DONE', len(ex), steps, round(time.time() - t0, 1))


if __name__ == '__main__':
    main()
