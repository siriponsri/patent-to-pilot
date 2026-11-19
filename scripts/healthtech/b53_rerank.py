"""B53 Stage 2 reranker: Qwen3-Reranker-0.6B @e61197ed with the Paper 53 Table I instruction arms (exact bodies from the
Paper 53 LaTeX source, IS_1/revision_05/source/main.tex lines 102-105).
Pair serialisation follows the model card. Query ≤ 2,048 and document ≤ 4,096 tokens, right-truncated, as Paper 53 §III.
Score = P(yes) over {yes, no} at the final position.
Subcommands:
  timing <in_dir> <runs_dir> <model_dir> <out_json> [n_pairs=1000]   speed and pair-count planning (no labels read)
  check-scrambled <model_dir>                                         token counts of the four bodies (Table I: 13/29/119/113)
"""
import fcntl, json, os, random, sys, time
from pathlib import Path

GENERIC = 'Given a web search query, retrieve relevant passages that answer the query'
PATENT_AWARE = ('Given the title, abstract, and claims of a query patent, judge whether the candidate patent document is '
                'relevant prior art for the query patent.')
CLAIM_FOCUSED = ('Judge whether the candidate patent document is relevant prior art for the query patent. Relevant prior art '
                 'discloses, in whole or in part, the same or a closely related technical feature, mechanism, method, or '
                 'composition: compare the technical problem addressed, the mechanism or method of the solution, and the '
                 'claimed subject matter, giving most weight to the claims. A document from a different technical field that '
                 'discloses the same underlying mechanism using different terminology is still relevant. A document that '
                 'merely shares vocabulary or general topic with the query, without overlapping technical substance, is not '
                 'relevant.')


def scrambled():
    items = CLAIM_FOCUSED.split()
    random.Random(42).shuffle(items)
    return ' '.join(items)


ARMS = {'generic': GENERIC, 'patent_aware': PATENT_AWARE, 'claim_focused': CLAIM_FOCUSED, 'scrambled': scrambled()}
PREFIX = ('<|im_start|>system\nJudge whether the Document meets the requirements based on the Query and the Instruct provided. '
          'Note that the answer can only be "yes" or "no".<|im_end|>\n<|im_start|>user\n')
SUFFIX = '<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n'
LOCK = '/home/chaw/patent-to-pilot-jobs/research-product-o1-o4-20261031/models/.GPU-277ccc57-c3e5-0731-cd49-f4f8695f7089.lock'


class Reranker:
    def __init__(self, model_dir, frac='0.15'):
        import torch
        import transformers.integrations.sdpa_attention as sa
        sa.use_gqa_in_sdpa = lambda *a, **k: False   # enable_gqa has no memory-efficient SDPA kernel on the V100 -> O(L^2) math path OOM
        from transformers import AutoModelForCausalLM, AutoTokenizer
        torch.cuda.set_per_process_memory_fraction(float(frac), 0)
        self.torch = torch
        self.tok = AutoTokenizer.from_pretrained(model_dir, padding_side='left')
        self.model = AutoModelForCausalLM.from_pretrained(model_dir, torch_dtype=torch.float16, attn_implementation='sdpa').cuda().eval()
        self.yes = self.tok.convert_tokens_to_ids('yes'); self.no = self.tok.convert_tokens_to_ids('no')
        self.pre = self.tok.encode(PREFIX, add_special_tokens=False); self.suf = self.tok.encode(SUFFIX, add_special_tokens=False)

    def ids(self, instruction, q, d):
        qi = self.tok.encode(q, add_special_tokens=False)[:2048]
        di = self.tok.encode(d, add_special_tokens=False)[:4096]
        body = (self.tok.encode(f'<Instruct>: {instruction}\n<Query>: ', add_special_tokens=False) + qi +
                self.tok.encode('\n<Document>: ', add_special_tokens=False) + di)
        return self.pre + body + self.suf

    def score(self, batch_ids):
        torch = self.torch
        L = max(len(x) for x in batch_ids)
        pad = self.tok.pad_token_id
        inp = torch.tensor([[pad] * (L - len(x)) + x for x in batch_ids], device='cuda')
        att = torch.tensor([[0] * (L - len(x)) + [1] * len(x) for x in batch_ids], device='cuda')
        with torch.inference_mode():
            if len(batch_ids) == 1:   # no padding -> no mask, so SDPA can use the memory-efficient kernel on the V100
                logits = self.model(input_ids=inp, logits_to_keep=1).logits[:, -1, :]
            else:
                logits = self.model(input_ids=inp, attention_mask=att, logits_to_keep=1).logits[:, -1, :]   # last position only
            two = torch.stack([logits[:, self.no], logits[:, self.yes]], dim=1).float()
            return torch.softmax(two, dim=1)[:, 1].cpu().tolist()


def read_jsonl(p):
    return [json.loads(l) for l in open(p, encoding='utf-8')]


def cmd_timing(in_dir, runs_dir, model_dir, out_json, n_pairs='1000'):
    texts = {r['id']: r['text'] for r in read_jsonl(Path(in_dir) / 'corpus.jsonl')}
    qtext = {r['id']: r['text'] for r in read_jsonl(Path(in_dir) / 'queries.jsonl')}
    runs = {}
    for arm in ('F0', 'F1', 'F2', 'F3', 'F4'):
        rr = {}
        for l in open(Path(runs_dir) / f'{arm}.tsv', encoding='utf-8'):
            q, r, fam, s = l.rstrip('\n').split('\t')
            if int(r) <= 100:
                rr.setdefault(q, []).append(fam)
        runs[arm] = rr
    qs = sorted(qtext)
    union_all = sum(len(set().union(*[set(runs[a].get(q, [])) for a in runs])) for q in qs)
    union_f012 = sum(len(set().union(*[set(runs[a].get(q, [])) for a in ('F0', 'F1', 'F2')])) for q in qs)
    rng = random.Random(20261119)
    pairs = [(q, rng.choice(runs['F0'][q])) for q in rng.sample(qs, int(n_pairs))]
    lockf = open(LOCK, 'a'); fcntl.flock(lockf, fcntl.LOCK_EX)
    rk = Reranker(model_dir, os.environ.get('MEM_FRAC', '0.15'))
    ids = [rk.ids(GENERIC, qtext[q], texts[d]) for q, d in pairs]
    lens = sorted(len(x) for x in ids)
    order = sorted(range(len(ids)), key=lambda i: len(ids[i]))
    res = {}
    t0 = time.time()
    for k, i in enumerate(order):
        rk.score([ids[i]])
        if k % 100 == 0:
            print('timing', k, len(ids[i]), round(time.time() - t0, 1), flush=True)
    full = len(order) / (time.time() - t0)
    fcntl.flock(lockf, fcntl.LOCK_UN)
    out = {'n_pairs': len(ids), 'token_len_p50': lens[len(lens) // 2], 'token_len_p90': lens[int(0.9 * len(lens))], 'token_len_max': lens[-1],
           'pairs_per_s_bs1_all': round(full, 2), **res,
           'unique_pairs_top100_F0toF4_all_queries': union_all, 'unique_pairs_top100_F0F1F2_all_queries': union_f012,
           'note': 'labels not read; pairs sampled from F0 top-100 (seed 20261119); Generic instruction; V100 under 0.15 memory cap'}
    for name, upairs in (('F0toF4', union_all), ('F0F1F2', union_f012)):
        out[f'projected_hours_4arms_{name}'] = round(4 * upairs / full / 3600, 1)
    Path(out_json).write_text(json.dumps(out, indent=2)); print(json.dumps(out, indent=1))


def cmd_check(model_dir):
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(model_dir)
    print({k: len(tok.encode(v, add_special_tokens=False)) for k, v in ARMS.items()})


def _pools(runs_dir, k=100):
    pools = {}
    for arm in ('F0', 'F1', 'F2', 'F3', 'F4'):
        for l in open(Path(runs_dir) / f'{arm}.tsv', encoding='utf-8'):
            q, r, fam, s = l.rstrip('\n').split('\t')
            if int(r) <= k:
                pools.setdefault(arm, {}).setdefault(q, []).append(fam)
    return pools


def _out_queries(in_dir):
    return sorted({r['query_id'] for r in read_jsonl(Path(in_dir) / 'qrels-pos.jsonl') if r['domain'] == 'OUT'})


def cmd_rerank(in_dir, runs_dir, model_dir, out_dir):
    """Score every unique (OUT query, family) pair in the F0-F4 top-100 pools under the 4 instructions. Resumable:
    queries already present in all four score files are skipped. Holds the shared GPU lock per query only."""
    out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    texts = {r['id']: r['text'] for r in read_jsonl(Path(in_dir) / 'corpus.jsonl')}
    qtext = {r['id']: r['text'] for r in read_jsonl(Path(in_dir) / 'queries.jsonl')}
    pools = _pools(runs_dir); qs = _out_queries(in_dir)
    done = None
    for arm in ARMS:
        p = out / f'scores-{arm}.tsv'
        s = {l.split('\t')[0] for l in open(p, encoding='utf-8')} if p.exists() else set()
        done = s if done is None else done & s
    rk = Reranker(model_dir, os.environ.get('MEM_FRAC', '0.15'))
    fh = {arm: open(out / f'scores-{arm}.tsv', 'a', encoding='utf-8') for arm in ARMS}
    t0 = time.time(); n = 0
    lockf = open(LOCK, 'a')
    for qi, q in enumerate(qs):
        if q in done:
            continue
        fams = sorted(set().union(*[set(pools[a].get(q, [])) for a in pools]))
        fcntl.flock(lockf, fcntl.LOCK_EX)
        rows = {arm: [] for arm in ARMS}
        for arm, instr in ARMS.items():
            for f in fams:
                rows[arm].append((f, rk.score([rk.ids(instr, qtext[q], texts[f])])[0]))
        fcntl.flock(lockf, fcntl.LOCK_UN)
        for arm in ARMS:                        # a query is written to all four files together (resume unit)
            fh[arm].write(''.join(f'{q}\t{f}\t{s:.6f}\n' for f, s in rows[arm])); fh[arm].flush()
        n += len(fams) * len(ARMS)
        if qi % 20 == 0:
            print('rerank', qi, len(qs), n, round(time.time() - t0, 1), flush=True)
    print('RERANK_DONE', n, round(time.time() - t0, 1))


def cmd_rerank_bge(in_dir, runs_dir, model_dir, out_dir):
    import torch
    from transformers import AutoModelForSequenceClassification, AutoTokenizer
    torch.cuda.set_per_process_memory_fraction(float(os.environ.get('MEM_FRAC', '0.15')), 0)
    out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    texts = {r['id']: r['text'] for r in read_jsonl(Path(in_dir) / 'corpus.jsonl')}
    qtext = {r['id']: r['text'] for r in read_jsonl(Path(in_dir) / 'queries.jsonl')}
    pools = _pools(runs_dir); qs = _out_queries(in_dir)
    p = out / 'scores-bge.tsv'
    done = {l.split('\t')[0] for l in open(p, encoding='utf-8')} if p.exists() else set()
    tok = AutoTokenizer.from_pretrained(model_dir)
    m = AutoModelForSequenceClassification.from_pretrained(model_dir, torch_dtype=torch.float16).cuda().eval()
    fh = open(p, 'a', encoding='utf-8'); lockf = open(LOCK, 'a'); t0 = time.time()
    for qi, q in enumerate(qs):
        if q in done:
            continue
        fams = sorted(set().union(*[set(pools[a].get(q, [])) for a in pools]))
        qi_ = tok.encode(qtext[q], add_special_tokens=False)[:2048]
        fcntl.flock(lockf, fcntl.LOCK_EX); rows = []
        for f in fams:
            di = tok.encode(texts[f], add_special_tokens=False)[:4096]
            ids = [tok.cls_token_id] + qi_ + [tok.sep_token_id, tok.sep_token_id] + di + [tok.sep_token_id]
            with torch.inference_mode():
                s = m(input_ids=torch.tensor([ids], device='cuda')).logits[0, 0].float().item()
            rows.append((f, s))
        fcntl.flock(lockf, fcntl.LOCK_UN)
        fh.write(''.join(f'{q}\t{f}\t{s:.6f}\n' for f, s in rows)); fh.flush()
        if qi % 50 == 0:
            print('bge', qi, len(qs), round(time.time() - t0, 1), flush=True)
    print('BGE_DONE', round(time.time() - t0, 1))


if __name__ == '__main__':
    c, a = sys.argv[1], sys.argv[2:]
    {'timing': cmd_timing, 'check-scrambled': cmd_check, 'rerank': cmd_rerank, 'rerank-bge': cmd_rerank_bge}[c](*a)
