"""Paper 1 S5 CPU-only dev evaluation (frozen protocol sections 5-6 + A1 C1-C3); dev qrels only.

Aggregates are public (summary.json); per-query values stay private. Descriptive only: no significance claims,
no gatekeeping verdicts (protocol section 6). No model, no GPU, no test data.
"""
import hashlib, json, resource, sys, time
from pathlib import Path
sys.path.insert(0, '/code/src')
INPUTS = ('corpus.jsonl', 'queries.jsonl', 'qrels.jsonl', 'reference.jsonl', 'shuffle.jsonl',
          'FA-panel.jsonl', 'GR-panel.jsonl', 'SACR-panel.jsonl', 'retrieval-completion.json')


def stream_sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''): h.update(block)
    return h.hexdigest()


def main():
    raw = Path('/declaration.json').read_bytes()
    if hashlib.sha256(raw).hexdigest() != sys.argv[1]: raise RuntimeError('declaration changed')
    d = json.loads(raw)
    if d.get('kind') != 'paper1-dev-eval' or d.get('model_calls') != 0 or not 1 <= d.get('cpu_seconds', 0) <= 600:
        raise RuntimeError('CPU-only evaluation scope required')
    resource.setrlimit(resource.RLIMIT_CPU, (d['cpu_seconds'], d['cpu_seconds']))
    out = Path('/out/attempt'); out.mkdir(exist_ok=False); started = time.monotonic()
    try:
        from patent_to_pilot.research.r7_dispatch_files import validate_worker_package
        validate_worker_package('/code', d['files_sha256'], d['package_sha256'])
        for name in INPUTS:
            if stream_sha('/input/' + name) != d['inputs_sha256'][name]: raise RuntimeError('pinned input changed: ' + name)
        from patent_to_pilot.research.paper1_dev_eval import build_systems, evaluate_dev
        def load(p): return [json.loads(l) for l in Path('/input/' + p).read_text(encoding='utf-8').splitlines() if l.strip()]
        corpus = []  # streamed: the corpus file is ~330 MB and only family IDs are needed
        with open('/input/corpus.jsonl', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    corpus.append({'relevant_id': json.loads(line)['id'], 'title_en': '', 'abstract_en': '', 'claims_text': ''})
        queries = [{'query_id': r['id'], 'title_en': '', 'abstract_en': ''} for r in load('queries.jsonl')]
        relations = load('qrels.jsonl')
        table = lambda p: {r['query_id']: r['families'] for r in load(p)}
        retrieval = json.loads(Path('/input/retrieval-completion.json').read_bytes())
        if retrieval.get('status') != 'PAPER1_RANKINGS_COMPLETE_NOT_EVALUATED' or retrieval.get('labels_used') is not False:
            raise RuntimeError('retrieval receipt not complete')
        c1 = {arm: retrieval['c1_manipulation_and_truncation'][arm]['verdict'] for arm in ('FA', 'GR', 'SACR')}
        systems = build_systems(table('reference.jsonl'), table('shuffle.jsonl'),
                                {arm: table(arm + '-panel.jsonl') for arm in ('FA', 'GR', 'SACR')}, c1)
        if set(systems['B0']) != {q['query_id'] for q in queries}: raise RuntimeError('rankings must cover all dev queries')
        public, private = evaluate_dev(corpus, queries, relations, systems)
        (out / 'private-per-query.json').write_text(json.dumps(private) + '\n')
        summary = {'status': 'PAPER1_DEV_EVALUATED_DESCRIPTIVE', 'dev_queries': len(queries), 'results': public,
                   'retrieval_reference': retrieval['anchor_check']['reference'], 'panel_counts': retrieval['panel_counts'],
                   'c1': retrieval['c1_manipulation_and_truncation'], 'protected_test_access': False,
                   'significance_claim': False, 'gatekeeping_applied': False,
                   'process_cpu_seconds': time.process_time(), 'wall_seconds': time.monotonic() - started}
        (out / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    except BaseException as error:
        (out / 'failure.json').write_text(json.dumps({'exception_type': type(error).__name__, 'message': str(error)[:300],
                                                      'process_cpu_seconds': time.process_time()}) + '\n')
        raise


if __name__ == '__main__':
    main()
