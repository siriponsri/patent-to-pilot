"""Durable R3 profile/generic/critic orchestration; external admission required."""
import hashlib
import json
from pathlib import Path
from .mtm_runtime import InputBoundaryError
from .sacr_generation import GenerationLimits, validate_generation
from .sacr_generation_receipt import bind_generation_record
from .sacr_generated_profile import profile_generation_identity
from .sacr_generated_evidence_v3 import CONTRACT, generated_evidence_result
from .sacr_generated_critic_v3 import generated_critic_result
from .sacr_generated_view import GenerationEvidenceFailure
from .sacr_evidence_prompt_v3 import build_messages, proposal_schema
from .sacr_evidence_review_v3 import review_payload
from .sacr_prompts import build_messages as legacy_messages
from .sacr_native_fidelity import write_new
from .sacr_outcomes import summarize_costs


def sha(raw): return hashlib.sha256(raw).hexdigest()


def run_bundle(*, destination, source, query_id, execution, prompt_root,
               generic_prompt_sha256, invoke, check_admission, maximum_characters):
    limits=GenerationLimits(**{k:execution['limits'][k] for k in
                             ('input_tokens','output_tokens','context_tokens','response_bytes')})
    if execution.get('profile_contract')!=CONTRACT or limits!=GenerationLimits():
        raise InputBoundaryError('R3 contract/frozen limits required')
    generic=legacy_messages(prompt_root=Path(prompt_root),kind='generic',query_id=query_id,
                            input_kind='DAPFAM_TA',source=source)
    if generic['prompt_sha256']!=generic_prompt_sha256:
        raise InputBoundaryError('generic prompt identity mismatch')
    profile_messages=build_messages(source,query_id)
    schema=proposal_schema(source,query_id)
    if type(maximum_characters) is not int or maximum_characters<=0:
        raise InputBoundaryError('invalid text cap')
    out=Path(destination);out.mkdir(parents=True,exist_ok=False)
    events=[]; active=None
    write_new(out/'input.json',{'query_id':query_id,'source_sha256':sha(source.encode()),
              'execution':execution,'generic_prompt_sha256':generic_prompt_sha256,'retry':False})

    def call(stage,messages,schema=None):
        nonlocal active
        check_admission(stage)
        active=stage
        attempt=out/stage
        metrics=invoke(stage,attempt,messages,schema)
        reservation=json.loads((attempt/'reservation.json').read_bytes())
        if (reservation.get('messages_sha256')!=sha(json.dumps(messages,ensure_ascii=False,sort_keys=True).encode())
                or reservation.get('status')!='RESERVED' or reservation.get('retry') is not False
                or reservation.get('limits')!=limits.__dict__):
            raise InputBoundaryError('same-attempt request mismatch')
        raw=(attempt/'generation.json').read_bytes()
        binding=bind_generation_record(raw,expected_sha256=sha(raw),limits=limits,metrics=metrics)
        event={'event_id':stage,'query_id':query_id,'stage':stage,'status':'COMPLETED','metrics':metrics}
        summarize_costs([event]);write_new(attempt/'cost.json',event);events.append(event)
        active=None
        identity=profile_generation_identity(execution,attempt_id=stage,query_id=query_id,source=source)
        identity.update(kind=stage,artifact_sha256=sha(raw))
        return raw,identity,binding,metrics,reservation

    def finish(status,**extra):
        result={'status':status,'query_id':query_id,'events':events,'costs':summarize_costs(events),
                'semantic_pass':False,'retrieval_ready':False,'retry':False,**extra}
        write_new(out/'result.json',result);return result

    try:
        raw,identity,binding,metrics,reservation=call('profile',profile_messages,schema)
        try:
            profile=generated_evidence_result(raw,identity,execution=execution,attempt_id='profile',
                query_id=query_id,source=source,metrics=metrics,reservation=reservation,
                maximum_characters=maximum_characters)
        except GenerationEvidenceFailure as failure:
            write_new(out/'profile-rejection.json',failure.output)
            return finish('UNASSESSABLE',reason='REJECTED_PROFILE')
        write_new(out/'prepared-profile.json',profile)
        if profile['prepared']['compiled']['anchor_fallback_required']:
            return finish('UNASSESSABLE',reason='PROFILE_ABSTAINED')
        raw,identity,binding,metrics,reservation=call('generic',generic['messages'])
        try:
            if binding['record']['status']!='EOS_COMPLETE':raise InputBoundaryError('generic not EOS')
            views=validate_generation(binding['record'],kind='generic',source=source,query_id=query_id,
                                       input_kind='DAPFAM_TA',limits=limits)['views']
            if not views:raise InputBoundaryError('generic empty')
            for text in views:text.encode('utf-8')
        except (InputBoundaryError,UnicodeError):
            return finish('UNASSESSABLE',reason='REJECTED_GENERIC_PROFILE_VIEWS_RETAINED')
        write_new(out/'generic-views.json',views)
        payload=review_payload(profile['proposal'],source=source,query_id=query_id,generic_views=views)
        raw,identity,binding,metrics,reservation=call('critic',payload['messages'])
        try:
            critic=generated_critic_result(raw,identity,proposal=profile['proposal'],execution=execution,
                attempt_id='critic',query_id=query_id,source=source,metrics=metrics,reservation=reservation,
                maximum_characters=maximum_characters,generic_views=views)
        except GenerationEvidenceFailure as failure:
            write_new(out/'critic-rejection.json',failure.output)
            return finish('UNASSESSABLE',reason='REJECTED_CRITIC')
        write_new(out/'critic-result.json',critic)
        return finish(critic['review']['status'])
    except BaseException as error:
        write_new(out/'failure.json',{'status':'INFRA_OR_INTEGRITY_STOP','exception_type':type(error).__name__,
                  'events':events,'unsettled_attempt':active,'unsettled_attempt_cost':'UNKNOWN' if active else 'NONE',
                  'retry':False})
        raise
