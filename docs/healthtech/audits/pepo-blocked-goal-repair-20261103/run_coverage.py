"""Reproduce coverage with measured hashes and scoped Git metadata; no network."""
from pathlib import Path
import argparse
import datetime
import hashlib
import importlib.util
import json
import subprocess
import time


def sha256_file(path):
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def hashes(paths):
    return {name: sha256_file(path) for name, path in paths.items()}


def changed_inputs(before, after):
    return sorted(name for name in before.keys() | after.keys()
                  if before.get(name) != after.get(name))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--data-root', type=Path, required=True)
    parser.add_argument('--duckdb', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--candidate-head', required=True)
    args = parser.parse_args()
    repo, data = args.repo.resolve(), args.data_root.resolve()
    git = ['git', '--no-optional-locks', '-c', 'safe.directory=' + str(repo), '-C', str(repo)]
    actual_head = subprocess.check_output(git + ['rev-parse', 'HEAD'], text=True).strip()
    if actual_head != args.candidate_head:
        raise RuntimeError('candidate HEAD mismatch')
    # A changed tracked source proves dirty=True. An unchanged scoped source
    # cannot prove the whole checkout clean: record unknown instead of False.
    scope = 'scripts/healthtech/analyze_dapfam_coverage.py'
    diff = subprocess.run(git + ['diff', '--quiet', 'HEAD', '--', scope], check=False)
    if diff.returncode not in (0, 1):
        raise RuntimeError('scoped Git diff failed')
    dirty = True if diff.returncode == 1 else None
    source = repo / scope
    paths = {name: data / name for name in ('corpus.parquet', 'queries.parquet', 'qrels_all.parquet')}
    paths['analyzer_source'] = source
    paths['runner_source'] = Path(__file__).resolve()
    before = hashes(paths)
    root = args.output.resolve()
    root.mkdir(parents=True, exist_ok=False)
    spec = importlib.util.spec_from_file_location('repaired_coverage', source)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    # Only Git metadata probes are substituted, using measured observations.
    # All input SQL, data hashing and result writing remain the real analyzer.
    mod.git_revision = lambda: actual_head
    mod.git_worktree_dirty = lambda: dirty
    start = datetime.datetime.now(datetime.timezone.utc).isoformat()
    tick = time.perf_counter()
    result = mod.run(argparse.Namespace(duckdb=args.duckdb.resolve(),
        corpus=data / 'corpus.parquet', queries=data / 'queries.parquet',
        qrels=data / 'qrels_all.parquet', output=root / 'coverage-corrected'))
    after = hashes(paths)
    final_head = subprocess.check_output(git + ['rev-parse', 'HEAD'], text=True).strip()
    changed = changed_inputs(before, after)
    stable = not changed and actual_head == final_head
    receipt = {
        'status': 'PASS' if stable else 'INVALID_CONCURRENT_MUTATION',
        'started_utc': start,
        'completed_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'wall_seconds': time.perf_counter() - tick,
        'candidate_head': actual_head, 'final_head': final_head, 'dirty': dirty,
        'source_sha256': before['analyzer_source'],
        'git_metadata_probe': 'rev-parse HEAD before/after; tracked analyzer diff against HEAD only; null dirty means whole-checkout cleanliness unknown',
        'scoped_diff_path': scope, 'scoped_diff_exit_code': diff.returncode,
        'execution': 'real repaired analyzer.run and native DuckDB; no data/results mocked',
        'duckdb_version': result['runtime']['duckdb_version'],
        'source_hashes_before': before, 'source_hashes_after': after,
        'changed_inputs': changed, 'source_inputs_unchanged': not changed,
        'head_unchanged': actual_head == final_head,
        'provider_calls': 0, 'paid_cost_usd': 0, 'gpu_jobs': 0,
        'threads': 4, 'memory_limit': '4GB',
        'screening': result['screening'], 'positive_qrels': result['positive_qrels'],
    }
    if not stable:
        # Keep invalid evidence, but prevent a stray analyzer PASS being reused.
        summary_path = root / 'coverage-corrected/summary.json'
        result['status'] = 'INVALID_CONCURRENT_MUTATION'
        summary_path.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    (root / 'coverage-run-receipt.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(receipt))
    if not stable:
        raise RuntimeError('input/source/HEAD changed during evaluation; outputs invalid')


if __name__ == '__main__':
    main()
