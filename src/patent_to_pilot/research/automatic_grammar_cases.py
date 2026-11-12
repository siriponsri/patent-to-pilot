"""Authored grammar fixtures only; not independent semantic calibration gold."""
from copy import deepcopy
import json
from .patent_structure_marking import prepare, sha, VERSION
from .km_automatic_review import prepare_review, CHECKS


SOURCE = 'The pump reduces pressure below 5 kPa except during cleaning.'


def cases(km_text):
    request = prepare(SOURCE, 'synthetic-auto-001', km_text, sha(km_text))
    base = {'version': VERSION, 'query_id': 'synthetic-auto-001', 'source_sha256': sha(SOURCE),
            'labels': ['none', 'none', 'action', 'operand', 'condition', 'condition', 'condition',
                       'exception', 'exception', 'exception'], 'uncertain_roles': [],
            'abstraction': SOURCE}
    abstain = dict(base, labels=['none'] * len(base['labels']), abstraction=None)
    invalid = dict(base, query_id='WRONG-ID')
    too_short = dict(base, labels=base['labels'][:-1])
    too_long = dict(base, labels=base['labels'] + ['none'])
    rows = [('marking-valid', request, base, True), ('marking-abstain', request, abstain, True),
            ('marking-wrong-identity', request, invalid, False),
            ('marking-labels-too-short', request, too_short, False),
            ('marking-labels-too-long', request, too_long, False)]
    review = prepare_review(item_id='synthetic-auto-001', source=SOURCE, candidate=SOURCE,
                            track='SACR', km_text=km_text, km_sha256=sha(km_text))
    output = {'binding_sha256': review['binding_sha256'], 'checks': {k: {
        'status': 'screened', 'source_quote': '', 'candidate_quote': '', 'reason': 'No issue detected.'} for k in CHECKS}}
    flagged = deepcopy(output)
    flagged['checks']['conditions_exceptions'].update(status='uncertain', source_quote=SOURCE,
                                                     reason='Attachment requires interpretation.')
    missing = deepcopy(output); del missing['checks']['roles_direction']
    paraphrased = deepcopy(output)
    paraphrased['checks']['conditions_exceptions'].update(status='flagged', source_quote='The pump reduces pressure.',
                                                       reason='Paraphrased quote must be impossible.')
    rows += [('review-valid', review, output, True), ('review-uncertain', review, flagged, True),
             ('review-missing-check', review, missing, False),
             ('review-paraphrased-quote', review, paraphrased, False)]
    out = [{'name': name, 'request': req, 'output': value, 'expected_grammar_acceptance': expected,
             'output_text': json.dumps(value,ensure_ascii=False,separators=(',', ':'))}
            for name,req,value,expected in rows]
    # Whitespace runaway (native v2 review): only rejected when the backend declares a small cap.
    runaway = dict(out[-4], name='review-whitespace-runaway', expected_grammar_acceptance=False)
    runaway['output_text'] = runaway['output_text'].replace(',', ',' + '\n' * 100, 1)
    # Key-order violation (native v3 review wrote binding_sha256 last): rejected under declared field order.
    valid = out[-4]['output']
    disorder = dict(out[-4], name='review-key-order-violation', expected_grammar_acceptance=False)
    disorder['output_text'] = json.dumps({'checks': valid['checks'], 'binding_sha256': valid['binding_sha256']},
                                         ensure_ascii=False, separators=(',', ':'))
    return out + [runaway, disorder]


def qualify(backend, km_text):
    results = []
    for row in cases(km_text):
        req = row['request']
        result = backend.qualify(row['name'], req['schema'], req['messages'], row['output_text'])
        results.append({'name': row['name'], 'expected': row['expected_grammar_acceptance'], **result})
    return {'status': 'PASS_GRAMMAR_ONLY' if all(r['accepted'] == r['expected'] for r in results) else 'FAIL_GRAMMAR',
            'results': results, 'model_calls': 0, 'semantic_certified': False}
