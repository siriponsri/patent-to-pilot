"""CPU-only Graph extractor v3: corpus postings + query census + frozen gate; no qrels/model."""
import hashlib, json, resource, sys, time
from pathlib import Path
sys.path.insert(0, '/code/src')


def main():
    raw = Path('/declaration.json').read_bytes()
    if hashlib.sha256(raw).hexdigest() != sys.argv[1]: raise RuntimeError('declaration changed')
    d = json.loads(raw)
    if d.get('kind') != 'graph-extractor-v3' or d.get('model_calls') != 0 or not 1 <= d.get('cpu_seconds', 0) <= 270:
        raise RuntimeError('CPU-only census scope required')
    resource.setrlimit(resource.RLIMIT_CPU, (d['cpu_seconds'], d['cpu_seconds']))
    out = Path('/out/attempt'); out.mkdir(exist_ok=False); started = time.monotonic()
    try:
        from patent_to_pilot.research.r7_dispatch_files import validate_worker_package
        validate_worker_package('/code', d['files_sha256'], d['package_sha256'])
        q_raw = Path('/input/queries.jsonl').read_bytes()
        h = hashlib.sha256()
        with open('/input/corpus.jsonl', 'rb') as f:
            for block in iter(lambda: f.read(1 << 20), b''): h.update(block)
        if hashlib.sha256(q_raw).hexdigest() != d['queries_sha256'] or h.hexdigest() != d['corpus_sha256']:
            raise RuntimeError('pinned input changed')
        from patent_to_pilot.research.graph_extractor_v3_census import evaluate
        queries = [json.loads(line) for line in q_raw.decode().splitlines() if line.strip()]
        with open('/input/corpus.jsonl', encoding='utf-8') as corpus:
            result, _ = evaluate(corpus, [{'id': q['id'], 'text': q['text']} for q in queries])
        pilot = json.dumps(result['pilot_ids']).encode()
        private = {'rows': result.pop('rows'), 'pilot_ids': result.pop('pilot_ids')}
        result.update(pilot_ids_sha256=hashlib.sha256(pilot).hexdigest(), queries_sha256=d['queries_sha256'],
                      corpus_sha256=d['corpus_sha256'], wall_seconds=time.monotonic()-started,
                      process_cpu_seconds=time.process_time(), model_calls=0, status='CENSUS_COMPLETE')
        (out/'private.json').write_text(json.dumps(private) + '\n')
        (out/'aggregate.json').write_text(json.dumps(result, indent=2) + '\n')
    except BaseException as error:
        (out/'failure.json').write_text(json.dumps({'exception_type': type(error).__name__,
            'process_cpu_seconds': time.process_time(), 'model_calls': 0}) + '\n'); raise


if __name__ == '__main__': main()
