"""Deterministic finite alphabet for a prospective source-aware JSON grammar."""
import hashlib

from patent_to_pilot.research.mtm_runtime import InputBoundaryError


def build_alphabet(tokenizer, source: str) -> dict:
    """Union printable ASCII, decoded vocabulary and all source scalar values.

    This does not claim every possible Unicode scalar is available literally.
    JSON escapes are still needed for controls; final decoded quotations must
    match the unmodified source. Pin tokenizer identity separately before use.
    """
    if type(source) is not str or not source.strip():
        raise InputBoundaryError('invalid alphabet source')
    if any(0xD800 <= ord(c) <= 0xDFFF for c in source):
        raise InputBoundaryError('source contains non-scalar Unicode')
    chars = {chr(i) for i in range(32, 127)} | set(source)
    for token_id in range(len(tokenizer)):
        chars.update(tokenizer.decode([token_id], skip_special_tokens=False))
    alphabet = ''.join(sorted(c for c in chars if ord(c) >= 32 and not 0xD800 <= ord(c) <= 0xDFFF))
    return {'version': 'sacr-vocabulary-source-alphabet-v1', 'alphabet': alphabet,
            'sha256': hashlib.sha256(alphabet.encode('utf-8')).hexdigest(),
            'characters': len(alphabet),
            'scope': 'FINITE_VOCABULARY_PLUS_SOURCE_NOT_ALL_UNICODE'}
