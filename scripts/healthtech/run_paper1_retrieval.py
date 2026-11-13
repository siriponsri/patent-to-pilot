"""Paper 1 retrieval (frozen protocol 2026-11-13 + amendment A1): encode anchors, the F-shuffle control and arm
texts with exactly the B0 encoder, prefix, passage vectors, owners and rank_maxp; write private top-200 rankings.

No qrels, no evaluation, no generation. C1 manipulation statistics (label-free) are written to the receipt.
Arm jobs are mounted read-only at /arm/<ARM>/<k>/{dispatch,out}; decisions are hash-pinned in the declaration.
"""
import hashlib, json, sys, time
from pathlib import Path
sys.path[:0] = ['/code/src', '/code/scripts/healthtech']
sha = lambda b: hashlib.sha256(b).hexdigest()
STAGE_SECONDS = {'pilot': 1800, 'full_dev': 10800}


def load_arm(root, kind, pins):
    """-> [(job_queries, decisions, texts)] for the arm's jobs in declared order."""
    sources = []
    for k, pin in enumerate(pins):
        base = root / str(k)
        queries_raw = (base / 'dispatch/queries.jsonl').read_bytes(); decisions_raw = (base / 'out/decisions-private.json').read_bytes()
        if sha(queries_raw) != pin['queries_sha256'] or sha(decisions_raw) != pin['decisions_sha256']:
            raise RuntimeError('arm job input changed')
        queries = [json.loads(line) for line in queries_raw.decode().splitlines() if line.strip()]
        texts = {}
        for i, q in enumerate(queries):
            folder = base / 'out/queries' / ('q%03d' % i)
            if kind == 'rewrite':
                result = json.loads((folder / 'result.json').read_bytes())
                if result['query_id'] != q['id']: raise RuntimeError('arm result identity mismatch')
                if result.get('text'): texts[q['id']] = result['text']
            elif (folder / 'candidate.json').exists():
                texts[q['id']] = json.loads((folder / 'candidate.json').read_bytes()).get('selective')
        sources.append((queries, json.loads(decisions_raw), texts))
    return sources


def main():
    from patent_to_pilot.healthtech.local_execution import check_local_window, local_gpu_slot
    from patent_to_pilot.research.r7_dispatch_files import validate_worker_package, validate_deadline
    from patent_to_pilot.research.paper1_retrieval_panel import merge_sources, encode_plan, anchor_check, assemble, USE_ACTIONS
    from patent_to_pilot.research.paper1_controls import manipulation_check, truncation_share
    from run_dapfam_native_baseline import verify_inputs, MeanPoolEncoder, rank_maxp, DENSE_QUERY_PREFIX, dense_passages
    from run_dapfam_dense_pool import _read_jsonl, _sha256
    stop = float(sys.argv[1]); raw = Path('/dispatch/declaration.json').read_bytes()
    if sha(raw) != sys.argv[2]: raise RuntimeError('dispatch declaration changed')
    d = json.loads(raw)
    # maximum_calls=1 only satisfies the journal's positive-ceiling rule; this stage makes 0 generation calls.
    if (d['stage'] not in STAGE_SECONDS or d['seconds'] > STAGE_SECONDS[d['stage']] or d['maximum_calls'] != 1
            or d.get('generation_calls') != 0 or type(d.get('arms')) is not dict or not d['arms']
            or any(a.get('kind') not in USE_ACTIONS or not a.get('jobs') for a in d['arms'].values())):
        raise RuntimeError('Paper 1 retrieval contract required')
    validate_deadline(stop, time.monotonic(), d['seconds'])
    validate_worker_package(Path('/code'), d['files_sha256'], d['package_sha256'])
    check_local_window()
    queries_raw = Path('/dispatch/queries.jsonl').read_bytes()
    if sha(queries_raw) != d['input_manifest_sha256']: raise RuntimeError('retrieval query set changed')
    queries = [json.loads(line) for line in queries_raw.decode().splitlines() if line.strip()]
    if len(queries) != d['queries']: raise RuntimeError('frozen query count required')
    arms = {name: merge_sources(queries, load_arm(Path('/arm') / name, a['kind'], a['jobs']), a['kind'])
            for name, a in d['arms'].items()}
    b0_path = Path('/b0/rankings-top200.jsonl')
    if _sha256(b0_path) != d['b0_rankings_sha256']: raise RuntimeError('B0 rankings changed')
    b0 = {r['query_id']: r for r in _read_jsonl(b0_path, None)}
    import numpy as np
    runtime, model, vectors_path = Path('/runtime'), Path('/models/patembed-large'), Path('/vectors/passage-vectors-f32.npy')
    verify_inputs(runtime, model, vectors_path)
    corpus = _read_jsonl(runtime / 'corpus.jsonl', None); ids = [r['id'] for r in corpus]
    owners = np.asarray([i for i, r in enumerate(corpus) for _ in dense_passages(r['title'], r['abstract'], r['claims'])], dtype=np.int64)
    vectors = np.load(vectors_path, mmap_mode='r', allow_pickle=False)
    if vectors.shape != (188944, 1024) or len(owners) != len(vectors): raise RuntimeError('passage/vector mismatch')
    rows = encode_plan(queries, arms, DENSE_QUERY_PREFIX)
    out = Path('/out/attempt'); out.mkdir(exist_ok=False); started = time.monotonic()
    with local_gpu_slot(model):
        encoder = MeanPoolEncoder(model, 32, device='cuda'); torch = encoder.torch
        torch.set_num_threads(8); torch.backends.cuda.matmul.allow_tf32 = False
        lengths = {}
        for kind, qid, text in rows:
            lengths.setdefault(kind, []).append(len(encoder.tokenizer(text, truncation=False)['input_ids']))
        t = time.monotonic(); encoded = encoder.encode([text for _, _, text in rows]); encode_s = time.monotonic() - t
        matrix = torch.from_numpy(np.array(vectors)).to('cuda'); rankings = {}
        for (kind, qid, _), vec in zip(rows, encoded, strict=True):
            scores = (torch.from_numpy(vec).to('cuda') @ matrix.T).cpu().numpy()
            rankings.setdefault(kind, {})[qid] = {'query_id': qid, **rank_maxp(scores, owners, ids)}
    check = anchor_check(rankings['anchor'], b0)
    reference = {q['id']: b0[q['id']] for q in queries} if check['reference'] == 'B0_PINNED' else rankings['anchor']
    tables = {'anchor': rankings['anchor'], 'reference': reference, 'shuffle': rankings['shuffle']}
    families = lambda table: {q: r['families'] for q, r in table.items()}
    controls = {'shuffle': dict(manipulation_check(families(reference), families(rankings['shuffle']), set(rankings['shuffle'])),
                                truncation=truncation_share(lengths['shuffle'], encoder.max_length))}
    counts = {}
    for name, (decisions, texts) in arms.items():
        used = rankings.get(name, {})
        panel, counts[name] = assemble(queries, texts, used, reference)
        tables[name + '-used'] = used; tables[name + '-panel'] = panel
        controls[name] = dict(manipulation_check(families(reference), families(panel), set(texts)),
                              truncation=truncation_share(lengths[name], encoder.max_length) if texts else None)
    controls['anchor_truncation'] = truncation_share(lengths['anchor'], encoder.max_length)
    for name, table in tables.items():
        with (out / (name + '-top200-private.jsonl')).open('x', encoding='utf-8') as f:
            for q in queries:
                if q['id'] in table: f.write(json.dumps(dict(table[q['id']], query_id=q['id'])) + '\n')
    receipt = {'status': 'PAPER1_RANKINGS_COMPLETE_NOT_EVALUATED', 'stage': d['stage'], 'queries': len(queries), 'encoded_texts': len(rows),
               'anchor_check': check, 'panel_counts': counts, 'c1_manipulation_and_truncation': controls,
               'query_prefix': DENSE_QUERY_PREFIX, 'encoder_max_length': encoder.max_length, 'encode_seconds': encode_s,
               'wall_seconds': time.monotonic() - started, 'process_cpu_seconds': time.process_time(), 'labels_used': False, 'model_calls': 0,
               'files_sha256': {p.name: _sha256(p) for p in sorted(out.glob('*-private.jsonl'))}}
    (out / 'completion.json').write_text(json.dumps(receipt, indent=2) + '\n')


if __name__ == '__main__':
    main()
