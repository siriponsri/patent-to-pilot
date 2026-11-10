import hashlib
import json

import pytest

from patent_to_pilot.research.mtm_runtime import InputBoundaryError
from patent_to_pilot.research.sacr_components import digest
from patent_to_pilot.research.sacr_controller import BoundProfileController
from patent_to_pilot.research.sacr_outcomes import METRICS
from test_sacr_input_snapshots import inputs, sha
from test_sacr_profile import SOURCE, fixture


def setup(tmp_path, *, missing=False, tampered=False, index_manifest=None, anchor_factory=None,
          require_generation=False):
    plan, data, manifests, _, _ = inputs()
    payload = json.dumps({'id': 'q', 'text': SOURCE}).encode()
    manifest = json.loads(manifests['query_manifest'])
    manifest['sha256'] = sha(payload)
    if missing:
        plan['query_ids'].append('missing')
        plan['slots'] += [{**s, 'query_id': 'missing', 'attempt_id': 'missing-' + s['stage']}
                          for s in list(plan['slots'])]
        data['plan_sha256'] = digest(plan)
        data['sources'].append({'query_id': 'missing', 'source_sha256': None})
        manifest['missing_ids'] = ['missing']
    manifests['query_manifest'] = json.dumps(manifest).encode()
    data['identities']['query_manifest'] = sha(manifests['query_manifest'])
    if index_manifest is not None:
        manifests['index_manifest'] = index_manifest
        data['identities']['index_manifest'] = sha(index_manifest)
    data['sources'][0]['source_sha256'] = hashlib.sha256(SOURCE.encode()).hexdigest()
    anchor_raw = None
    if anchor_factory is not None:
        anchor_raw = anchor_factory(data)
        data['format'] = 'sacr-dev-execution-v2'
        data['anchor_bundle_sha256'] = sha(anchor_raw)
    if require_generation:
        data['format'] = 'sacr-dev-execution-v3'
    if tampered:
        payload += b'changed'
    return BoundProfileController(tmp_path / 'run', plan, data, manifest_bytes=manifests,
                                  query_payload=payload, expected_plan_sha256=digest(plan),
                                  expected_execution_sha256=digest(data), anchor_bundle_raw=anchor_raw)


def adapter(query, source):
    assert query == 'q' and source == SOURCE
    profile = fixture()
    profile['query_id'] = query
    return profile, {key: 0 for key in METRICS}


def test_source_bound_profile_is_not_semantically_approved(tmp_path):
    controller = setup(tmp_path)
    result = controller.profile('q', adapter)
    assert result['decision'] == 'PROFILE_STRUCTURALLY_PREPARED_FIDELITY_PENDING'
    assert result['components']['fidelity_review'] == 'REQUIRED'
    assert result['semantic_status'] == 'unknown'
    with pytest.raises(FileExistsError):
        controller.profile('q', adapter)


@pytest.mark.parametrize('case,decision', [('failed', 'PROFILE_FAILED_FALLBACK_REQUIRED'),
                                         ('empty', 'PROFILE_EMPTY_FALLBACK_REQUIRED'),
                                         ('unknown', 'REVIEW_REQUIRED'),
                                         ('normalization', 'REVIEW_REQUIRED')])
def test_semantic_stop_and_fallback_are_not_ready(case, decision, tmp_path):
    controller = setup(tmp_path)
    def work(query, source):
        p, metrics = adapter(query, source)
        if case in ('empty', 'failed'):
            p['blocks'] = []
            if case == 'failed':
                p['extraction_status'] = 'failed'
                p['failure_reasons'] = ['authored abstention']
        elif case == 'unknown':
            p['unknowns'] = [{'description': 'authored unresolved attachment', 'reason': 'ambiguity'}]
        else:
            p['blocks'][0]['relation_text'] = 'Prevent backflow'
        return p, metrics
    result = controller.profile('q', work)
    assert result['decision'] == decision
    assert not (controller.journal.destination / digest('embedding')).exists()
    assert 'rankings' not in result


def test_invalid_profile_is_failed_inside_reservation(tmp_path):
    controller = setup(tmp_path)
    def work(query, source):
        p, metrics = adapter(query, source)
        p['source_sha256'] = 'a' * 64
        return p, metrics
    with pytest.raises(InputBoundaryError):
        controller.profile('q', work)
    path = controller.journal.destination / digest('profile')
    assert json.loads((path / 'receipt.json').read_text())['status'] == 'FAILED'
    assert not (path / 'output.json').exists()
    with pytest.raises(FileExistsError):
        controller.profile('q', adapter)


def test_missing_source_never_calls_adapter(tmp_path):
    controller = setup(tmp_path, missing=True)
    result = controller.profile('missing', lambda *_: pytest.fail('missing input dispatched'))
    assert result['decision'] == 'MISSING_INPUT'
    receipt = controller.journal.destination / digest('missing-profile') / 'receipt.json'
    assert json.loads(receipt.read_text())['status'] == 'SKIPPED'


def test_bad_bytes_rejected_before_journal_allocation(tmp_path):
    with pytest.raises(InputBoundaryError):
        setup(tmp_path, tampered=True)
    assert not (tmp_path / 'run').exists()
