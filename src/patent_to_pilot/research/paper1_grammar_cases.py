"""Paper 1 S1: authored grammar cases for the frozen FA/GR schemas (grammar mechanics only, no model).

Each case replays an authored output through the real tokenizer + R6Backend callback and EOS guard.
Accepted means the grammar permits the token sequence; it says nothing about semantic quality.
"""
import json
from . import paper1_rewrite_arms as arms

SOURCE = 'A pump reduces line pressure below 5 kPa except during cleaning.'
QID = 'paper1-s1-001'


def _text(value):
    return json.dumps(value, ensure_ascii=False, separators=(',', ':'))


def cases():
    fa_req, gr_req = arms.prepare('FA', SOURCE, QID), arms.prepare('GR', SOURCE, QID)
    head = {'query_id': QID, 'source_sha256': arms.sha(SOURCE)}
    fa = {'version': arms.FA_VERSION, **head,
          'function': 'Lowers the pressure of a fluid in a conduit.',
          'mechanism': 'A pumping element draws fluid so that conduit pressure falls.',
          'problem': 'Keeps conduit pressure below a limit during normal operation.',
          'conditions': 'Pressure is kept below 5 kPa, except during cleaning.'}
    gr = {'version': arms.GR_VERSION, **head,
          'abstract': 'A pumping system keeps line pressure below 5 kPa during operation; a cleaning mode suspends the limit.'}
    rows = [
        ('fa-valid', fa_req, _text(fa), True),
        ('fa-escaped-quote-and-newline', fa_req, _text(dict(fa, problem='Avoids a "pressure spike"\nin the conduit.')), True),
        ('fa-field-too-long', fa_req, _text(dict(fa, mechanism='x' * (arms.FA_FIELD_MAX + 1))), False),
        ('fa-blank-field', fa_req, _text(dict(fa, conditions='')), False),
        ('fa-wrong-query-id', fa_req, _text(dict(fa, query_id='WRONG-ID')), False),
        ('fa-extra-field', fa_req, _text(dict(fa, note='x')), False),
        ('fa-key-order-violation', fa_req, _text({k: fa[k] for k in ['function'] + [k for k in fa if k != 'function']}), False),
        ('fa-raw-newline-in-string', fa_req, _text(fa).replace('Lowers the', 'Lowers' + chr(10) + 'the', 1), False),
        ('fa-whitespace-runaway', fa_req, _text(fa).replace(',', ',' + '\n' * 100, 1), False),
        ('gr-valid', gr_req, _text(gr), True),
        ('gr-too-long', gr_req, _text(dict(gr, abstract='y' * (arms.GR_MAX + 1))), False),
        ('gr-wrong-version', gr_req, _text(dict(gr, version=arms.FA_VERSION)), False),
        ('gr-blank', gr_req, _text(dict(gr, abstract='')), False),
    ]
    return [{'name': n, 'request': r, 'output_text': t, 'expected_grammar_acceptance': e} for n, r, t, e in rows]


def qualify(backend):
    results = []
    for row in cases():
        req = row['request']
        result = backend.qualify(row['name'], req['schema'], req['messages'], row['output_text'])
        results.append({'name': row['name'], 'expected': row['expected_grammar_acceptance'], **result})
    return {'status': 'PASS_GRAMMAR_ONLY' if all(r['accepted'] == r['expected'] for r in results) else 'FAIL_GRAMMAR',
            'case_set': 'paper1-rewrite', 'results': results, 'model_calls': 0, 'semantic_certified': False}
