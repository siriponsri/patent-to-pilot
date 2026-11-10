"""Quote-profile generation binding and deterministic replay; no model loading."""
from copy import deepcopy
import hashlib

from patent_to_pilot.research.mtm_runtime import InputBoundaryError, exact_fields
from patent_to_pilot.research.sacr_generation import GenerationLimits, validate_generation
from patent_to_pilot.research.sacr_generation_receipt import bind_generation_record
from patent_to_pilot.research.sacr_generated_view import GenerationEvidenceFailure
from patent_to_pilot.research.sacr_outcomes import summarize_costs
from patent_to_pilot.research.sacr_profile_result import profile_result


def profile_generation_identity(execution, *, attempt_id, query_id, source):
    return {'query_id': query_id, 'kind': 'profile', 'run_id': execution['run_id'],
            'attempt_id': attempt_id, 'source_sha256': hashlib.sha256(source.encode()).hexdigest(),
            'generator_manifest_sha256': execution['identities']['generator_manifest'],
            'prompt_manifest_sha256': execution['identities']['prompt_manifest']}


def generated_profile_result(raw, identity, *, execution, attempt_id, query_id, source, metrics):
    expected = profile_generation_identity(execution, attempt_id=attempt_id, query_id=query_id, source=source)
    exact_fields(identity, set(expected) | {'artifact_sha256'})
    if any(identity[key] != value for key, value in expected.items()):
        raise InputBoundaryError('profile generation identity differs from execution')
    limits = GenerationLimits(**{k: execution['limits'][k] for k in
                                ('input_tokens', 'output_tokens', 'context_tokens', 'response_bytes')})
    binding = bind_generation_record(raw, expected_sha256=identity['artifact_sha256'], limits=limits, metrics=metrics)
    summarize_costs([{'event_id': attempt_id, 'query_id': query_id, 'stage': 'profile',
                     'status': 'FAILED', 'metrics': metrics}])
    if binding['record']['status'] != 'EOS_COMPLETE':
        raise GenerationEvidenceFailure(raw=raw, identity=identity, binding=binding, metrics=metrics,
                                        reason='GENERATION_NOT_EOS_COMPLETE')
    try:
        aligned = validate_generation(binding['record'], kind='profile_quotes', source=source,
                                      query_id=query_id, input_kind='MTM_P', limits=limits)
        canonical = profile_result(aligned['profile'], source=source, query_id=query_id)
    except InputBoundaryError:
        raise GenerationEvidenceFailure(raw=raw, identity=identity, binding=binding, metrics=metrics,
                                        reason='PROFILE_ACCEPTANCE_FAILED') from None
    return {**canonical, 'format': 'sacr-profile-stage-v2', 'generation': binding,
            'generation_identity': deepcopy(identity), 'generation_artifact_utf8': raw.decode('utf-8'),
            'alignment': aligned['alignment']}


def replay_generated_profile(output, *, execution, attempt_id, query_id, source, metrics):
    replayed = generated_profile_result(
        output['generation_artifact_utf8'].encode('utf-8'), output['generation_identity'],
        execution=execution, attempt_id=attempt_id, query_id=query_id, source=source, metrics=metrics)
    if replayed != output:
        raise InputBoundaryError('generated profile evidence changed')
    return profile_result(replayed['profile'], source=source, query_id=query_id)
