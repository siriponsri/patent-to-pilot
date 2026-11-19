"""P1 BridgeRet amendment AM-6 (c): general-domain forgetting check on three small public BEIR tasks.

Compares a fine-tuned checkpoint with the Qwen3-Embedding-0.6B zero-shot base on SciFact, NFCorpus and ArguAna (test
qrels, pinned revisions in paper1-bridgeret/am6-general-download-approval.json). Descriptive only; never used to select or
tune anything. Same encoder settings as the P1 dense runs (dense_bridgeret_v3.py): fp16, last-token pooling, left padding,
max length 512, L2-normalised. Queries get the per-task instruction in the P1 query format ("Instruct: ...\nQuery: ");
documents get none. Documents are "title text" as in BEIR. Metrics: nDCG@10 (linear gain, as pytrec_eval) and
Recall@100, query-macro over test queries with a positive qrel. ArguAna: the query's own id is removed from its ranking
(standard MTEB practice).
Usage:
  build <beir_dir> <out_dir>                     (local, needs pyarrow) -> <out_dir>/<task>/{corpus,queries}.jsonl, qrels.tsv
  run <model_dir> <data_dir> <out_json> <mem_fraction>   (dr-train V100, takes the shared GPU lock)
"""
import json, math, sys
from pathlib import Path

TASKS = {
    'scifact': 'Given a scientific claim, retrieve documents that support or refute the claim',
    'nfcorpus': 'Given a question, retrieve relevant documents that best answer the question',
    'arguana': 'Given a claim, find documents that refute the claim',
}
SELF_EXCLUDE = {'arguana'}
LOCK = '/home/chaw/patent-to-pilot-jobs/research-product-o1-o4-20261031/models/.GPU-277ccc57-c3e5-0731-cd49-f4f8695f7089.lock'


def read_qrels(path):
    rel = {}
    with open(path, encoding='utf-8') as f:
        next(f)
        for line in f:
            q, d, s = line.rstrip('\n').split('\t')
            if int(s) > 0:
                rel.setdefault(q, {})[d] = int(s)
    return rel


def ndcg10(ranked, rel):
    dcg = sum(rel.get(d, 0) / math.log2(i + 2) for i, d in enumerate(ranked[:10]))
    ideal = sorted(rel.values(), reverse=True)[:10]
    return dcg / sum(g / math.log2(i + 2) for i, g in enumerate(ideal))


def recall100(ranked, rel):
    return len(set(ranked[:100]) & set(rel)) / len(rel)


def score_task(rankings, rel):
    qs = sorted(q for q in rel if q in rankings)
    if len(qs) != len(rel):
        raise SystemExit(f'missing rankings for {len(rel) - len(qs)} queries')
    return {'n': len(qs), 'nDCG@10': round(sum(ndcg10(rankings[q], rel[q]) for q in qs) / len(qs), 5),
            'R@100': round(sum(recall100(rankings[q], rel[q]) for q in qs) / len(qs), 5)}


def cmd_build(beir_dir, out_dir):
    import hashlib, pyarrow.parquet as pq
    man = {}
    for t in TASKS:
        src, dst = Path(beir_dir) / t, Path(out_dir) / t
        dst.mkdir(parents=True, exist_ok=True)
        files = ['corpus/corpus-00000-of-00001.parquet', 'queries/queries-00000-of-00001.parquet', 'test.tsv']
        man[t] = {f: hashlib.sha256((src / f).read_bytes()).hexdigest() for f in files}
        rel = read_qrels(src / 'test.tsv')
        with open(dst / 'corpus.jsonl', 'w', encoding='utf-8') as f:
            for r in pq.read_table(src / files[0]).to_pylist():
                f.write(json.dumps({'id': str(r['_id']), 'text': ((r.get('title') or '') + ' ' + (r.get('text') or '')).strip()}) + '\n')
        n = 0
        with open(dst / 'queries.jsonl', 'w', encoding='utf-8') as f:
            for r in pq.read_table(src / files[1]).to_pylist():
                if str(r['_id']) in rel:
                    f.write(json.dumps({'id': str(r['_id']), 'text': r['text']}) + '\n'); n += 1
        (dst / 'qrels.tsv').write_bytes((src / 'test.tsv').read_bytes())
        man[t]['n_test_queries_with_text'] = n
        man[t]['n_test_queries_qrels'] = len(rel)
    Path(out_dir, 'manifest.json').write_text(json.dumps(man, indent=1))
    print(json.dumps(man, indent=1))


def cmd_run(mdir, data_dir, out_json, frac):
    import fcntl, time, torch, torch.nn.functional as F
    from transformers import AutoModel, AutoTokenizer
    # Only the approved V100 may be used (19 Nov incident: an unpinned run landed on the RTX 2080 Ti and OOM'd).
    if torch.cuda.device_count() != 1 or 'V100' not in torch.cuda.get_device_name(0):
        raise SystemExit('refusing: set CUDA_VISIBLE_DEVICES to the approved V100 only')
    lockf = open(LOCK, 'a'); fcntl.flock(lockf, fcntl.LOCK_EX)
    try:
        torch.cuda.set_per_process_memory_fraction(float(frac), 0)
        tok = AutoTokenizer.from_pretrained(mdir, padding_side='left')
        model = AutoModel.from_pretrained(mdir, torch_dtype=torch.float16).to('cuda').eval()

        def enc(texts, bs=16):
            out = []
            for i in range(0, len(texts), bs):
                b = tok(texts[i:i + bs], padding=True, truncation=True, max_length=512, return_tensors='pt').to('cuda')
                with torch.no_grad():
                    h = model(**b).last_hidden_state
                out.append(F.normalize(h[:, -1].float(), dim=-1))
            return torch.cat(out)

        res = {'format': 'ptp-bridgeret-general-v1', 'amendment': 'AM-6(c)', 'model': mdir, 'tasks': {}}
        for t, instr in TASKS.items():
            t0 = time.time(); d = Path(data_dir) / t
            corpus = [json.loads(l) for l in open(d / 'corpus.jsonl', encoding='utf-8')]
            queries = [json.loads(l) for l in open(d / 'queries.jsonl', encoding='utf-8')]
            rel = read_qrels(d / 'qrels.tsv')
            D = enc([c['text'] for c in corpus])
            Q = enc([f'Instruct: {instr}\nQuery: {q["text"]}' for q in queries])
            ids = [c['id'] for c in corpus]
            rankings = {}
            for i, q in enumerate(queries):
                order = torch.argsort(D @ Q[i], descending=True, stable=True)[:101].tolist()
                r = [ids[j] for j in order if not (t in SELF_EXCLUDE and ids[j] == q['id'])]
                rankings[q['id']] = r[:100]
            res['tasks'][t] = {**score_task(rankings, rel), 'n_docs': len(corpus), 'seconds': round(time.time() - t0, 1)}
            print(t, res['tasks'][t], flush=True)
        Path(out_json).write_text(json.dumps(res, indent=1))
    finally:
        fcntl.flock(lockf, fcntl.LOCK_UN)


if __name__ == '__main__':
    cmd, args = sys.argv[1], sys.argv[2:]
    {'build': cmd_build, 'run': cmd_run}[cmd](*args)
