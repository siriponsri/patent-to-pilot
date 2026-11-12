"""CPU-only pilot-20 evaluation of B0 vs SACR panel; dev qrels only; aggregates public, per-query private."""
import hashlib, json, resource, sys, time
from pathlib import Path
sys.path.insert(0, '/code/src')


def stream_sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''): h.update(block)
    return h.hexdigest()


def main():
    raw = Path('/declaration.json').read_bytes()
    if hashlib.sha256(raw).hexdigest() != sys.argv[1]: raise RuntimeError('declaration changed')
    d = json.loads(raw)
    if d.get('kind') != 'sacr-pilot-eval' or d.get('model_calls') != 0 or not 1 <= d.get('cpu_seconds', 0) <= 90:
        raise RuntimeError('CPU-only evaluation scope required')
    resource.setrlimit(resource.RLIMIT_CPU, (d['cpu_seconds'], d['cpu_seconds']))
    out = Path('/out/attempt'); out.mkdir(exist_ok=False); started = time.monotonic()
    try:
        from patent_to_pilot.research.r7_dispatch_files import validate_worker_package
        validate_worker_package('/code', d['files_sha256'], d['package_sha256'])
        for name in ('corpus.jsonl', 'queries.jsonl', 'qrels.jsonl', 'panel.jsonl', 'reference.jsonl'):
            if stream_sha('/input/' + name) != d[name.replace('.jsonl', '_sha256')]:
                raise RuntimeError('pinned input changed: ' + name)
        from patent_to_pilot.research.sacr_pilot_eval import evaluate_arms
        corpus = []
        with open('/input/corpus.jsonl', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    corpus.append({'relevant_id': json.loads(line)['id'], 'title_en': '', 'abstract_en': '', 'claims_text': ''})
        def load(p): return [json.loads(l) for l in Path(p).read_text(encoding='utf-8').splitlines() if l.strip()]
        queries = [{'query_id': r['id'], 'title_en': '', 'abstract_en': ''} for r in load('/input/queries.jsonl')]
        relations = load('/input/qrels.jsonl')
        panel = {r['query_id']: r['families'] for r in load('/input/panel.jsonl')}
        reference_rows = load('/input/reference.jsonl')
        reference = {r['query_id']: r['families'] for r in reference_rows}
        pilot = [r['query_id'] for r in reference_rows]
        public, private = evaluate_arms(corpus, queries, relations, pilot, {'B0': reference, 'SACR': panel})
        (out / 'private-per-query.json').write_text(json.dumps(private) + '\n')
        summary = {'status': 'PILOT_EVALUATED_DEV_ONLY', 'pilot_queries': len(pilot), 'partitions': public,
                   'reference': 'B0_PINNED (anchor check 20/20 identical)', 'protected_test_access': False,
                   'significance_claim': False, 'process_cpu_seconds': time.process_time(),
                   'wall_seconds': time.monotonic() - started}
        (out / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    except BaseException as error:
        (out / 'failure.json').write_text(json.dumps({'exception_type': type(error).__name__, 'message': str(error)[:300],
                                                      'process_cpu_seconds': time.process_time()}) + '\n')
        raise


if __name__ == '__main__':
    main()
