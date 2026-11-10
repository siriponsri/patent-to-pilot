"""Pinned original-anchor result bundle; byte agreement is not baseline parity."""
import hashlib

from patent_to_pilot.research.mtm_runtime import InputBoundaryError, decode_json, exact_fields
from patent_to_pilot.research.sacr_outcomes import finalize_query


def bind_anchor_bundle(raw, execution):
    if (type(raw) is not bytes or execution['format'] != 'sacr-dev-execution-v2' or
            hashlib.sha256(raw).hexdigest() != execution['anchor_bundle_sha256']):
        raise InputBoundaryError('original anchor bundle differs from predeclared digest')
    bundle = decode_json(raw)
    exact_fields(bundle, {'format', 'split', 'baseline_receipt_sha256', 'query_manifest_sha256',
                          'index_manifest_sha256', 'encoder_manifest_sha256', 'depth', 'rows'})
    if (bundle['format'] != 'sacr-original-anchor-v1' or bundle['split'] != 'dev' or
            type(bundle['depth']) is not int or bundle['depth'] != execution['limits']['depth']):
        raise InputBoundaryError('invalid original anchor protocol')
    for key in ('query_manifest', 'index_manifest', 'encoder_manifest'):
        if bundle[key + '_sha256'] != execution['identities'][key]:
            raise InputBoundaryError('original anchor input identities disagree')
    sha = bundle['baseline_receipt_sha256']
    if type(sha) is not str or len(sha) != 64 or any(c not in '0123456789abcdef' for c in sha):
        raise InputBoundaryError('original baseline receipt digest required')
    if type(bundle['rows']) is not list or len(bundle['rows']) != len(execution['sources']):
        raise InputBoundaryError('original anchor cohort mismatch')
    for row, source in zip(bundle['rows'], execution['sources'], strict=True):
        exact_fields(row, {'query_id', 'source_sha256', 'mask_sha256', 'ranking'})
        if any(row[k] != source[k] for k in ('query_id', 'source_sha256')):
            raise InputBoundaryError('original anchor query/source order mismatch')
        mask = row['mask_sha256']
        if type(mask) is not str or len(mask) != 64 or any(c not in '0123456789abcdef' for c in mask):
            raise InputBoundaryError('original anchor mask digest required')
        finalize_query(query_id=row['query_id'], state='PROFILE_EMPTY', anchor=row['ranking'])
        if len(row['ranking']) > bundle['depth'] or (source['source_sha256'] is None and row['ranking']):
            raise InputBoundaryError('original anchor ranking exceeds declared availability/depth')
    return bundle
