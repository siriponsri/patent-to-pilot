"""Canonical private profile-stage output; includes allowed source for replay."""
from copy import deepcopy

from patent_to_pilot.research.sacr_components import compile_components
from patent_to_pilot.research.sacr_views import compact_view


def profile_result(profile, *, source, query_id, input_kind='MTM_P'):
    profile = deepcopy(profile)
    components = compile_components(profile, source=source, query_id=query_id, input_kind=input_kind)
    compact = compact_view(profile, source=source, query_id=query_id, input_kind=input_kind)
    if components['status'] == 'ANCHOR_FALLBACK':
        decision = ('PROFILE_FAILED_FALLBACK_REQUIRED' if profile['extraction_status'] == 'failed'
                    else 'PROFILE_EMPTY_FALLBACK_REQUIRED')
    elif components['status'] == 'REVIEW_REQUIRED' or compact['status'] == 'REVIEW_REQUIRED':
        decision = 'REVIEW_REQUIRED'
    else:
        decision = 'PROFILE_STRUCTURALLY_PREPARED_FIDELITY_PENDING'
    return {'format': 'sacr-profile-stage-v1', 'query_id': query_id, 'source': source,
            'decision': decision, 'profile': profile, 'components': components,
            'compact': compact, 'semantic_status': 'unknown'}
