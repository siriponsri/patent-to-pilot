"""Run one bounded local Qwen3 generation canary on the owned V100."""
from __future__ import annotations

import hashlib
import json
import os
import platform
import resource
import time
from pathlib import Path

import psutil
import torch
import transformers
from transformers import AutoModelForCausalLM, AutoTokenizer


MODEL_ROOT = Path(os.environ.get(
    "HT_REMOTE_QWEN_ROOT",
    "/home/chaw/patent-to-pilot-jobs/research-product-o1-o4-20261031/models/qwen3-8b",
))
OUTPUT_PATH = Path(os.environ.get(
    "HT_REMOTE_QWEN_OUTPUT",
    "/home/chaw/patent-to-pilot-jobs/research-product-o1-o4-20261031/outputs/qwen3-local-canary-20261031.json",
))
APPROVED_GPU_UUID = "GPU-277ccc57-c3e5-0731-cd49-f4f8695f7089"


def main() -> int:
    if not torch.cuda.is_available() or torch.cuda.device_count() != 1:
        raise RuntimeError("expected exactly one visible CUDA device")
    torch.set_num_threads(8)
    device_name = torch.cuda.get_device_name(0)
    if "V100" not in device_name:
        raise RuntimeError(f"unexpected visible GPU: {device_name}")

    torch.cuda.reset_peak_memory_stats()
    messages = [{
        "role": "user",
        "content": (
            "CANARY ONLY. Given this synthetic evidence: device=DemoClip; "
            "source=synthetic://canary; locator=paragraph-1; fact=demo. "
            "Return exactly one JSON object with keys source, locator, "
            "evidence_type, and unresolved. Do not add explanation."
        ),
    }]

    load_started = time.perf_counter()
    tokenizer = AutoTokenizer.from_pretrained(
        MODEL_ROOT,
        local_files_only=True,
        trust_remote_code=False,
    )
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_ROOT,
        local_files_only=True,
        trust_remote_code=False,
        torch_dtype=torch.float16,
        device_map="cuda:0",
        low_cpu_mem_usage=True,
        attn_implementation="eager",
    )
    model.eval()
    load_seconds = time.perf_counter() - load_started

    encoded = tokenizer.apply_chat_template(
        messages,
        tokenize=True,
        add_generation_prompt=True,
        return_tensors="pt",
        return_dict=True,
        enable_thinking=False,
    )
    if hasattr(encoded, "items"):
        inputs = {key: value.to("cuda:0") for key, value in encoded.items()}
    else:
        inputs = {
            "input_ids": encoded.to("cuda:0"),
            "attention_mask": torch.ones_like(encoded, device="cuda:0"),
        }
    prompt_tokens = int(inputs["input_ids"].shape[-1])

    generation_started = time.perf_counter()
    with torch.inference_mode():
        generated = model.generate(
            **inputs,
            max_new_tokens=128,
            do_sample=False,
            use_cache=True,
            pad_token_id=tokenizer.eos_token_id,
        )
    latency_seconds = time.perf_counter() - generation_started
    output_tokens = generated[:, prompt_tokens:]
    text = tokenizer.batch_decode(output_tokens, skip_special_tokens=True)[0].strip()
    output_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
    try:
        parsed = json.loads(text)
        schema_valid = isinstance(parsed, dict) and set(parsed) == {
            "source",
            "locator",
            "evidence_type",
            "unresolved",
        }
    except json.JSONDecodeError:
        schema_valid = False

    rss_peak_bytes = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024)
    receipt = {
        "status": "PASS_LOCAL_QWEN3_GENERATION_CANARY" if schema_valid else "PASS_GENERATION_SCHEMA_REJECTED",
        "model_id": "Qwen/Qwen3-8B",
        "model_revision": "b968826d9c46dd6066d109eabc6255188de91218",
        "license": "apache-2.0",
        "python": platform.python_version(),
        "torch": torch.__version__,
        "transformers": transformers.__version__,
        "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES"),
        "approved_gpu_uuid": APPROVED_GPU_UUID,
        "visible_gpu_count": int(torch.cuda.device_count()),
        "visible_gpu_name": device_name,
        "torch_threads": torch.get_num_threads(),
        "dtype": "float16",
        "attention": "eager",
        "thinking": False,
        "prompt_tokens": prompt_tokens,
        "output_tokens": int(output_tokens.shape[-1]),
        "load_seconds": load_seconds,
        "generation_latency_seconds": latency_seconds,
        "rss_peak_bytes": rss_peak_bytes,
        "gpu_peak_allocated_bytes": int(torch.cuda.max_memory_allocated()),
        "gpu_peak_reserved_bytes": int(torch.cuda.max_memory_reserved()),
        "output_sha256": output_hash,
        "schema_valid": schema_valid,
        "output_text": text,
        "provider_calls": 0,
        "paid_cost_usd": 0.0,
    }
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in receipt.items() if key != "output_text"}, ensure_ascii=False))
    return 0 if schema_valid else 2


if __name__ == "__main__":
    raise SystemExit(main())
