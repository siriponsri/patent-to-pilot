"""Replayable private view-stage evidence; lexical screening is not entailment."""
from patent_to_pilot.research.mtm_runtime import InputBoundaryError
from patent_to_pilot.research.sacr_components import digest
from patent_to_pilot.research.sacr_profile_result import profile_result
from patent_to_pilot.research.sacr_views import collect_screened_views, parse_view_response


def view_result(raw, *, kind, profile_output, maximum_bytes, maximum_views):
    if type(raw) is not bytes:
        raise InputBoundaryError('view adapter must return immutable response bytes')
    canonical = profile_result(profile_output['profile'], source=profile_output['source'],
                               query_id=profile_output['query_id'])
    if (canonical != profile_output or
            canonical['decision'] != 'PROFILE_STRUCTURALLY_PREPARED_FIDELITY_PENDING'):
        raise InputBoundaryError('view result requires structurally prepared profile')
    proposals = parse_view_response(raw, kind=kind, maximum_bytes=maximum_bytes)
    generated_count = len(proposals)
    if kind == 'selective':
        proposals.append(canonical['compact']['text'])
    protected = [c['raw_text'] for b in canonical['profile']['blocks'] for c in b['attached_conditions']
                 if c['relation_to_block'] == 'explicit']
    screened = collect_screened_views(canonical['source'], proposals, protected_phrases=protected,
                                       maximum_characters=maximum_bytes)
    if type(maximum_views) is not int or not 1 <= maximum_views <= 3 or len(screened['views']) > maximum_views:
        raise InputBoundaryError('screened views exceed declared count cap')
    review = any(r['status'] == 'REVIEW_REQUIRED' for r in screened['proposals'])
    try:
        response_text = raw.decode('utf-8')
    except UnicodeDecodeError:
        raise InputBoundaryError('response must be UTF-8') from None
    retained = sum(r['included'] for r in screened['proposals'][:generated_count])
    return {'format': 'sacr-view-stage-v2', 'query_id': canonical['query_id'], 'kind': kind,
            'profile_output_sha256': digest(canonical), 'response_utf8': response_text,
            'decision': 'REVIEW_REQUIRED' if review else 'VIEWS_SCREENED_FIDELITY_PENDING',
            'retained_generated_views': retained, 'no_generated_view_retained': retained == 0,
            'screened': screened, 'semantic_status': 'unknown'}
