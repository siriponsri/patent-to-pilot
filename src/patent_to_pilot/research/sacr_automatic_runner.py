"""Two-call prospective SACR pipeline. Controller owns live admission and costs.

Grammar refusal (owner decision A extended to SACR, 2026-11-15; protocol section 3): when the caller proves from the
private backend diagnostics that a marking or review call was refused by the strict EOS guard (classify_grammar_refusal
raises GrammarRefusal), the query falls back to the original query (reason GRAMMAR_REFUSED; one consumed call with
unknown tokens). Every other exception still persists a HOLD marker and propagates.

Grammar dead end (owner decision 2026-11-15, 'A: ขยายกติกา'): 'grammar has no continuation' raised by the EOS guard in
the grammar callback (no allowed next token), verified the same way (classify_sacr_grammar_failure), falls back with
reason GRAMMAR_NO_CONTINUATION (reported separately from GRAMMAR_REFUSED).
"""
import hashlib
import json
import os
from pathlib import Path
from .mtm_runtime import InputBoundaryError, decode_json
from .patent_structure_marking import prepare, validate_and_render
from .km_automatic_review import prepare_review, interpret_review
from .automatic_screening import route_result
from .sacr_generation import GenerationLimits
from .sacr_generation_receipt import bind_generation_record
from .r6_dispatch_journal import document_hash
from .paper1_rewrite_runner import GrammarRefusal, classify_grammar_refusal

NO_CONTINUATION = 'grammar has no continuation'


def classify_sacr_grammar_failure(error, diagnostics_dir):
    """GrammarRefusal for a verified EOS-guard refusal OR a verified grammar dead end; otherwise None."""
    refusal = classify_grammar_refusal(error, diagnostics_dir)
    if refusal is not None:
        refusal.evidence['kind'] = 'REFUSED'
        return refusal
    if not isinstance(error, InputBoundaryError) or str(error) != NO_CONTINUATION:
        return None
    path = Path(diagnostics_dir) / 'failure-private.json'
    if not path.is_file():
        return None
    try:
        record = json.loads(path.read_bytes())
    except ValueError:
        return None
    prefix = record.get('last_generated_prefix') or {}
    if (record.get('stage') != 'grammar-callback' or record.get('message') != NO_CONTINUATION
            or record.get('exception_type') != 'InputBoundaryError'
            or record.get('backend_invocations_observed') != 1 or record.get('backend_returns_observed') != 0
            or type(prefix.get('generated_tokens_seen')) is not int):
        return None
    return GrammarRefusal({'stage': 'grammar-callback', 'kind': 'NO_CONTINUATION', 'message_sha256': record.get('message_sha256'),
                           'generated_tokens_seen': prefix['generated_tokens_seen'],
                           'failure_private_sha256': hashlib.sha256(path.read_bytes()).hexdigest()})


def run_query(*, destination, query_id, source, km_text, km_sha256,
              invoke, admit, count_tokens, limits=GenerationLimits()):
    """invoke(stage,request) returns (original_generation_bytes, metrics).

    External adapter MUST persist its actual backend reservation and return only
    after normal terminal completion. Exceptions leave an unresolved marker.
    This function does not grant GPU authority or settle the cumulative ledger.
    """
    limits.validate()
    request = prepare(source, query_id, km_text, km_sha256)
    out = Path(destination); out.mkdir(parents=True, exist_ok=False)
    events = []; active = None; candidate = None

    def save(name, value):
        with (out / name).open('x', encoding='utf-8') as handle:
            json.dump(value, handle, ensure_ascii=False, sort_keys=True)
            handle.write('\n'); handle.flush(); os.fsync(handle.fileno())

    save('input.json', {'query_id': query_id, 'source_sha256': request['payload']['source_sha256'],
                        'km_sha256': km_sha256, 'maximum_calls': 2, 'retry': False})

    def call(stage, req):
        nonlocal active
        frozen = document_hash(req)
        tokens = count_tokens(req['messages'])
        if document_hash(req) != frozen or type(tokens) is not int or tokens < 1:
            raise InputBoundaryError('invalid preflight or changed request')
        save(stage + '-request.json', req)
        if tokens > limits.input_tokens:
            save(stage + '-input-limit.json', {'input_tokens': tokens, 'model_calls': 0})
            return None
        admit(stage, frozen, limits)
        if document_hash(req) != frozen:
            raise InputBoundaryError('admission changed request')
        save(stage + '-dispatch.json', {'request_sha256': frozen, 'input_tokens': tokens,
                                        'limits': limits.__dict__, 'retry': False})
        active = stage
        raw, metrics = invoke(stage, req)
        with (out / (stage + '-generation.json')).open('xb') as handle:
            handle.write(raw); handle.flush(); os.fsync(handle.fileno())
        save(stage + '-metrics.json', metrics)
        if document_hash(req) != frozen:
            raise InputBoundaryError('backend changed request')
        bound = bind_generation_record(raw, expected_sha256=hashlib.sha256(raw).hexdigest(),
                                       limits=limits, metrics=metrics)
        if bound['record']['input_tokens'] != tokens:
            raise InputBoundaryError('actual input tokens differ from preflight')
        events.append({'stage': stage, 'metrics': metrics, 'generation_sha256': hashlib.sha256(raw).hexdigest()})
        save(stage + '-terminal.json', {'status': 'NORMAL_RETURN_BOUND', 'event': events[-1]})
        active = None
        return bound['record']

    def finish(screening, reason, candidate=None):
        result = {'query_id': query_id, 'decision': route_result('SACR', 'completed', True, screening),
                  'reason': reason, 'candidate': candidate, 'events': events,
                  'retry': False, 'cumulative_accounting': 'CONTROLLER_SETTLEMENT_REQUIRED'}
        save('result.json', result)
        return result

    try:
        record = call('marking', request)
        if record is None or record['status'] != 'EOS_COMPLETE':
            return finish('invalid_output', 'MARKING_INPUT_OR_NORMAL_OUTPUT_LIMIT')
        try:
            candidate = validate_and_render(decode_json(record['text'].encode()), request)
        except (InputBoundaryError, UnicodeError):
            return finish('invalid_output', 'MARKING_REJECTED')
        save('candidate.json', candidate)
        if not candidate['candidate_available']:
            return finish('uncertain', 'MARKING_ABSTAINED', candidate)
        review_request = prepare_review(item_id=query_id, source=source, candidate=candidate['selective'],
                                       track='SACR', km_text=km_text, km_sha256=km_sha256)
        review_record = call('review', review_request)
        if review_record is None or review_record['status'] != 'EOS_COMPLETE':
            return finish('invalid_output', 'REVIEW_INPUT_OR_NORMAL_OUTPUT_LIMIT', candidate)
        try:
            review = interpret_review(decode_json(review_record['text'].encode()), review_request)
        except (InputBoundaryError, UnicodeError):
            return finish('invalid_output', 'REVIEW_REJECTED', candidate)
        save('review.json', review)
        return finish(review['screening'], 'AUTOMATIC_SCREEN_COMPLETED', candidate)
    except BaseException as error:
        if not (isinstance(error, GrammarRefusal) and active in ('marking', 'review')):
            save('failure.json', {'status': 'HOLD', 'exception_type': type(error).__name__,
                                 'unresolved_stage': active, 'events': events, 'retry': False})
            raise
        reason = 'GRAMMAR_NO_CONTINUATION' if error.evidence.get('kind') == 'NO_CONTINUATION' else 'GRAMMAR_REFUSED'
        events.append({'stage': active, 'status': reason, 'model_calls': 1,
                       'input_output_tokens': 'UNKNOWN', 'evidence': error.evidence})
        save(active + '-grammar-refused.json', {'status': reason, 'evidence': error.evidence,
                                                'model_calls': 1, 'retry': False})
        return finish('invalid_output', reason, candidate)
