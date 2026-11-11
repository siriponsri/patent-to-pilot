"""One-attempt local generation contract; injected model/tokenizer, no loading.

Caller owns immutable model/config hashes, GPU authorization/lock and durable
attempt reservation. Returned text is a private artifact, never a public audit.
"""
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from patent_to_pilot.research.mtm_runtime import InputBoundaryError, decode_json
from patent_to_pilot.research.sacr_profile import validate_profile
from patent_to_pilot.research.sacr_quote_profile import align_quote_profile
from patent_to_pilot.research.sacr_token_profile import align_token_profile
from patent_to_pilot.research.sacr_views import parse_view_response


@dataclass(frozen=True)
class GenerationLimits:
    input_tokens: int = 8192
    output_tokens: int = 4096
    context_tokens: int = 40960
    response_bytes: int = 65536

    def validate(self):
        values = (self.input_tokens, self.output_tokens, self.context_tokens, self.response_bytes)
        if any(type(value) is not int or value <= 0 for value in values):
            raise InputBoundaryError("invalid generation limits")
        if self.input_tokens + self.output_tokens > self.context_tokens:
            raise InputBoundaryError("generation limits exceed model context")


def generate_once(*, messages, tokenizer, model, device, eos_token_ids, limits: GenerationLimits) -> dict:
    limits.validate()
    if (type(eos_token_ids) is not list or not eos_token_ids or
            any(type(i) is not int or i < 0 for i in eos_token_ids)):
        raise InputBoundaryError("explicit EOS token IDs required")
    encoded = tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True,
                                            return_tensors="pt", return_dict=True, enable_thinking=False)
    if len(encoded["input_ids"].shape) != 2 or encoded["input_ids"].shape[0] != 1:
        raise InputBoundaryError("generation contract requires one input")
    input_count = encoded["input_ids"].shape[1]
    if input_count > limits.input_tokens:
        return {"status": "INPUT_LIMIT", "model_calls": 0, "input_tokens": input_count,
                "output_tokens": 0, "text": None, "retry": False}
    # Historical query generation uses local fp16/eager; caller pins loading.
    import torch
    with torch.inference_mode():
        result = model.generate(**encoded.to(device), max_new_tokens=limits.output_tokens,
                                do_sample=False, num_beams=1, use_cache=True,
                                eos_token_id=eos_token_ids, pad_token_id=tokenizer.pad_token_id)
    if len(result.shape) != 2 or result.shape[0] != 1 or result.shape[1] < input_count:
        raise InputBoundaryError("unexpected generation output shape")
    if not torch.equal(result[0, :input_count].cpu(), encoded["input_ids"][0].cpu()):
        raise InputBoundaryError("generation did not preserve prompt prefix")
    generated = result[0, input_count:]
    output_count = len(generated)
    if output_count > limits.output_tokens:
        raise InputBoundaryError("model exceeded declared output token cap")
    text = tokenizer.decode(generated, skip_special_tokens=True)
    raw = text.encode("utf-8")
    finished = output_count > 0 and int(generated[-1]) in eos_token_ids
    status = "EOS_COMPLETE" if finished else "OUTPUT_LIMIT" if output_count >= limits.output_tokens else "NO_EOS"
    if len(raw) > limits.response_bytes:
        status = "RESPONSE_BYTE_LIMIT"
    return {"status": status, "model_calls": 1, "input_tokens": input_count, "output_tokens": output_count,
            "text": text, "response_sha256": hashlib.sha256(raw).hexdigest(), "retry": False}


def validate_generation(record: dict, *, kind: str, source: str, query_id: str, input_kind: str,
                        limits: GenerationLimits) -> dict:
    """No fence stripping, JSON salvage, retry or post-outcome output repair."""
    limits.validate()
    if record.get("status") != "EOS_COMPLETE" or type(record.get("text")) is not str:
        return {"status": "GENERATION_UNUSABLE", "anchor_fallback_required": kind in ("profile", "profile_quotes", "profile_tokens")}
    raw = record["text"].encode("utf-8")
    if len(raw) > limits.response_bytes or hashlib.sha256(raw).hexdigest() != record.get("response_sha256"):
        raise InputBoundaryError("response receipt content mismatch")
    if kind == "profile":
        profile = decode_json(raw)
        validation = validate_profile(profile, source=source, query_id=query_id, input_kind=input_kind)
        return {"status": "PROFILE_STRUCTURALLY_VALID", "profile": profile, "validation": validation,
                "semantic_status": "unknown"}
    if kind == "profile_quotes":
        aligned = align_quote_profile(decode_json(raw), source=source, query_id=query_id, input_kind=input_kind)
        return {"status": "QUOTE_PROFILE_STRUCTURALLY_VALID", **aligned, "semantic_status": "unknown"}
    if kind == 'profile_tokens':
        aligned = align_token_profile(decode_json(raw), source=source, query_id=query_id, input_kind=input_kind)
        return {'status': 'TOKEN_PROFILE_STRUCTURALLY_VALID', **aligned, 'semantic_status': 'unknown'}
    views = parse_view_response(raw, kind=kind, maximum_bytes=limits.response_bytes)
    return {"status": "VIEWS_STRUCTURALLY_VALID", "views": views, "semantic_status": "unknown"}


def run_reserved_attempt(destination: Path, *, messages, tokenizer, model, device, eos_token_ids,
                         limits: GenerationLimits) -> dict:
    """Exclusive private artifact directory. Interrupted reservations never resume.

    The outcome includes raw generated text; do not commit it to public Git.
    Validation/scoring are subsequent operations and cannot overwrite this attempt.
    """
    limits.validate()
    destination.mkdir(parents=True, exist_ok=False)
    raw = json.dumps(messages, ensure_ascii=False, sort_keys=True).encode("utf-8")
    def write(name, value):
        artifact = (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
        with (destination / name).open("xb") as handle:
            handle.write(artifact)
        return artifact
    write("reservation.json", {"status": "RESERVED", "messages_sha256": hashlib.sha256(raw).hexdigest(),
                                "limits": limits.__dict__, "retry": False})
    try:
        result = generate_once(messages=messages, tokenizer=tokenizer, model=model, device=device,
                               eos_token_ids=eos_token_ids, limits=limits)
        artifact = write("generation.json", result)
        # Import here to keep the record binder usable with GenerationLimits.
        from patent_to_pilot.research.sacr_generation_receipt import bind_generation_record
        binding = bind_generation_record(
            artifact, expected_sha256=hashlib.sha256(artifact).hexdigest(), limits=limits,
            metrics={key: result[key] for key in ("model_calls", "input_tokens", "output_tokens")})
        write("generation-binding.json", binding)
    except BaseException as error:
        write("failure.json", {"status": "FAILED_OR_INTERRUPTED", "exception_type": type(error).__name__,
                               "model_calls": "UNKNOWN", "retry": False})
        raise
    return result
