"""Normal-return critic evidence bound to the exact R3 source/proposal request."""
from copy import deepcopy
import hashlib
import json
from .mtm_runtime import InputBoundaryError, exact_fields
from .sacr_generated_profile import profile_generation_identity
from .sacr_generated_evidence_v3 import CONTRACT
from .sacr_generated_view import GenerationEvidenceFailure
from .sacr_generation import GenerationLimits
from .sacr_generation_receipt import bind_generation_record
from .sacr_evidence_review_v3 import review_payload, interpret_review
from .sacr_outcomes import summarize_costs


def generated_critic_result(raw, identity, *, proposal, execution, attempt_id,
                            query_id, source, metrics, reservation, maximum_characters=8192, generic_views=None):
    if execution.get('profile_contract') != CONTRACT:
        raise InputBoundaryError('R3 critic requires explicit execution contract')
    expected = profile_generation_identity(execution,attempt_id=attempt_id,query_id=query_id,source=source)
    expected['kind']='critic'
    exact_fields(identity,set(expected)|{'artifact_sha256'})
    if any(identity[k]!=v for k,v in expected.items()):
        raise InputBoundaryError('R3 critic identity mismatch')
    prepared=review_payload(proposal,source=source,query_id=query_id,generic_views=generic_views)
    messages_hash=hashlib.sha256(json.dumps(prepared['messages'],ensure_ascii=False,sort_keys=True).encode()).hexdigest()
    limits=GenerationLimits(**{k:execution['limits'][k] for k in
                              ('input_tokens','output_tokens','context_tokens','response_bytes')})
    if (type(reservation) is not dict or reservation.get('messages_sha256')!=messages_hash
            or reservation.get('status')!='RESERVED' or reservation.get('retry') is not False
            or reservation.get('limits')!=limits.__dict__):
        raise InputBoundaryError('R3 critic request does not match proposal')
    binding=bind_generation_record(raw,expected_sha256=identity['artifact_sha256'],limits=limits,metrics=metrics)
    summarize_costs([{'event_id':attempt_id,'query_id':query_id,'stage':'critic','status':'FAILED','metrics':metrics}])
    def reject(reason):
        raise GenerationEvidenceFailure(raw=raw,identity=identity,binding=binding,metrics=metrics,reason=reason)
    if binding['record']['status']!='EOS_COMPLETE':reject('CRITIC_NOT_EOS_COMPLETE')
    try:
        result=interpret_review(binding['record']['text'].encode(),proposal,source=source,
                                query_id=query_id,maximum_characters=maximum_characters,generic_views=generic_views)
    except (InputBoundaryError,TypeError,ValueError,KeyError,UnicodeError):
        reject('CRITIC_MALFORMED_OR_AMBIGUOUS')
    return {'format':'sacr-critic-evidence-v3','review':result,'generation':binding,
            'generation_identity':deepcopy(identity),'reservation':deepcopy(reservation),
            'generation_artifact_utf8':raw.decode('utf-8'),'semantic_pass':False,'retrieval_ready':False}
