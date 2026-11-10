"""Private v3 view evidence: bound normal-return record, no failure-policy adoption."""
from copy import deepcopy

from patent_to_pilot.research.mtm_runtime import InputBoundaryError, exact_fields
from patent_to_pilot.research.sacr_generation import GenerationLimits
from patent_to_pilot.research.sacr_generation_receipt import bind_generation_record
from patent_to_pilot.research.sacr_view_result import view_result
from patent_to_pilot.research.sacr_outcomes import summarize_costs


class GenerationEvidenceFailure(InputBoundaryError):
    """A verified normal return failed acceptance; private evidence is retained."""

    def __init__(self, *, raw, identity, binding, metrics, reason):
        super().__init__('bound generation failed view acceptance; no retry or fallback')
        self.output = {'format': 'sacr-generation-failure-v1', 'query_id': identity['query_id'],
                       'kind': identity['kind'], 'attempt_id': identity['attempt_id'],
                       'reason': reason, 'generation': deepcopy(binding),
                       'generation_artifact_utf8': raw.decode('utf-8'),
                       'generation_identity': deepcopy(identity), 'retry': False,
                       'semantic_status': 'unknown'}
        self.metrics = deepcopy(metrics)


def generated_view_result(raw, identity, *, expected_identity, metrics, profile_output, limits):
    exact_fields(identity, set(expected_identity) | {'artifact_sha256'})
    if any(identity[key] != value for key, value in expected_identity.items()):
        raise InputBoundaryError('generation identity differs from bound execution/query/stage')
    binding = bind_generation_record(
        raw, expected_sha256=identity['artifact_sha256'], metrics=metrics,
        limits=GenerationLimits(**{k: limits[k] for k in
                                   ('input_tokens', 'output_tokens', 'context_tokens', 'response_bytes')}))
    # Validate all reported costs before preserving them as failure evidence.
    summarize_costs([{'event_id': identity['attempt_id'], 'query_id': identity['query_id'],
                     'stage': identity['kind'], 'status': 'FAILED', 'metrics': metrics}])
    if binding['record']['status'] != 'EOS_COMPLETE':
        raise GenerationEvidenceFailure(raw=raw, identity=identity, binding=binding,
                                        metrics=metrics, reason='GENERATION_NOT_EOS_COMPLETE')
    try:
        output = view_result(binding['record']['text'].encode('utf-8'), kind=expected_identity['kind'],
                             profile_output=profile_output, maximum_bytes=limits['response_bytes'],
                             maximum_views=limits['views'])
    except InputBoundaryError:
        raise GenerationEvidenceFailure(raw=raw, identity=identity, binding=binding,
                                        metrics=metrics, reason='VIEW_ACCEPTANCE_FAILED') from None
    return {**output, 'format': 'sacr-view-stage-v3', 'generation': binding,
            'generation_artifact_utf8': raw.decode('utf-8'), 'generation_identity': deepcopy(identity)}
