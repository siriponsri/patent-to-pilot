"""Evaluate the completed native baseline on the isolated dev projection only.

No runtime invocation or GPU/model imports. Full-precision per-query outputs
are private; summary.json contains aggregates and provenance only.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'src'))
from patent_to_pilot.evaluation.dapfam_native import native_dev_task, evaluate_paper1_dev

PINS = {
    'runtime/manifest.json': 'fd950817b3cab234c4175bb6c68cc9942ae4fcafd8c7108f2adeaab1ce161c1f',
    'runtime/corpus.jsonl': '42f895cd411b344f7be4de4c77bfab66797aa2a1d92353dbee82669fc569af0d',
    'runtime/queries-ta.jsonl': '6fa09d71c96b0e18f5b7986add7011d17ba6826bad753d7a0cc52a2ce5859d2a',
    'evaluation/manifest.json': '604a4d33f29913a5d6bcd78c9d069b16f4505dadf3b06c27192ba8d612713881',
    'evaluation/qrels-dev.jsonl': 'ca693dc8a1d5c5bf10249c8e9438be5198346349dcd1b6a6194e0eeb96923473',
    'rankings/completion.json': 'e8491731e484cb6e14ee9c6b39656dab7a17ba9ef0bf4b420244194a4235c062',
    'rankings/rankings-top200.jsonl': '26cfc1e0b9aa02477ca367cb07faee65d37f5e994e1625f29facbee2e007fb29',
    'rankings/query-vectors-f32.npy': '2a3573d615dccaeff4ae0c44850fad64813d56068538e0c5df29a1700a4ee8ea',
}


def sha(path):
    d = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024**2), b''):
            d.update(block)
    return d.hexdigest()


def rows(path):
    with path.open(encoding='utf-8') as f:
        return [json.loads(line) for line in f if line.strip()]


def checked_rankings(records, query_ids):
    result = {}
    for row in records:
        query, families, scores = row['query_id'], row['families'], row['scores']
        if query in result or query not in query_ids or len(families) != 200 or len(scores) != 200:
            raise ValueError('invalid baseline output population or depth')
        if any(type(v) not in (int, float) or not math.isfinite(v) for v in scores):
            raise ValueError('invalid baseline scores')
        if list(zip(scores, families)) != sorted(zip(scores, families), key=lambda x: (-x[0], x[1])):
            raise ValueError('baseline order violates declared score/tie rule')
        if len(set(families)) != len(families):
            raise ValueError('duplicate baseline family')
        result[query] = families
    if set(result) != query_ids:
        raise ValueError('completed baseline missing query output')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError('exclusive evaluator destination exists')
    for name, expected in PINS.items():
        if sha(args.inputs / name) != expected:
            raise ValueError('evaluator input pin mismatch')
    raw_corpus = rows(args.inputs / 'runtime/corpus.jsonl')
    corpus = [{'relevant_id': r['id'], 'title_en': '', 'abstract_en': '', 'claims_text': ''}
              for r in raw_corpus]
    del raw_corpus  # Text is irrelevant to metric calculation.
    queries = [{'query_id': r['id'], 'title_en': '', 'abstract_en': ''}
               for r in rows(args.inputs / 'runtime/queries-ta.jsonl')]
    relations = rows(args.inputs / 'evaluation/qrels-dev.jsonl')
    if len(corpus) != 45336 or len(queries) != 474:
        raise ValueError('unexpected native evaluation population')
    rankings = checked_rankings(rows(args.inputs / 'rankings/rankings-top200.jsonl'),
                                {r['query_id'] for r in queries})
    summaries, private = {}, {}
    for partition, count in [('ALL', 474), ('IN', 450), ('OUT', 349)]:
        task = native_dev_task(corpus, queries, relations, partition=partition)
        result = evaluate_paper1_dev(task, rankings)
        if result['queries'] != count:
            raise ValueError('native eligible denominator changed')
        private[partition] = result.pop('per_query')
        summaries[partition] = result
    args.output.mkdir(exist_ok=False)
    private_path = args.output / 'private-per-query.json'
    private_path.write_text(json.dumps(private, indent=2), encoding='utf-8')
    summary = {'status': 'COMPLETED_DEV_ONLY', 'partitions': summaries,
               'input_pins': PINS, 'private_per_query_sha256': sha(private_path),
               'protected_test_access': False, 'published_score_replication': False}
    (args.output / 'summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print(json.dumps({'status': summary['status'], 'summary_sha256': sha(args.output / 'summary.json')}))


if __name__ == '__main__':
    main()
