import hashlib
import json

import pytest

from patent_to_pilot.research.mtm_runtime import InputBoundaryError
from patent_to_pilot.research.sacr_components import digest
from patent_to_pilot.research.sacr_execution import IDENTITIES, bind_dapfam_input_snapshots
from test_sacr_execution import declaration
from test_sacr_run_reconcile import fixture


def setup(rows=None, change_manifest=None):
    source = 'Title\nAbstract: retain  low pressure.\nNo external power.'
    rows = rows if rows is not None else [{'id': 'q', 'text': source}, {'id': 'other-dev', 'text': 'Other'}]
    payload = ('\n'.join(json.dumps(r) for r in rows) + '\n').encode()
    manifest = {'format': 'ptp-dapfam-runtime-dev-v1', 'split': 'dev', 'query_view': 'TA',
                'corpus_view': 'TAC', 'candidate_policy': 'full', 'input_queries': len(rows),
                'files': {'corpus.jsonl': 'a' * 64, 'queries-ta.jsonl': hashlib.sha256(payload).hexdigest()}}
    manifest.update(change_manifest or {})
    snapshots = {k: b'{}' for k in IDENTITIES}
    snapshots['query_manifest'] = json.dumps(manifest).encode()
    plan = fixture()['manifest']
    data = declaration(plan)
    data['sources'][0]['source_sha256'] = hashlib.sha256(source.encode()).hexdigest()
    data['identities'] = {k: hashlib.sha256(v).hexdigest() for k, v in snapshots.items()}
    return data, plan, snapshots, payload, source


def bind(data, plan, snapshots, payload):
    return bind_dapfam_input_snapshots(data, plan, manifest_bytes=snapshots, query_payload=payload,
        expected_execution_sha256=digest(data), expected_plan_sha256=digest(plan))


def test_exact_ta_preserved_and_only_declared_dev_subset_returned():
    d, p, m, q, source = setup()
    assert bind(d, p, m, q) == (('q', source),)


@pytest.mark.parametrize('change', [{'split': 'test'}, {'query_view': 'TAC'}, {'query_view': 'P'},
                                  {'candidate_policy': 'X'}, {'input_queries': True}, {'input_queries': 1}])
def test_wrong_semantics_rejected_even_if_hashes_rebound(change):
    d, p, m, q, _ = setup(change_manifest=change)
    with pytest.raises(InputBoundaryError):
        bind(d, p, m, q)


@pytest.mark.parametrize('case', ['claims', 'duplicate', 'missing', 'text_change', 'payload_change', 'manifest_change'])
def test_source_and_population_integrity_fail_closed(case):
    d, p, m, q, source = setup()
    if case in ('claims', 'duplicate', 'missing', 'text_change'):
        row = {'id': 'q', 'text': source}
        if case == 'claims': row['claims'] = 'forbidden extra input'
        if case == 'missing': row['id'] = 'other-dev'
        if case == 'text_change': row['text'] = source.replace('  ', ' ')
        d, p, m, q, _ = setup([row, row] if case == 'duplicate' else [row])
    if case == 'payload_change': q += b'\n'
    if case == 'manifest_change': m['query_manifest'] += b' '
    with pytest.raises(InputBoundaryError):
        bind(d, p, m, q)
