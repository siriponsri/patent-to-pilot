"""Bind automatic-screened relation memberships to exact original extraction.

This is source integrity, never independent semantic or alias certification.
All rejected/uncertain rows remain counted; no implicit screening of absent rows.
"""
from .mtm_runtime import InputBoundaryError
from .sg_relations_v2 import extract_family_v2
from .automatic_screening import route_result
from .r6_dispatch_journal import document_hash


def bind_screened_relations(families, records, screenings):
    expected = {}
    seen_families = set()
    for family in families:
        if family['id'] in seen_families:
            raise InputBoundaryError('duplicate source family')
        seen_families.add(family['id'])
        for record in extract_family_v2(family)['records']:
            expected[record['relation_id']] = record
    supplied = {}
    for record in records:
        rid = record['relation_id']
        if rid in supplied or expected.get(rid) != record:
            raise InputBoundaryError('relation source binding differs from extraction')
        supplied[rid] = record
    if set(screenings) != set(supplied):
        raise InputBoundaryError('screening population mismatch')
    postings, witnesses, counts = {}, {}, {}
    for rid, record in sorted(supplied.items()):
        screen = screenings[rid]
        if screen.get('record_sha256') != document_hash(record):
            raise InputBoundaryError('screening bound to another relation')
        decision = route_result('GRAPH', screen['terminal'], True, screen['screening'])
        counts[screen['screening']] = counts.get(screen['screening'], 0) + 1
        if decision['action'] == 'HOLD':
            raise InputBoundaryError('unresolved relation screening execution')
        if decision['action'] == 'USE_SCREENED_CANDIDATE':
            key, fid = record['alias_key'], record['family_id']
            postings.setdefault(key, {}).setdefault(fid, []).append(rid)
            witnesses[rid] = record
    return {'postings': postings, 'witnesses': witnesses, 'screening_counts': counts,
            'supplied_relations': len(supplied), 'source_relations': len(expected),
            'omitted_relations': len(expected) - len(supplied),
            'source_families': len(seen_families), 'semantic_certified': False,
            'edge_type': 'SAME_LEXICAL_FUNCTION_DESCRIPTOR_NOT_EQUIVALENCE'}


def bind_path_witnesses(path, graph):
    """Return evidence for every alternating key/family edge in a path."""
    if len(path) < 2 or path[0][0] != 'key' or path[-1][0] != 'family':
        raise InputBoundaryError('invalid graph path endpoints')
    evidence = []
    for left, right in zip(path, path[1:]):
        if (left[0], right[0]) == ('key', 'family'):
            key, fid = left[1], right[1]
        elif (left[0], right[0]) == ('family', 'key'):
            fid, key = left[1], right[1]
        else:
            raise InputBoundaryError('nonalternating path')
        ids = graph['postings'].get(key, {}).get(fid, [])
        if not ids:
            raise InputBoundaryError('path edge lacks original evidence')
        for rid in ids:
            row = graph['witnesses'].get(rid, {})
            if row.get('family_id') != fid or row.get('alias_key') != key:
                raise InputBoundaryError('edge witness identity mismatch')
        evidence.append({'key': key, 'family_id': fid, 'relation_ids': list(ids)})
    return evidence
