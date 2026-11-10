import json

import pytest

from patent_to_pilot.research.mtm_runtime import InputBoundaryError
from patent_to_pilot.research.sacr_components import digest, vector_digest
from patent_to_pilot.research.sacr_index import BoundCPUIndex
from patent_to_pilot.research.sacr_outcomes import finalize_query
from test_sacr_controller import setup, adapter
from test_sacr_embedding_inputs import generated
from test_sacr_embedding_controller import fake_encoder
from test_sacr_factorial import fixture
from test_sacr_input_snapshots import sha


def index_inputs():
    p = fixture()
    manifest = {'format': 'sacr-cpu-index-v1', 'family_ids_sha256': digest(p['family_ids']),
                'passage_order_sha256': p['expected_order_sha256'],
                'vectors_sha256': vector_digest(p['passage_vectors']),
                'query_mask_sha256': {'q': digest(p['eligible'].tolist())}}
    return p, json.dumps(manifest).encode()


def make_index(p, raw):
    return BoundCPUIndex(raw, expected_sha256=sha(raw), family_ids=p['family_ids'],
                          passage_ids=p['passage_ids'], passage_owner=p['passage_owner'],
                          vectors=p['passage_vectors'])


def ready(tmp_path):
    p, raw = index_inputs()
    index = make_index(p, raw)
    controller = setup(tmp_path, index_manifest=raw)
    controller.profile('q', adapter)
    for kind in ('generic', 'selective'):
        generated(controller, kind)
    controller.embed('q', fake_encoder)
    return controller, index, p


def test_six_stage_authored_run_uses_bound_index_without_repeat_search(tmp_path, monkeypatch):
    controller, index, p = ready(tmp_path)
    controller.acquire('q', index, p['eligible'])
    def forbidden(**kwargs):
        pytest.fail('selection repeated acquisition')
    monkeypatch.setattr('patent_to_pilot.research.sacr_factorial.acquire_union', forbidden)
    output = controller.select('q', index, p['eligible'])
    arms = {arm: [row['family_id'] for row in ranking] for arm, ranking in output['result']['arms'].items()}
    assert all('outside' not in ranking for ranking in arms.values())
    report = controller.journal.finalize([finalize_query(query_id='q', state='READY', arms=arms)])
    assert report['attempts'] == 6
    assert report['costs']['metrics']['index_dot_products']['value'] == 12
    assert report['costs']['metrics']['candidate_dot_products']['value'] == 9
    assert report['costs']['metrics']['peak_memory_bytes']['value'] is None
    assert not report['protected_evaluation_authorized']


@pytest.mark.parametrize('case', ['family_order', 'passage_order', 'vector_bytes'])
def test_index_mismatch_rejected(case):
    p, raw = index_inputs()
    if case == 'family_order':
        p['family_ids'].reverse()
    elif case == 'passage_order':
        p['passage_ids'].reverse()
    else:
        p['passage_vectors'][0] = [0, 1]
    with pytest.raises((InputBoundaryError, ValueError)):
        make_index(p, raw)


def test_changed_mask_rejected_before_search_reservation(tmp_path):
    controller, index, p = ready(tmp_path)
    p['eligible'][2] = True
    with pytest.raises(InputBoundaryError, match='mask differs'):
        controller.acquire('q', index, p['eligible'])
    assert not (controller.journal.destination / digest('acquisition')).exists()


def test_index_detaches_caller_arrays(tmp_path):
    controller, index, p = ready(tmp_path)
    p['passage_vectors'][:] = 0
    p['passage_owner'][:] = 0
    p['family_ids'][0] = 'changed'
    result = controller.acquire('q', index, p['eligible'])
    assert set(result['acquired']['G']['family_ids']) == {'split', 'joint'}


def test_changed_acquisition_blocks_selection(tmp_path):
    controller, index, p = ready(tmp_path)
    controller.acquire('q', index, p['eligible'])
    path = controller.journal.destination / digest('acquisition') / 'output.json'
    path.write_bytes(path.read_bytes() + b' ')
    with pytest.raises(InputBoundaryError, match='bytes changed'):
        controller.select('q', index, p['eligible'])
    assert not (controller.journal.destination / digest('selection')).exists()
