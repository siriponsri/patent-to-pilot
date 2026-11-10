"""Owner-adopted completed-generation rejection policy for bounded runners.

Never handles infrastructure exceptions, unknown termination or semantic-review
decisions. Caller must retain raw attempt bytes and verify actual process state.
No model calls, output repairs, retries, retrieval or automatic fidelity PASS.
"""
from copy import deepcopy

from patent_to_pilot.research.mtm_runtime import InputBoundaryError, identifier
from patent_to_pilot.research.sacr_generation import validate_generation
from patent_to_pilot.research.sacr_generation_receipt import bind_generation_record
from patent_to_pilot.research.sacr_outcomes import summarize_costs

POLICY = 'sacr-completed-family-rejection-v1'


def assess_profile_attempt(raw, *, expected_sha256, source, query_id, input_kind, limits, metrics):
    """Classify only an intact, cost-bound normally returned profile record.

    Rejection permits planning independent work, not relabeling a FAILED journal
    stage as successful. Compact cannot be claimed valid when its profile failed.
    """
    identifier(query_id)
    if input_kind not in ('MTM_P', 'DAPFAM_TA') or type(source) is not str or not source.strip():
        raise InputBoundaryError('invalid caller source contract; not a generated rejection')
    binding = bind_generation_record(raw, expected_sha256=expected_sha256, limits=limits, metrics=metrics)
    summarize_costs([{'event_id': expected_sha256, 'query_id': query_id, 'stage': 'profile',
                     'status': 'FAILED', 'metrics': metrics}])
    status = binding['record']['status']
    if status == 'INPUT_LIMIT':
        return {'policy': POLICY, 'status': 'STOP_INPUT_LIMIT_NO_MODEL_CALL',
                'generation': binding, 'metrics': deepcopy(metrics), 'retry': False}
    reason, accepted = None, None
    if status != 'EOS_COMPLETE':
        reason = 'COMPLETED_NON_EOS_OR_RESPONSE_LIMIT'
    else:
        try:
            accepted = validate_generation(binding['record'], kind='profile_quotes', source=source,
                query_id=query_id, input_kind=input_kind, limits=limits)
        except (InputBoundaryError, ValueError, TypeError, KeyError):
            reason = 'COMPLETED_PROFILE_ACCEPTANCE_FAILED'
    if reason is not None:
        return {'policy': POLICY, 'status': 'REJECTED_GENERATED_FAMILY', 'reason': reason,
                'generation': binding, 'metrics': deepcopy(metrics), 'retry': False,
                'repair': False, 'compact_from_this_profile': 'UNAVAILABLE',
                'independent_anchor': 'REQUIRES_SEPARATE_VALID_BINDING',
                'semantic_status': 'NOT_ASSESSED'}
    return {'policy': POLICY, 'status': 'STRUCTURAL_RESULT_FIDELITY_PENDING',
            'generation': binding, 'metrics': deepcopy(metrics), 'validation': accepted,
            'retry': False, 'semantic_status': 'NOT_ASSESSED'}
