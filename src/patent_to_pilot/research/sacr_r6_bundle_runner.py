"""R6-only durable bundle; external frozen package/resource admission required."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError
from .mtm_runtime import InputBoundaryError, decode_json
from .sacr_generation import GenerationLimits, validate_generation
from .sacr_generation_receipt import bind_generation_record
from .sacr_native_fidelity import write_new
from .sacr_outcomes import summarize_costs
from .sacr_prompts import build_messages as generic_messages
from .sacr_r6_candidate import VERSION, build_messages, proposal_schema, validate_proposal, render_views, review_request
from .reference_critic_v1 import interpret


def sha(raw):return hashlib.sha256(raw).hexdigest()


def encoded(value):return json.dumps(value,ensure_ascii=False,sort_keys=True).encode()


def run_bundle(*, destination,source,query_id,execution,prompt_root,generic_prompt_sha256,
               invoke,check_admission,count_tokens,maximum_characters):
    """count_tokens must use exact pinned chat template without loading a model.

    Normal non-EOS/parser rejection is retained as UNASSESSABLE. Infrastructure
    exceptions and unknown backend state propagate with a durable failure receipt.
    A screening-unflagged result is never a human fidelity pass.
    """
    limits=GenerationLimits(**execution['limits'])
    if execution.get('profile_contract')!=VERSION or limits!=GenerationLimits():
        raise InputBoundaryError('frozen R6 contract and limits required')
    if type(maximum_characters) is not int or not 0<maximum_characters<=65536:
        raise InputBoundaryError('invalid rendered text ceiling')
    generic=generic_messages(prompt_root=Path(prompt_root),kind='generic',query_id=query_id,
        input_kind='DAPFAM_TA',source=source)
    if generic['prompt_sha256']!=generic_prompt_sha256:raise InputBoundaryError('generic prompt identity changed')
    messages=build_messages(source,query_id); schema=proposal_schema(source,query_id)
    out=Path(destination);out.mkdir(parents=True,exist_ok=False)
    write_new(out/'input.json',{'query_id':query_id,'source_sha256':sha(source.encode()),
        'execution':execution,'generic_prompt_sha256':generic_prompt_sha256,'retry':False})
    events=[];active=None;preflights=[]

    def finish(status,reason,**extra):
        result={'status':status,'reason':reason,'query_id':query_id,'events':events,
            'costs':summarize_costs(events),'input_preflights':preflights,
            'semantic_pass':False,'retrieval_ready':False,'retry':False,**extra}
        write_new(out/'result.json',result);return result

    def call(stage,messages,schema=None):
        nonlocal active
        check_admission(stage)
        messages=deepcopy(messages);schema=deepcopy(schema)
        before=encoded(messages);schema_before=encoded(schema)
        tokens=count_tokens(messages)
        if encoded(messages)!=before or encoded(schema)!=schema_before:
            raise InputBoundaryError('token counter mutated frozen request before dispatch')
        if type(tokens) is not int or tokens<1:raise InputBoundaryError('invalid exact prompt token count')
        receipt={'stage':stage,'messages_sha256':sha(before),'schema_sha256':sha(schema_before),
            'input_tokens':tokens,'status':'INPUT_LIMIT' if tokens>limits.input_tokens else 'ADMITTED',
            'model_calls':0}
        write_new(out/(stage+'-input-admission.json'),receipt);preflights.append(receipt)
        if tokens>limits.input_tokens:return None
        check_admission(stage)
        active=stage;attempt=out/stage
        metrics=invoke(stage,attempt,messages,schema)
        if encoded(messages)!=before or encoded(schema)!=schema_before:
            raise InputBoundaryError('invocation mutated frozen request')
        reservation=json.loads((attempt/'reservation.json').read_bytes())
        if (reservation.get('status')!='RESERVED' or reservation.get('retry') is not False
                or reservation.get('messages_sha256')!=sha(before) or reservation.get('limits')!=limits.__dict__):
            raise InputBoundaryError('same-attempt reservation mismatch')
        raw=(attempt/'generation.json').read_bytes()
        binding=bind_generation_record(raw,expected_sha256=sha(raw),limits=limits,metrics=metrics)
        if binding['record']['input_tokens']!=tokens:raise InputBoundaryError('preflight/generated input token mismatch')
        event={'event_id':sha(encoded([execution['run_id'],query_id,stage])),
            'query_id':query_id,'stage':stage,'status':'COMPLETED','metrics':metrics}
        summarize_costs([event]);write_new(attempt/'cost.json',event);events.append(event)
        # Known generation costs remain settled even if later metadata persistence fails.
        active=None
        write_new(attempt/'r6-binding.json',{'generation_sha256':sha(raw),'messages_sha256':sha(before),
            'schema_sha256':sha(schema_before),'execution_sha256':sha(encoded(execution)),
            'event_sha256':sha(encoded(event)),'execution_attestation':'REQUIRES_WORKER_DIAGNOSTICS'})
        active=None
        return binding['record']

    try:
        record=call('profile',messages,schema)
        if record is None:return finish('UNASSESSABLE','PROFILE_INPUT_LIMIT')
        if record['status']!='EOS_COMPLETE':return finish('UNASSESSABLE','PROFILE_'+record['status'])
        try:
            proposal=decode_json(record['text'].encode())
            Draft202012Validator(schema).validate(proposal)
            checked=validate_proposal(proposal,source,query_id)
        except (InputBoundaryError,UnicodeError,ValidationError) as error:
            return finish('UNASSESSABLE','REJECTED_PROFILE',exception_type=type(error).__name__)
        # Deterministic rendering faults are engineering failures, not bad model text.
        views=render_views(proposal,source=source,query_id=query_id)
        write_new(out/'prepared-profile.json',{'proposal':proposal,'prepared':checked,'views':views})
        if checked['compiled']['anchor_fallback_required']:return finish('UNASSESSABLE','PROFILE_ABSTAINED')
        if any(len(views[k])>maximum_characters for k in ('source_anchor','compact','selective')):
            return finish('UNASSESSABLE','RENDERED_VIEW_LIMIT')
        record=call('generic',generic['messages'])
        if record is None:return finish('UNASSESSABLE','GENERIC_INPUT_LIMIT_PROFILE_RETAINED')
        if record['status']!='EOS_COMPLETE':return finish('UNASSESSABLE','GENERIC_'+record['status'])
        try:
            controls=validate_generation(record,kind='generic',source=source,query_id=query_id,
                input_kind='DAPFAM_TA',limits=limits)['views']
            if not 1<=len(controls)<=2:raise InputBoundaryError('generic view count')
            for value in controls:
                value.encode('utf-8')
                if not value.strip() or len(value)>maximum_characters:raise InputBoundaryError('generic view limit')
        except (InputBoundaryError,UnicodeError,ValidationError) as error:
            return finish('UNASSESSABLE','REJECTED_GENERIC',exception_type=type(error).__name__)
        try:request=review_request(proposal,source=source,query_id=query_id,generic_views=controls)
        except InputBoundaryError as error:
            return finish('UNASSESSABLE','CRITIC_INPUT_CONTRACT_LIMIT',exception_type=type(error).__name__)
        write_new(out/'generic-views.json',controls);write_new(out/'critic-request.json',request)
        record=call('critic',request['messages'],request['schema'])
        if record is None:return finish('UNASSESSABLE','CRITIC_INPUT_LIMIT_VIEWS_RETAINED')
        if record['status']!='EOS_COMPLETE':return finish('UNASSESSABLE','CRITIC_'+record['status'])
        try:review=interpret(record['text'].encode(),request)
        except (InputBoundaryError,UnicodeError,ValidationError) as error:
            return finish('UNASSESSABLE','REJECTED_CRITIC',exception_type=type(error).__name__)
        write_new(out/'critic-result.json',review)
        return finish('AUTOMATIC_UNFLAGGED_NOT_FIDELITY_PASS' if review['method_screen']=='UNFLAGGED'
            else 'AUTOMATIC_METHOD_FLAG','VALID_CRITIC',screening=review)
    except BaseException as error:
        write_new(out/'failure.json',{'status':'INFRA_OR_INTEGRITY_STOP','exception_type':type(error).__name__,
            'events':events,'unsettled_attempt':active,'unsettled_attempt_cost':'UNKNOWN' if active else 'NONE',
            'retry':False})
        raise


def request_bound_executor(*,tokenizer,model_factory,device,eos_token_ids,check_admission,peak_memory_bytes):
    """Factory receives actual immutable message content for alphabet construction."""
    from .sacr_failure_diagnostics import local_executor
    def invoke(stage,destination,messages,schema):
        frozen=deepcopy(messages)
        def factory(actual_stage,actual_schema,diagnostics):
            supplied_messages=deepcopy(frozen);supplied_schema=deepcopy(actual_schema)
            before_messages=encoded(supplied_messages);before_schema=encoded(supplied_schema)
            model=model_factory(actual_stage,supplied_schema,diagnostics,supplied_messages)
            if (encoded(supplied_messages)!=before_messages or encoded(supplied_schema)!=before_schema
                    or diagnostics.backend_invocations!=0):
                raise InputBoundaryError('factory mutated request or dispatched during construction')
            return model
        executor=local_executor(tokenizer=tokenizer,model_factory=factory,device=device,
            eos_token_ids=eos_token_ids,check_admission=check_admission,peak_memory_bytes=peak_memory_bytes)
        return executor(stage,destination,messages,schema)
    return invoke
