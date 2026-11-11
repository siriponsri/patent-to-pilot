import copy
import json

import pytest

from patent_to_pilot.research.mtm_runtime import InputBoundaryError
from patent_to_pilot.research.r6_critic_tasks import ALIAS_CRITERIA
from patent_to_pilot.research.sg_compact_transport import prepare, reconstruct, interpret, preflight


def example(source=None):
    source = source or ('α pressure  12 µm\n\t' * 90 + 'Do not apply without cooling.\n')
    return dict(query_id='authored-alias', source=source,
                artifacts={'left': source, 'right': source + ' separate condition'},
                criteria=dict(ALIAS_CRITERIA), scope={'branch': 'SG_ALIAS'})


def test_exact_unicode_whitespace_and_references():
    args = example()
    prepared = prepare(**args)
    assert reconstruct(prepared) == {k: args[k] for k in ('source', 'artifacts')}
    assert prepared['dispatch_authorized'] is False
    assert 'text_ref' in prepared['messages'][1]['content']
    original = prepared['original']
    assert len(prepared['messages'][1]['content']) < len(original['messages'][1]['content'])


@pytest.mark.parametrize('target', ['wire', 'hash', 'scope', 'schema'])
def test_tampering_rejected(target):
    prepared = copy.deepcopy(prepare(**example()))
    if target == 'wire': prepared['messages'][1]['content'] += ' '
    elif target == 'hash': prepared['messages_sha256'] = '0' * 64
    elif target == 'scope': prepared['original']['payload']['scope']['branch'] = 'changed'
    else: prepared['original']['schema']['additionalProperties'] = True
    with pytest.raises(InputBoundaryError): reconstruct(prepared)


def test_interpret_preserves_no_semantic_acceptance():
    prepared = prepare(**example())
    raw = json.dumps({'binding_sha256': prepared['original']['binding_sha256'],
                      'dimensions': {k: 'supported' for k in ALIAS_CRITERIA},
                      'findings': []})
    result = interpret(raw, prepared)
    assert result['method_screen'] == 'UNFLAGGED'
    assert result['semantic_pass'] is False
    assert result['retrieval_ready'] is False


def test_catalogue_ceiling_unchanged():
    with pytest.raises(InputBoundaryError, match='catalogue too large'):
        prepare(**example('word ' * (64 * 256 + 1)))


def manifest():
    return {'units': [dict(example('Short authored source.'),
                          query_id=f'fixed-{i}', unit_type='source' if i < 14 else 'alias')
                      for i in range(114)],
            'coverage': [{'status': 'ABSTENTION' if i < 86 else 'SCREENING_PENDING'}
                         for i in range(100)]}


@pytest.mark.parametrize('risks, expected', [(20, 'INPUT_ADMISSION_ONLY'), (21, 'STOP_INPUT_RISK_CAP')])
def test_fixed_denominator_and_risk_boundary(risks, expected):
    counts = iter([8193] * risks + [8192] * (114-risks))
    result = preflight(manifest(), count_tokens=lambda messages: next(counts))
    assert result['status'] == expected
    assert result['risk_units'] == risks
    assert result['source_abstentions'] == 86
    assert result['model_calls'] == 0
    assert result['historical_r6_reopened'] is False


def test_tokenizer_mutation_rejected():
    def mutate(messages):
        messages[1]['content'] = 'truncated'
        return 1
    with pytest.raises(InputBoundaryError, match='mutated'):
        preflight(manifest(), count_tokens=mutate)


def test_empty_and_cross_artifact_references():
    args = example('Source independent of artifact.')
    args['artifacts'] = {'a': '', 'b': 'Shared artifact text.', 'c': 'Shared artifact text.'}
    prepared = prepare(**args)
    assert reconstruct(prepared)['artifacts'] == args['artifacts']
    wire = json.loads(prepared['messages'][1]['content'])
    assert wire['artifact_units']['c'][0][1] == {'text_ref': 'a1:000'}


def test_flagged_finding_keeps_original_offsets_and_membership():
    prepared = prepare(**example())
    original = prepared['original']
    dimensions = {k: 'supported' for k in ALIAS_CRITERIA}
    dimensions['polarity_exceptions'] = 'unsupported'
    value = {'binding_sha256': original['binding_sha256'], 'dimensions': dimensions,
             'findings': [{'dimension': 'polarity_exceptions', 'artifact': 'right',
                           'source_units': ['s:001'], 'candidate_units': ['a1:001'],
                           'reason': 'Authored test finding.'}]}
    result = interpret(json.dumps(value), prepared)
    finding = result['findings'][0]
    assert finding['source_evidence'] == [original['payload']['source_units'][1]]
    assert finding['candidate_evidence'] == [original['payload']['artifact_units']['right'][1]]
    value['findings'][0]['candidate_units'] = ['a0:001']
    from jsonschema import ValidationError
    with pytest.raises(ValidationError): interpret(json.dumps(value), prepared)
