from contextlib import nullcontext
import hashlib
import json
import sys
from types import SimpleNamespace

import numpy as np
import pytest

from patent_to_pilot.research.mtm_runtime import InputBoundaryError
from patent_to_pilot.research.sacr_generation import GenerationLimits, generate_once, run_reserved_attempt, validate_generation
from test_sacr_profile import SOURCE, fixture


class Tensor(np.ndarray):
    def cpu(self):
        return self


class Encoding(dict):
    def to(self, device):
        return self


class Tokenizer:
    pad_token_id = 0

    def __init__(self, count=3, text='{"views": []}'):
        self.count, self.text = count, text

    def apply_chat_template(self, messages, **kwargs):
        assert kwargs["enable_thinking"] is False
        return Encoding(input_ids=np.ones((1, self.count), dtype=int).view(Tensor))

    def decode(self, tokens, **kwargs):
        return self.text


class Model:
    def __init__(self, tokens=(5, 9), error=False):
        self.tokens, self.error, self.calls = tokens, error, 0

    def generate(self, **kwargs):
        self.calls += 1
        assert kwargs["do_sample"] is False and kwargs["num_beams"] == 1
        if self.error:
            raise RuntimeError("private error detail")
        return np.concatenate([kwargs["input_ids"], [self.tokens]], axis=1).view(Tensor)


@pytest.fixture(autouse=True)
def fake_torch(monkeypatch):
    # Local torch is absent. This is contract testing, not a model/backend test.
    monkeypatch.setitem(sys.modules, "torch", SimpleNamespace(inference_mode=nullcontext, equal=np.array_equal))


def args(model=None, tokenizer=None, limits=None):
    return dict(messages=[{"role": "user", "content": "synthetic"}], tokenizer=tokenizer or Tokenizer(),
                model=model or Model(), device="cpu", eos_token_ids=[9],
                limits=limits or GenerationLimits(input_tokens=4, output_tokens=2, context_tokens=6))


def test_input_cap_precedes_model_call_and_does_not_truncate():
    model = Model()
    result = generate_once(**args(model=model, tokenizer=Tokenizer(count=5)))
    assert result["status"] == "INPUT_LIMIT" and model.calls == 0
    assert result["input_tokens"] == 5 and result["retry"] is False


@pytest.mark.parametrize("tokens,status", [((5, 9), "EOS_COMPLETE"), ((5, 6), "OUTPUT_LIMIT"), ((5,), "NO_EOS")])
def test_stop_classification_including_eos_at_exact_cap(tokens, status):
    model = Model(tokens=tokens)
    result = generate_once(**args(model=model))
    assert result["status"] == status and model.calls == 1
    assert result["output_tokens"] == len(tokens)


def test_limit_and_response_binding():
    with pytest.raises(InputBoundaryError):
        generate_once(**args(limits=GenerationLimits(4, 3, 6)))
    result = generate_once(**args())
    result["text"] += "changed"
    with pytest.raises(InputBoundaryError):
        validate_generation(result, kind="generic", source=SOURCE, query_id="q1", input_kind="MTM_P", limits=GenerationLimits())


def test_profile_decode_is_strict_and_not_semantic_acceptance():
    text = json.dumps(fixture())
    record = {"status": "EOS_COMPLETE", "text": text, "response_sha256": hashlib.sha256(text.encode()).hexdigest()}
    out = validate_generation(record, kind="profile", source=SOURCE, query_id="q1", input_kind="MTM_P", limits=GenerationLimits())
    assert out["status"] == "PROFILE_STRUCTURALLY_VALID" and out["semantic_status"] == "unknown"
    record["status"] = "OUTPUT_LIMIT"
    assert validate_generation(record, kind="profile", source=SOURCE, query_id="q1", input_kind="MTM_P",
                               limits=GenerationLimits())["anchor_fallback_required"]


@pytest.mark.parametrize("fail", [False, True])
def test_attempt_reserved_before_call_and_never_reused(tmp_path, fail):
    target = tmp_path / "attempt"
    model = Model(error=fail)
    if fail:
        with pytest.raises(RuntimeError):
            run_reserved_attempt(target, **args(model=model))
        failure = (target / "failure.json").read_text()
        assert "private error detail" not in failure and "UNKNOWN" in failure
    else:
        run_reserved_attempt(target, **args(model=model))
        assert (target / "generation.json").exists()
    assert (target / "reservation.json").exists()
    with pytest.raises(FileExistsError):
        run_reserved_attempt(target, **args(model=model))
    assert model.calls == 1
