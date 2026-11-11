"""Separate audit axes without promoting unassessed work or changing R5 gates."""
from .mtm_runtime import InputBoundaryError


def critic_axes(*, backend_state, contract_valid=None, method_flagged=None):
    if backend_state not in ('COMPLETED', 'FAILED', 'UNKNOWN', 'NOT_RUN'):
        raise InputBoundaryError('invalid backend state')
    if backend_state != 'COMPLETED':
        if contract_valid is not None or method_flagged is not None:
            raise InputBoundaryError('nonterminal/absent output cannot carry verdicts')
        return {'execution': backend_state, 'evaluator': 'NOT_ASSESSED', 'method': 'NOT_ASSESSED', 'admissible': False}
    if type(contract_valid) is not bool or (contract_valid and type(method_flagged) is not bool) or (not contract_valid and method_flagged is not None):
        raise InputBoundaryError('invalid evaluator/method evidence combination')
    return {'execution': 'COMPLETED', 'evaluator': 'VALID' if contract_valid else 'INVALID',
            'method': ('FLAGGED' if method_flagged else 'UNFLAGGED_NOT_VALIDATED') if contract_valid else 'NOT_ASSESSED',
            'admissible': False}


def extraction_axes(record_count):
    if type(record_count) is not int or record_count < 0:
        raise InputBoundaryError('invalid extraction count')
    return {'record_count': record_count, 'nonempty_family': bool(record_count),
            'coverage': 'PARTIAL_OR_UNKNOWN' if record_count else 'ZERO_EXTRACTED_RECORDS',
            'retained_claim_fidelity': 'PENDING' if record_count else 'NOT_ASSESSED_ABSTENTION',
            'full_source_fidelity_pass': False, 'accepted_edges': 0}
