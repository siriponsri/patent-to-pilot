import json

import numpy as np
import pytest

from patent_to_pilot.research.mtm_runtime import InputBoundaryError
from patent_to_pilot.research.sacr_components import digest, vector_digest
from patent_to_pilot.research.sacr_embedding import bind_embeddings
from test_sacr_controller import setup, adapter
from test_sacr_embedding_inputs import generated
from test_sacr_view_controller import metrics


def ready(tmp_path):
    controller = setup(tmp_path)
    controller.profile('q', adapter)
    for kind in ('generic', 'selective'):
        generated(controller, kind)
    return controller


def fake_encoder(plan, encoder):
    matrix = np.zeros((len(plan['rows']), 2), dtype=np.float32)
    matrix[np.arange(len(matrix)), np.arange(len(matrix)) % 2] = 1
    receipt = {'format': 'sacr-query-embeddings-v1', 'plan_sha256': plan['plan_sha256'],
               'encoder_sha256': encoder, 'row_ids': [r['row_id'] for r in plan['rows']],
               'vectors_sha256': vector_digest(matrix)}
    costs = metrics()
    costs['embedding_texts'] = len(matrix)
    return matrix, receipt, costs


def test_reserved_embedding_roundtrips_shared_anchor_and_rows(tmp_path):
    controller = ready(tmp_path)
    def encode(plan, encoder):
        assert (controller.journal.destination / digest('embedding') / 'reservation.json').is_file()
        assert plan['view_rows']['generic'][0] == plan['view_rows']['selective'][0]
        assert len({r['text'] for r in plan['rows']}) == len(plan['rows'])
        return fake_encoder(plan, encoder)
    output = controller.embed('q', encode)
    saved = controller.journal.read_completed_output('embedding')
    assert saved == output
    matrix = bind_embeddings(saved['plan'], np.asarray(saved['vectors_float32'], dtype=np.float32),
                             saved['receipt'], expected_plan_sha256=saved['plan']['plan_sha256'],
                             expected_encoder_sha256=saved['receipt']['encoder_sha256'])
    assert not matrix.flags.writeable
    assert len(saved['plan']['component_rows']) == 3
    with pytest.raises(FileExistsError):
        controller.embed('q', encode)


@pytest.mark.parametrize('case', ['row_order', 'encoder', 'plan', 'bytes', 'dtype', 'nonunit', 'nan'])
def test_bad_embedding_receipt_or_vectors_preserved_as_failure(tmp_path, case):
    controller = ready(tmp_path)
    def encode(plan, encoder):
        matrix, receipt, costs = fake_encoder(plan, encoder)
        if case == 'row_order':
            receipt['row_ids'].reverse()
        elif case == 'encoder':
            receipt['encoder_sha256'] = 'f' * 64
        elif case == 'plan':
            receipt['plan_sha256'] = 'f' * 64
        elif case == 'bytes':
            matrix[0] = matrix[0][::-1]
        elif case == 'dtype':
            matrix = matrix.astype(np.float64)
        elif case == 'nonunit':
            matrix *= 2
            receipt['vectors_sha256'] = vector_digest(matrix)
        else:
            matrix[0, 0] = np.nan
        return matrix, receipt, costs
    with pytest.raises(InputBoundaryError):
        controller.embed('q', encode)
    path = controller.journal.destination / digest('embedding')
    assert json.loads((path / 'receipt.json').read_text())['status'] == 'FAILED'
    assert not (path / 'output.json').exists()


def test_review_stops_before_embedding_adapter_or_reservation(tmp_path):
    controller = setup(tmp_path)
    controller.profile('q', adapter)
    generated(controller, 'generic')
    generated(controller, 'selective', 'Novelmechanism ' + controller._sources['q'])
    with pytest.raises(InputBoundaryError):
        controller.embed('q', lambda *_: pytest.fail('embedding adapter dispatched'))
    assert not (controller.journal.destination / digest('embedding')).exists()
