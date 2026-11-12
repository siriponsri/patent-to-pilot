from jsonschema import Draft202012Validator
from patent_to_pilot.research.automatic_grammar_cases import cases
from patent_to_pilot.research.patent_structure_marking import validate_and_render
from patent_to_pilot.research.km_automatic_review import interpret_review


def test_authored_grammar_cases_match_independent_schema_validator():
    rows = cases('Preserve conditions and exceptions.')
    assert len(rows) == 6
    for row in rows:
        assert Draft202012Validator(row['request']['schema']).is_valid(row['output']) == row['expected_grammar_acceptance']
        if row['expected_grammar_acceptance']:
            if row['name'].startswith('marking'):
                result = validate_and_render(row['output'], row['request'])
                assert result['anchor'].endswith('except during cleaning.')
            else:
                assert interpret_review(row['output'], row['request'])['semantic_certified'] is False
