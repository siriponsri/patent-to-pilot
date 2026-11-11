"""R3 evidence compiler: literal text is program-owned, semantics remain unverified.

This is a new proposal format, not an adapter that repairs retained R1/R2 outputs.
No generation, retrieval or fidelity admission is performed by this module.
"""
import hashlib
from copy import deepcopy

from .mtm_runtime import InputBoundaryError, exact_fields, identifier
from .sacr_token_profile import source_catalogue, _resolve

VERSION = 'sacr-evidence-roles-v3'
ROLES = {'action', 'operand', 'effect', 'direction', 'negation', 'quantity', 'unit'}
KINDS = {'numeric', 'qualitative', 'polarity', 'direction', 'material', 'other'}


def compile_evidence(proposal, *, source, query_id):
    """Resolve independently selected occurrences, retaining uncovered source.

    Explicit/uncertain attachment and role names are model assertions, never
    validated facts. No output is usable as a fidelity-passed query by itself.
    """
    catalogue = source_catalogue(source)
    identifier(query_id)
    exact_fields(proposal, {'version', 'query_id', 'source_sha256', 'blocks'})
    if (proposal['version'] != VERSION or proposal['query_id'] != query_id or
            proposal['source_sha256'] != catalogue['source_sha256']):
        raise InputBoundaryError('R3 identity mismatch')
    if type(proposal['blocks']) is not list or not 0 <= len(proposal['blocks']) <= 8:
        raise InputBoundaryError('R3 block count')
    ids = set()

    def unique(value):
        identifier(value)
        if value in ids:
            raise InputBoundaryError('duplicate R3 identifier')
        ids.add(value)

    def spans(refs):
        if type(refs) is not list or not 1 <= len(refs) <= 16:
            raise InputBoundaryError('R3 evidence count')
        resolved = [_resolve(r, source, catalogue['tokens']) for r in refs]
        pairs = [(r['start'], r['end']) for r in resolved]
        if len(set(pairs)) != len(pairs) or pairs != sorted(pairs):
            raise InputBoundaryError('duplicate or unordered R3 evidence')
        return resolved

    blocks = []
    previous = -1
    for block in proposal['blocks']:
        exact_fields(block, {'id', 'evidence', 'roles', 'conditions', 'abstraction'})
        unique(block['id'])
        evidence = spans(block['evidence'])
        if evidence[0]['start'] < previous:
            raise InputBoundaryError('R3 blocks not in source order')
        previous = evidence[0]['start']
        if type(block['roles']) is not dict or set(block['roles']) - ROLES:
            raise InputBoundaryError('unknown R3 role')
        roles = {}
        for role, refs in block['roles'].items():
            roles[role] = spans(refs)
            if any(not any(e['start'] <= r['start'] < r['end'] <= e['end']
                           for e in evidence) for r in roles[role]):
                raise InputBoundaryError('role evidence outside relation evidence')
        if type(block['conditions']) is not list or len(block['conditions']) > 8:
            raise InputBoundaryError('R3 condition count')
        conditions = []
        for condition in block['conditions']:
            exact_fields(condition, {'id', 'kind', 'attachment', 'evidence', 'attachment_evidence'})
            unique(condition['id'])
            if condition['kind'] not in KINDS or condition['attachment'] not in ('explicit', 'uncertain'):
                raise InputBoundaryError('invalid R3 condition assertion')
            conditions.append({'id': condition['id'], 'kind_proposal': condition['kind'],
                'attachment_proposal': condition['attachment'],
                'literal_evidence': spans(condition['evidence']),
                'attachment_evidence': spans(condition['attachment_evidence']),
                'semantic_status': 'UNKNOWN_REQUIRES_REVIEW'})
        abstraction = block['abstraction']
        if abstraction is not None:
            if type(abstraction) is not str or not abstraction.strip():
                raise InputBoundaryError('invalid R3 abstraction proposal')
            try:
                abstraction.encode('utf-8')
            except UnicodeError:
                raise InputBoundaryError('invalid R3 Unicode') from None
        blocks.append({'id': block['id'], 'literal_evidence': evidence,
            'role_evidence': roles, 'conditions': conditions,
            'abstraction_proposal': abstraction})
    return {'version': VERSION, 'query_id': query_id,
        'source_sha256': hashlib.sha256(source.encode('utf-8')).hexdigest(),
        'blocks': deepcopy(blocks), 'retained_source': source,
        'status': 'LITERAL_COMPILATION_ONLY' if blocks else 'ABSTAINED_NO_EVIDENCE',
        'anchor_fallback_required': not blocks,
        'semantic_status': 'UNKNOWN_REQUIRES_REVIEW',
        'required_reviews': ['span_selection', 'role_and_direction', 'condition_attachment',
                             'negation', 'quantity_and_unit', 'omissions', 'selective_abstraction'],
        'retrieval_ready': False, 'automatic_fidelity_pass': False}
