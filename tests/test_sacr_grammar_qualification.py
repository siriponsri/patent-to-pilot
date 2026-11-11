import json
import pytest
from jsonschema import Draft202012Validator
from patent_to_pilot.research.sacr_grammar_qualification import fixture_matrix
from patent_to_pilot.research.sacr_evidence_prompt_v5 import validate_proposal
from patent_to_pilot.research.mtm_runtime import InputBoundaryError


def test_matrix_labels_are_independently_bound_to_schema_and_compiler():
    matrix=fixture_matrix();validator=Draft202012Validator(matrix['schemas']['r5'])
    names=set()
    for case in matrix['cases']:
        assert case['name'] not in names;names.add(case['name'])
        proposal=json.loads(case['text'])
        assert validator.is_valid(proposal) is case['expected'],case['name']
        if case['layer']=='compiler-must-reject':
            with pytest.raises(InputBoundaryError):validate_proposal(proposal,matrix['source'],matrix['query_id'])
    assert len(names)==33
