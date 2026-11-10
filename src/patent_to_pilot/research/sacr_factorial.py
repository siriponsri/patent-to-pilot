"""CPU factorial scoring on pre-embedded inputs; no generation or evaluation labels."""
import hashlib
import json

import numpy as np

from patent_to_pilot.research.sacr_acquisition import acquire_union
from patent_to_pilot.research.sacr_selector import local_coverage, select_union


def passage_order_digest(family_ids, passage_owner, passage_ids):
    owner_array = np.asarray(passage_owner)
    if (owner_array.shape != (len(passage_ids),) or owner_array.dtype.kind not in 'iu' or
            (owner_array < 0).any() or (owner_array >= len(family_ids)).any()):
        raise ValueError('invalid passage ownership for identity binding')
    rows = [(passage_id, family_ids[int(owner)]) for passage_id, owner in zip(passage_ids, passage_owner, strict=True)]
    return hashlib.sha256(json.dumps(rows, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()


def compare_factorial(*, family_ids, passage_owner, passage_ids, passage_vectors,
                      expected_order_sha256, eligible, generic_views, invariant_views,
                      component_blocks, depth=200, chunk_size=16384, acquired=None):
    """Share one anchor, index/mask and component profile across four arms.

    Each views pair is (IDs, float32 vectors); blocks are component matrices with
    relation first and explicit conditions thereafter. This cannot establish that
    embeddings encode the declared texts. Trusted index/encoder preflight remains
    mandatory. Order digest is a supplied binding, not independent provenance.
    Supplied acquisition must come from a separately verified sealed stage. Its
    structure/exposure is checked here; this does not authenticate score values.
    """
    matrix = np.asarray(passage_vectors)
    if type(depth) is not int or not 1 <= depth <= 200 or type(chunk_size) is not int or chunk_size <= 0:
        raise ValueError('invalid factorial depth or chunk size')
    if (type(passage_ids) is not list or len(passage_ids) != len(matrix) or
            any(type(p) is not str or not p or p != p.strip() for p in passage_ids) or
            len(set(passage_ids)) != len(passage_ids)):
        raise ValueError('invalid passage identities')
    if not np.array_equal(generic_views[1][0], invariant_views[1][0]):
        raise ValueError('factorial arms require the identical anchor vector')
    if type(component_blocks) is not list or not 1 <= len(component_blocks) <= 8:
        raise ValueError('one to eight relation blocks required; empty profile needs declared fallback')
    blocks = [np.asarray(block) for block in component_blocks]
    for block in blocks:
        if (block.ndim != 2 or not 1 <= len(block) <= 9 or matrix.ndim != 2 or
                block.shape[1] != matrix.shape[1] or block.dtype != np.float32 or
                not np.isfinite(block).all() or
                not np.allclose(np.linalg.norm(block, axis=1), 1, atol=1e-4, rtol=0)):
            raise ValueError('invalid component vectors')
    digest = passage_order_digest(family_ids, passage_owner, passage_ids)
    if digest != expected_order_sha256:
        raise ValueError('passage identity/order binding mismatch')
    # Bind ordered passage identities before either acquisition is performed.
    reused = acquired is not None
    if not reused:
        acquired = {}
        for name, (view_ids, vectors) in [('G', generic_views), ('I', invariant_views)]:
            acquired[name] = acquire_union(family_ids=family_ids, passage_owner=passage_owner,
                                          passage_vectors=matrix, view_ids=view_ids, view_vectors=vectors,
                                          eligible=eligible, depth=depth, chunk_size=chunk_size)
    else:
        if type(acquired) is not dict or set(acquired) != {'G', 'I'}:
            raise ValueError('both sealed acquisition arms required')
        if (type(family_ids) is not list or not family_ids or
                any(type(f) is not str or not f or f != f.strip() for f in family_ids) or
                len(set(family_ids)) != len(family_ids) or matrix.dtype != np.float32 or
                matrix.ndim != 2 or not matrix.size or len(np.unique(passage_owner)) != len(family_ids)):
            raise ValueError('invalid reused acquisition index')
        for start in range(0, len(matrix), chunk_size):
            block = matrix[start:start + chunk_size]
            if not np.isfinite(block).all() or not np.allclose(np.linalg.norm(block, axis=1), 1, atol=1e-4, rtol=0):
                raise ValueError('invalid reused passage vectors')
        for view_ids, vectors in (generic_views, invariant_views):
            if (type(view_ids) is not list or not 1 <= len(view_ids) <= 3 or view_ids[0] != 'anchor' or
                    any(type(v) is not str or not v for v in view_ids) or len(set(view_ids)) != len(view_ids) or
                    vectors.dtype != np.float32 or vectors.shape != (len(view_ids), matrix.shape[1]) or
                    not np.isfinite(vectors).all() or
                    not np.allclose(np.linalg.norm(vectors, axis=1), 1, atol=1e-4, rtol=0)):
                raise ValueError('invalid reused acquisition views')
        mask = np.asarray(eligible)
        if mask.dtype != np.bool_ or mask.shape != (len(family_ids),):
            raise ValueError('invalid selection eligibility mask')
        allowed = {f for f, keep in zip(family_ids, mask, strict=True) if keep}
        for name, views in [('G', generic_views), ('I', invariant_views)]:
            result = acquired[name]
            ids = result['family_ids']
            scores = np.asarray(result['anchor_scores'])
            if (type(ids) is not list or any(type(f) is not str for f in ids) or
                    ids != sorted(set(ids)) or not set(ids) <= allowed or
                    len(ids) > len(views[0]) * depth or scores.shape != (len(ids),) or
                    not np.isfinite(scores).all() or (np.abs(scores) > 1 + 1e-6).any() or
                    set(result['rankings']) != set(views[0])):
                raise ValueError('invalid sealed acquisition exposure')
            union = set()
            for ranking in result['rankings'].values():
                ranked = [row['family_id'] for row in ranking]
                if len(ranked) > depth or len(set(ranked)) != len(ranked) or not set(ranked) <= allowed:
                    raise ValueError('invalid sealed per-view ranking')
                union.update(ranked)
            if union != set(ids):
                raise ValueError('sealed acquisition union mismatch')
    candidates = set(acquired['G']['family_ids']) | set(acquired['I']['family_ids'])
    family_positions = {f: i for i, f in enumerate(family_ids)}
    owner = np.asarray(passage_owner)
    selected_positions = np.flatnonzero(np.isin(owner, [family_positions[f] for f in candidates]))
    grouped = {f: [] for f in candidates}
    for index in selected_positions:
        grouped[family_ids[int(owner[index])]].append(int(index))
    coverage, evidence = {}, {}
    for family_id in sorted(candidates):
        indices = grouped[family_id]
        # Every block gets the exact same ordered passage slice, with no per-row maxima.
        cosines = [block @ matrix[indices].T for block in blocks]
        coverage[family_id] = {beta: local_coverage(cosines, beta) for beta in (0.0, 0.5)}
        evidence[family_id] = {'passage_ids': [passage_ids[i] for i in indices],
                               'passage_positions': indices, 'semantic_status': 'unknown'}
    arms = {}
    for view_kind, acquisition in acquired.items():
        ids = acquisition['family_ids']
        for selector_kind, beta in [('G', 0.0), ('L', 0.5)]:
            arms[view_kind + '/' + selector_kind] = select_union(
                ids, acquisition['anchor_scores'], [coverage[f][beta] for f in ids],
                depth=depth, alpha=0.5)
    component_count = sum(map(len, blocks))
    return {'arms': arms, 'acquisition': acquired, 'candidate_passages': evidence,
            'passage_order_sha256': digest, 'semantic_status': 'unknown',
            'status': 'PREEMBEDDED_FACTORIAL_ONLY_NOT_END_TO_END_SACR',
            'accounting': {
                'actual_acquisition_dot_products': 0 if reused else sum(
                    a['accounting']['view_passage_dot_products'] for a in acquired.values()),
                'acquisition_reused': reused,
                'actual_component_passage_dot_products': component_count * len(selected_positions),
                'component_rows': component_count, 'shared_candidate_passages': len(selected_positions),
                'standalone_component_dot_products': {k: component_count * sum(len(grouped[f]) for f in a['family_ids'])
                                                      for k, a in acquired.items()},
                'generation_and_embedding_cost': 'NOT_INCLUDED_PREEMBEDDED_INPUT',
                'timing_and_peak_memory': 'NOT_MEASURED'}}
