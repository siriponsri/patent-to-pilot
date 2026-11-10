"""CPU-only private history seal; no retry grant, model loading or generation."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))
from patent_to_pilot.research.sacr_continuation import seal_terminal_history, canonical_continuation_root
from patent_to_pilot.research.sacr_native_fidelity import bind_sample, write_new


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('prior-output', 'terminal', 'queries', 'sample', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    for name in ('container', 'terminal-sha256', 'query-sha256', 'sample-sha256'):
        parser.add_argument('--' + name, required=True)
    args = parser.parse_args()
    start = time.monotonic()
    if args.output.resolve().is_relative_to(args.prior_output.resolve()):
        raise ValueError('private plan cannot modify the prior sealed output')
    if args.output.exists():
        raise ValueError('plan destination already exists')
    entries = bind_sample(args.queries.read_bytes(), args.sample.read_bytes(),
        query_sha256=args.query_sha256, sample_sha256=args.sample_sha256)
    observed = json.loads(subprocess.run(['docker', 'inspect', args.container],
        check=True, capture_output=True, text=True, timeout=10).stdout)[0]['State']
    manifest = seal_terminal_history(entries=entries, prior_output=args.prior_output,
        terminal_raw=args.terminal.read_bytes(), terminal_sha256=args.terminal_sha256,
        observed_state=observed, prompt_root=ROOT / 'docs/healthtech/research/prompts',
        sample_sha256=args.sample_sha256, query_sha256=args.query_sha256)
    destination = canonical_continuation_root(args.prior_output, manifest)
    args.output.mkdir(parents=True, exist_ok=False)
    manifest_hash = write_new(args.output / 'continuation.json', manifest)
    write_new(args.output / 'observed-prior-state.json', observed)
    summary = {'status': 'PRIVATE_HISTORY_SEALED_NO_GENERATION', 'sample_queries': 100,
        'never_started_queries': len(manifest['selected_indices']),
        'blocked_prior_queries': len(manifest['blocked_indices']),
        'normal_return_consumed_queries': sum(r['state'] == 'NORMAL_RETURN_CONSUMED' for r in manifest['records']),
        'manifest_sha256': manifest_hash, 'prior_terminal_sha256': args.terminal_sha256,
        'canonical_output_directory_name': destination.parent.name,
        'sealed_files': len(manifest['prior_files_sha256']), 'model_calls': 0,
        'retry_authorized': False, 'wall_seconds': time.monotonic() - start,
        'preparer_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    write_new(args.output / 'public-summary.json', summary)
    print(json.dumps(summary))


if __name__ == '__main__':
    main()
