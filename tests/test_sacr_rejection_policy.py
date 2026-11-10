import hashlib
import json
import pytest

from patent_to_pilot.research.mtm_runtime import InputBoundaryError
from patent_to_pilot.research.sacr_generation import GenerationLimits
from patent_to_pilot.research.sacr_outcomes import METRICS
from patent_to_pilot.research.sacr_rejection_policy import assess_profile_attempt
from test_sacr_generation_receipt import record
from test_sacr_quote_profile import proposal
from test_sacr_profile import SOURCE


def assess(value, **overrides):
    raw = json.dumps(value).encode()
    costs = {key: 0 for key in METRICS}
    costs.update({k: value[k] for k in ('model_calls', 'input_tokens', 'output_tokens')})
    args = dict(expected_sha256=hashlib.sha256(raw).hexdigest(), source=SOURCE,
                query_id='q1', input_kind='MTM_P', limits=GenerationLimits(4, 2, 6, 65536), metrics=costs)
    args.update(overrides)
    return assess_profile_attempt(raw, **args)


@pytest.mark.parametrize('state', ['EOS_COMPLETE', 'NO_EOS', 'OUTPUT_LIMIT'])
def test_completed_invalid_output_rejected_without_repair_or_free_compact(state):
    value = record(state, text='{bad')
    out = assess(value)
    assert out['status'] == 'REJECTED_GENERATED_FAMILY'
    assert out['generation']['record'] == value
    assert out['metrics']['model_calls'] == 1 and out['retry'] is False and out['repair'] is False
    assert out['compact_from_this_profile'] == 'UNAVAILABLE'


@pytest.mark.parametrize('state', ['RUNNING', 'INTERRUPTED', 'FAILED'])
def test_unknown_infrastructure_states_cannot_be_rejected_families(state):
    with pytest.raises(InputBoundaryError):
        assess(record(state))


def test_input_limit_and_valid_profile_are_not_semantic_passes():
    assert assess(record('INPUT_LIMIT'))['status'] == 'STOP_INPUT_LIMIT_NO_MODEL_CALL'
    out = assess(record(text=json.dumps(proposal())))
    assert out['status'] == 'STRUCTURAL_RESULT_FIDELITY_PENDING'
    assert out['semantic_status'] == 'NOT_ASSESSED'


def test_tampered_artifact_and_bad_caller_contract_stop_instead_of_rejecting():
    for overrides in ({'expected_sha256': '0' * 64}, {'source': ''}, {'input_kind': 'TAC'}):
        with pytest.raises(InputBoundaryError):
            assess(record(), **overrides)
