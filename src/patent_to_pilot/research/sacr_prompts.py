"""Deterministic prompt assembly only; no model call, tokenizer or hidden input."""
import hashlib
import json
from pathlib import Path

from patent_to_pilot.research.mtm_runtime import InputBoundaryError, identifier
from patent_to_pilot.research.sacr_profile import validate_profile
from patent_to_pilot.research.sacr_token_profile import source_catalogue, VERSION as TOKEN_VERSION

PROMPT_FILES = {"profile": "sacr_profile_v0.txt", "selective": "sacr_selective_v0.txt",
                "generic": "sacr_generic_views_v0.txt", "profile_quotes": "sacr_profile_quotes_v1.txt",
                "profile_tokens": "sacr_profile_tokens_v1.txt"}


def build_messages(*, prompt_root: Path, kind: str, query_id: str, input_kind: str,
                   source: str, profile=None, prompt_variant: str = "default") -> dict:
    if kind not in PROMPT_FILES or input_kind not in ("MTM_P", "DAPFAM_TA"):
        raise InputBoundaryError("unsupported generation contract")
    identifier(query_id)
    if type(source) is not str or not source.strip():
        raise InputBoundaryError("empty allowed query")
    if kind != "selective" and profile is not None:
        raise InputBoundaryError("profile forbidden for this prompt")
    root = prompt_root.resolve(strict=True)
    if prompt_variant not in ("default", "source_order_v2") or (prompt_variant != "default" and kind != "profile_quotes"):
        raise InputBoundaryError("unsupported prompt variant")
    filename = "sacr_profile_quotes_order_v2.txt" if prompt_variant == "source_order_v2" else PROMPT_FILES[kind]
    path = root / filename
    if path.is_symlink() or path.resolve().parent != root:
        raise InputBoundaryError("prompt path escapes declared root")
    raw = path.read_bytes()
    version = "sacr-profile-quotes-v1" if kind == "profile_quotes" else "sacr-profile-v0"
    if kind == 'profile_tokens':
        version = TOKEN_VERSION
    identity = {"profile_version": version, "query_id": query_id, "input_kind": input_kind,
                "source_sha256": hashlib.sha256(source.encode("utf-8")).hexdigest()}
    payload = {"identity": identity, "allowed_query": source}
    if kind == 'profile_tokens':
        payload['source_tokens'] = [[t['id'], t['text']] for t in source_catalogue(source)['tokens']]
    if kind == "selective":
        validation = validate_profile(profile, source=source, query_id=query_id, input_kind=input_kind)
        if validation["anchor_fallback_required"]:
            raise InputBoundaryError("unusable profile requires anchor fallback")
        payload["requirement_profile"] = profile
    messages = [{"role": "system", "content": raw.decode("utf-8")},
                {"role": "user", "content": json.dumps(payload, ensure_ascii=False, sort_keys=True)}]
    encoded = json.dumps(messages, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return {"messages": messages, "prompt_sha256": hashlib.sha256(raw).hexdigest(),
            "messages_sha256": hashlib.sha256(encoded).hexdigest(), "source_sha256": identity["source_sha256"],
            "semantic_status": "unknown", "generation": "NOT_RUN"}
