import pytest
from jsonschema import Draft202012Validator
from patent_to_pilot.research.r6_qualification import matrix,validate_contract


@pytest.mark.parametrize('kind',['profile','critic'])
def test_declared_schema_and_contract_expectations_match_separate_layers(kind):
    import json
    cases=matrix(kind)
    assert len({c['name'] for c in cases})==len(cases)
    for case in cases:
        try:valid=Draft202012Validator(case['prepared']['schema']).is_valid(json.loads(case['text']))
        except json.JSONDecodeError:valid=False
        assert valid==case['expected_schema'],case['name']
        try:validate_contract(case);valid=True
        except Exception:valid=False
        assert valid==case['expected_contract'],case['name']
    assert any(c['expected_schema'] and not c['expected_contract'] for c in cases)
