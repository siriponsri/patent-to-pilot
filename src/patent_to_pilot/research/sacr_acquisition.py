"""Chunked full-index MaxP acquisition; no encoder, labels or benchmark adapters."""
import numpy as np


def acquire_union(*, family_ids, passage_owner, passage_vectors, view_ids,
                  view_vectors, eligible, depth=200, chunk_size=16384):
    """Search every passage for each view, then union eligible family top-k lists.

    The first view must be anchor. Caller binds vectors/owner order to the audited
    index and supplies an independently computed runtime eligibility mask. This
    CPU NumPy implementation is not historical GPU numerical-parity evidence.
    No source text is normalized, no vectors are re-encoded or renormalized.
    """
    if (type(depth) is not int or not 1 <= depth <= 200 or
            type(chunk_size) is not int or chunk_size <= 0):
        raise ValueError('invalid acquisition depth or chunk size')
    for ids in (family_ids, view_ids):
        if (type(ids) is not list or not ids or any(type(i) is not str or not i or i != i.strip() for i in ids) or
                len(ids) != len(set(ids))):
            raise ValueError('invalid or duplicate acquisition identities')
    if len(view_ids) > 3 or view_ids[0] != 'anchor':
        raise ValueError('one anchor and at most two additional views required')
    matrix = np.asarray(passage_vectors)
    queries = np.asarray(view_vectors)
    owner = np.asarray(passage_owner)
    mask = np.asarray(eligible)
    n = len(family_ids)
    if (matrix.ndim != 2 or 0 in matrix.shape or matrix.dtype != np.float32 or
            queries.dtype != np.float32 or queries.shape != (len(view_ids), matrix.shape[1]) or
            owner.shape != (len(matrix),) or owner.dtype.kind not in 'iu' or
            mask.dtype != np.bool_ or mask.shape != (n,)):
        raise ValueError('acquisition dimensions or dtypes disagree')
    if (owner >= n).any() or (owner < 0).any() or len(np.unique(owner)) != n:
        raise ValueError('passage ownership must cover every indexed family exactly by identity')
    if not np.isfinite(queries).all() or not np.allclose(np.linalg.norm(queries, axis=1), 1, atol=1e-4, rtol=0):
        raise ValueError('view vectors must be finite unit vectors')
    best = np.full((len(view_ids), n), -np.inf, dtype=np.float32)
    chunks = 0
    for start in range(0, len(matrix), chunk_size):
        block = matrix[start:start + chunk_size]
        if not np.isfinite(block).all() or not np.allclose(np.linalg.norm(block, axis=1), 1, atol=1e-4, rtol=0):
            raise ValueError('passage vectors must be finite unit vectors')
        scores = queries @ block.T
        if not np.isfinite(scores).all():
            raise ValueError('nonfinite acquisition scores')
        for i in range(len(view_ids)):
            np.maximum.at(best[i], owner[start:start + len(block)], scores[i])
        chunks += 1
    eligible_positions = np.flatnonzero(mask)
    rankings = {}
    union = set()
    for i, view_id in enumerate(view_ids):
        candidates = eligible_positions
        if len(candidates) > depth:
            # Include every boundary tie before the global family-ID tie break.
            cutoff = np.partition(best[i, candidates], len(candidates) - depth)[len(candidates) - depth]
            candidates = candidates[best[i, candidates] >= cutoff]
        order = sorted(candidates.tolist(), key=lambda j: (-float(best[i, j]), family_ids[j]))[:depth]
        rankings[view_id] = [{'family_id': family_ids[j], 'score': float(best[i, j])} for j in order]
        union.update(order)
    positions = sorted(union, key=lambda j: family_ids[j])
    return {'rankings': rankings, 'family_ids': [family_ids[j] for j in positions],
            'anchor_scores': [float(best[0, j]) for j in positions],
            'accounting': {'views': len(view_ids), 'indexed_families': n,
                           'eligible_families': int(mask.sum()), 'passages_scanned': len(matrix),
                           'view_passage_dot_products': len(view_ids) * len(matrix),
                           'chunks': chunks, 'union_size': len(positions),
                           'duplicate_family_occurrences': sum(map(len, rankings.values())) - len(positions)},
            'backend': 'numpy_float32_cpu', 'semantic_status': 'unknown'}
