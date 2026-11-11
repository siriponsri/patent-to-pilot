"""Prospective finite integer grammar; R4 prompt semantics remain unchanged.

LMFE 0.11.3 does not enforce numeric minimum/maximum. Enumerate finite integer
domains instead. Independent source/compiler checks remain mandatory: enumerated
endpoints do not establish start < end, ordering, uniqueness or fidelity.
"""
from copy import deepcopy
import json
from jsonschema import Draft202012Validator
from .mtm_runtime import InputBoundaryError
from .sacr_evidence_prompt_v4 import proposal_schema as r4_schema, build_messages as r4_messages

VERSION = 'sacr-context-finite-integers-v5'


def finite_integer_schema(schema):
    result = deepcopy(schema)
    def visit(node):
        if isinstance(node, list):
            for value in node: visit(value)
        elif isinstance(node, dict):
            if node.get('type') == 'integer' and 'enum' not in node:
                low, high = node.get('minimum'), node.get('maximum')
                if type(low) is not int or type(high) is not int or not 0 <= low <= high <= 8192:
                    raise InputBoundaryError('finite integer grammar domain unavailable or excessive')
                node['enum'] = list(range(low, high + 1))
                del node['minimum'], node['maximum']
            for value in node.values(): visit(value)
    visit(result)
    return result


def proposal_schema(source, query_id):
    return finite_integer_schema(r4_schema(source, query_id))


def build_messages(source, query_id):
    messages = r4_messages(source, query_id)
    payload = json.loads(messages[1]['content'])
    payload['configuration'] = VERSION
    messages[1]['content'] = json.dumps(payload, ensure_ascii=False, separators=(',', ':'))
    return messages


def validate_proposal(proposal, source, query_id):
    from .sacr_evidence_v3 import compile_evidence
    try:
        Draft202012Validator(proposal_schema(source, query_id)).validate(proposal)
    except Exception as error:
        if isinstance(error, InputBoundaryError): raise
        raise InputBoundaryError('R5 finite context schema rejected proposal') from error
    return compile_evidence(proposal, source=source, query_id=query_id)
