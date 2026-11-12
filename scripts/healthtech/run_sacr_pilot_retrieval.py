"""SACR pilot retrieval (NATIVE-STAGES-20261112 addendum, frozen before any SACR score).

Encodes the 20 pilot anchors (original TA) and every screened SACR candidate with exactly the
B0 encoder, prefix, passage vectors, owners and rank_maxp; writes private top-200 rankings and
the anchor reproduction check. No qrels, no evaluation, no model generation.
"""
import hashlib, json, sys, time
from pathlib import Path
sys.path[:0] = ['/code/src', '/code/scripts/healthtech']
sha = lambda b: hashlib.sha256(b).hexdigest()


def main():
    from patent_to_pilot.healthtech.local_execution import check_local_window, local_gpu_slot
    from patent_to_pilot.research.r7_dispatch_files import validate_worker_package, validate_deadline
    from patent_to_pilot.research.sacr_pilot_panel import encode_plan, anchor_check, assemble
    from run_dapfam_native_baseline import verify_inputs, MeanPoolEncoder, rank_maxp, DENSE_QUERY_PREFIX, dense_passages
    from run_dapfam_dense_pool import _read_jsonl, _sha256
    stop = float(sys.argv[1]); raw = Path('/dispatch/declaration.json').read_bytes()
    if sha(raw) != sys.argv[2]: raise RuntimeError('dispatch declaration changed')
    d = json.loads(raw)
    # maximum_calls=1 only satisfies the journal's positive-ceiling rule; this stage makes 0 generation calls.
    if d['stage'] != 'pilot' or d['seconds'] > 1800 or d['maximum_calls'] != 1:
        raise RuntimeError('pilot retrieval contract required')
    validate_deadline(stop, time.monotonic(), d['seconds'])
    validate_worker_package(Path('/code'), d['files_sha256'], d['package_sha256'])
    check_local_window()
    native = Path('/native'); pilot_raw = (native / 'dispatch/queries.jsonl').read_bytes()
    if sha(pilot_raw) != d['input_manifest_sha256']: raise RuntimeError('pilot input changed')
    pilot = [json.loads(line) for line in pilot_raw.decode().splitlines() if line.strip()]
    decisions_raw = (native / 'out/attempt/decisions-private.json').read_bytes()
    if sha(decisions_raw) != d['decisions_sha256']: raise RuntimeError('native decisions changed')
    decisions = json.loads(decisions_raw); candidates = {}
    for i, p in enumerate(pilot):
        c = native / 'out/attempt/queries' / ('q%03d' % i) / 'candidate.json'
        if c.exists(): candidates[p['id']] = json.loads(c.read_bytes()).get('selective')
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
    rows = encode_plan(pilot, decisions, candidates, DENSE_QUERY_PREFIX)
    out = Path('/out/attempt'); out.mkdir(exist_ok=False); started = time.monotonic()
    with local_gpu_slot(model):
        encoder = MeanPoolEncoder(model, 32, device='cuda'); torch = encoder.torch
        torch.set_num_threads(8); torch.backends.cuda.matmul.allow_tf32 = False
        t = time.monotonic(); encoded = encoder.encode([text for _, _, text in rows]); encode_s = time.monotonic() - t
        matrix = torch.from_numpy(np.array(vectors)).to('cuda'); rankings = {'anchor': {}, 'sacr': {}}
        for (kind, qid, _), vec in zip(rows, encoded, strict=True):
            scores = (torch.from_numpy(vec).to('cuda') @ matrix.T).cpu().numpy()
            rankings[kind][qid] = {'query_id': qid, **rank_maxp(scores, owners, ids)}
    check = anchor_check(rankings['anchor'], b0)
    reference = {q: b0[q] for q in rankings['anchor']} if check['reference'] == 'B0_PINNED' else rankings['anchor']
    panel, counts = assemble(pilot, decisions, rankings['sacr'], reference)
    for name, table in (('anchor', rankings['anchor']), ('sacr', rankings['sacr']), ('panel', panel), ('reference', reference)):
        with (out / (name + '-top200-private.jsonl')).open('x', encoding='utf-8') as f:
            for p in pilot:
                if p['id'] in table: f.write(json.dumps(dict(table[p['id']], query_id=p['id'])) + '\n')
    receipt = {'status': 'PILOT_RANKINGS_COMPLETE_NOT_EVALUATED', 'queries': len(pilot), 'encoded_texts': len(rows),
               'anchor_check': check, 'panel_counts': counts, 'query_prefix': DENSE_QUERY_PREFIX,
               'encode_seconds': encode_s, 'wall_seconds': time.monotonic() - started, 'labels_used': False, 'model_calls': 0,
               'files_sha256': {p.name: _sha256(p) for p in sorted(out.glob('*-private.jsonl'))}}
    (out / 'completion.json').write_text(json.dumps(receipt, indent=2) + '\n')


if __name__ == '__main__':
    main()
