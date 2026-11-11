from copy import deepcopy
import pytest
from jsonschema import Draft202012Validator
from patent_to_pilot.research.sacr_evidence_prompt_v5 import proposal_schema, validate_proposal, finite_integer_schema
from patent_to_pilot.research.mtm_runtime import InputBoundaryError
from test_sacr_evidence_prompt_v4 import SOURCE, proposal, ref


def test_all_integer_leaves_are_finite_enums_including_conditions():
    schema = proposal_schema(SOURCE, 'q')
    count = 0
    def walk(node):
        nonlocal count
        if isinstance(node, dict):
            if node.get('type') == 'integer':
                count += 1
                assert 'enum' in node and 'minimum' not in node and 'maximum' not in node
            for value in node.values(): walk(value)
        elif isinstance(node, list):
            for value in node: walk(value)
    walk(schema)
    assert count > 20


@pytest.mark.parametrize('outside', [True, False])
def test_outside_selected_branch_fails_even_with_roles_first(outside):
    p = proposal()
    p['blocks'][0]['roles']['quantity'] = [ref(8, 9)]
    if not outside: p['blocks'][0]['evidence'] = [ref(0, 12)]
    p['blocks'][0] = dict(reversed(list(p['blocks'][0].items())))
    assert Draft202012Validator(proposal_schema(SOURCE, 'q')).is_valid(p) is (not outside)
    if not outside:
        assert validate_proposal(p, SOURCE, 'q')['automatic_fidelity_pass'] is False


def test_schema_does_not_replace_source_compiler():
    p = proposal(); p['blocks'][0]['roles'] = {'action': [ref(3, 2)]}
    assert Draft202012Validator(proposal_schema(SOURCE, 'q')).is_valid(p)
    with pytest.raises(InputBoundaryError): validate_proposal(p, SOURCE, 'q')


@pytest.mark.parametrize('schema', [{'type': 'integer'}, {'type': 'integer', 'minimum': 0, 'maximum': 1000000}])
def test_unbounded_or_excessive_domains_stop_before_generation(schema):
    with pytest.raises(InputBoundaryError): finite_integer_schema(schema)


def test_conversion_does_not_mutate_input():
    schema = {'type': 'integer', 'minimum': 2, 'maximum': 4}
    old = deepcopy(schema)
    assert finite_integer_schema(schema)['enum'] == [2, 3, 4]
    assert schema == old
