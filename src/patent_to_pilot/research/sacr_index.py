"""Detached CPU index snapshot and predeclared mask binding; not eligibility proof."""
import hashlib

import numpy as np

from patent_to_pilot.research.mtm_runtime import InputBoundaryError, decode_json, exact_fields, identifier
from patent_to_pilot.research.sacr_components import digest, vector_digest
from patent_to_pilot.research.sacr_factorial import passage_order_digest


class BoundCPUIndex:
    """Copies arrays once; full-scale memory/cost acceptance remains required.

    Manifest mask hashes must be derived independently using the declared runtime
    eligibility policy. Agreement here does not establish that policy correctness.
    No labels, model loading, filesystem discovery or normalization is performed.
    """

    def __init__(self, manifest_bytes, *, expected_sha256, family_ids, passage_ids, passage_owner, vectors):
        if type(manifest_bytes) is not bytes or hashlib.sha256(manifest_bytes).hexdigest() != expected_sha256:
            raise InputBoundaryError('index manifest bytes differ from trusted digest')
        manifest = decode_json(manifest_bytes)
        exact_fields(manifest, {'format', 'family_ids_sha256', 'passage_order_sha256',
                               'vectors_sha256', 'query_mask_sha256'})
        if manifest['format'] != 'sacr-cpu-index-v1' or type(manifest['query_mask_sha256']) is not dict:
            raise InputBoundaryError('invalid index snapshot manifest')
        for ids in (family_ids, passage_ids):
            if type(ids) is not list or not ids:
                raise InputBoundaryError('index identities require nonempty lists')
            for value in ids:
                identifier(value)
            if len(set(ids)) != len(ids):
                raise InputBoundaryError('duplicate index identities')
        matrix, owner = np.asarray(vectors), np.asarray(passage_owner)
        if (matrix.dtype != np.float32 or matrix.ndim != 2 or not matrix.size or
                len(matrix) != len(passage_ids) or owner.shape != (len(matrix),) or
                owner.dtype.kind not in 'iu' or len(np.unique(owner)) != len(family_ids)):
            raise InputBoundaryError('invalid index array dimensions or types')
        order = passage_order_digest(family_ids, owner, passage_ids)
        if (digest(family_ids) != manifest['family_ids_sha256'] or order != manifest['passage_order_sha256'] or
                vector_digest(matrix) != manifest['vectors_sha256']):
            raise InputBoundaryError('index content differs from manifest')
        for start in range(0, len(matrix), 16384):
            block = matrix[start:start + 16384]
            if not np.isfinite(block).all() or not np.allclose(np.linalg.norm(block, axis=1), 1, atol=1e-4, rtol=0):
                raise InputBoundaryError('invalid index vector geometry')
        self.identity = expected_sha256
        self._manifest = manifest
        self._family_ids, self._passage_ids = tuple(family_ids), tuple(passage_ids)
        self._matrix, self._owner = matrix.copy(), owner.copy()
        self._matrix.setflags(write=False)
        self._owner.setflags(write=False)

    def context(self, query_id, eligible, *, expected_index_sha256):
        if self.identity != expected_index_sha256:
            raise InputBoundaryError('controller and index identity disagree')
        mask = np.asarray(eligible)
        if mask.dtype != np.bool_ or mask.shape != (len(self._family_ids),):
            raise InputBoundaryError('invalid eligibility mask')
        mask_sha = digest(mask.tolist())
        if self._manifest['query_mask_sha256'].get(query_id) != mask_sha:
            raise InputBoundaryError('query mask differs from predeclared index binding')
        mask = mask.copy()
        mask.setflags(write=False)
        return {'family_ids': list(self._family_ids), 'passage_ids': list(self._passage_ids),
                'passage_owner': self._owner, 'passage_vectors': self._matrix,
                'expected_order_sha256': self._manifest['passage_order_sha256'], 'eligible': mask}
