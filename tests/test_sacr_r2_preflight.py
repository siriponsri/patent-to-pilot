import json
from types import SimpleNamespace

import pytest

from patent_to_pilot.research.mtm_runtime import InputBoundaryError
from patent_to_pilot.research.sacr_generation import GenerationLimits
from patent_to_pilot.research.sacr_native_fidelity import digest
from patent_to_pilot.research.sacr_r2_preflight import preflight_token_profiles
from test_sacr_native_fidelity import inputs, ROOT


class Tokenizer:
    def __init__(self, over_at=None):
        self.calls = 0
        self.over_at = over_at

    def apply_chat_template(self, messages, **kwargs):
        assert kwargs == dict(tokenize=True, add_generation_prompt=True,
                              return_tensors='pt', return_dict=True, enable_thinking=False)
        self.calls += 1
        return {'input_ids': SimpleNamespace(shape=(1, 8193 if self.calls == self.over_at else 100))}


def run(tokenizer, reverse=False):
    raw, sample = inputs()
    if reverse: sample['entries'].reverse()
    sraw = json.dumps(sample).encode()
    return preflight_token_profiles(query_bytes=raw, sample_bytes=sraw,
        query_sha256=digest(raw), sample_sha256=digest(sraw),
        prompt_root=ROOT/'docs/healthtech/research/prompts', tokenizer=tokenizer,
        limits=GenerationLimits())


def test_all100_admitted_without_claiming_full_bundle_or_budget():
    t = Tokenizer(); result = run(t)
    assert t.calls == result['sample_size'] == 100
    assert result['total_input_tokens'] == 10000
    assert result['status'] == 'PROFILE_INPUT_LIMIT_PASS_ONLY'
    assert result['generation_budget'] == result['bundle_input_limits'] == 'NOT_ESTABLISHED'
    assert result['model_calls'] == 0


def test_one_oversized_input_stops_cohort_without_dropping_or_truncating():
    t = Tokenizer(over_at=42); result = run(t)
    assert result['status'] == 'STOP_INPUT_LIMIT'
    assert result['exceeded'] == 1 and len(result['records']) == 100
    assert result['maximum_input_tokens'] == 8193 and result['truncation'] is False


def test_reselected_cohort_rejected_before_tokenization():
    t = Tokenizer()
    with pytest.raises(InputBoundaryError): run(t, reverse=True)
    assert t.calls == 0
