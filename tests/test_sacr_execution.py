import json

import pytest

from patent_to_pilot.research.mtm_runtime import InputBoundaryError
from patent_to_pilot.research.sacr_components import digest
from patent_to_pilot.research.sacr_execution import IDENTITIES, bind_execution
from patent_to_pilot.research.sacr_journal import DevStageJournal
from patent_to_pilot.research.sacr_outcomes import finalize_query
from test_sacr_run_reconcile import fixture


def declaration(plan):
    return {'format': 'sacr-dev-execution-v1', 'split': 'dev', 'run_id': plan['run_id'],
            'plan_sha256': digest(plan), 'sources': [{'query_id': 'q', 'source_sha256': 'a' * 64}],
            'identities': {key: 'b' * 64 for key in IDENTITIES},
            'limits': {'input_tokens': 8192, 'output_tokens': 4096, 'context_tokens': 40960,
                       'response_bytes': 65536, 'model_calls': 3, 'wall_seconds': 120,
                       'gpu_seconds': 120, 'peak_memory_bytes': 1024, 'depth': 200, 'views': 3}}


def test_binding_is_detached_and_missing_source_remains_explicit():
    plan = fixture()['manifest']
    data = declaration(plan)
    data['sources'][0]['source_sha256'] = None
    bound = bind_execution(data, plan, expected_execution_sha256=digest(data),
                           expected_plan_sha256=digest(plan))
    data['limits']['model_calls'] = 999
    assert bound['limits']['model_calls'] == 3
    assert bound['sources'][0]['source_sha256'] is None


@pytest.mark.parametrize('case', ['test', 'run', 'plan', 'source_id', 'source_missing', 'source_sha',
                                  'extra_identity', 'missing_identity', 'name_not_hash', 'bool_limit',
                                  'zero_limit', 'context', 'views', 'depth', 'calls', 'unpinned'])
def test_bad_declarations_rejected_before_directory_allocation(tmp_path, case):
    plan = fixture()['manifest']
    data = declaration(plan)
    original = digest(data)
    if case == 'test':
        data['split'] = 'test'
    elif case == 'run':
        data['run_id'] = 'other'
    elif case == 'plan':
        data['plan_sha256'] = 'c' * 64
    elif case == 'source_id':
        data['sources'][0]['query_id'] = 'other'
    elif case == 'source_missing':
        data['sources'] = []
    elif case == 'source_sha':
        data['sources'][0]['source_sha256'] = ''
    elif case == 'extra_identity':
        data['identities']['extra'] = 'a' * 64
    elif case == 'missing_identity':
        del data['identities']['encoder_manifest']
    elif case == 'name_not_hash':
        data['identities']['generator_manifest'] = 'Qwen3-8B'
    else:
        key, value = {'bool_limit': ('wall_seconds', True), 'zero_limit': ('gpu_seconds', 0),
                      'context': ('context_tokens', 10), 'views': ('views', 4),
                      'depth': ('depth', 201), 'calls': ('model_calls', 4),
                      'unpinned': ('wall_seconds', 121)}[case]
        data['limits'][key] = value
    with pytest.raises(InputBoundaryError):
        DevStageJournal(tmp_path / 'run', plan, expected_manifest_sha256=digest(plan),
                        execution=data, expected_execution_sha256=original if case == 'unpinned' else digest(data))
    assert not (tmp_path / 'run').exists()


@pytest.mark.parametrize('target', ['disk_execution', 'memory_execution', 'disk_plan', 'memory_slots'])
def test_mutation_stops_before_callback_and_reservation(tmp_path, target):
    plan = fixture()['manifest']
    data = declaration(plan)
    journal = DevStageJournal(tmp_path / 'run', plan, expected_manifest_sha256=digest(plan),
                              execution=data, expected_execution_sha256=digest(data))
    if target == 'disk_execution':
        data['limits']['wall_seconds'] += 1
        (journal.destination / 'execution.json').write_text(json.dumps(data))
    elif target == 'memory_execution':
        journal.execution['limits']['wall_seconds'] += 1
    elif target == 'disk_plan':
        plan['run_id'] = 'other'
        (journal.destination / 'manifest.json').write_text(json.dumps(plan))
    else:
        journal.slots['profile']['query_id'] = 'other'
    called = []
    with pytest.raises(InputBoundaryError):
        journal.execute('profile', lambda: called.append(True))
    assert not called
    assert not (journal.destination / digest('profile')).exists()


def test_bound_completion_keeps_execution_digest(tmp_path):
    plan = fixture()['manifest']
    data = declaration(plan)
    data['sources'][0]['source_sha256'] = None
    journal = DevStageJournal(tmp_path / 'run', plan, expected_manifest_sha256=digest(plan),
                              execution=data, expected_execution_sha256=digest(data))
    for slot in journal.slots:
        journal.skip(slot, reason='authored missing input')
    journal.finalize([finalize_query(query_id='q', state='MISSING_INPUT')])
    receipt = json.loads((journal.destination / 'completion.json').read_text())
    assert receipt['execution_sha256'] == digest(data)
