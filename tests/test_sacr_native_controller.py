import hashlib
import json

import pytest

from patent_to_pilot.research.mtm_runtime import InputBoundaryError
from patent_to_pilot.research.sacr_components import digest
from patent_to_pilot.research.sacr_controller import BoundProfileController
from test_sacr_input_snapshots import inputs
from test_sacr_profile import SOURCE
from test_sacr_quote_profile import proposal
from test_sacr_generated_view_controller import evidence


def native_controller(tmp_path):
    plan, data, manifests, _, _ = inputs()
    payload = json.dumps({'id': 'q', 'text': SOURCE}).encode()
    manifest = {'format': 'ptp-dapfam-runtime-dev-v1', 'split': 'dev', 'query_view': 'TA',
                'corpus_view': 'TAC', 'candidate_policy': 'full', 'input_queries': 1,
                'files': {'corpus.jsonl': 'a' * 64, 'queries-ta.jsonl': hashlib.sha256(payload).hexdigest()}}
    manifests['query_manifest'] = json.dumps(manifest).encode()
    data['identities']['query_manifest'] = hashlib.sha256(manifests['query_manifest']).hexdigest()
    data['sources'][0]['source_sha256'] = hashlib.sha256(SOURCE.encode()).hexdigest()
    return BoundProfileController(tmp_path / 'run', plan, data, manifest_bytes=manifests,
        query_payload=payload, expected_plan_sha256=digest(plan), expected_execution_sha256=digest(data))


def test_native_generated_profile_is_validated_and_replayed_as_ta(tmp_path):
    controller = native_controller(tmp_path)
    p = proposal()
    p.update(query_id='q', input_kind='DAPFAM_TA')
    supplied = evidence(controller, 'profile', text=json.dumps(p), status='EOS_COMPLETE')
    result = controller.generated_profile('q', lambda *_: supplied)
    assert result['profile']['input_kind'] == 'DAPFAM_TA'
    replayed = controller._checked_profile('q', result)
    assert replayed['profile']['input_kind'] == 'DAPFAM_TA'
    assert replayed['semantic_status'] == 'unknown'
    assert controller._sources == {'q': SOURCE}


def test_native_controller_rejects_mtm_profile_and_preserves_failed_attempt(tmp_path):
    controller = native_controller(tmp_path)
    p = proposal()
    p['query_id'] = 'q'
    supplied = evidence(controller, 'profile', text=json.dumps(p), status='EOS_COMPLETE')
    with pytest.raises(InputBoundaryError):
        controller.generated_profile('q', lambda *_: supplied)
    receipt, output = controller.journal.read_terminal_attempt('profile')
    assert receipt['status'] == 'FAILED'
    assert output['generation_artifact_utf8'].encode() == supplied[0]
