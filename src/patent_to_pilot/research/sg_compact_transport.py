"""Prospective lossless Graph wire candidate; no dispatch or gate reopening.

Keep the original critic catalogue, schema, criteria and binding. Only repeated
offset keys and identical text are compressed. Qualification remains required.
"""
import hashlib
import json

from .mtm_runtime import InputBoundaryError
from .reference_critic_v1 import prepare as reference_prepare, interpret as reference_interpret

VERSION = 'sg-compact-transport-v2'


def prepare(**kwargs):
    original = reference_prepare(**kwargs)
    payload = original['payload']
    seen = {}

    def pack(units):
        packed = []
        for unit in units:
            text = unit['text']
            if text in seen:
                packed.append([unit['id'], {'text_ref': seen[text]}])
            else:
                packed.append([unit['id'], text])
                seen[text] = unit['id']
        return packed

    wire = {k: v for k, v in payload.items()
            if k not in ('source_units', 'artifact_units')}
    wire['source_units'] = pack(payload['source_units'])
    wire['artifact_units'] = {name: pack(units)
                              for name, units in payload['artifact_units'].items()}
    wire.update(binding_sha256=original['binding_sha256'], output_schema=original['schema'])
    instruction = original['messages'][0]['content'] + (
        ' Compact catalogue format: each entry is [unit ID, exact text] or '
        '[unit ID, {"text_ref": earlier unit ID}]. Resolve text_ref verbatim. '
        'Concatenate entries in order to recover the complete source or artifact; '
        'no text was removed. Unit IDs and artifact membership remain distinct. '
        'Include findings ONLY for dimensions marked unsupported or uncertain; '
        'do not include findings for supported dimensions. Every unsupported or '
        'uncertain dimension must have at least one finding. If all dimensions '
        'are supported, findings must be an empty array. Every finding must '
        'include a nonblank reason and at least one source or candidate unit ID.')
    messages = [{'role': 'system', 'content': instruction},
                {'role': 'user', 'content': json.dumps(wire, ensure_ascii=False,
                                                     separators=(',', ':'))}]
    return {'version': VERSION, 'original': original, 'messages': messages,
            'messages_sha256': hashlib.sha256(json.dumps(
                messages, ensure_ascii=False, sort_keys=True).encode()).hexdigest(),
            'dispatch_authorized': False}


def reconstruct(prepared):
    """Return exact original source/artifacts; reject any wire or receipt change."""
    original = prepared['original']
    payload = original['payload']
    kwargs = dict(query_id=payload['query_id'],
                  source=''.join(u['text'] for u in payload['source_units']),
                  artifacts={name: ''.join(u['text'] for u in units)
                             for name, units in payload['artifact_units'].items()},
                  criteria=payload['criteria'], scope=payload['scope'])
    if prepared != prepare(**kwargs):
        raise InputBoundaryError('compact transport or original receipt changed')
    wire = json.loads(prepared['messages'][1]['content'])
    resolved = {}

    def unpack(units):
        texts = []
        for identity, value in units:
            text = value if isinstance(value, str) else resolved[value['text_ref']]
            resolved[identity] = text
            texts.append(text)
        return ''.join(texts)

    result = {'source': unpack(wire['source_units']),
              'artifacts': {name: unpack(units)
                            for name, units in wire['artifact_units'].items()}}
    if result != {key: kwargs[key] for key in result}:
        raise InputBoundaryError('compact transport failed exact reconstruction')
    return result


def interpret(raw, prepared):
    reconstruct(prepared)
    return reference_interpret(raw, prepared['original'])


def preflight(manifest, *, count_tokens):
    """Measure every fixed parent without truncation, dispatch or acceptance."""
    units = manifest['units']
    if (len(units) != 114 or len(manifest['coverage']) != 100
            or len({u['query_id'] for u in units}) != 114):
        raise InputBoundaryError('fixed Graph parent denominator changed')
    rows = []
    for unit in units:
        row = {'query_id': unit['query_id'], 'unit_type': unit['unit_type']}
        try:
            prepared = prepare(**{k: unit[k] for k in
                ('query_id', 'source', 'artifacts', 'criteria', 'scope')})
        except InputBoundaryError as error:
            if str(error) != 'catalogue too large; no truncation':
                raise
            row.update(status='CATALOGUE_LIMIT', input_tokens=None)
        else:
            reconstruct(prepared)
            before = json.dumps(prepared, ensure_ascii=False, sort_keys=True)
            count = count_tokens(prepared['messages'])
            if (type(count) is not int or count < 1
                    or json.dumps(prepared, ensure_ascii=False, sort_keys=True) != before):
                raise InputBoundaryError('tokenizer count invalid or request mutated')
            row.update(status='INPUT_LIMIT' if count > 8192 else 'ADMITTED',
                       input_tokens=count, messages_sha256=prepared['messages_sha256'])
        rows.append(row)
    risks = sum(row['status'] != 'ADMITTED' for row in rows)
    return {'version': VERSION, 'status': 'STOP_INPUT_RISK_CAP' if risks > 20
            else 'INPUT_ADMISSION_ONLY', 'units': rows, 'risk_units': risks,
            'screening_units': 114, 'source_coverage_units': 100,
            'source_abstentions': sum(r['status'] == 'ABSTENTION'
                                     for r in manifest['coverage']),
            'model_calls': 0, 'semantic_fidelity': 'NOT_ASSESSED',
            'dispatch_authorized': False, 'historical_r6_reopened': False}
