"""Bound first-stage orchestration; not a production research runner."""
from copy import deepcopy

from patent_to_pilot.research.mtm_runtime import InputBoundaryError
from patent_to_pilot.research.sacr_components import compile_components
from patent_to_pilot.research.sacr_execution import bind_input_snapshots
from patent_to_pilot.research.sacr_journal import DevStageJournal
from patent_to_pilot.research.sacr_views import compact_view


class BoundProfileController:
    """Own immutable allowed sources and journal profile validation atomically.

    The injected adapter receives only (query_id, source), returning a canonical
    profile and complete cost metrics. It must preserve raw model attempts in its
    private artifacts. This controller does not load models, approve fidelity,
    attest an anchor fallback, schedule retrieval, or enforce live resource caps.
    A successful callback can still yield a stop/fallback-required decision.
    """

    def __init__(self, destination, plan, execution, *, manifest_bytes, query_payload,
                 expected_plan_sha256, expected_execution_sha256):
        sources = bind_input_snapshots(
            execution, plan, manifest_bytes=manifest_bytes, query_payload=query_payload,
            expected_execution_sha256=expected_execution_sha256,
            expected_plan_sha256=expected_plan_sha256)
        self._sources = dict(sources)
        self._attempts = {(s['query_id'], s['stage']): s['attempt_id'] for s in plan['slots']}
        self.journal = DevStageJournal(destination, plan, expected_manifest_sha256=expected_plan_sha256,
                                       execution=execution,
                                       expected_execution_sha256=expected_execution_sha256)

    def profile(self, query_id, adapter):
        if query_id not in self._sources:
            raise InputBoundaryError('query is outside bound cohort')
        source = self._sources[query_id]
        attempt = self._attempts[query_id, 'profile']
        if source is None:
            self.journal.skip(attempt, reason='bound source is missing')
            return {'decision': 'MISSING_INPUT', 'query_id': query_id}

        def validated_work():
            profile, metrics = adapter(query_id, source)
            # Detach before checking: downstream code consumes exactly these records.
            profile = deepcopy(profile)
            components = compile_components(profile, source=source, query_id=query_id, input_kind='MTM_P')
            compact = compact_view(profile, source=source, query_id=query_id, input_kind='MTM_P')
            if components['status'] == 'ANCHOR_FALLBACK':
                decision = ('PROFILE_FAILED_FALLBACK_REQUIRED' if profile['extraction_status'] == 'failed'
                            else 'PROFILE_EMPTY_FALLBACK_REQUIRED')
            elif components['status'] == 'REVIEW_REQUIRED' or compact['status'] == 'REVIEW_REQUIRED':
                decision = 'REVIEW_REQUIRED'
            else:
                decision = 'PROFILE_STRUCTURALLY_PREPARED_FIDELITY_PENDING'
            return {'query_id': query_id, 'decision': decision, 'profile': profile,
                    'components': components, 'compact': compact, 'semantic_status': 'unknown'}, metrics

        # Structural failure happens within the reserved attempt, never after it
        # has been sealed as COMPLETED. No retry or downstream dispatch here.
        return self.journal.execute(attempt, validated_work)
