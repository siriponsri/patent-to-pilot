"""Single-query R2 bundle orchestration with durable per-stage evidence.

Injected invoke writes run_reserved_attempt artifacts at the supplied fresh path
and returns measured metrics. It must not retry. The outer supervisor owns model
identity/loading, budget, GPU lock and termination; this module never loads one.
"""
import hashlib
import json
import time
from pathlib import Path

from .mtm_runtime import InputBoundaryError
from .sacr_fidelity_bundle import screen_bundle, critic_messages, combine_screen
from .sacr_generated_profile import profile_generation_identity
from .sacr_generated_token_profile import generated_token_profile_result, CONTRACT
from .sacr_generated_view import GenerationEvidenceFailure
from .sacr_generation import GenerationLimits, validate_generation, run_reserved_attempt
from .sacr_generation_receipt import bind_generation_record
from .sacr_native_fidelity import write_new
from .sacr_outcomes import summarize_costs, METRICS
from .sacr_prompts import build_messages
from .sacr_schema import token_profile_schema


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def local_executor(*, tokenizer, model_factory, device, eos_token_ids,
                   check_admission, peak_memory_bytes):
    """Adapter to the existing one-call generator, no loading/lock ownership.

    Factory receives stage/schema and returns a model wrapper. Source/profile
    grammar setup must finish before the second deadline/resource admission.
    Outer supervision still charges whole elapsed time, including setup/cleanup.
    """
    def invoke(stage, destination, messages, schema):
        model = model_factory(stage, schema)
        check_admission(stage)
        start = time.monotonic()
        record = run_reserved_attempt(destination, messages=messages, tokenizer=tokenizer,
            model=model, device=device, eos_token_ids=eos_token_ids, limits=GenerationLimits())
        elapsed = time.monotonic()-start
        metrics = {key:0 for key in METRICS}
        metrics.update({key:record[key] for key in ('model_calls','input_tokens','output_tokens')})
        metrics.update(operation_wall_seconds=elapsed, gpu_seconds=elapsed,
                       peak_memory_bytes=peak_memory_bytes())
        return metrics
    return invoke


def run_bundle(*, destination, query_id, source, execution, prompt_root,
               expected_prompt_hashes, invoke, check_admission, maximum_characters):
    """Returns screening only; no cards, retrieval or semantic acceptance.

    Infrastructure/identity/cost uncertainty propagates after a durable failure
    marker. Completed unusable generation is retained as unassessable, not retried.
    """
    limits = GenerationLimits(**{k: execution['limits'][k] for k in
        ('input_tokens', 'output_tokens', 'context_tokens', 'response_bytes')})
    if limits != GenerationLimits():
        raise InputBoundaryError('frozen bundle limits required')
    if set(expected_prompt_hashes) != {'profile_tokens', 'generic', 'selective', 'critic'}:
        raise InputBoundaryError('all bundle prompt hashes required')
    if execution.get('profile_contract') != CONTRACT:
        raise InputBoundaryError('explicit R2 execution contract required before dispatch')
    if type(maximum_characters) is not int or maximum_characters <= 0:
        raise InputBoundaryError('invalid predeclared text limit')
    files = {'profile_tokens':'sacr_profile_tokens_v1.txt', 'generic':'sacr_generic_views_v0.txt',
             'selective':'sacr_selective_v0.txt', 'critic':'sacr_fidelity_screen_v1.txt'}
    for kind, name in files.items():
        if sha((Path(prompt_root)/name).read_bytes()) != expected_prompt_hashes[kind]:
            raise InputBoundaryError('bundle prompt differs before any generation')
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=False)
    events = []
    write_new(destination/'input.json', {'query_id':query_id, 'source_sha256':sha(source.encode()),
        'execution':execution, 'prompt_hashes':expected_prompt_hashes,
        'maximum_characters':maximum_characters, 'retry':False})

    def call(stage, messages, schema=None):
        check_admission(stage)
        attempt = destination/stage
        metrics = invoke(stage, attempt, messages, schema)
        # Read the exact exclusive directory passed to the executor, not a supplied
        # response object or caller-selected artifact from another attempt.
        reservation = json.loads((attempt/'reservation.json').read_bytes())
        expected = sha(json.dumps(messages, ensure_ascii=False, sort_keys=True).encode())
        if (reservation.get('messages_sha256') != expected or reservation.get('status') != 'RESERVED'
                or reservation.get('retry') is not False or reservation.get('limits') != limits.__dict__):
            raise InputBoundaryError('stage request reservation mismatch')
        raw = (attempt/'generation.json').read_bytes()
        binding = bind_generation_record(raw, expected_sha256=sha(raw), limits=limits, metrics=metrics)
        event = {'event_id':stage, 'query_id':query_id, 'stage':stage,
                 'status':'COMPLETED', 'metrics':metrics}
        summarize_costs([event])
        write_new(attempt/'cost.json', event)
        events.append(event)
        if binding['record']['status'] == 'INPUT_LIMIT':
            raise InputBoundaryError('stage input limit; no truncation or retry')
        return raw, binding, metrics, reservation

    def prompt(kind, profile=None):
        built = build_messages(prompt_root=prompt_root, kind=kind, query_id=query_id,
                               input_kind='DAPFAM_TA', source=source, profile=profile)
        if built['prompt_sha256'] != expected_prompt_hashes[kind]:
            raise InputBoundaryError('stage prompt differs from declaration')
        return built['messages']

    def finish(status, **extra):
        result = {'status':status, 'query_id':query_id, 'events':events,
                  'costs':summarize_costs(events), 'semantic_pass':False, 'retry':False, **extra}
        write_new(destination/'result.json', result)
        return result

    try:
        messages = prompt('profile_tokens')
        raw, binding, metrics, _ = call('profile', messages,
            token_profile_schema(source=source, query_id=query_id, input_kind='DAPFAM_TA'))
        identity = {**profile_generation_identity(execution, attempt_id='profile',
                    query_id=query_id, source=source), 'artifact_sha256':sha(raw)}
        try:
            prepared = generated_token_profile_result(raw, identity, execution=execution,
                attempt_id='profile', query_id=query_id, source=source, metrics=metrics)
        except GenerationEvidenceFailure as failure:
            write_new(destination/'profile-rejection.json', failure.output)
            return finish('UNASSESSABLE', reason='REJECTED_PROFILE')
        write_new(destination/'prepared-profile.json', prepared)
        if prepared['decision'] != 'PROFILE_STRUCTURALLY_PREPARED_FIDELITY_PENDING':
            return finish('UNASSESSABLE', reason='PROFILE_REQUIRES_REVIEW_OR_FALLBACK')
        artifacts = {'profile':json.dumps(prepared['profile'], ensure_ascii=False, sort_keys=True),
                     'compact':prepared['compact']['text']}
        # Retain either usable view independently even if its peer is rejected.
        unavailable = []
        for kind in ('generic', 'selective'):
            messages = prompt(kind, prepared['profile'] if kind == 'selective' else None)
            raw, binding, _, _ = call(kind, messages)
            try:
                if binding['record']['status'] != 'EOS_COMPLETE':
                    raise InputBoundaryError('unusable normal return')
                parsed = validate_generation(binding['record'], kind=kind, source=source,
                    query_id=query_id, input_kind='DAPFAM_TA', limits=limits)['views']
                for text in parsed:
                    text.encode('utf-8')  # reject invalid Unicode without repair
                if not parsed:
                    raise InputBoundaryError('empty generated view')
            except (InputBoundaryError, UnicodeError):
                unavailable.append(kind)
                continue
            if kind == 'generic':
                artifacts.update({f'generic_{i}':text for i,text in enumerate(parsed)})
            else:
                artifacts['selective'] = parsed[0]
        write_new(destination/'artifacts.json', artifacts)
        if unavailable:
            return finish('UNASSESSABLE', reason='REJECTED_VIEW', unavailable=unavailable)
        protected = [c['raw_text'] for b in prepared['profile']['blocks'] for c in b['attached_conditions']]
        protected += [c['raw_text'] for c in prepared['profile']['context_items'] if c['action']=='retain']
        screen = screen_bundle(query_id=query_id, source=source, artifacts=artifacts,
            protected_phrases=protected, maximum_characters=maximum_characters, structurally_valid=True)
        write_new(destination/'lexical-screen.json', screen)
        critic_prompt = (Path(prompt_root)/'sacr_fidelity_screen_v1.txt').read_bytes()
        messages = critic_messages(prompt_raw=critic_prompt, expected_prompt_sha256=expected_prompt_hashes['critic'],
            query_id=query_id, source=source, artifacts=artifacts, screening=screen)
        raw, binding, _, reservation = call('critic', messages)
        text = binding['record']['text'] if binding['record']['status']=='EOS_COMPLETE' else None
        try:
            critic_raw = text.encode('utf-8') if text is not None else None
        except UnicodeError:
            critic_raw = None
        result = combine_screen(screening=screen, critic_raw=critic_raw, query_id=query_id,
            source=source, artifacts=artifacts, critic_reservation=reservation,
            prompt_raw=critic_prompt, expected_prompt_sha256=expected_prompt_hashes['critic'])
        return finish(result['status'], screening=result)
    except BaseException as error:
        write_new(destination/'failure.json', {'status':'STOP_INFRA_OR_IDENTITY_OR_BUDGET',
            'exception_type':type(error).__name__, 'known_events':events,
            'unsettled_attempt_cost':'UNKNOWN_INSPECT_ATTEMPT_AND_SUPERVISOR', 'retry':False})
        raise
