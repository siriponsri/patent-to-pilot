"""One fixed synthetic Qwen engineering smoke; no benchmark or query-file input."""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import signal
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from patent_to_pilot.healthtech.local_execution import check_local_window, local_gpu_slot  # noqa: E402
from patent_to_pilot.research.mtm_runtime import InputBoundaryError  # noqa: E402
from patent_to_pilot.research.sacr_generation import GenerationLimits, run_reserved_attempt, validate_generation  # noqa: E402
from patent_to_pilot.research.sacr_prompts import build_messages  # noqa: E402

SOURCE = "Reduce reverse flow of liquid at low pressure without external electrical power."


def write(path, value):
    with path.open("x", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-root", type=Path, required=True)
    parser.add_argument("--identity", type=Path, required=True)
    parser.add_argument("--identity-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    check_local_window()
    if args.output.exists():
        raise InputBoundaryError("smoke output exists; no retry")
    raw = args.identity.read_bytes()
    if hashlib.sha256(raw).hexdigest() != args.identity_sha256:
        raise InputBoundaryError("identity receipt digest mismatch")
    expected = json.loads(raw)
    args.output.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    limits = GenerationLimits(input_tokens=8192, output_tokens=4096, context_tokens=40960, response_bytes=65536)
    write(args.output / "run-manifest.json", {"experiment": "SYNTHETIC_ENGINEERING_ONLY", "source": SOURCE,
          "source_sha256": hashlib.sha256(SOURCE.encode()).hexdigest(), "identity_sha256": args.identity_sha256,
          "limits": limits.__dict__, "maximum_calls": 3, "dtype": "float16", "attention": "eager",
          "visible_gpu": os.environ.get("CUDA_VISIBLE_DEVICES"), "retries": 0, "soft_deadline_seconds": 900})
    with (args.output / "status.log").open("x", encoding="utf-8", buffering=1) as status:
        status.write(datetime.now(timezone.utc).isoformat() + " START SYNTHETIC_SMOKE\n")
        def alarm(signum, frame):
            raise TimeoutError("declared smoke deadline reached")
        signal.signal(signal.SIGALRM, alarm)
        signal.alarm(900)
        try:
            spec = importlib.util.spec_from_file_location("qwen_identity", Path(__file__).with_name("inspect_qwen_weight_identity.py"))
            inspector = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(inspector)
            observed = inspector.observe(args.model_root)
            if observed["files"] != expected["files"]:
                raise InputBoundaryError("model files differ from pinned identity")
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer, GenerationConfig
            with local_gpu_slot(args.model_root):
                check_local_window()
                tokenizer = AutoTokenizer.from_pretrained(args.model_root, local_files_only=True)
                config = GenerationConfig.from_pretrained(args.model_root, local_files_only=True)
                config.update(do_sample=False, num_beams=1, max_new_tokens=limits.output_tokens, use_cache=True,
                              eos_token_id=[151645, 151643], pad_token_id=151643)
                config_raw = json.dumps(config.to_dict(), sort_keys=True, separators=(",", ":")).encode()
                config_hash = hashlib.sha256(config_raw).hexdigest()
                if config_hash != "20232bca268d86c6e4bad73eb53be74c881ad06e004eb0aaa6ddb5af831368ae":
                    raise InputBoundaryError("effective decoder differs from observed contract")
                load_start = time.monotonic()
                model = AutoModelForCausalLM.from_pretrained(args.model_root, local_files_only=True,
                    torch_dtype=torch.float16, device_map="cuda:0", low_cpu_mem_usage=True,
                    attn_implementation="eager").eval()
                model.generation_config = config
                torch.cuda.reset_peak_memory_stats()
                load_seconds = time.monotonic() - load_start
                outcomes, profile = [], None
                for kind in ("profile", "generic", "selective"):
                    check_local_window()
                    if kind == "selective" and profile is None:
                        outcomes.append({"kind": kind, "status": "SKIPPED_UNUSABLE_PROFILE", "model_calls": 0})
                        continue
                    prompt = build_messages(prompt_root=ROOT / "docs/healthtech/research/prompts", kind=kind,
                        source=SOURCE, query_id="synthetic-001", input_kind="MTM_P", profile=profile if kind == "selective" else None)
                    write(args.output / (kind + "-prompt-receipt.json"), {k:v for k,v in prompt.items() if k != "messages"})
                    call_start = time.monotonic()
                    record = run_reserved_attempt(args.output / kind, messages=prompt["messages"], tokenizer=tokenizer,
                        model=model, device="cuda:0", eos_token_ids=[151645,151643], limits=limits)
                    outcome = {k:v for k,v in record.items() if k != "text"}
                    outcome.update(kind=kind, seconds=round(time.monotonic()-call_start,3))
                    try:
                        validated = validate_generation(record, kind=kind, source=SOURCE, query_id="synthetic-001",
                                                         input_kind="MTM_P", limits=limits)
                        outcome["validation_status"] = validated["status"]
                        if kind == "profile" and validated.get("profile") is not None:
                            if not validated["validation"]["anchor_fallback_required"]:
                                profile = validated["profile"]
                    except (InputBoundaryError, ValueError, TypeError, KeyError):
                        outcome["validation_status"] = "INVALID_RESPONSE_PRESERVED"
                    outcomes.append(outcome)
                    write(args.output / (kind + "-outcome.json"), outcome)
                    status.write(datetime.now(timezone.utc).isoformat() + " COMPLETED " + kind + "\n")
                report = {"status": "SMOKE_COMPLETED_NOT_RESEARCH_VALIDATION", "outcomes": outcomes,
                    "model_load_seconds": round(load_seconds,3), "total_seconds": round(time.monotonic()-started,3),
                    "peak_gpu_allocated_bytes": torch.cuda.max_memory_allocated(),
                    "peak_gpu_reserved_bytes": torch.cuda.max_memory_reserved(),
                    "effective_decoder_sha256": config_hash, "torch": torch.__version__, "semantic_validation": "NOT_PERFORMED"}
                write(args.output / "summary.json", report)
            status.write(datetime.now(timezone.utc).isoformat() + " EXIT 0\n")
        except BaseException as error:
            write(args.output / "failure.json", {"status": "FAILED_OR_INTERRUPTED", "type": type(error).__name__,
                  "seconds": round(time.monotonic()-started,3), "retry": False})
            status.write(datetime.now(timezone.utc).isoformat() + " EXIT 1\n")
            raise
        finally:
            signal.alarm(0)


if __name__ == "__main__":
    main()
