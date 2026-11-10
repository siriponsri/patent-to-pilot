"""Bound profile/view orchestration; not a production research runner."""
from copy import deepcopy

from patent_to_pilot.research.mtm_runtime import InputBoundaryError
from patent_to_pilot.research.sacr_execution import bind_input_snapshots
from patent_to_pilot.research.sacr_journal import DevStageJournal
from patent_to_pilot.research.sacr_profile_result import profile_result
from patent_to_pilot.research.sacr_views import collect_screened_views, parse_view_response


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

    def views(self, query_id, kind, adapter):
        """Require prepared profile before either matched factorial view arm.

        Generic adapter receives (query_id, source); selective additionally gets
        a detached profile. Adapter returns raw response bytes and complete costs.
        Raw generation attempts stay in adapter-owned private artifacts. Lexical
        screening is not fidelity approval; review decisions stop later retrieval.
        """
        if query_id not in self._sources or kind not in ('generic', 'selective'):
            raise InputBoundaryError('unknown query or view stage')
        source = self._sources[query_id]
        if source is None:
            raise InputBoundaryError('missing source cannot dispatch view generation')
        output = self.journal.read_completed_output(self._attempts[query_id, 'profile'])
        if type(output) is not dict or 'profile' not in output:
            raise InputBoundaryError('typed profile dependency required')
        canonical = profile_result(output['profile'], source=source, query_id=query_id)
        if output != canonical or output['decision'] != 'PROFILE_STRUCTURALLY_PREPARED_FIDELITY_PENDING':
            raise InputBoundaryError('profile is not structurally prepared for dependent views')
        profile = canonical['profile']
        protected = [c['raw_text'] for b in profile['blocks'] for c in b['attached_conditions']
                     if c['relation_to_block'] == 'explicit']
        cap = self.journal.execution['limits']['response_bytes']

        def validated_work():
            args = (query_id, source) if kind == 'generic' else (query_id, source, deepcopy(profile))
            raw, metrics = adapter(*args)
            if type(raw) is not bytes:
                raise InputBoundaryError('view adapter must return immutable response bytes')
            proposals = parse_view_response(raw, kind=kind, maximum_bytes=cap)
            if kind == 'selective':
                proposals.append(canonical['compact']['text'])
            screened = collect_screened_views(source, proposals, protected_phrases=protected,
                                               maximum_characters=cap)
            if len(screened['views']) > self.journal.execution['limits']['views']:
                raise InputBoundaryError('screened views exceed declared count cap')
            review = any(r['status'] == 'REVIEW_REQUIRED' for r in screened['proposals'])
            return {'format': 'sacr-view-stage-v1', 'query_id': query_id, 'kind': kind,
                    'decision': 'REVIEW_REQUIRED' if review else 'VIEWS_SCREENED_FIDELITY_PENDING',
                    'screened': screened, 'semantic_status': 'unknown'}, metrics

        return self.journal.execute(self._attempts[query_id, kind], validated_work)
