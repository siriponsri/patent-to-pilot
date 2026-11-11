"""Prospective R6 source-context guard and condition renderer; never repair R5.

Complete profile context coverage is deliberately conservative. It can make the
compact control identical to the source anchor; no independent benefit is claimed.
Role/attachment and selective-view fidelity still require a calibrated critic.
"""
import json
from jsonschema import Draft202012Validator
from .mtm_runtime import InputBoundaryError
from .sacr_r6_prompt import build_messages as previous_messages, proposal_schema as full_schema, contexts
from .sacr_evidence_v3 import compile_evidence
from .sacr_token_profile import source_catalogue
from .sacr_views_v3 import render_views as old_views, _union

VERSION = 'sacr-r6-complete-context-guard'
CRITERIA = {
    'roles_direction': 'Check asserted roles, action/operand and direction against source evidence, not just literal overlap.',
    'quantities_units': 'Retain every source quantity/unit pairing in the proposed view; flag changed or missing constraints.',
    'polarity_exceptions': 'Preserve negation, exceptions and their scope.',
    'condition_attachment': 'Check conditions attach to the same action/operand as in the source. Wider context does not prove attachment.',
    'essential_coverage': 'Identify essential functions/constraints omitted from the actual selective view. Full profile context alone does not satisfy this criterion.',
    'abstraction_support': 'Abstraction may generalize application context only while retaining the supported mechanism and constraints.',
    'context_preservation': 'Do not convert background, examples or unclaimed capabilities into invention assertions.'}


def context_coverage(proposal, source):
    tokens = source_catalogue(source)['tokens']
    covered = set()
    for block in proposal['blocks']:
        for ref in block['evidence']:
            covered.update(range(ref['start_token'], ref['end_token']))
    missing = sorted(set(range(len(tokens))) - covered)
    return {'source_tokens': len(tokens), 'covered_source_tokens': len(set(range(len(tokens))) & covered),
            'uncovered_token_ids': missing, 'complete_context': not missing, 'semantic_pass': False}


def proposal_schema(source, query_id):
    return full_schema(source, query_id)


def validate_proposal(proposal, source, query_id):
    compiled = compile_evidence(proposal, source=source, query_id=query_id)
    coverage = context_coverage(proposal, source)
    if proposal['blocks'] and not coverage['complete_context']:
        raise InputBoundaryError('R6 profile context coverage gap')
    try:Draft202012Validator(proposal_schema(source,query_id)).validate(proposal)
    except Exception as error:
        if isinstance(error,InputBoundaryError):raise
        raise InputBoundaryError('R6 full-context schema rejected proposal') from error
    return {'compiled': compiled, 'coverage': coverage, 'semantic_pass': False}


def build_messages(source, query_id):
    messages = previous_messages(source, query_id)
    messages[0]['content'] += (' Across all nonempty blocks the evidence contexts MUST cover every source token. '
        'Context inclusion does not assert that background text is an invention function. Do not invent roles for background text. '
        'Use the full-source context if needed; empty blocks remain abstention. The selective view still requires complete semantic fidelity.')
    payload = json.loads(messages[1]['content']); payload['configuration'] = VERSION
    payload['context_choices']=[{'start_token':0,'end_token':len(source_catalogue(source)['tokens'])}]
    messages[1]['content'] = json.dumps(payload, ensure_ascii=False, separators=(',', ':'))
    return messages


def render_views(proposal, *, source, query_id):
    checked = validate_proposal(proposal, source, query_id)
    result = old_views(proposal, source=source, query_id=query_id)
    if not proposal['blocks']:
        return {**result, 'coverage': checked['coverage']}
    tokens = source_catalogue(source)['tokens']; choices = contexts(source)
    intervals = []; abstractions = []
    for block, compiled in zip(proposal['blocks'], checked['compiled']['blocks']):
        if block['abstraction'] is not None:
            abstractions.append(block['abstraction'])
        else:
            intervals.extend((x['start'], x['end']) for x in compiled['literal_evidence'])
        for condition in block['conditions']:
            refs = condition['evidence'] + condition['attachment_evidence']
            lo = min(x['start_token'] for x in refs); hi = max(x['end_token'] for x in refs)
            eligible = [c for c in choices if c['start_token'] <= lo and c['end_token'] >= hi]
            chosen = min(eligible, key=lambda c: (c['end_token']-c['start_token'], c['start_token']))
            intervals.append((tokens[chosen['start_token']]['start'], tokens[chosen['end_token']-1]['end']))
    merged = _union(intervals)
    return {**result, 'selective': '\n'.join(abstractions + [source[a:b] for a,b in merged]),
            'selective_source_intervals': merged, 'coverage': checked['coverage'],
            'condition_context_policy': 'complete enclosing declared context; attachment remains unverified',
            'compact_equals_anchor': result['compact'] == source,
            'retrieval_ready': False}


def review_request(proposal, *, source, query_id, generic_views=None):
    from .reference_critic_v1 import prepare
    checked = validate_proposal(proposal, source, query_id)
    views = render_views(proposal, source=source, query_id=query_id)
    if not proposal['blocks']:
        raise InputBoundaryError('abstention is not a critic-ready candidate')
    artifacts = {'evidence_and_roles': json.dumps(checked['compiled']['blocks'], ensure_ascii=False, sort_keys=True),
                 'source_anchor': source, 'compact': views['compact'], 'selective': views['selective']}
    if generic_views is not None:
        if not isinstance(generic_views, list) or not 1 <= len(generic_views) <= 2 or any(not isinstance(v, str) or not v.strip() for v in generic_views):
            raise InputBoundaryError('invalid generic controls')
        artifacts.update({f'generic_{i}': value for i,value in enumerate(generic_views)})
    return prepare(query_id=query_id, source=source, artifacts=artifacts, criteria=CRITERIA,
                   scope={'branch':'SACR','version':VERSION,'semantic_acceptance':'human gate required'})
