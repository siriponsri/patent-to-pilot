import json

import pytest

from patent_to_pilot.research.mtm_runtime import InputBoundaryError
from patent_to_pilot.research.sacr_components import digest
from patent_to_pilot.research.sacr_journal import DevStageJournal
from patent_to_pilot.research.sacr_outcomes import ARMS, METRICS, finalize_query
from test_sacr_run_reconcile import fixture


def create(tmp_path):
    f = fixture()
    j = DevStageJournal(tmp_path / 'run', f['manifest'], expected_manifest_sha256=f['expected_manifest_sha256'])
    return j


def callback():
    return {'synthetic': True}, {key: 0 for key in METRICS}


def test_six_stage_run_reserves_before_callback_and_reconciles(tmp_path):
    j = create(tmp_path)
    for stage in ('profile', 'generic', 'selective', 'embedding', 'acquisition', 'selection'):
        def work():
            assert (j.destination / digest(stage) / 'reservation.json').is_file()
            return callback()
        j.execute(stage, work)
    outcomes = [finalize_query(query_id='q', state='READY', arms={a: ['f'] for a in ARMS})]
    r = j.finalize(outcomes)
    assert r['attempts'] == 6 and r['cohort']['scorable']
    assert r['costs']['metrics']['operation_wall_seconds']['value'] >= 0
    with pytest.raises(FileExistsError):
        j.finalize(outcomes)
    with pytest.raises(FileExistsError):
        create(tmp_path)


@pytest.mark.parametrize('error,status', [(RuntimeError, 'FAILED'), (KeyboardInterrupt, 'INTERRUPTED')])
def test_failure_record_retained_unknown_costs_no_retry_or_error_text(tmp_path, error, status):
    j = create(tmp_path)
    def work():
        raise error('private detail')
    with pytest.raises(error):
        j.execute('profile', work)
    for slot in j.slots:
        if slot != 'profile':
            j.skip(slot, reason='profile unusable')
    r = j.finalize([finalize_query(query_id='q', state='PROFILE_FAILED', anchor=['f'])])
    assert r['costs']['metrics']['model_calls']['value'] is None
    receipt = (j.destination / digest('profile') / 'receipt.json').read_text()
    assert status in receipt and 'private detail' not in receipt
    with pytest.raises(FileExistsError):
        j.execute('profile', callback)


@pytest.mark.parametrize('artifact', ['output.json', 'event.json', 'receipt.json'])
def test_changed_artifact_rejected(tmp_path, artifact):
    j = create(tmp_path)
    for slot in j.slots:
        j.execute(slot, callback)
    path = j.destination / digest('profile') / artifact
    data = json.loads(path.read_text())
    data['changed'] = True
    path.write_text(json.dumps(data))
    with pytest.raises(InputBoundaryError, match='bytes changed'):
        j.finalize([finalize_query(query_id='q', state='READY', arms={a: [] for a in ARMS})])


def test_unsealed_reservation_is_not_assumed_interrupted(tmp_path):
    j = create(tmp_path)
    j._reserve('profile')
    with pytest.raises(InputBoundaryError, match='unsealed'):
        j.finalize([finalize_query(query_id='q', state='REVIEW_REQUIRED')])
    assert not (j.destination / 'outcomes.json').exists()


def test_test_manifest_refused_before_directory_creation(tmp_path):
    f = fixture()
    f['manifest']['split'] = 'test'
    with pytest.raises(InputBoundaryError):
        DevStageJournal(tmp_path / 'run', f['manifest'], expected_manifest_sha256=digest(f['manifest']))
    assert not (tmp_path / 'run').exists()


def test_authored_profile_to_real_cpu_kernels_with_injected_embeddings(tmp_path):
    import numpy as np
    from patent_to_pilot.research.sacr_components import compile_components, bind_component_vectors, vector_digest
    from patent_to_pilot.research.sacr_acquisition import acquire_union
    from patent_to_pilot.research.sacr_factorial import compare_factorial
    from test_sacr_profile import SOURCE, fixture as profile_fixture
    from test_sacr_factorial import fixture as index_fixture

    j = create(tmp_path)
    def measured(output, **counts):
        metrics = {key: 0 for key in METRICS}
        metrics.update(counts)
        return output, metrics
    authored_profile = profile_fixture()
    authored_profile['query_id'] = 'q'
    profile = j.execute('profile', lambda: measured(authored_profile))
    j.execute('generic', lambda: measured({'views': ['authored generic']}))
    j.execute('selective', lambda: measured({'view': 'authored selective'}))
    plan = compile_components(profile, source=SOURCE, query_id='q', input_kind='MTM_P')
    vectors = np.array([[1, 0], [0, 1], [0, 1]], dtype=np.float32)
    receipt = {'format': 'sacr-component-vectors-v1', 'plan_sha256': plan['plan_sha256'],
               'encoder_sha256': 'a' * 64, 'row_ids': [r['row_id'] for r in plan['rows']],
               'vectors_sha256': vector_digest(vectors)}
    j.execute('embedding', lambda: measured({'injected_not_encoded': True, 'receipt': receipt}))
    inputs = index_fixture()
    inputs['component_blocks'] = bind_component_vectors(plan, vectors, receipt,
                                                       expected_plan_sha256=plan['plan_sha256'],
                                                       expected_encoder_sha256='a' * 64)
    common = {k: inputs[k] for k in ('family_ids', 'passage_owner', 'passage_vectors', 'eligible', 'depth', 'chunk_size')}
    def acquire():
        acquired = acquire_union(**common, view_ids=inputs['generic_views'][0], view_vectors=inputs['generic_views'][1])
        return measured(acquired, index_dot_products=acquired['accounting']['view_passage_dot_products'])
    j.execute('acquisition', acquire)
    def select():
        r = compare_factorial(**inputs)
        # This integration test deliberately recomputes acquisition; charge it.
        return measured(r, index_dot_products=r['accounting']['actual_acquisition_dot_products'],
                        candidate_dot_products=r['accounting']['actual_component_passage_dot_products'])
    ranked = j.execute('selection', select)
    outcome = finalize_query(query_id='q', state='READY',
                             arms={a: [r['family_id'] for r in rows] for a, rows in ranked['arms'].items()})
    report = j.finalize([outcome])
    assert report['costs']['metrics']['index_dot_products']['value'] == 24
    assert report['costs']['metrics']['candidate_dot_products']['value'] == 9
    assert report['costs']['metrics']['model_calls']['value'] == 0
    assert (j.destination / 'completion.json').is_file()
