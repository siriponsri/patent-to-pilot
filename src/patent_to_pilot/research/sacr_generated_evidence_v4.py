"""Bind R4 profile output to retained normal-return evidence; no model dispatch."""
from copy import deepcopy
import hashlib
import json

from .mtm_runtime import InputBoundaryError, exact_fields, decode_json
from .sacr_generated_profile import profile_generation_identity
from .sacr_generated_view import GenerationEvidenceFailure
from .sacr_generation import GenerationLimits
from .sacr_generation_receipt import bind_generation_record
from .sacr_outcomes import summarize_costs
from .sacr_evidence_prompt_v4 import build_messages, validate_proposal
from .sacr_evidence_review_v3 import review_payload, lexical_screen

CONTRACT = 'sacr-context-constrained-v4-bound'


def generated_evidence_result(raw, identity, *, execution, attempt_id, query_id,
                              source, metrics, reservation, maximum_characters=8192):
    if execution.get('profile_contract') != CONTRACT:
        raise InputBoundaryError('explicit R4 execution contract required')
    expected = profile_generation_identity(execution, attempt_id=attempt_id, query_id=query_id, source=source)
    exact_fields(identity, set(expected) | {'artifact_sha256'})
    if any(identity[k] != v for k,v in expected.items()):
        raise InputBoundaryError('R4 generation identity mismatch')
    limits = GenerationLimits(**{k:execution['limits'][k] for k in
                                ('input_tokens','output_tokens','context_tokens','response_bytes')})
    request_hash = hashlib.sha256(json.dumps(build_messages(source,query_id),
                          ensure_ascii=False,sort_keys=True).encode()).hexdigest()
    if (type(reservation) is not dict or reservation.get('messages_sha256') != request_hash
            or reservation.get('status') != 'RESERVED' or reservation.get('retry') is not False
            or reservation.get('limits') != limits.__dict__):
        raise InputBoundaryError('R4 request reservation mismatch')
    binding = bind_generation_record(raw,expected_sha256=identity['artifact_sha256'],limits=limits,metrics=metrics)
    summarize_costs([{'event_id':attempt_id,'query_id':query_id,'stage':'profile','status':'FAILED','metrics':metrics}])
    def reject(reason):
        raise GenerationEvidenceFailure(raw=raw,identity=identity,binding=binding,metrics=metrics,reason=reason)
    if binding['record']['status'] != 'EOS_COMPLETE': reject('GENERATION_NOT_EOS_COMPLETE')
    try:
        proposal = decode_json(binding['record']['text'].encode('utf-8'))
        validate_proposal(proposal,source,query_id)
        prepared = review_payload(proposal,source=source,query_id=query_id)
        screen = lexical_screen(proposal,source=source,query_id=query_id,maximum_characters=maximum_characters)
    except (InputBoundaryError, UnicodeError, TypeError, ValueError, KeyError):
        reject('R4_PROFILE_ACCEPTANCE_FAILED')
    return {'format':CONTRACT,'proposal':proposal,'prepared':prepared,'lexical':screen,
            'generation':binding,'generation_identity':deepcopy(identity),
            'reservation':deepcopy(reservation),'generation_artifact_utf8':raw.decode('utf-8'),
            'semantic_pass':False,'retrieval_ready':False}


def replay_generated_evidence(output, **kwargs):
    replay = generated_evidence_result(output['generation_artifact_utf8'].encode(),
                   output['generation_identity'],reservation=output['reservation'],**kwargs)
    if replay != output: raise InputBoundaryError('R4 retained result changed')
    return replay
