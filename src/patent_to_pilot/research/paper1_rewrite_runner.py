"""Paper 1 FA/GR one-call rewrite per query (frozen protocol 2026-11-13). Controller owns admission and costs.

Outcomes: USE_REWRITE (validated text to encode) or ORIGINAL_QUERY_FALLBACK (input over cap, output limit,
schema/blank rejection, grammar refusal). Any other exception persists a HOLD marker and propagates; nothing is
retried here.

Grammar refusal (owner decision A, 2026-11-14; protocol section 3): the strict EOS guard raises
'premature grammar termination refused' inside the grammar callback when the decoder reaches an incomplete
JSON state where only EOS remains. The caller must prove this from the private backend diagnostics
(classify_grammar_refusal) and raise GrammarRefusal; the query then falls back (reason GRAMMAR_REFUSED).
The call counts as one consumed model call whose token counts are unknown.
"""
import hashlib
import json
import os
from pathlib import Path
from .mtm_runtime import InputBoundaryError, decode_json
from .paper1_rewrite_arms import prepare, validate_and_text, lexical_descriptives
from .sacr_generation import GenerationLimits
from .sacr_generation_receipt import bind_generation_record
from .r6_dispatch_journal import document_hash

USE, FALLBACK = 'USE_REWRITE', 'ORIGINAL_QUERY_FALLBACK'
REFUSAL_MESSAGE = 'premature grammar termination refused'


class GrammarRefusal(Exception):
    """A verified grammar refusal of one dispatched call (no normal backend return)."""
    def __init__(self, evidence):
        super().__init__(REFUSAL_MESSAGE)
        self.evidence = evidence


def classify_grammar_refusal(error, diagnostics_dir):
    """Return GrammarRefusal only when the exception AND the private diagnostics both show a callback refusal."""
    if not isinstance(error, InputBoundaryError) or str(error) != REFUSAL_MESSAGE:
        return None
    path = Path(diagnostics_dir) / 'failure-private.json'
    if not path.is_file():
        return None
    try:
        record = json.loads(path.read_bytes())
    except ValueError:
        return None
    prefix = record.get('last_generated_prefix') or {}
    if (record.get('stage') != 'grammar-callback' or record.get('message') != REFUSAL_MESSAGE
            or record.get('exception_type') != 'InputBoundaryError'
            or record.get('backend_invocations_observed') != 1 or record.get('backend_returns_observed') != 0
            or type(prefix.get('generated_tokens_seen')) is not int):
        return None
    return GrammarRefusal({'stage': 'grammar-callback', 'message_sha256': record.get('message_sha256'),
                           'generated_tokens_seen': prefix['generated_tokens_seen'],
                           'failure_private_sha256': hashlib.sha256(path.read_bytes()).hexdigest()})


def run_rewrite(*, destination, arm, query_id, source, invoke, admit, count_tokens, input_token_cap,
                limits=GenerationLimits()):
    """invoke('rewrite', request) -> (original_generation_bytes, metrics) after normal backend return."""
    limits.validate()
    if type(input_token_cap) is not int or not 1 <= input_token_cap <= limits.input_tokens:
        raise InputBoundaryError('declared input cap required')
    request = prepare(arm, source, query_id)
    out = Path(destination); out.mkdir(parents=True, exist_ok=False)
    events = []; active = None

    def save(name, value):
        with (out / name).open('x', encoding='utf-8') as handle:
            json.dump(value, handle, ensure_ascii=False, sort_keys=True)
            handle.write('\n'); handle.flush(); os.fsync(handle.fileno())

    def finish(action, reason, text=None):
        result = {'query_id': query_id, 'arm': arm, 'action': action, 'reason': reason, 'text': text,
                  'lexical_descriptives': lexical_descriptives(source, text) if text else None,
                  'events': events, 'retry': False, 'semantic_certified': False,
                  'cumulative_accounting': 'CONTROLLER_SETTLEMENT_REQUIRED'}
        save('result.json', result)
        return result

    save('input.json', {'query_id': query_id, 'arm': arm, 'source_sha256': request['payload']['source_sha256'],
                        'maximum_calls': 1, 'retry': False})
    try:
        frozen = document_hash(request)
        tokens = count_tokens(request['messages'])
        if document_hash(request) != frozen or type(tokens) is not int or tokens < 1:
            raise InputBoundaryError('invalid preflight or changed request')
        save('rewrite-request.json', request)
        if tokens > input_token_cap:
            save('rewrite-input-limit.json', {'input_tokens': tokens, 'input_token_cap': input_token_cap, 'model_calls': 0})
            return finish(FALLBACK, 'INPUT_LIMIT')
        admit('rewrite', frozen, limits)
        if document_hash(request) != frozen:
            raise InputBoundaryError('admission changed request')
        save('rewrite-dispatch.json', {'request_sha256': frozen, 'input_tokens': tokens, 'limits': limits.__dict__, 'retry': False})
        active = 'rewrite'
        raw, metrics = invoke('rewrite', request)
        with (out / 'rewrite-generation.json').open('xb') as handle:
            handle.write(raw); handle.flush(); os.fsync(handle.fileno())
        save('rewrite-metrics.json', metrics)
        if document_hash(request) != frozen:
            raise InputBoundaryError('backend changed request')
        record = bind_generation_record(raw, expected_sha256=hashlib.sha256(raw).hexdigest(), limits=limits, metrics=metrics)['record']
        if record['input_tokens'] != tokens:
            raise InputBoundaryError('actual input tokens differ from preflight')
        events.append({'stage': 'rewrite', 'metrics': metrics, 'generation_sha256': hashlib.sha256(raw).hexdigest()})
        save('rewrite-terminal.json', {'status': 'NORMAL_RETURN_BOUND', 'event': events[-1]})
        active = None
        if record['status'] != 'EOS_COMPLETE':
            return finish(FALLBACK, 'NORMAL_OUTPUT_LIMIT')
        try:
            text = validate_and_text(decode_json(record['text'].encode()), request)
        except (InputBoundaryError, UnicodeError):
            return finish(FALLBACK, 'REWRITE_REJECTED')
        return finish(USE, 'REWRITE_VALIDATED', text)
    except BaseException as error:
        if not (isinstance(error, GrammarRefusal) and active == 'rewrite'):
            save('failure.json', {'status': 'HOLD', 'exception_type': type(error).__name__,
                                  'unresolved_stage': active, 'events': events, 'retry': False})
            raise
        refusal = error
        events.append({'stage': 'rewrite', 'status': 'GRAMMAR_REFUSED', 'model_calls': 1,
                       'input_output_tokens': 'UNKNOWN', 'evidence': refusal.evidence})
        save('rewrite-grammar-refused.json', {'status': 'GRAMMAR_REFUSED', 'evidence': refusal.evidence,
                                              'model_calls': 1, 'retry': False})
        return finish(FALLBACK, 'GRAMMAR_REFUSED')
