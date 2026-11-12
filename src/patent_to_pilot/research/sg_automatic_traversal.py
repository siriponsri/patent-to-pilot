"""Automatic-round Graph operators (protocol GRAPH-AUTOMATIC-ROUND-20261112, frozen before scores).

S       non-traversal: a family scores the number of distinct query keys whose postings contain it.
G       S hop-1 scores + HOP2_WEIGHT x number of distinct bridge keys (keys of S-discovered
        families that are not query keys) whose postings reach it; bounded edges.
S-deep  matched-work non-traversal control: same scoring as S, but may also consume the
        high-degree query keys S skips (ascending degree) until it has examined as many
        edges as G (membership + reverse). Any shortfall is reported, never hidden.
Ties are broken by a fixed salted SHA-256 of the family ID, never alphabetically.
Lexical key bridges are not semantic aliases; postings must come from screened relations.
"""
import hashlib
from .mtm_runtime import InputBoundaryError

SALT = 'ptp-graph-auto-20261112'
HOP2_WEIGHT = 0.5


def _tie(fid):
    return hashlib.sha256((SALT + '|' + fid).encode()).hexdigest()


def _order(scores):
    return sorted(scores, key=lambda fid: (-scores[fid], _tie(fid)))


def rank_graph_arms(query_keys, postings, *, edge_budget=2000, max_key_degree=100):
    if type(edge_budget) is not int or edge_budget < 1 or type(max_key_degree) is not int or max_key_degree < 1:
        raise InputBoundaryError('positive integer limits required')
    index = {}
    for key, members in postings.items():
        values = list(members)
        if type(key) is not str or not key or any(type(f) is not str or not f for f in values) or len(values) != len(set(values)):
            raise InputBoundaryError('invalid postings')
        index[key] = tuple(sorted(values, key=_tie))
    seeds = sorted(set(query_keys))
    if any(type(k) is not str or not k for k in seeds):
        raise InputBoundaryError('invalid query key')
    family_keys = {}
    for key, members in index.items():
        for fid in members:
            family_keys.setdefault(fid, set()).add(key)

    def direct(keys, budget):
        scores, examined, truncated = {}, 0, False
        for key in keys:
            for fid in index.get(key, ()):
                if examined >= budget:
                    truncated = True; break
                examined += 1
                scores[fid] = scores.get(fid, 0) + 1
            if truncated: break
        return scores, examined, truncated

    usable = [k for k in seeds if len(index.get(k, ())) <= max_key_degree]
    hubs = sorted((k for k in seeds if len(index.get(k, ())) > max_key_degree), key=lambda k: (len(index[k]), k))
    s_scores, s_edges, s_trunc = direct(usable, edge_budget)

    g_scores = dict(s_scores); g_edges = s_edges; reverse = 0; g_trunc = s_trunc; bridge_hits = {}
    bridges = sorted({k for fid in _order(s_scores) for k in family_keys.get(fid, ())} - set(seeds))
    reverse = sum(len(family_keys.get(fid, ())) for fid in s_scores)
    for key in bridges:
        members = index.get(key, ())
        if len(members) > max_key_degree: continue
        for fid in members:
            if g_edges >= edge_budget:
                g_trunc = True; break
            g_edges += 1
            bridge_hits.setdefault(fid, set()).add(key)
        if g_trunc: break
    for fid, keys in bridge_hits.items():
        g_scores[fid] = g_scores.get(fid, 0) + HOP2_WEIGHT * len(keys)

    target = g_edges + reverse
    d_scores, d_edges, d_trunc = direct(usable + hubs, target)
    return {'S': {'ranking': _order(s_scores), 'scores': s_scores, 'edges': s_edges, 'truncated': s_trunc},
            'G': {'ranking': _order(g_scores), 'scores': g_scores, 'edges': g_edges, 'reverse_edges': reverse,
                  'work': g_edges + reverse, 'truncated': g_trunc,
                  'hop2_families': sorted(set(bridge_hits) - set(s_scores), key=_tie)},
            'S_deep': {'ranking': _order(d_scores), 'scores': d_scores, 'edges': d_edges, 'truncated': d_trunc,
                       'work_target': target, 'work_shortfall': max(0, target - d_edges)},
            'skipped_hub_keys_in_S_and_G': hubs, 'tie_salt': SALT, 'hop2_weight': HOP2_WEIGHT,
            'semantics': 'UNVALIDATED_LEXICAL_KEY_BRIDGES_OVER_SCREENED_RELATIONS'}
