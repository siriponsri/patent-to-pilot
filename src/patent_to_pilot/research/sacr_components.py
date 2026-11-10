"""Source/profile-bound component plan and prospective embedding row receipts."""
import hashlib
import json

import numpy as np

from patent_to_pilot.research.mtm_runtime import InputBoundaryError, exact_fields
from patent_to_pilot.research.sacr_profile import validate_profile


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                     separators=(',', ':')).encode('utf-8')).hexdigest()


def compile_components(profile, *, source, query_id, input_kind):
    validation = validate_profile(profile, source=source, query_id=query_id, input_kind=input_kind)
    status = ('ANCHOR_FALLBACK' if validation['anchor_fallback_required'] else
              'REVIEW_REQUIRED' if validation['review_flags'] else 'COMPONENTS_PREPARED')
    rows, blocks = [], []
    if status == 'COMPONENTS_PREPARED':
        for block in profile['blocks']:
            begin = len(rows)
            entries = [('relation', block['block_id'], block['relation_text'])]
            entries += [('condition', c['condition_id'], c['raw_text']) for c in block['attached_conditions']
                        if c['relation_to_block'] == 'explicit']
            for role, item_id, text in entries:
                rows.append({'row_id': digest([block['block_id'], role, item_id]),
                             'block_id': block['block_id'], 'item_id': item_id,
                             'role': role, 'text': text, 'text_sha256': hashlib.sha256(text.encode()).hexdigest()})
            blocks.append({'block_id': block['block_id'], 'start': begin, 'end': len(rows)})
    body = {'format': 'sacr-component-plan-v1', 'status': status, 'query_id': query_id,
            'input_kind': input_kind, 'source_sha256': profile['source_sha256'],
            'profile_sha256': digest(profile), 'rows': rows, 'blocks': blocks,
            'excluded_uncertain_conditions': validation['uncertain_conditions'],
            'review_flags': validation['review_flags'], 'fidelity_review': 'REQUIRED',
            'semantic_status': 'unknown'}
    return {**body, 'plan_sha256': digest(body)}


def vector_digest(matrix):
    """Canonical shape + little-endian float32 bytes, distinct from a .npy hash."""
    return hashlib.sha256(json.dumps(list(matrix.shape)).encode() + b'\n' +
                          np.ascontiguousarray(matrix, dtype='<f4').tobytes()).hexdigest()


def bind_component_vectors(plan, vectors, receipt, *, expected_plan_sha256, expected_encoder_sha256):
    """Check row-order/byte bindings; this is not proof of encoder execution.

    Encoder identity is the digest of its complete separately pinned identity
    manifest (weights, tokenizer, preprocessing/prefix/settings), not a model name.
    No encoding, normalization, reordering, fuzzy matching or repair is performed.
    """
    body = {key: value for key, value in plan.items() if key != 'plan_sha256'}
    if digest(body) != expected_plan_sha256 or plan.get('plan_sha256') != expected_plan_sha256:
        raise InputBoundaryError('component plan changed or is not the expected version')
    if plan['status'] != 'COMPONENTS_PREPARED' or not plan['rows']:
        raise InputBoundaryError('component plan is not eligible for embedding')
    exact_fields(receipt, {'format', 'plan_sha256', 'encoder_sha256', 'row_ids', 'vectors_sha256'})
    if (receipt['format'] != 'sacr-component-vectors-v1' or receipt['plan_sha256'] != expected_plan_sha256 or
            receipt['encoder_sha256'] != expected_encoder_sha256 or
            type(expected_encoder_sha256) is not str or len(expected_encoder_sha256) != 64 or
            any(c not in '0123456789abcdef' for c in expected_encoder_sha256) or
            receipt['row_ids'] != [row['row_id'] for row in plan['rows']]):
        raise InputBoundaryError('component embedding identity/order mismatch')
    matrix = np.asarray(vectors)
    if (matrix.dtype != np.float32 or matrix.ndim != 2 or matrix.shape[0] != len(plan['rows']) or
            matrix.shape[1] == 0 or not np.isfinite(matrix).all() or
            not np.allclose(np.linalg.norm(matrix, axis=1), 1, atol=1e-4, rtol=0) or
            vector_digest(matrix) != receipt['vectors_sha256']):
        raise InputBoundaryError('component vector content mismatch')
    # Detached read-only arrays prevent later caller mutation from changing bound rows.
    blocks = []
    for block in plan['blocks']:
        array = matrix[block['start']:block['end']].copy()
        array.setflags(write=False)
        blocks.append(array)
    return blocks
