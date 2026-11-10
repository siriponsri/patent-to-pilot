"""Seal terminal profile history and identify only never-started sample entries.

No generation, retry permission, ledger reset or automatic semantic acceptance.
Interrupted/prepared entries remain blocked even when a model call is unproven.
"""
import hashlib
import json
from pathlib import Path

from .mtm_runtime import InputBoundaryError, decode_json
from .sacr_generation import GenerationLimits
from .sacr_generation_receipt import bind_generation_record
from .sacr_native_fidelity import digest, schema_digest
from .sacr_prompts import build_messages
from .sacr_schema import quote_profile_schema


def canonical_continuation_root(prior_output, manifest):
    """One irreversible destination for this history; supervisor fixes host mapping."""
    key = digest(json.dumps(manifest, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode())
    return Path(prior_output).resolve(strict=True).parent / ('continuation-' + key) / 'attempt'


def seal_terminal_history(*, entries, prior_output, terminal_raw, terminal_sha256,
                          observed_state, prompt_root, sample_sha256, query_sha256):
    """Caller freshly observes the same unique container; this binds its receipts.

    Entries must already be returned by bind_sample. The private manifest carries
    query IDs, so publish only its digest and aggregate counts.
    """
    if len(entries) != 100 or len({q for q, _, _ in entries}) != 100:
        raise InputBoundaryError('complete fixed sample required')
    if digest(terminal_raw) != terminal_sha256:
        raise InputBoundaryError('prior terminal digest mismatch')
    terminal = decode_json(terminal_raw)
    state = terminal['container_state']
    for value in (state, observed_state):
        if value.get('Running') is not False or value.get('Status') not in ('exited', 'dead'):
            raise InputBoundaryError('terminal prior execution required')
    if any(state.get(k) != observed_state.get(k) for k in ('ExitCode', 'StartedAt', 'FinishedAt')):
        raise InputBoundaryError('prior terminal observations disagree')
    root = Path(prior_output).resolve(strict=True)
    if Path(prior_output).is_symlink():
        raise InputBoundaryError('prior output symlink forbidden')
    files = {}
    def read(relative):
        path = root / relative
        if path.is_symlink() or not path.resolve(strict=True).is_relative_to(root):
            raise InputBoundaryError('prior artifact escapes output root')
        raw = path.read_bytes()
        files[relative] = digest(raw)
        return decode_json(raw), raw
    declaration, _ = read('declaration.json')
    if (declaration['maximum_calls'] != 100 or declaration['retry'] is not False or
            declaration['sample_sha256'] != sample_sha256 or declaration['query_sha256'] != query_sha256):
        raise InputBoundaryError('prior declaration differs from fixed sample')
    profiles = root / 'profiles'
    if profiles.is_symlink():
        raise InputBoundaryError('prior profiles symlink forbidden')
    directories = sorted(p for p in profiles.iterdir() if p.is_dir()) if profiles.exists() else []
    if [p.name for p in directories] != [f'{i:03d}' for i in range(len(directories))] or len(directories) > 100:
        raise InputBoundaryError('prior attempts are not an ordered sample prefix')
    records = []
    for index, (query_id, source, schema) in enumerate(entries):
        if schema != quote_profile_schema(source=source, query_id=query_id, input_kind='DAPFAM_TA'):
            raise InputBoundaryError('entry schema differs from source identity')
        prefix = f'profiles/{index:03d}'
        if index >= len(directories):
            records.append({'index': index, 'query_id': query_id, 'state': 'NEVER_STARTED'})
            continue
        inp, _ = read(prefix + '/input.json')
        prompt = build_messages(prompt_root=prompt_root, kind='profile_quotes', source=source,
            query_id=query_id, input_kind='DAPFAM_TA', prompt_variant='source_order_v2')
        expected = {'query_id': query_id, 'source_sha256': digest(source.encode()),
                    'schema_sha256': schema_digest(schema), 'prompt': prompt}
        if inp != expected or prompt['prompt_sha256'] != declaration['prompt_sha256']:
            raise InputBoundaryError('prior input/prompt identity mismatch')
        generation = root / prefix / 'profile/generation.json'
        reservation = root / prefix / 'profile/reservation.json'
        if generation.exists():
            if not reservation.exists():
                raise InputBoundaryError('generation without durable reservation')
            reserve, _ = read(prefix + '/profile/reservation.json')
            record, raw = read(prefix + '/profile/generation.json')
            limits = GenerationLimits()
            if (reserve['limits'] != limits.__dict__ or reserve['retry'] is not False or
                    reserve['status'] != 'RESERVED' or reserve['messages_sha256'] !=
                    digest(json.dumps(prompt['messages'], ensure_ascii=False, sort_keys=True).encode())):
                raise InputBoundaryError('prior reservation identity mismatch')
            bind_generation_record(raw, expected_sha256=digest(raw), limits=limits,
                metrics={k: record[k] for k in ('model_calls', 'input_tokens', 'output_tokens')})
            status = 'NORMAL_RETURN_CONSUMED'
        else:
            if reservation.exists():
                read(prefix + '/profile/reservation.json')
            status = 'INTERRUPTED_OR_PREPARED_BLOCKED'
        # Seal every retained file, not only the subset needed for classification.
        for path in sorted((root / prefix).rglob('*')):
            if path.is_symlink():
                raise InputBoundaryError('symlink inside prior attempt')
            if path.is_file():
                relative = path.relative_to(root).as_posix()
                files[relative] = digest(path.read_bytes())
        records.append({'index': index, 'query_id': query_id, 'state': status})
    selected = [r['index'] for r in records if r['state'] == 'NEVER_STARTED']
    blocked = [r['index'] for r in records if r['state'] == 'INTERRUPTED_OR_PREPARED_BLOCKED']
    for path in sorted(root.rglob('*')):
        if path.is_symlink():
            raise InputBoundaryError('symlink inside prior output')
        if path.is_file():
            files[path.relative_to(root).as_posix()] = digest(path.read_bytes())
    return {'version': 'sacr-unstarted-continuation-v1', 'sample_sha256': sample_sha256,
        'query_sha256': query_sha256, 'prior_terminal_sha256': terminal_sha256,
        'source_count': 100, 'records': records, 'selected_indices': selected,
        'blocked_indices': blocked, 'prior_files_sha256': files,
        'maximum_new_profile_calls': len(selected), 'retry_authorized': False,
        'cohort_fidelity': 'INCOMPLETE_NO_PASS',
        'requires_separate_decision_for_blocked': bool(blocked)}


def verify_history_files(prior_output, manifest):
    """Check before any later dispatch and again before each new call."""
    root = Path(prior_output).resolve(strict=True)
    current = set()
    for path in root.rglob('*'):
        if path.is_symlink():
            raise InputBoundaryError('symlink inside sealed output')
        if path.is_file():
            current.add(path.relative_to(root).as_posix())
    if current != set(manifest['prior_files_sha256']):
        raise InputBoundaryError('sealed prior file set changed')
    for relative, expected in manifest['prior_files_sha256'].items():
        path = root / relative
        if (path.is_symlink() or not path.resolve(strict=True).is_relative_to(root) or
                hashlib.sha256(path.read_bytes()).hexdigest() != expected):
            raise InputBoundaryError('sealed prior history changed')
    expected_indices = {r['index'] for r in manifest['records'] if r['state'] != 'NEVER_STARTED'}
    observed = {p.name for p in (root / 'profiles').iterdir() if p.is_dir()}
    if observed != {f'{i:03d}' for i in expected_indices}:
        raise InputBoundaryError('prior attempt set changed')
    return True
