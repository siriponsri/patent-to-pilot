"""Independent, read-only DAPFAM arithmetic review; emits aggregates only."""
from pathlib import Path
import argparse, ast, collections, datetime, hashlib, json, math, statistics, time
import pyarrow as pa
import pyarrow.parquet as pq

pa.set_cpu_count(4)
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--repo', type=Path, required=True)
parser.add_argument('--historical-worktree', type=Path, required=True)
parser.add_argument('--data-root', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
ROOT = args.output.resolve()
ROOT.mkdir(parents=True, exist_ok=False)
REPO = args.repo.resolve()
OLD = args.historical_worktree.resolve()
DATA = args.data_root.resolve()
AUDIT = REPO / 'docs/healthtech/audits/pepo-blocked-goal-repair-20261103'
TERMS = ('balloon', 'catheter', 'cardiac', 'cardiovascular', 'delivery system', 'embol',
         'endovascular', 'graft', 'guidewire', 'implant', 'medical device', 'occluder',
         'prosthesis', 'stent', 'surgical', 'thrombectomy', 'valve', 'vascular')

def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()

def selected(path, key):
    # Literal substring matching, independently of regex, SQL, or production code.
    records = pq.read_table(path, columns=[key, 'title_en', 'abstract_en']).to_pylist()
    ids = [r[key] for r in records]
    assert len(ids) == len(set(ids)), 'duplicate input IDs'
    chosen = {r[key] for r in records if any(t in ((r['title_en'] or '') + ' ' +
              (r['abstract_en'] or '')).lower() for t in TERMS)}
    return set(ids), chosen

paths = {n: DATA / n for n in ('corpus.parquet', 'queries.parquet', 'qrels_all.parquet')}
paths['coverage_source'] = REPO / 'scripts/healthtech/analyze_dapfam_coverage.py'
paths['coverage_tests'] = REPO / 'tests/test_healthtech_dapfam_coverage.py'
paths['reported_medical'] = AUDIT / 'medical-subset-results.json'
paths['reported_coverage'] = AUDIT / 'coverage-summary.json'
paths['independent_reviewer_source'] = Path(__file__).resolve()
for model in ('patembed', 'e5'):
    folder = OLD / 'results/healthtech' / ('ht-transformer-eval-20261031-' + model)
    paths[model + '_rankings'] = folder / 'rankings.jsonl'
    paths[model + '_summary'] = folder / 'summary.json'
started = datetime.datetime.now(datetime.timezone.utc).isoformat()
tick = time.perf_counter()
before = {name: digest(path) for name, path in paths.items()}
tree = ast.parse(paths['coverage_source'].read_text(encoding='utf-8-sig'))
declared = next(ast.literal_eval(n.value) for n in tree.body
                if isinstance(n, ast.AnnAssign) and getattr(n.target, 'id', None) == 'LEXICON')
assert tuple(declared['medical_device']) == TERMS
all_queries, queries = selected(DATA / 'queries.parquet', 'query_id')
all_targets, targets = selected(DATA / 'corpus.parquet', 'relevant_id')
rows = pq.read_table(DATA / 'qrels_all.parquet').to_pylist()
seen = set()
positive = collections.defaultdict(set)
labels = collections.Counter()
partition = collections.Counter()
domain = collections.defaultdict(collections.Counter)
for r in rows:
    q, d, v = r['query_id'], r['relevant_id'], r['relevance_score']
    assert (q, d) not in seen, 'duplicate qrel pair'
    seen.add((q, d))
    assert q in all_queries and d in all_targets
    labels[str(v)] += 1
    assert v in (0, 1), 'binary-only review must not silently accept graded labels'
    if v > 0:
        positive[q].add(d)
        p = ('query_yes' if q in queries else 'query_no') + '_' + ('target_yes' if d in targets else 'target_no')
        partition[p] += 1
        domain[r['domain_rel']][p] += 1
denominator = sum(len(positive[q]) for q in queries)
both = sum(len(positive[q] & targets) for q in queries)
assert (len(queries), len(targets), denominator, both) == (96, 3061, 1920, 983)
reported = json.loads(paths['reported_medical'].read_text())
reported_lookup = {(r['model'], r['method']): r for r in reported['results']}
results, saved = [], {}
for model in ('patembed', 'e5'):
    predictions = collections.defaultdict(dict)
    with paths[model + '_rankings'].open() as f:
        for line in f:
            r = json.loads(line)
            q, m = r['query_id'], r['method']
            if q not in queries:
                continue
            assert q not in predictions[m], 'duplicate ranking record'
            pred = r['ranked_ids']
            assert len(pred) == 100 and len(set(pred)) == 100
            assert set(pred) <= all_targets
            predictions[m][q] = pred
    assert set(predictions) == {'bm25', 'dense', 'hybrid_rrf'}
    saved[model] = predictions
    for method, by_query in predictions.items():
        assert set(by_query) == queries
        counts, recalls, ndcgs, self_hits = [], [], [], 0
        for q in sorted(queries):
            pred = by_query[q]
            relevant = positive[q]
            ranks = [i + 1 for i, d in enumerate(pred) if d in relevant]
            count = len(ranks)
            counts.append(count)
            recalls.append(count / len(relevant))
            # Binary gain: discounted contribution only at relevant ranks.
            numerator = math.fsum(1 / math.log2(rank + 1) for rank in ranks)
            ideal = math.fsum(1 / math.log2(rank + 1) for rank in range(1, min(100, len(relevant)) + 1))
            ndcgs.append(numerator / ideal)
            self_hits += int(q in relevant and q in pred)
        actual = {'hits_at_100': sum(counts), 'positive_pairs': denominator,
                  'macro_recall_at_100': statistics.mean(recalls),
                  'micro_recall_at_100': sum(counts) / denominator,
                  'macro_ndcg_at_100': statistics.mean(ndcgs)}
        expected = reported_lookup[(model, method)]
        deltas = {name: actual[name] - expected[name] for name in actual}
        assert all(abs(d) < 1e-12 for d in deltas.values())
        results.append({'model': model, 'method': method, **actual,
                        'positive_self_hits_in_top100': self_hits,
                        'difference_from_reported': deltas, 'status': 'VERIFIED'})
assert saved['patembed']['bm25'] == saved['e5']['bm25'], 'BM25 reference mismatch'
membership = hashlib.sha256('\n'.join(sorted(queries)).encode()).hexdigest()
assert membership == reported['query_membership_sha256']
after = {name: digest(path) for name, path in paths.items()}
assert before == after, 'concurrent input/source change during review'
out = {'status': 'VERIFIED_INDEPENDENT_ARITHMETIC', 'started_utc': started,
       'completed_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
       'wall_seconds': time.perf_counter() - tick,
       'method': 'PyArrow selected columns + literal substring screen; set-based binary qrels and rank-position DCG; no production function imported or called',
       'corpus_rows': len(all_targets), 'query_rows': len(all_queries), 'qrel_rows': len(rows),
       'medical_queries': len(queries), 'medical_targets': len(targets),
       'query_screen_positive_denominator': denominator, 'both_screen_positives': both,
       'query_screen_positive_targets_outside_medical_screen': denominator - both,
       'partition': dict(partition), 'domain_partition': {k: dict(v) for k,v in domain.items()},
       'qrel_labels': dict(labels), 'duplicate_qrel_pairs': 0,
       'positive_counts_per_selected_query': dict(collections.Counter(len(positive[q]) for q in queries)),
       'selected_query_ids_in_corpus': len(queries & all_targets),
       'selected_positive_self_pairs': sum(q in positive[q] for q in queries),
       'selected_queries_without_any_both_screen_positive': sum(not (positive[q] & targets) for q in queries),
       'query_membership_sha256': membership, 'matched_bm25_rankings_identical': True,
       'metrics': results, 'source_hashes_before': before, 'source_hashes_after': after,
       'inputs_stable_during_check': before == after,
       'scope': 'Posthoc query-side diagnostic using full corpus and Oct31 saved rankings; not a held-out semantic medical-device benchmark; family dependence and training contamination not ruled out',
       'new_model_calls': 0, 'paid_calls': 0, 'metadata_calls': 0, 'gpu_jobs': 0}
(ROOT / 'independent-review.json').write_text(json.dumps(out, indent=2) + '\n')
print(json.dumps({k:v for k,v in out.items() if 'hashes' not in k}, indent=2))
