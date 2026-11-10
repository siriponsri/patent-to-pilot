"""Per-query text-row plan and injected embedding receipts, not model attestation."""
import hashlib

import numpy as np

from patent_to_pilot.research.mtm_runtime import InputBoundaryError, exact_fields
from patent_to_pilot.research.sacr_components import digest, vector_digest


def embedding_plan(prepared):
    """Compile controller-validated inputs; share exact text in one query encoder mode.

    The encoder manifest must bind prefix/tokenizer/preprocessing as well as weights.
    Text reuse is within this one query only, not a cache across queries or runs.
    """
    rows, positions = [], {}
    def add(text):
        if type(text) is not str or not text.strip():
            raise InputBoundaryError('invalid embedding text')
        if text not in positions:
            positions[text] = len(rows)
            sha = hashlib.sha256(text.encode()).hexdigest()
            rows.append({'row_id': digest(['query-text', text]), 'text': text, 'text_sha256': sha})
        return positions[text]
    arms = prepared['arms']
    if arms['generic']['views'][0] != arms['selective']['views'][0]:
        raise InputBoundaryError('embedding arms require identical anchor text')
    view_rows = {kind: [add(text) for text in arms[kind]['views']] for kind in ('generic', 'selective')}
    component_rows = [add(row['text']) for row in prepared['components']['rows']]
    body = {'format': 'sacr-query-embedding-plan-v1', 'query_id': prepared['query_id'],
            'inputs_sha256': digest(prepared), 'rows': rows, 'view_rows': view_rows,
            'component_rows': component_rows, 'component_blocks': prepared['components']['blocks']}
    return {**body, 'plan_sha256': digest(body)}


def bind_embeddings(plan, vectors, receipt, *, expected_plan_sha256, expected_encoder_sha256):
    body = {key: value for key, value in plan.items() if key != 'plan_sha256'}
    if plan.get('plan_sha256') != expected_plan_sha256 or digest(body) != expected_plan_sha256:
        raise InputBoundaryError('embedding plan changed')
    exact_fields(receipt, {'format', 'plan_sha256', 'encoder_sha256', 'row_ids', 'vectors_sha256'})
    if (type(expected_encoder_sha256) is not str or len(expected_encoder_sha256) != 64 or
            any(c not in '0123456789abcdef' for c in expected_encoder_sha256) or
            receipt['format'] != 'sacr-query-embeddings-v1' or
            receipt['encoder_sha256'] != expected_encoder_sha256 or
            receipt['plan_sha256'] != expected_plan_sha256 or
            receipt['row_ids'] != [row['row_id'] for row in plan['rows']]):
        raise InputBoundaryError('embedding receipt identity or row order mismatch')
    matrix = np.asarray(vectors)
    if (matrix.dtype != np.float32 or matrix.ndim != 2 or matrix.shape[0] != len(plan['rows']) or
            not matrix.size or not np.isfinite(matrix).all() or
            not np.allclose(np.linalg.norm(matrix, axis=1), 1, atol=1e-4, rtol=0) or
            vector_digest(matrix) != receipt['vectors_sha256']):
        raise InputBoundaryError('embedding vector bytes or geometry mismatch')
    matrix = matrix.copy()
    matrix.setflags(write=False)
    return matrix
