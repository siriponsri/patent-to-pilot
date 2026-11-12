"""Graph query-side coverage census + pilot-20 freeze (protocol GRAPH-AUTOMATIC-ROUND-20261112).

Uses only dev query texts and lexical (unscreened) R4 postings: no qrels, no scores, no model.
Reports how many queries yield relation keys and how many keys have postings, so screening
scope and call caps can be declared before any GPU dispatch.
"""
import hashlib
from .sg_relations_v2 import extract_family_v2
from .mtm_runtime import InputBoundaryError

PILOT_SALT = 'ptp-paper1-pilot20-20261112'
PILOT_SIZE = 20


def pilot_ids(query_ids):
    ids = sorted(set(query_ids))
    if len(ids) != len(query_ids) or len(ids) < PILOT_SIZE:
        raise InputBoundaryError('unique query identities required')
    return sorted(ids, key=lambda q: hashlib.sha256((PILOT_SALT + '|' + q).encode()).hexdigest())[:PILOT_SIZE]


def census(queries, postings, *, max_key_degree=100):
    """queries: [{'id','text'}]; postings: {key: {family_id: relation_id}}."""
    rows, pilot = [], set(pilot_ids([q['id'] for q in queries]))
    for q in queries:
        keys = sorted({r['alias_key'] for r in extract_family_v2(
            {'id': q['id'], 'title': '', 'abstract': q['text'], 'claims': ''})['records']})
        hit = [k for k in keys if postings.get(k)]
        usable = [k for k in hit if len(postings[k]) <= max_key_degree]
        fams = {f for k in usable for f in postings[k]}
        rows.append({'id': q['id'], 'keys': len(keys), 'keys_with_postings': len(hit),
                     'usable_keys': len(usable), 'direct_families': len(fams), 'pilot': q['id'] in pilot})
    def summary(sel):
        n = len(sel)
        return {'queries': n, 'zero_keys': sum(r['keys'] == 0 for r in sel),
                'zero_hits': sum(r['usable_keys'] == 0 for r in sel),
                'with_structure': sum(r['usable_keys'] > 0 for r in sel),
                'keys_total': sum(r['keys'] for r in sel), 'direct_families_total': sum(r['direct_families'] for r in sel)}
    pilot_rows = [r for r in rows if r['pilot']]
    pilot_keys = set()
    for q in queries:
        if q['id'] in pilot:
            pilot_keys |= {r['alias_key'] for r in extract_family_v2({'id': q['id'], 'title': '', 'abstract': q['text'], 'claims': ''})['records']}
    pilot_keys = {k for k in pilot_keys if postings.get(k) and len(postings[k]) <= max_key_degree}
    direct = {f for k in pilot_keys for f in postings[k]}
    family_keys = {}
    for k, members in postings.items():
        for f in members:
            family_keys.setdefault(f, set()).add(k)
    hop_keys = {k for f in direct for k in family_keys.get(f, ()) if len(postings[k]) <= max_key_degree} - pilot_keys
    reachable_relations = {(k, f) for k in pilot_keys | hop_keys for f in postings[k]}
    return {'all': summary(rows), 'pilot': summary(pilot_rows),
            'pilot_screening_scope': {'query_keys': len(pilot_keys), 'one_hop_bridge_keys': len(hop_keys),
                                      'reachable_key_family_relations': len(reachable_relations)},
            'rows': rows, 'pilot_ids': sorted(pilot), 'max_key_degree': max_key_degree,
            'postings_status': 'LEXICAL_UNSCREENED_R4', 'qrels_used': False, 'scores_computed': False}
