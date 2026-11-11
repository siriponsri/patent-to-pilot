"""Strict local-critic receipt parsing; uncertainty escalates, never auto-PASS."""
import json
from .mtm_runtime import InputBoundaryError, decode_json, exact_fields
from .sacr_native_fidelity import digest

DIMENSIONS = ('roles_direction', 'quantities_units', 'polarity_exceptions',
              'condition_attachment', 'essential_coverage', 'abstraction_support', 'context_preservation')


def parse_critic(raw, *, query_id, source, artifacts):
    """Caller binds normal EOS/record costs first. Bad envelopes raise to flag.

    A fully supported result means merely unflagged by this critic. Human
    sentinel review and lexical/structural screening remain independent gates.
    """
    if (type(source) is not str or not source.strip() or type(artifacts) is not dict or
            not artifacts or any(type(k) is not str or type(v) is not str for k, v in artifacts.items())):
        raise InputBoundaryError('invalid critic source/artifact contract')
    value = decode_json(raw)
    try:
        json.dumps(value, ensure_ascii=False).encode('utf-8')
    except UnicodeError:
        raise InputBoundaryError('invalid Unicode scalar in critic; no repair') from None
    exact_fields(value, {'query_id', 'source_sha256', 'dimensions', 'findings'})
    if value['query_id'] != query_id or value['source_sha256'] != digest(source.encode()):
        raise InputBoundaryError('critic identity mismatch')
    dimensions = value['dimensions']
    exact_fields(dimensions, set(DIMENSIONS))
    if any(v not in ('supported', 'unsupported', 'uncertain') for v in dimensions.values()):
        raise InputBoundaryError('invalid critic dimension status')
    findings = value['findings']
    if type(findings) is not list:
        raise InputBoundaryError('invalid critic findings')
    flagged = {d for d, status in dimensions.items() if status != 'supported'}
    covered = set()
    for finding in findings:
        exact_fields(finding, {'dimension', 'artifact', 'source_quote', 'candidate_quote', 'reason'})
        if (any(type(v) is not str for v in finding.values()) or
                finding['dimension'] not in flagged or finding['artifact'] not in artifacts or
                not finding['reason'].strip() or finding['source_quote'] not in source or
                finding['candidate_quote'] not in artifacts[finding['artifact']]):
            raise InputBoundaryError('critic finding is unsupported or inconsistent')
        covered.add(finding['dimension'])
    if covered != flagged:
        raise InputBoundaryError('critic omitted findings for flagged dimensions')
    return {'status': 'ESCALATE' if flagged else 'CRITIC_UNFLAGGED_NOT_FIDELITY_PASS',
            'dimensions': dimensions, 'findings': findings, 'semantic_pass': False}
