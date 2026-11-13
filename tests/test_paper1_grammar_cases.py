import json
from jsonschema import Draft202012Validator
from patent_to_pilot.research import paper1_grammar_cases as g

# Cases whose rejection is a JSON-text property (order, raw control char, whitespace), not a schema property.
TEXT_LEVEL = {'fa-key-order-violation', 'fa-raw-newline-in-string', 'fa-whitespace-runaway'}


def test_cases_consistent_with_schema_and_unique():
    rows = g.cases()
    assert len({r['name'] for r in rows}) == len(rows) == 13
    assert sum(r['expected_grammar_acceptance'] for r in rows) == 3
    for r in rows:
        if r['name'] in TEXT_LEVEL:
            continue
        valid = Draft202012Validator(r['request']['schema']).is_valid(json.loads(r['output_text']))
        assert valid == r['expected_grammar_acceptance'], r['name']


def test_text_level_cases_are_schema_valid_but_malformed_text():
    rows = {r['name']: r for r in g.cases()}
    order = json.loads(rows['fa-key-order-violation']['output_text'])
    assert list(order)[0] == 'function' and Draft202012Validator(rows['fa-key-order-violation']['request']['schema']).is_valid(order)
    assert '\n' * 100 in rows['fa-whitespace-runaway']['output_text']
    try:
        json.loads(rows['fa-raw-newline-in-string']['output_text']); raise AssertionError('raw newline must be invalid JSON')
    except json.JSONDecodeError:
        pass
