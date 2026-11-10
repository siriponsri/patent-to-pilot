"""Private v3 view evidence: bound normal-return record, no failure-policy adoption."""
from copy import deepcopy

from patent_to_pilot.research.mtm_runtime import InputBoundaryError, exact_fields
from patent_to_pilot.research.sacr_generation import GenerationLimits
from patent_to_pilot.research.sacr_generation_receipt import bind_generation_record
from patent_to_pilot.research.sacr_view_result import view_result


def generated_view_result(raw, identity, *, expected_identity, metrics, profile_output, limits):
    exact_fields(identity, set(expected_identity) | {'artifact_sha256'})
    if any(identity[key] != value for key, value in expected_identity.items()):
        raise InputBoundaryError('generation identity differs from bound execution/query/stage')
    binding = bind_generation_record(
        raw, expected_sha256=identity['artifact_sha256'], metrics=metrics,
        limits=GenerationLimits(**{k: limits[k] for k in
                                   ('input_tokens', 'output_tokens', 'context_tokens', 'response_bytes')}))
    if binding['record']['status'] != 'EOS_COMPLETE':
        raise InputBoundaryError('generation unusable; family rejection policy is not adopted')
    output = view_result(binding['record']['text'].encode('utf-8'), kind=expected_identity['kind'],
                         profile_output=profile_output, maximum_bytes=limits['response_bytes'],
                         maximum_views=limits['views'])
    return {**output, 'format': 'sacr-view-stage-v3', 'generation': binding,
            'generation_artifact_utf8': raw.decode('utf-8'), 'generation_identity': deepcopy(identity)}
