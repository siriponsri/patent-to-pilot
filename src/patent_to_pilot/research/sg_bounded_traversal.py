"""Prospective fixed family/key traversal; lexical bridges are not semantic aliases.

S and G receive identical postings. S scores direct query-key membership; G
expands through additional keys of discovered families. This differs from the
historical one-hop parity control. No query labels, embeddings or database.
"""
from collections import deque
from .mtm_runtime import InputBoundaryError


def rank_structured_and_graph(query_keys, postings, universe, *, max_hops=2,
                              edge_budget=2000, max_key_degree=100,
                              reverse_edge_budget=2000, frontier_budget=2000):
    for value in (max_hops, edge_budget, max_key_degree, reverse_edge_budget, frontier_budget):
        if type(value) is not int or value < 1:
            raise InputBoundaryError('positive integer traversal limits required')
    universe = list(universe)
    if any(type(fid) is not str or not fid for fid in universe) or len(universe) != len(set(universe)):
        raise InputBoundaryError('invalid or duplicate universe family')
    known = set(universe)
    index = {}
    family_keys = {}
    for key, members in postings.items():
        if type(key) is not str or not key:
            raise InputBoundaryError('invalid relation key')
        values = list(members)
        if (any(type(fid) is not str or not fid for fid in values)
                or len(values) != len(set(values)) or not set(values) <= known):
            raise InputBoundaryError('duplicate or unknown posting family')
        index[key] = tuple(sorted(values))
        for fid in values:
            family_keys.setdefault(fid, set()).add(key)
    seeds = list(query_keys)
    if any(type(key) is not str or not key for key in seeds):
        raise InputBoundaryError('invalid query key')
    seeds = sorted(set(seeds))
    family_keys = {fid: tuple(sorted(keys)) for fid, keys in family_keys.items()}

    def search(traverse):
        frontier = deque((key, 1) for key in seeds[:frontier_budget])
        queued = set(seeds[:frontier_budget])
        routes = {key: [('key', key)] for key in queued}
        reverse_examined = 0
        frontier_truncated = len(seeds) > frontier_budget
        forward_truncated = False
        reverse_truncated = False
        scores, paths, examined = {}, {}, 0
        skipped_hubs = set()
        while frontier and examined < edge_budget:
            key, depth = frontier.popleft()
            members = index.get(key, ())
            if len(members) > max_key_degree:
                skipped_hubs.add(key)
                continue
            for fid in members:
                if examined >= edge_budget:
                    forward_truncated = True
                    break
                examined += 1
                # One strongest path; stable ranking cannot benefit from cycles.
                score = 1.0 / depth
                if score > scores.get(fid, 0):
                    scores[fid] = score
                    paths[fid] = {'via_key': key, 'hops': depth,
                                  'path': routes[key] + [('family', fid)]}
                if traverse and depth < max_hops:
                    for nxt in family_keys.get(fid, ()):
                        if reverse_examined >= reverse_edge_budget:
                            reverse_truncated = True
                            break
                        reverse_examined += 1
                        if nxt not in queued:
                            if len(queued) >= frontier_budget:
                                frontier_truncated = True
                                break
                            routes[nxt] = routes[key] + [('family', fid), ('key', nxt)]
                            queued.add(nxt)
                            frontier.append((nxt, depth + 1))
        return {'ranking': sorted(scores, key=lambda fid: (-scores[fid], fid)),
                'scores': scores, 'path_summary': paths,
                'examined_membership_edges': examined,
                'examined_reverse_edges': reverse_examined,
                'frontier_truncated': frontier_truncated,
                'forward_truncated': forward_truncated or bool(frontier),
                'reverse_truncated': reverse_truncated,
                'reverse_budget_reached': reverse_examined == reverse_edge_budget,
                'skipped_hub_keys': sorted(skipped_hubs),
                'budget_reached': examined == edge_budget}

    return {'S': search(False), 'G': search(True),
            'semantics': 'UNVALIDATED_LEXICAL_KEY_BRIDGES',
            'hop_definition': 'key-expansion rounds; one round traverses key-to-family',
            'limits': {'max_hops': max_hops, 'edge_budget': edge_budget,
                       'max_key_degree': max_key_degree, 'reverse_edge_budget': reverse_edge_budget,
                       'frontier_budget': frontier_budget}}
