import json

import pytest
from jsonschema import Draft202012Validator

from patent_to_pilot.research.mtm_runtime import InputBoundaryError
from patent_to_pilot.research.sacr_grammar_guard import CompleteJsonEOSGuard


class Tokenizer:
    def decode(self, tokens, **kwargs):
        assert kwargs == {'skip_special_tokens': False}
        return ''.join(chr(token) for token in tokens)


def guard(allowed):
    schema = {'type': 'object', 'required': ['text'], 'additionalProperties': False,
              'properties': {'text': {'type': 'string'}}}
    return CompleteJsonEOSGuard(prefix_fn=lambda batch, sent: allowed, tokenizer=Tokenizer(),
                               prompt_tokens=2, eos_token_ids=[900000, 900001],
                               validate=Draft202012Validator(schema).validate)


def seq(text):
    return [1, 2] + [ord(c) for c in text]


@pytest.mark.parametrize('text', ['{"text":', '{"wrong":1}', '[]',
                                 '{"text":"a","text":"b"}', '{"text":NaN}',
                                 '{"text":"a"} trailing'])
def test_premature_or_invalid_eos_only_raises_without_text_leak(text):
    with pytest.raises(InputBoundaryError, match='premature grammar termination refused') as error:
        guard([900000, 900001])(0, seq(text))
    assert text not in str(error.value)


def test_premature_eos_removed_when_real_continuation_exists():
    assert guard([900000, 900001, 42])(0, seq('{')) == [42]


def test_complete_unicode_object_allows_eos_and_trailing_whitespace_token():
    text = json.dumps({'text': 'ไทย 🧪'}, ensure_ascii=False)
    assert guard([900000, 900001, 32])(0, seq(text)) == [900000, 900001, 32]


def test_no_eos_does_not_decode_incomplete_utf8_prefix():
    assert guard([42])(0, seq('{')) == [42]


def test_empty_continuation_and_wrong_batch_fail():
    with pytest.raises(InputBoundaryError, match='no continuation'):
        guard([])(0, seq('{'))
    with pytest.raises(InputBoundaryError, match='one untruncated sequence'):
        guard([42])(1, seq('{'))
