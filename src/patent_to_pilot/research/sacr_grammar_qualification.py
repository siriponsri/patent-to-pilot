"""Authored matrix shared by character and future tokenizer qualification.

No data/model inputs, no retrieval scores, no claim of exhaustive language proof.
"""
from copy import deepcopy
import hashlib
import json
from .sacr_evidence_prompt_v4 import contexts, proposal_schema as r4_schema
from .sacr_evidence_prompt_v5 import proposal_schema as r5_schema

SOURCE = 'A valve stops reverse flow. It operates below 40 C without power.'
QUERY = 'grammar-fixture'


def ref(start, end):
    return {'field': 'allowed_query', 'start_token': start, 'end_token': end}


def fixture_matrix():
    base = {'version': 'sacr-evidence-roles-v3', 'query_id': QUERY,
            'source_sha256': hashlib.sha256(SOURCE.encode()).hexdigest(),
            'blocks': [{'id': 'b1', 'evidence': [ref(0, 5)],
                        'roles': {'action': [ref(2, 3)]}, 'conditions': [], 'abstraction': None}]}
    cases = []
    def add(name, value, expected, layer='schema'):
        cases.append({'name': name, 'text': json.dumps(value, ensure_ascii=False),
                      'expected': expected, 'layer': layer})
    for i, context in enumerate(contexts(SOURCE)):
        p = deepcopy(base); s, e = context['start_token'], context['end_token']
        p['blocks'][0]['evidence'] = [ref(s, e)]
        p['blocks'][0]['roles'] = {'action': [ref(s, e)], 'unit': [ref(e-1, e)]}
        p['blocks'][0]['conditions'] = [{'id': 'c1', 'kind': 'numeric', 'attachment': 'explicit',
            'evidence': [ref(8, 10)], 'attachment_evidence': [ref(5, 12)]}]
        p['blocks'][0]['abstraction'] = 'A "quoted" mechanism \\ path ไทย 🧪.'
        add(f'context-{i}-populated', p, True)
        p['blocks'][0] = dict(reversed(list(p['blocks'][0].items())))
        add(f'context-{i}-reversed-fields', p, True)
    p = deepcopy(base); p['blocks'] = []; add('abstention', p, True)
    for name, mutate in [
        ('role-outside-context', lambda b: b['roles'].update(quantity=[ref(8, 9)])),
        ('role-upper-bound', lambda b: b['roles'].update(action=[ref(2, 6)])),
        ('role-negative', lambda b: b['roles'].update(action=[ref(-1, 3)])),
        ('role-fraction', lambda b: b['roles'].update(action=[ref(2.5, 3)])),
        ('evidence-empty', lambda b: b.update(evidence=[])),
        ('evidence-multiple', lambda b: b.update(evidence=[ref(0, 5), ref(5, 12)])),
        ('evidence-unlisted', lambda b: b.update(evidence=[ref(1, 5)])),
        ('unknown-field', lambda b: b.update(unexpected=True)),
        ('missing-field', lambda b: b.pop('conditions')),
        ('unknown-role', lambda b: b['roles'].update(invented=[ref(1, 2)])),
        ('condition-outside-source', lambda b: b.update(conditions=[{'id': 'c', 'kind': 'numeric',
            'attachment': 'explicit', 'evidence': [ref(100, 101)], 'attachment_evidence': [ref(0, 5)]}])),
    ]:
        p = deepcopy(base); mutate(p['blocks'][0]); add(name, p, False)
        p['blocks'][0] = dict(reversed(list(p['blocks'][0].items())))
        add(name+'-reversed-fields', p, False)
    for name, mutate in [
        ('reversed-span', lambda b: b['roles'].update(action=[ref(3, 2)])),
        ('zero-width-span', lambda b: b['roles'].update(action=[ref(2, 2)])),
    ]:
        p = deepcopy(base); mutate(p['blocks'][0]); add(name, p, True, 'compiler-must-reject')
    p = deepcopy(base); p['blocks'].append(deepcopy(p['blocks'][0]))
    add('duplicate-block-id', p, True, 'compiler-must-reject')
    p = deepcopy(base); p['blocks'] *= 9; add('too-many-blocks', p, False)
    return {'format': 'sacr-grammar-matrix-v1', 'source': SOURCE, 'query_id': QUERY,
            'schemas': {'r4': r4_schema(SOURCE, QUERY), 'r5': r5_schema(SOURCE, QUERY)}, 'cases': cases}
