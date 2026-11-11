"""Prospective grammar v1; source alignment and semantic review remain mandatory."""
import hashlib

from patent_to_pilot.research.mtm_runtime import InputBoundaryError, identifier


def quote_profile_schema(*, source: str, query_id: str, input_kind: str) -> dict:
    """Inline JSON Schema, with identity bound to the allowed input only.

    Cross-field consistency, unique IDs, source order, exact quotation matches and
    semantic correctness are deliberately left to post-generation validation.
    Optional nullable fields mirror the existing structural validator.
    """
    identifier(query_id)
    if type(source) is not str or not source.strip() or input_kind not in ('MTM_P', 'DAPFAM_TA'):
        raise InputBoundaryError('invalid schema input identity')

    def text():
        return {'type': 'string', 'minLength': 1}

    def enum(values):
        return {'type': 'string', 'enum': values}

    def nullable():
        return {'anyOf': [text(), {'type': 'null'}]}

    def obj(required, optional=None):
        return {'type': 'object', 'properties': {**required, **(optional or {})},
                'required': list(required), 'additionalProperties': False}

    def array(items, minimum=0, maximum=None):
        result = {'type': 'array', 'items': items, 'minItems': minimum}
        if maximum is not None:
            result['maxItems'] = maximum
        return result

    def spans(minimum=1):
        return array(obj({'field': enum(['allowed_query']), 'text': text()}), minimum)

    condition = obj({
        'condition_id': text(), 'raw_text': text(), 'normalized_text': text(),
        'kind': enum(['numeric', 'qualitative', 'polarity', 'direction', 'material', 'other']),
        'relation_to_block': enum(['explicit', 'uncertain']), 'source_spans': spans(),
    }, {'numeric_value': nullable(), 'unit': nullable()})
    block = obj({'block_id': text(), 'relation_text': text(), 'source_spans': spans(),
                 'attached_conditions': array(condition, maximum=8)},
                {role: nullable() for role in ('action', 'operand', 'effect')})
    context = obj({'raw_text': text(), 'action': enum(['retain', 'proposed_abstraction', 'unresolved']),
                   'reason': text(), 'source_spans': spans()}, {'replacement': nullable()})
    unknown = obj({'description': text(),
                   'reason': enum(['ambiguity', 'insufficient_text', 'unsupported_normalization', 'other'])},
                  {'source_spans': spans(0)})
    return obj({
        'profile_version': enum(['sacr-profile-quotes-v1']), 'query_id': enum([query_id]),
        'source_sha256': enum([hashlib.sha256(source.encode('utf-8')).hexdigest()]),
        'input_kind': enum([input_kind]), 'blocks': array(block, maximum=8),
        'context_items': array(context), 'unknowns': array(unknown),
        'extraction_status': enum(['valid', 'partial', 'failed']), 'failure_reasons': array(text()),
    })


def token_profile_schema(*, source: str, query_id: str, input_kind: str) -> dict:
    """Source-bound grammar for the explicit R2 token-reference contract.

    Range ordering and semantic checks remain mandatory after generation.
    Every call constructs an independent schema; legacy grammar is unchanged.
    """
    from .sacr_token_profile import source_catalogue, VERSION
    schema = quote_profile_schema(source=source, query_id=query_id, input_kind=input_kind)
    count = len(source_catalogue(source)['tokens'])
    schema['properties']['profile_version']['enum'] = [VERSION]

    def walk(node):
        if type(node) is dict:
            props = node.get('properties', {})
            if 'source_spans' in props:
                props['source_spans']['items'] = {
                    'type': 'object', 'additionalProperties': False,
                    'required': ['field', 'start_token', 'end_token'],
                    'properties': {
                        'field': {'type': 'string', 'enum': ['allowed_query']},
                        'start_token': {'type': 'integer', 'minimum': 0, 'maximum': count-1},
                        'end_token': {'type': 'integer', 'minimum': 1, 'maximum': count},
                    }}
            for value in node.values():
                walk(value)
        elif type(node) is list:
            for value in node:
                walk(value)

    walk(schema)
    return schema
