"""Fail-closed EOS wrapper for a prospective single-sequence grammar decoder."""
import json

from patent_to_pilot.research.mtm_runtime import InputBoundaryError


class CompleteJsonEOSGuard:
    """Do not accept a library fallback EOS as proof of a complete JSON object.

    validate is an independent schema validator whose validate method raises on
    invalid instances. Final source alignment and semantic gates still apply.
    No library installation, model call or generated-text logging occurs here.
    """

    def __init__(self, *, prefix_fn, tokenizer, prompt_tokens, eos_token_ids, validate):
        if type(prompt_tokens) is not int or prompt_tokens < 1:
            raise InputBoundaryError('invalid grammar prompt boundary')
        if not eos_token_ids or any(type(i) is not int or i < 0 for i in eos_token_ids):
            raise InputBoundaryError('invalid grammar EOS IDs')
        self.prefix_fn = prefix_fn
        self.tokenizer = tokenizer
        self.prompt_tokens = prompt_tokens
        self.eos = set(eos_token_ids)
        self.validate = validate

    def __call__(self, batch_id, sent):
        if batch_id != 0 or len(sent) < self.prompt_tokens:
            raise InputBoundaryError('grammar requires one untruncated sequence')
        allowed = list(self.prefix_fn(batch_id, sent))
        if not allowed:
            raise InputBoundaryError('grammar has no continuation')
        if self.eos.intersection(allowed):
            text = self.tokenizer.decode(sent[self.prompt_tokens:], skip_special_tokens=False)
            try:
                # Duplicates must not be silently overwritten by json.loads.
                def pairs(items):
                    result = {}
                    for key, value in items:
                        if key in result:
                            raise ValueError('duplicate key')
                        result[key] = value
                    return result
                def constant(_):
                    raise ValueError('non-JSON constant')
                value = json.loads(text, object_pairs_hook=pairs, parse_constant=constant)
                if type(value) is not dict:
                    raise ValueError('not an object')
                self.validate(value)
            except Exception:
                allowed = [token for token in allowed if token not in self.eos]
                if not allowed:
                    raise InputBoundaryError('premature grammar termination refused') from None
        return allowed
