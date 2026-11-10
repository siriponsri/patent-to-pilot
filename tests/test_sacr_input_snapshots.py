import hashlib
import json
from pathlib import Path

import pytest

from patent_to_pilot.research.mtm_queries import load_dev_queries
from patent_to_pilot.research.mtm_runtime import InputBoundaryError
from patent_to_pilot.research.sacr_components import digest
from patent_to_pilot.research.sacr_execution import IDENTITIES, bind_input_snapshots
from test_sacr_execution import declaration
from test_sacr_run_reconcile import fixture


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def inputs():
    plan = fixture()['manifest']
    data = declaration(plan)
    text = 'Authored requirement: preserve pressure ≤ 5 kPa.'
    payload = json.dumps({'id': 'q', 'text': text}, ensure_ascii=False).encode()
    manifests = {key: ('authored ' + key).encode() for key in IDENTITIES}
    manifests['query_manifest'] = json.dumps({'format': 'ptp-mtm-query-text-v1', 'split': 'dev',
                                             'view': 'P', 'sha256': sha(payload), 'queries': 1,
                                             'missing_ids': []}).encode()
    data['identities'] = {key: sha(raw) for key, raw in manifests.items()}
    data['sources'][0]['source_sha256'] = sha(text.encode())
    return plan, data, manifests, payload, text


def bind(plan, data, manifests, payload):
    return bind_input_snapshots(data, plan, manifest_bytes=manifests, query_payload=payload,
                                expected_execution_sha256=digest(data), expected_plan_sha256=digest(plan))


def test_exact_unicode_text_is_returned_as_immutable_snapshot():
    plan, data, manifests, payload, text = inputs()
    result = bind(plan, data, manifests, payload)
    manifests.clear()
    data['sources'].clear()
    assert result == (('q', text),)


def test_missing_text_stays_in_ordered_cohort():
    plan, data, manifests, payload, text = inputs()
    plan['query_ids'].insert(0, 'missing')
    plan['slots'] += [{**slot, 'query_id': 'missing', 'attempt_id': 'missing-' + slot['stage']}
                      for slot in list(plan['slots'])]
    data['plan_sha256'] = digest(plan)
    data['sources'].insert(0, {'query_id': 'missing', 'source_sha256': None})
    m = json.loads(manifests['query_manifest'])
    m['missing_ids'] = ['missing']
    manifests['query_manifest'] = json.dumps(m).encode()
    data['identities']['query_manifest'] = sha(manifests['query_manifest'])
    assert bind(plan, data, manifests, payload) == (('missing', None), ('q', text))


@pytest.mark.parametrize('case', ['manifest', 'payload', 'source', 'missing', 'view', 'split', 'foreign', 'mutable'])
def test_changed_or_ineligible_snapshot_refused(case):
    plan, data, manifests, payload, _ = inputs()
    if case == 'manifest':
        manifests['encoder_manifest'] += b'changed'
    elif case == 'payload':
        payload = payload.replace(b'pressure', b'volume')
    elif case == 'source':
        data['sources'][0]['source_sha256'] = 'f' * 64
    elif case == 'missing':
        data['sources'][0]['source_sha256'] = None
    elif case == 'mutable':
        payload = bytearray(payload)
    else:
        m = json.loads(manifests['query_manifest'])
        if case == 'view':
            m['view'] = 'T'
        elif case == 'split':
            m['split'] = 'test'
        else:
            payload = payload.replace(b'"q"', b'"foreign"')
            m['sha256'] = sha(payload)
        manifests['query_manifest'] = json.dumps(m).encode()
        data['identities']['query_manifest'] = sha(manifests['query_manifest'])
    with pytest.raises(InputBoundaryError):
        bind(plan, data, manifests, payload)


def test_loader_hashes_and_decodes_single_read_snapshots(tmp_path, monkeypatch):
    _, _, manifests, payload, text = inputs()
    (tmp_path / 'manifest.json').write_bytes(manifests['query_manifest'])
    (tmp_path / 'queries.jsonl').write_bytes(payload)
    original = Path.read_bytes
    counts = {}
    def once(path):
        counts[path.name] = counts.get(path.name, 0) + 1
        assert counts[path.name] == 1, 'must not reopen after hashing'
        return original(path)
    monkeypatch.setattr(Path, 'read_bytes', once)
    result = load_dev_queries(tmp_path, sha(manifests['query_manifest']), {'q'})
    assert result['rows'] == [{'id': 'q', 'text': text}]
    assert counts == {'manifest.json': 1, 'queries.jsonl': 1}


def test_loader_rejects_test_manifest_before_reading_payload(tmp_path, monkeypatch):
    _, _, manifests, _, _ = inputs()
    m = json.loads(manifests['query_manifest'])
    m['split'] = 'test'
    raw = json.dumps(m).encode()
    (tmp_path / 'manifest.json').write_bytes(raw)
    original = Path.read_bytes
    def only_manifest(path):
        assert path.name == 'manifest.json'
        return original(path)
    monkeypatch.setattr(Path, 'read_bytes', only_manifest)
    with pytest.raises(InputBoundaryError):
        load_dev_queries(tmp_path, sha(raw), {'q'})
