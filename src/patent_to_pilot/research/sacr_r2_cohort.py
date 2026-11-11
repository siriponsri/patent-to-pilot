"""Fixed 100-query R2 orchestration, frozen risk cap, no retries or card issuance."""
from pathlib import Path
import json
import hashlib

from .mtm_runtime import InputBoundaryError
from .sacr_native_fidelity import bind_sample, write_new

STATUSES = {'UNASSESSABLE', 'ESCALATE', 'AUTOMATIC_UNFLAGGED_NOT_FIDELITY_PASS'}


def run_cohort(*, query_bytes, sample_bytes, query_sha256, sample_sha256,
               destination, run_query, check_admission):
    """run_query(q, source, fresh_path) executes the evidence-bound bundle runner.

    Caller pins this module and callback in the execution manifest. All original
    entries remain in the denominator, including after early termination. Human
    cards and retrieval require separate gates; no screen state grants PASS.
    """
    entries = bind_sample(query_bytes, sample_bytes, query_sha256=query_sha256,
                          sample_sha256=sample_sha256)
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=False)
    write_new(destination/'reservation.json', {'sample_sha256':sample_sha256,
        'query_sha256':query_sha256, 'sample_size':100, 'risk_cap':20,
        'sentinels_required':10, 'maximum_generation_calls':400, 'retry':False})
    completed, risks = [], []
    active_index = None

    def close(status, **extra):
        result = {'status':status, 'original_sample_size':100,
            'completed_queries':len(completed), 'not_completed_queries':100-len(completed),
            'outcomes':completed, 'risk_count':len(risks), 'risk_query_ids':risks,
            'semantic_pass':False, 'human_cards_issued':0, 'retrieval':'NOT_RUN',
            'retry':False, **extra}
        write_new(destination/'cohort.json', result)
        return result

    try:
        for index,(query_id,source,_) in enumerate(entries):
            # This check precedes even creation of a per-query attempt.
            check_admission(index)
            active_index = index
            result = run_query(query_id, source, destination/f'{index:03d}')
            if (type(result) is not dict or result.get('query_id') != query_id
                    or result.get('status') not in STATUSES or result.get('semantic_pass') is not False
                    or result.get('retry') is not False):
                raise InputBoundaryError('invalid per-query bundle result')
            result_path = destination/f'{index:03d}'/'result.json'
            if result_path.is_symlink() or not result_path.resolve().is_relative_to(destination.resolve()):
                raise InputBoundaryError('bundle result path escapes cohort')
            raw = result_path.read_bytes()
            if json.loads(raw) != result:
                raise InputBoundaryError('returned bundle differs from durable result')
            completed.append({'index':index, 'query_id':query_id, 'status':result['status'],
                              'result_sha256':hashlib.sha256(raw).hexdigest()})
            active_index = None
            if result['status'] != 'AUTOMATIC_UNFLAGGED_NOT_FIDELITY_PASS':
                risks.append(query_id)
            write_new(destination/f'progress-{index:03d}.json', {
                'completed':len(completed), 'risk_count':len(risks), 'semantic_pass':False})
            if len(risks) > 20:
                return close('STOP_FROZEN_REVIEW_CAP', never_started_queries=100-len(completed))
        return close('AUTOMATIC_SCREEN_COMPLETE_HUMAN_REVIEW_REQUIRED', never_started_queries=0)
    except BaseException as error:
        close('STOP_INCOMPLETE_INFRA_OR_ADMISSION', exception_type=type(error).__name__,
              active_query_index=active_index,
              never_started_queries=100-len(completed)-(1 if active_index is not None else 0),
              incomplete_attempt_cost='INSPECT_RETAINED_QUERY_AND_SUPERVISOR' if active_index is not None else 'NO_QUERY_DISPATCHED',
              cost_accounting='WHOLE_SUPERVISOR_REQUIRED_NO_LEDGER_RESET')
        raise
