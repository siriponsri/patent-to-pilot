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
        from transformers import AutoModelForCausalLM, AutoTokenizer
        torch.cuda.set_per_process_memory_fraction(float(frac), 0)
        self.torch = torch
        self.tok = AutoTokenizer.from_pretrained(model_dir, padding_side='left')
        self.model = AutoModelForCausalLM.from_pretrained(model_dir, torch_dtype=torch.float16).cuda().eval()
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
            logits = self.model(input_ids=inp, attention_mask=att).logits[:, -1, :]
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
    rk = Reranker(model_dir)
    ids = [rk.ids(GENERIC, qtext[q], texts[d]) for q, d in pairs]
    lens = sorted(len(x) for x in ids)
    order = sorted(range(len(ids)), key=lambda i: len(ids[i]))
    res = {}
    for bs in (1, 4):
        t0 = time.time(); n = 0
        for s in range(0, min(len(order), 400), bs):
            rk.score([ids[i] for i in order[s:s + bs]]); n += len(order[s:s + bs])
        res[f'bs{bs}_pairs_per_s_shortest400'] = round(n / (time.time() - t0), 2)
    t0 = time.time()
    for i in order:
        rk.score([ids[i]])
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


if __name__ == '__main__':
    c, a = sys.argv[1], sys.argv[2:]
    {'timing': cmd_timing, 'check-scrambled': cmd_check}[c](*a)
