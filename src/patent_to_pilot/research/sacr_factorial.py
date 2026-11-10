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
                      component_blocks, depth=200, chunk_size=16384):
    """Share one anchor, index/mask and component profile across four arms.

    Each views pair is (IDs, float32 vectors); blocks are component matrices with
    relation first and explicit conditions thereafter. This cannot establish that
    embeddings encode the declared texts. Trusted index/encoder preflight remains
    mandatory. Order digest is a supplied binding, not independent provenance.
    """
    matrix = np.asarray(passage_vectors)
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
    acquired = {}
    for name, (view_ids, vectors) in [('G', generic_views), ('I', invariant_views)]:
        acquired[name] = acquire_union(family_ids=family_ids, passage_owner=passage_owner,
                                      passage_vectors=matrix, view_ids=view_ids, view_vectors=vectors,
                                      eligible=eligible, depth=depth, chunk_size=chunk_size)
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
                'actual_acquisition_dot_products': sum(a['accounting']['view_passage_dot_products'] for a in acquired.values()),
                'actual_component_passage_dot_products': component_count * len(selected_positions),
                'component_rows': component_count, 'shared_candidate_passages': len(selected_positions),
                'standalone_component_dot_products': {k: component_count * sum(len(grouped[f]) for f in a['family_ids'])
                                                      for k, a in acquired.items()},
                'generation_and_embedding_cost': 'NOT_INCLUDED_PREEMBEDDED_INPUT',
                'timing_and_peak_memory': 'NOT_MEASURED'}}
