"""Bound first-stage orchestration; not a production research runner."""
from patent_to_pilot.research.mtm_runtime import InputBoundaryError
from patent_to_pilot.research.sacr_execution import bind_input_snapshots
from patent_to_pilot.research.sacr_journal import DevStageJournal
from patent_to_pilot.research.sacr_profile_result import profile_result


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
            return profile_result(profile, source=source, query_id=query_id), metrics

        # Structural failure happens within the reserved attempt, never after it
        # has been sealed as COMPLETED. No retry or downstream dispatch here.
        return self.journal.execute(attempt, validated_work)
