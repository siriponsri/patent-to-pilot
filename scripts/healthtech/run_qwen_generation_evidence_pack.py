"""Run deterministic local Qwen generation over a frozen evidence pack."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import resource
import time
from typing import Any

import torch
import transformers
from transformers import AutoModelForCausalLM, AutoTokenizer


APPROVED_GPU_UUID = "GPU-277ccc57-c3e5-0731-cd49-f4f8695f7089"
MODEL_ID = "Qwen/Qwen3-8B"
MODEL_REVISION = "b968826d9c46dd6066d109eabc6255188de91218"


def _canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _read_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _load_pack(path: Path) -> dict[str, Any]:
    pack = _read_object(path)
    claimed_hash = pack.get("pack_sha256")
    if not isinstance(claimed_hash, str):
        raise ValueError("pack lacks pack_sha256")
    unsigned = dict(pack)
    unsigned.pop("pack_sha256", None)
    if _sha256_bytes(_canonical_json(unsigned)) != claimed_hash:
        raise ValueError("pack_sha256 mismatch")
    if pack.get("format") != "ht-o3-qwen3-frozen-evidence-pack-v1":
        raise ValueError("unexpected evidence pack format")
    if pack.get("model_condition", {}).get("model_revision") != MODEL_REVISION:
        raise ValueError("pack model revision mismatch")
    if pack.get("model_condition", {}).get("thinking") is not False:
        raise ValueError("pack must freeze non-thinking condition")
    cases = pack.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("pack has no cases")
    return pack


def _strip_fence(text: str) -> str:
    text = text.strip()
    if text.startswith("```") and text.endswith("```"):
        lines = text.splitlines()
        if len(lines) >= 3:
            return "\n".join(lines[1:-1]).strip()
    return text


def _validate_output(parsed: Any, case: dict[str, Any], max_findings: int) -> None:
    if not isinstance(parsed, dict) or set(parsed) != {"device_id", "device_name", "findings", "unresolved"}:
        raise ValueError("output keys do not match frozen schema")
    if parsed["device_id"] != case["query"]["device_id_canonical"]:
        raise ValueError("device_id does not match case")
    if not isinstance(parsed["device_name"], str):
        raise ValueError("device_name is not a string")
    findings = parsed["findings"]
    if not isinstance(findings, list) or len(findings) > max_findings:
        raise ValueError("findings violates maxItems")
    evidence_by_id = {row["evidence_id"]: row for row in case["evidence"]}
    candidate_by_id = {row["patent_id_canonical"]: row for row in case["candidates"]}
    allowed_types = {"source_fact", "disclosed_link", "retrieved_candidate", "unresolved"}
    for finding in findings:
        if not isinstance(finding, dict):
            raise ValueError("finding is not an object")
        required = {
            "record_type",
            "record_id",
            "source_id",
            "locator",
            "classification",
            "summary",
            "support_basis",
        }
        if set(finding) != required:
            raise ValueError("finding keys do not match frozen schema")
        if finding["record_type"] == "evidence":
            row = evidence_by_id.get(finding["record_id"])
            if row is None:
                raise ValueError("finding references unknown evidence_id")
            if finding["source_id"] != row["source_id"] or finding["locator"] != row["locator"]:
                raise ValueError("evidence source_id/locator mismatch")
        elif finding["record_type"] == "candidate":
            row = candidate_by_id.get(finding["record_id"])
            if row is None:
                raise ValueError("finding references unknown candidate")
            if finding["source_id"] != row["source_id"] or finding["locator"] != row["locator"]:
                raise ValueError("candidate source_id/locator mismatch")
        else:
            raise ValueError("unknown record_type")
        if finding["classification"] not in allowed_types:
            raise ValueError("unknown classification")
        if not isinstance(finding["summary"], str) or not isinstance(finding["support_basis"], str):
            raise ValueError("finding text fields are not strings")
    if not isinstance(parsed["unresolved"], list) or any(not isinstance(item, str) for item in parsed["unresolved"]):
        raise ValueError("unresolved must be a string array")


def _build_messages(pack: dict[str, Any], case: dict[str, Any]) -> list[dict[str, str]]:
    contract = pack["prompt_contract"]
    system_text = "\n".join(contract["system_instructions"])
    query = case["query"]
    compact_evidence = []
    for row in case["evidence"]:
        compact_row = dict(row)
        value = compact_row.get("structured_value")
        if isinstance(value, list) and len(value) > 8:
            compact_row["structured_value"] = {
                "count": len(value),
                "values_omitted_from_model_view": True,
            }
        compact_evidence.append(compact_row)
    compact_case = {
        "case_id": case["case_id"],
        "query": {
            key: query.get(key)
            for key in (
                "query_id",
                "device_id_canonical",
                "device_id_raw",
                "jurisdiction",
                "brief",
                "technical_description",
                "features_of_interest",
                "user_questions",
                "evidence_cutoff",
            )
        },
        "evidence": compact_evidence,
        "candidates": [
            {
                key: candidate.get(key)
                for key in (
                    "rank",
                    "association_status",
                    "disclosure_evidence_id",
                    "patent_id_canonical",
                    "patent_id_raw",
                    "source_id",
                    "source_revision",
                    "locator",
                )
            }
            for candidate in case["candidates"][:6]
        ],
        "candidate_preview": "first six candidates only; complete ordered candidate list remains in the frozen pack",
        "unresolved_items": case.get("unresolved_items", [])[:1],
    }
    compact_schema = (
        "Return one JSON object with exactly these top-level keys: device_id, device_name, findings, unresolved. "
        "Each finding must have exactly: record_type, record_id, source_id, locator, classification, summary, support_basis. "
        "record_type is evidence or candidate; classification is source_fact, disclosed_link, retrieved_candidate, or unresolved. "
        "Use exact IDs and locators from the case. unresolved must contain zero or one concise string."
    )
    user_payload = {
        "task": "Extract an auditable evidence summary for one named device.",
        "output_schema": compact_schema,
        "case": compact_case,
    }
    return [
        {"role": "system", "content": system_text},
        {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False, sort_keys=True)},
    ]


def run_generation(pack: dict[str, Any], model_root: Path, output_path: Path, max_new_tokens: int, max_findings: int) -> dict[str, Any]:
    if not torch.cuda.is_available() or torch.cuda.device_count() != 1:
        raise RuntimeError("expected exactly one visible CUDA device")
    device_name = torch.cuda.get_device_name(0)
    if "V100" not in device_name:
        raise RuntimeError(f"unexpected visible GPU: {device_name}")
    visible = os.environ.get("CUDA_VISIBLE_DEVICES")
    if visible not in {APPROVED_GPU_UUID, "1"}:
        raise RuntimeError("CUDA_VISIBLE_DEVICES is not bound to the approved GPU")
    torch.set_num_threads(8)
    torch.cuda.reset_peak_memory_stats()
    load_started = time.perf_counter()
    tokenizer = AutoTokenizer.from_pretrained(model_root, local_files_only=True, trust_remote_code=False)
    model = AutoModelForCausalLM.from_pretrained(
        model_root,
        local_files_only=True,
        trust_remote_code=False,
        torch_dtype=torch.float16,
        device_map="cuda:0",
        low_cpu_mem_usage=True,
        attn_implementation="eager",
    )
    model.eval()
    load_seconds = time.perf_counter() - load_started
    case_receipts = []
    for case in pack["cases"]:
        messages = _build_messages(pack, case)
        encoded = tokenizer.apply_chat_template(
            messages,
            tokenize=True,
            add_generation_prompt=True,
            return_tensors="pt",
            return_dict=True,
            enable_thinking=False,
        )
        inputs = {key: value.to("cuda:0") for key, value in encoded.items()}
        prompt_tokens = int(inputs["input_ids"].shape[-1])
        generation_started = time.perf_counter()
        with torch.inference_mode():
            generated = model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=False,
                use_cache=True,
                pad_token_id=tokenizer.eos_token_id,
            )
        latency_seconds = time.perf_counter() - generation_started
        output_tokens = generated[:, prompt_tokens:]
        output_text = tokenizer.batch_decode(output_tokens, skip_special_tokens=True)[0].strip()
        output_hash = _sha256_bytes(output_text.encode("utf-8"))
        schema_valid = False
        parse_error = None
        parsed: Any = None
        try:
            parsed = json.loads(_strip_fence(output_text))
            _validate_output(parsed, case, max_findings=max_findings)
            schema_valid = True
        except (json.JSONDecodeError, ValueError) as exc:
            parse_error = str(exc)
        case_receipts.append({
            "case_id": case["case_id"],
            "prompt_tokens": prompt_tokens,
            "output_tokens": int(output_tokens.shape[-1]),
            "generation_latency_seconds": latency_seconds,
            "output_sha256": output_hash,
            "schema_valid": schema_valid,
            "parse_error": parse_error,
            "output_text": output_text,
            "parsed_output": parsed,
        })
    receipt = {
        "status": "PASS_LOCAL_QWEN3_FROZEN_PACK_GENERATION" if all(item["schema_valid"] for item in case_receipts) else "PARTIAL_LOCAL_QWEN3_FROZEN_PACK_GENERATION",
        "model_id": MODEL_ID,
        "model_revision": MODEL_REVISION,
        "license": "apache-2.0",
        "pack_sha256": pack["pack_sha256"],
        "python": platform.python_version(),
        "torch": torch.__version__,
        "transformers": transformers.__version__,
        "cuda_visible_devices": visible,
        "approved_gpu_uuid": APPROVED_GPU_UUID,
        "visible_gpu_count": int(torch.cuda.device_count()),
        "visible_gpu_name": device_name,
        "torch_threads": torch.get_num_threads(),
        "dtype": "float16",
        "attention": "eager",
        "thinking": False,
        "load_seconds": load_seconds,
        "gpu_peak_allocated_bytes": int(torch.cuda.max_memory_allocated()),
        "gpu_peak_reserved_bytes": int(torch.cuda.max_memory_reserved()),
        "rss_peak_bytes": int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024),
        "provider_calls": 0,
        "paid_cost_usd": 0.0,
        "cases": case_receipts,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pack", type=Path, required=True)
    parser.add_argument("--model-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--max-new-tokens", type=int, default=512)
    parser.add_argument("--max-findings", type=int, default=4)
    args = parser.parse_args()
    pack = _load_pack(args.pack)
    receipt = run_generation(pack, args.model_root, args.output, args.max_new_tokens, args.max_findings)
    print(json.dumps({key: value for key, value in receipt.items() if key != "cases"}, ensure_ascii=False))
    print(json.dumps({
        "cases": [
            {
                "case_id": item["case_id"],
                "schema_valid": item["schema_valid"],
                "prompt_tokens": item["prompt_tokens"],
                "output_tokens": item["output_tokens"],
                "output_sha256": item["output_sha256"],
            }
            for item in receipt["cases"]
        ]
    }, ensure_ascii=False))
    return 0 if receipt["status"] == "PASS_LOCAL_QWEN3_FROZEN_PACK_GENERATION" else 2


if __name__ == "__main__":
    raise SystemExit(main())
