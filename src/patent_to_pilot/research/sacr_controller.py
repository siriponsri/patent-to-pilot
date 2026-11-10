"""Bound profile/view orchestration; not a production research runner."""
from copy import deepcopy

import numpy as np

from patent_to_pilot.research.mtm_runtime import InputBoundaryError
from patent_to_pilot.research.sacr_execution import bind_input_snapshots
from patent_to_pilot.research.sacr_journal import DevStageJournal
from patent_to_pilot.research.sacr_profile_result import profile_result
from patent_to_pilot.research.sacr_components import digest
from patent_to_pilot.research.sacr_view_result import view_result
from patent_to_pilot.research.sacr_embedding import embedding_plan, bind_embeddings
from patent_to_pilot.research.sacr_acquisition import acquire_union
from patent_to_pilot.research.sacr_factorial import compare_factorial
from patent_to_pilot.research.sacr_outcomes import METRICS, finalize_query
from patent_to_pilot.research.sacr_selection_result import selection_outcome


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
        cap = self.journal.execution['limits']['response_bytes']

        def validated_work():
            args = (query_id, source) if kind == 'generic' else (query_id, source, deepcopy(profile))
            raw, metrics = adapter(*args)
            return view_result(raw, kind=kind, profile_output=canonical, maximum_bytes=cap,
                               maximum_views=self.journal.execution['limits']['views']), metrics

        return self.journal.execute(self._attempts[query_id, kind], validated_work)

    def embedding_inputs(self, query_id):
        """Replay both view decisions before preparing texts; no adapter dispatch.

        Returns detached inputs with explicit degeneracy flags. This is not
        fidelity approval or proof an embedding adapter actually used these texts.
        Failed/unsealed view attempts need their declared failure policy, not an
        invented successful view record, and are refused here.
        """
        if query_id not in self._sources or self._sources[query_id] is None:
            raise InputBoundaryError('embedding requires bound available source')
        profile = self.journal.read_completed_output(self._attempts[query_id, 'profile'])
        if type(profile) is not dict or 'profile' not in profile:
            raise InputBoundaryError('typed profile required')
        canonical = profile_result(profile['profile'], source=self._sources[query_id], query_id=query_id)
        if canonical != profile or canonical['decision'] != 'PROFILE_STRUCTURALLY_PREPARED_FIDELITY_PENDING':
            raise InputBoundaryError('embedding profile is not structurally prepared')
        limits = self.journal.execution['limits']
        results = {}
        for kind in ('generic', 'selective'):
            output = self.journal.read_completed_output(self._attempts[query_id, kind])
            if type(output) is not dict or type(output.get('response_utf8')) is not str:
                raise InputBoundaryError('replayable typed view result required')
            replayed = view_result(output['response_utf8'].encode('utf-8'), kind=kind,
                                   profile_output=canonical, maximum_bytes=limits['response_bytes'],
                                   maximum_views=limits['views'])
            if replayed != output or replayed['decision'] == 'REVIEW_REQUIRED':
                raise InputBoundaryError('view evidence changed or requires review')
            results[kind] = {'views': tuple(replayed['screened']['views']),
                             'view_output_sha256': digest(replayed),
                             'no_generated_view_retained': replayed['no_generated_view_retained']}
        return {'query_id': query_id, 'components': deepcopy(canonical['components']),
                'arms': results, 'semantic_status': 'unknown', 'fidelity_review': 'REQUIRED'}

    def embed(self, query_id, adapter):
        """Reserve once, then call an injected adapter on detached planned text rows.

        Adapter returns (float32 unit vectors, identity receipt, cost metrics).
        Its receipt is checked, not trusted as proof of actual encoder execution.
        Private small per-query vectors are journaled as float32-replayable JSON.
        """
        prepared = self.embedding_inputs(query_id)
        plan = embedding_plan(prepared)
        encoder = self.journal.execution['identities']['encoder_manifest']

        def work():
            vectors, receipt, metrics = adapter(deepcopy(plan), encoder)
            matrix = bind_embeddings(plan, vectors, receipt, expected_plan_sha256=plan['plan_sha256'],
                                     expected_encoder_sha256=encoder)
            return {'format': 'sacr-embedding-stage-v1', 'query_id': query_id, 'plan': plan,
                    'receipt': deepcopy(receipt), 'vectors_float32': matrix.tolist(),
                    'semantic_status': 'unknown', 'fidelity_review': 'REQUIRED'}, metrics

        return self.journal.execute(self._attempts[query_id, 'embedding'], work)

    def _retrieval_inputs(self, query_id, index, eligible):
        prepared = self.embedding_inputs(query_id)
        expected_plan = embedding_plan(prepared)
        output = self.journal.read_completed_output(self._attempts[query_id, 'embedding'])
        if (output.get('format') != 'sacr-embedding-stage-v1' or output.get('query_id') != query_id or
                output.get('plan') != expected_plan):
            raise InputBoundaryError('sealed embedding plan differs from replayed texts')
        vectors = bind_embeddings(expected_plan, np.asarray(output['vectors_float32'], dtype=np.float32),
                                  output['receipt'], expected_plan_sha256=expected_plan['plan_sha256'],
                                  expected_encoder_sha256=self.journal.execution['identities']['encoder_manifest'])
        identity = self.journal.execution['identities']['index_manifest']
        context = index.context(query_id, eligible, expected_index_sha256=identity)
        if vectors.shape[1] != context['passage_vectors'].shape[1]:
            raise InputBoundaryError('query and index vector dimensions disagree')
        views = {}
        for kind, rows in expected_plan['view_rows'].items():
            views[kind] = (['anchor'] + [f'view-{i}' for i in range(1, len(rows))], vectors[rows])
        components = vectors[expected_plan['component_rows']]
        context.update(generic_views=views['generic'], invariant_views=views['selective'],
                       component_blocks=[components[b['start']:b['end']] for b in expected_plan['component_blocks']],
                       depth=self.journal.execution['limits']['depth'])
        binding = {'index_sha256': identity, 'mask_sha256': digest(context['eligible'].tolist()),
                   'embedding_output_sha256': digest(output), 'depth': context['depth']}
        return context, binding

    def acquire(self, query_id, index, eligible):
        context, binding = self._retrieval_inputs(query_id, index, eligible)
        def work():
            acquired = {}
            for name, key in [('G', 'generic_views'), ('I', 'invariant_views')]:
                ids, vectors = context[key]
                acquired[name] = acquire_union(
                    family_ids=context['family_ids'], passage_owner=context['passage_owner'],
                    passage_vectors=context['passage_vectors'], eligible=context['eligible'],
                    view_ids=ids, view_vectors=vectors, depth=context['depth'])
            costs = {key: 0 for key in METRICS}
            costs['peak_memory_bytes'] = None
            costs['index_dot_products'] = sum(a['accounting']['view_passage_dot_products'] for a in acquired.values())
            return {'format': 'sacr-acquisition-stage-v1', 'query_id': query_id,
                    'binding': binding, 'acquired': acquired}, costs
        return self.journal.execute(self._attempts[query_id, 'acquisition'], work)

    def select(self, query_id, index, eligible):
        context, binding = self._retrieval_inputs(query_id, index, eligible)
        acquisition = self.journal.read_completed_output(self._attempts[query_id, 'acquisition'])
        if (acquisition.get('format') != 'sacr-acquisition-stage-v1' or
                acquisition.get('query_id') != query_id or acquisition.get('binding') != binding):
            raise InputBoundaryError('acquisition belongs to different query/index/mask/embedding/depth')
        def work():
            result = compare_factorial(**context, acquired=acquisition['acquired'])
            costs = {key: 0 for key in METRICS}
            costs['peak_memory_bytes'] = None
            costs['candidate_dot_products'] = result['accounting']['actual_component_passage_dot_products']
            return {'format': 'sacr-selection-stage-v1', 'query_id': query_id, 'binding': binding,
                    'acquisition_output_sha256': digest(acquisition), 'result': result}, costs
        return self.journal.execute(self._attempts[query_id, 'selection'], work)

    def finalize_ready(self, index, masks):
        """Derive every query from sealed outputs; no arbitrary rankings accepted.

        All-ready cohort path only. Missing/fallback/stopped queries are refused,
        never dropped; mixed-cohort finalization still needs bound failure/anchor
        evidence. READY denotes recorded rankings, not scientific/fidelity approval.
        No search, model call or reranking is performed during this verification.
        """
        queries = self.journal.manifest['query_ids']
        if type(masks) is not dict or set(masks) != set(queries):
            raise InputBoundaryError('finalization requires exact declared mask cohort')
        outcomes = []
        for query in queries:
            outcomes.append(self._ready_outcome(query, index, masks[query]))
        return self.journal.finalize(outcomes)

    def _ready_outcome(self, query, index, mask):
        context, binding = self._retrieval_inputs(query, index, mask)
        acquisition = self.journal.read_completed_output(self._attempts[query, 'acquisition'])
        selection = self.journal.read_completed_output(self._attempts[query, 'selection'])
        if (acquisition.get('format') != 'sacr-acquisition-stage-v1' or
                acquisition.get('query_id') != query or acquisition.get('binding') != binding or
                selection.get('query_id') != query or selection.get('binding') != binding or
                selection.get('acquisition_output_sha256') != digest(acquisition) or
                selection.get('result', {}).get('acquisition') != acquisition.get('acquired') or
                selection.get('result', {}).get('passage_order_sha256') != context['expected_order_sha256']):
            raise InputBoundaryError('selection dependency chain differs from bound run')
        outcome = selection_outcome(selection)
        for arm, ranking in outcome['rankings'].items():
            if (len(ranking) > binding['depth'] or
                    not set(ranking) <= set(acquisition['acquired'][arm[0]]['family_ids'])):
                raise InputBoundaryError('selection exceeds its bound candidate exposure')
        return outcome

    def finalize_mixed(self, index, masks):
        """Derive ready/missing/review/retrieval-failure states without dropping rows.

        Every declared slot must already be explicitly terminal. No automatic
        skip, guessed process death, fallback ranking or failure repair is made.
        Profile fallback and malformed generation remain blocked on their missing
        anchor/policy bindings rather than being silently relabelled.
        """
        queries = self.journal.manifest['query_ids']
        if type(masks) is not dict or set(masks) != set(queries):
            raise InputBoundaryError('finalization requires exact declared mask cohort')
        outcomes = []
        for query in queries:
            records = {stage: self.journal.read_terminal_attempt(attempt)
                       for (q, stage), attempt in self._attempts.items() if q == query}
            states = {stage: record[0]['status'] for stage, record in records.items()}
            if self._sources[query] is None:
                if any(status != 'SKIPPED' for status in states.values()):
                    raise InputBoundaryError('missing source has executed stages')
                outcomes.append(finalize_query(query_id=query, state='MISSING_INPUT'))
                continue
            if states['profile'] != 'COMPLETED':
                raise InputBoundaryError('profile failure requires separately bound original anchor')
            profile = records['profile'][1]
            if type(profile) is not dict or 'profile' not in profile:
                raise InputBoundaryError('typed profile terminal evidence required')
            canonical = profile_result(profile['profile'], source=self._sources[query], query_id=query)
            if canonical != profile:
                raise InputBoundaryError('profile terminal evidence changed')
            decision = canonical['decision']
            if decision.endswith('FALLBACK_REQUIRED'):
                raise InputBoundaryError('profile fallback requires separately bound original anchor')
            review = decision == 'REVIEW_REQUIRED'
            if not review:
                for kind in ('generic', 'selective'):
                    if states[kind] != 'COMPLETED':
                        raise InputBoundaryError('failed view generation requires declared family failure policy')
                    output = records[kind][1]
                    if type(output) is not dict or type(output.get('response_utf8')) is not str:
                        raise InputBoundaryError('typed view terminal evidence required')
                    limits = self.journal.execution['limits']
                    replayed = view_result(output['response_utf8'].encode(), kind=kind, profile_output=canonical,
                                           maximum_bytes=limits['response_bytes'], maximum_views=limits['views'])
                    if replayed != output:
                        raise InputBoundaryError('view terminal evidence changed')
                    review = review or replayed['decision'] == 'REVIEW_REQUIRED'
            retrieval = ('embedding', 'acquisition', 'selection')
            if review:
                if any(states[stage] != 'SKIPPED' for stage in retrieval):
                    raise InputBoundaryError('review-required query executed retrieval')
                outcomes.append(finalize_query(query_id=query, state='REVIEW_REQUIRED'))
            elif any(states[stage] in ('FAILED', 'INTERRUPTED') for stage in retrieval):
                first = next(i for i, stage in enumerate(retrieval) if states[stage] in ('FAILED', 'INTERRUPTED'))
                if (any(states[s] != 'COMPLETED' for s in retrieval[:first]) or
                        any(states[s] != 'SKIPPED' for s in retrieval[first + 1:])):
                    raise InputBoundaryError('retrieval failure chain is inconsistent')
                outcomes.append(finalize_query(query_id=query, state='RETRIEVAL_FAILED'))
            else:
                outcomes.append(self._ready_outcome(query, index, masks[query]))
        return self.journal.finalize(outcomes)
