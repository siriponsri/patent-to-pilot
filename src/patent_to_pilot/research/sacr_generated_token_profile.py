"""R2 generation evidence binding; explicit contract, immutable replay, no calls."""
from copy import deepcopy

from .mtm_runtime import InputBoundaryError, exact_fields
from .sacr_components import compile_components
from .sacr_compact_v2 import compact_view_v2
from .sacr_generated_profile import profile_generation_identity
from .sacr_generated_view import GenerationEvidenceFailure
from .sacr_generation import GenerationLimits, validate_generation
from .sacr_generation_receipt import bind_generation_record
from .sacr_outcomes import summarize_costs

CONTRACT = 'sacr-token-profile-compact-union-v1'


def generated_token_profile_result(raw, identity, *, execution, attempt_id,
                                   query_id, source, metrics, input_kind='DAPFAM_TA'):
    if execution.get('profile_contract') != CONTRACT:
        raise InputBoundaryError('explicit token profile execution contract required')
    expected = profile_generation_identity(execution, attempt_id=attempt_id,
                                           query_id=query_id, source=source)
    exact_fields(identity, set(expected) | {'artifact_sha256'})
    if any(identity[k] != v for k, v in expected.items()):
        raise InputBoundaryError('token profile identity differs from execution')
    limits = GenerationLimits(**{k: execution['limits'][k] for k in
        ('input_tokens', 'output_tokens', 'context_tokens', 'response_bytes')})
    binding = bind_generation_record(raw, expected_sha256=identity['artifact_sha256'],
                                     limits=limits, metrics=metrics)
    summarize_costs([{'event_id': attempt_id, 'query_id': query_id, 'stage': 'profile',
                     'status': 'FAILED', 'metrics': metrics}])
    if binding['record']['status'] != 'EOS_COMPLETE':
        raise GenerationEvidenceFailure(raw=raw, identity=identity, binding=binding,
                                        metrics=metrics, reason='GENERATION_NOT_EOS_COMPLETE')
    try:
        aligned = validate_generation(binding['record'], kind='profile_tokens', source=source,
                                      query_id=query_id, input_kind=input_kind, limits=limits)
        profile = aligned['profile']
        components = compile_components(profile, source=source, query_id=query_id, input_kind=input_kind)
        compact = compact_view_v2(profile, source=source, query_id=query_id, input_kind=input_kind)
    except InputBoundaryError:
        raise GenerationEvidenceFailure(raw=raw, identity=identity, binding=binding,
                                        metrics=metrics, reason='PROFILE_ACCEPTANCE_FAILED') from None
    if components['status'] == 'ANCHOR_FALLBACK':
        decision = ('PROFILE_FAILED_FALLBACK_REQUIRED' if profile['extraction_status'] == 'failed'
                    else 'PROFILE_EMPTY_FALLBACK_REQUIRED')
    elif components['status'] == 'REVIEW_REQUIRED' or compact['status'] == 'REVIEW_REQUIRED':
        decision = 'REVIEW_REQUIRED'
    else:
        decision = 'PROFILE_STRUCTURALLY_PREPARED_FIDELITY_PENDING'
    return {'format': CONTRACT, 'query_id': query_id, 'source': source, 'profile': profile,
            'components': components, 'compact': compact, 'decision': decision,
            'semantic_status': 'unknown', 'generation': binding,
            'generation_identity': deepcopy(identity),
            'generation_artifact_utf8': raw.decode('utf-8'), 'alignment': aligned['alignment']}


def replay_generated_token_profile(output, **kwargs):
    replayed = generated_token_profile_result(output['generation_artifact_utf8'].encode('utf-8'),
                                              output['generation_identity'], **kwargs)
    if output != replayed:
        raise InputBoundaryError('generated token profile evidence changed')
    return replayed
