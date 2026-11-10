"""Complete-bundle lexical screening and local-critic input, never semantic PASS.

Caller must first bind normal-return generation receipts and validate the profile.
No retrieval results, labels, generation retries or human-card issuance here.
"""
import hashlib
import json

from .mtm_runtime import InputBoundaryError, identifier
from .sacr_fidelity_screen import parse_critic
from .sacr_views import screen_view
from .sacr_generation import GenerationLimits


def screen_bundle(*, query_id, source, artifacts, protected_phrases,
                  maximum_characters, structurally_valid):
    identifier(query_id)
    if type(source) is not str or not source.strip() or type(artifacts) is not dict:
        raise InputBoundaryError('invalid bundle input')
    expected = {'profile', 'compact', 'selective', 'generic_0'}
    if (not expected <= set(artifacts) or set(artifacts) - expected - {'generic_1'} or
            any(type(v) is not str or not v.strip() for v in artifacts.values()) or
            structurally_valid is not True):
        return {'status': 'UNASSESSABLE_BUNDLE', 'critic_call_allowed': False,
                'semantic_pass': False, 'query_id': query_id}
    # Profile is canonical JSON: lexical comparison applies to retrieval text,
    # while the critic also sees the complete profile and its attachments.
    lexical = {k: screen_view(source, v, protected_phrases=protected_phrases,
                             maximum_characters=maximum_characters)
               for k, v in artifacts.items() if k != 'profile'}
    return {'status': 'BUNDLE_READY_FOR_CRITIC', 'query_id': query_id,
            'source_sha256': hashlib.sha256(source.encode()).hexdigest(),
            'artifacts_sha256': {k: hashlib.sha256(v.encode()).hexdigest() for k, v in artifacts.items()},
            'screen_parameters': {'protected_phrases': list(protected_phrases), 'maximum_characters': maximum_characters},
            'lexical': lexical, 'critic_call_allowed': True, 'semantic_pass': False}


def critic_messages(*, prompt_raw, expected_prompt_sha256, query_id, source, artifacts, screening):
    if hashlib.sha256(prompt_raw).hexdigest() != expected_prompt_sha256:
        raise InputBoundaryError('critic prompt hash mismatch')
    if (screening.get('status') != 'BUNDLE_READY_FOR_CRITIC' or
            screening.get('query_id') != query_id or
            screening.get('source_sha256') != hashlib.sha256(source.encode()).hexdigest() or
            screening.get('artifacts_sha256') != {k: hashlib.sha256(v.encode()).hexdigest() for k,v in artifacts.items()}):
        raise InputBoundaryError('critic bundle differs from screened artifacts')
    return [{'role': 'system', 'content': prompt_raw.decode('utf-8')},
            {'role': 'user', 'content': json.dumps({'query_id': query_id,
             'source_sha256': screening['source_sha256'], 'allowed_source': source,
             'artifacts': artifacts}, ensure_ascii=False, sort_keys=True)}]


def combine_screen(*, screening, critic_raw, query_id, source, artifacts,
                   critic_reservation=None, prompt_raw=None, expected_prompt_sha256=None):
    """critic_raw is EOS text, or None after a documented missing/unusable call.

    Infrastructure/hash/cost failures must stop upstream, not be passed here as
    normally completed malformed text. This function never validates call costs.
    """
    if screening.get('status') != 'BUNDLE_READY_FOR_CRITIC':
        return {'status': 'UNASSESSABLE', 'semantic_pass': False}
    if (screening['query_id'] != query_id or screening['source_sha256'] != hashlib.sha256(source.encode()).hexdigest()
            or screening['artifacts_sha256'] != {k: hashlib.sha256(v.encode()).hexdigest() for k,v in artifacts.items()}):
        raise InputBoundaryError('screen/critic identity mismatch')
    if critic_raw is None:
        return {'status': 'UNASSESSABLE', 'reason': 'MISSING_OR_UNUSABLE_CRITIC', 'semantic_pass': False}
    parameters = screening.get('screen_parameters')
    if type(parameters) is not dict or set(parameters) != {'protected_phrases', 'maximum_characters'}:
        raise InputBoundaryError('missing lexical screening parameters')
    replay = screen_bundle(query_id=query_id, source=source, artifacts=artifacts,
                           structurally_valid=True, **parameters)
    if replay != screening:
        raise InputBoundaryError('incomplete or inconsistent lexical evidence')
    # Reservation must come from the SAME retained attempt as the cost/EOS-bound
    # critic text. Its messages hash binds the critique to this exact bundle.
    if type(critic_reservation) is not dict or type(prompt_raw) is not bytes:
        raise InputBoundaryError('critic request reservation required')
    messages = critic_messages(prompt_raw=prompt_raw, expected_prompt_sha256=expected_prompt_sha256,
        query_id=query_id, source=source, artifacts=artifacts, screening=screening)
    expected = hashlib.sha256(json.dumps(messages, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
    if (critic_reservation.get('messages_sha256') != expected or critic_reservation.get('status') != 'RESERVED'
            or critic_reservation.get('retry') is not False or critic_reservation.get('limits') != GenerationLimits().__dict__):
        raise InputBoundaryError('critic request does not match this bundle')
    try:
        critic = parse_critic(critic_raw, query_id=query_id, source=source, artifacts=artifacts)
    except (InputBoundaryError, TypeError, ValueError, KeyError):
        return {'status': 'UNASSESSABLE', 'reason': 'MALFORMED_OR_AMBIGUOUS_CRITIC', 'semantic_pass': False}
    risk = any(v['status'] != 'LEXICAL_SCREEN_PASS' for v in screening['lexical'].values())
    risk |= critic['status'] != 'CRITIC_UNFLAGGED_NOT_FIDELITY_PASS'
    return {'status': 'ESCALATE' if risk else 'AUTOMATIC_UNFLAGGED_NOT_FIDELITY_PASS',
            'critic': critic, 'lexical': screening['lexical'], 'semantic_pass': False}
