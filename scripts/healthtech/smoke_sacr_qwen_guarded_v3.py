"""SYN-SACR-003 guarded quote-profile regression; no benchmark or query-file input."""
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
    parser.add_argument("--grammar-payload", type=Path, required=True)
    parser.add_argument("--grammar-declaration", type=Path, required=True)
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
    write(args.output / "run-manifest.json", {"experiment": "SYN-SACR-003_GUARDED_QUOTES_ENGINEERING_ONLY", "source": SOURCE,
          "source_sha256": hashlib.sha256(SOURCE.encode()).hexdigest(), "identity_sha256": args.identity_sha256,
          "limits": limits.__dict__, "maximum_calls": 1, "dtype": "float16", "attention": "eager",
          "visible_gpu": os.environ.get("CUDA_VISIBLE_DEVICES"), "retries": 0, "soft_deadline_seconds": 1740})
    with (args.output / "status.log").open("x", encoding="utf-8", buffering=1) as status:
        status.write(datetime.now(timezone.utc).isoformat() + " START SYNTHETIC_SMOKE\n")
        def alarm(signum, frame):
            raise TimeoutError("declared smoke deadline reached")
        signal.signal(signal.SIGALRM, alarm)
        signal.alarm(1740)
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
                from jsonschema import Draft202012Validator
                from lmformatenforcer import CharacterLevelParserConfig
                from lmformatenforcer.integrations.transformers import build_token_enforcer_tokenizer_data
                from patent_to_pilot.research.sacr_alphabet import build_alphabet
                from patent_to_pilot.research.sacr_escape_callback import build_escape_callback
                from patent_to_pilot.research.sacr_grammar_guard import CompleteJsonEOSGuard
                payload_raw = args.grammar_payload.read_bytes()
                grammar_declaration = json.loads(args.grammar_declaration.read_bytes())
                if hashlib.sha256(payload_raw).hexdigest() != grammar_declaration['payload_sha256']:
                    raise InputBoundaryError('grammar payload identity mismatch')
                payload = json.loads(payload_raw)
                if payload['source'] != SOURCE:
                    raise InputBoundaryError('authored source differs from CPU gate')
                validator = Draft202012Validator(payload['schema'])
                token_data = build_token_enforcer_tokenizer_data(tokenizer)
                alphabet = build_alphabet(tokenizer, SOURCE)
                parser_config = CharacterLevelParserConfig(alphabet=alphabet['alphabet'],
                    max_consecutive_whitespaces=4096, force_json_field_order=False, max_json_array_length=4096)
                loaded_model = model
                class GuardedModel:
                    def generate(self, **kwargs):
                        callback = build_escape_callback(token_data, payload['schema'], parser_config,
                            expected_source_sha256=grammar_declaration['lmfe_source_sha256'])
                        if callback.configuration_receipt['requested'] != callback.configuration_receipt['effective_root']:
                            raise InputBoundaryError('effective grammar configuration differs')
                        write(args.output / 'grammar-config.json', callback.configuration_receipt)
                        guard = CompleteJsonEOSGuard(prefix_fn=callback, tokenizer=tokenizer,
                            prompt_tokens=int(kwargs['input_ids'].shape[1]),
                            eos_token_ids=[151645,151643], validate=validator.validate)
                        return loaded_model.generate(**kwargs, prefix_allowed_tokens_fn=guard)
                model = GuardedModel()
                write(args.output / 'loaded-runtime.json', {'torch': torch.__version__,
                    'python': sys.version.split()[0], 'model_class': type(loaded_model).__name__,
                    'tokenizer_class': type(tokenizer).__name__, 'model_dtype': str(loaded_model.dtype),
                    'model_device': str(loaded_model.device), 'attention': loaded_model.config._attn_implementation,
                    'model_files_match': observed['files'] == expected['files'],
                    'decoder_sha256': config_hash, 'grammar_payload_sha256': grammar_declaration['payload_sha256'],
                    'model_load_seconds': load_seconds})
                outcomes, profile = [], None
                for kind in ("profile_quotes",):
                    check_local_window()
                    if kind == "selective" and profile is None:
                        outcomes.append({"kind": kind, "status": "SKIPPED_UNUSABLE_PROFILE", "model_calls": 0})
                        continue
                    prompt = build_messages(prompt_root=ROOT / "docs/healthtech/research/prompts", kind=kind,
                        source=SOURCE, query_id="q1", input_kind="MTM_P", profile=profile if kind == "selective" else None)
                    write(args.output / (kind + "-prompt-receipt.json"), {k:v for k,v in prompt.items() if k != "messages"})
                    call_start = time.monotonic()
                    record = run_reserved_attempt(args.output / kind, messages=prompt["messages"], tokenizer=tokenizer,
                        model=model, device="cuda:0", eos_token_ids=[151645,151643], limits=limits)
                    outcome = {k:v for k,v in record.items() if k != "text"}
                    outcome.update(kind=kind, seconds=round(time.monotonic()-call_start,3))
                    try:
                        validated = validate_generation(record, kind=kind, source=SOURCE, query_id="q1",
                                                         input_kind="MTM_P", limits=limits)
                        outcome["validation_status"] = validated["status"]
                        if kind == "profile_quotes" and validated.get("profile") is not None:
                            if not validated["validation"]["anchor_fallback_required"]:
                                profile = validated["profile"]
                                write(args.output / "canonical-profile.json", validated["profile"])
                                outcome["profile_validation"] = validated["validation"]
                                outcome["alignment"] = validated["alignment"]
                    except (InputBoundaryError, ValueError, TypeError, KeyError):
                        outcome["validation_status"] = "INVALID_RESPONSE_PRESERVED"
                    outcomes.append(outcome)
                    write(args.output / (kind + "-outcome.json"), outcome)
                    status.write(datetime.now(timezone.utc).isoformat() + " COMPLETED " + kind + "\n")
                report = {"status": "SMOKE_COMPLETED_NOT_RESEARCH_VALIDATION", "outcomes": outcomes,
                    "model_load_seconds": round(load_seconds,3), "total_seconds": round(time.monotonic()-started,3),
                    "peak_gpu_allocated_bytes": torch.cuda.max_memory_allocated(),
                    "peak_gpu_reserved_bytes": torch.cuda.max_memory_reserved(),
                    "effective_decoder_sha256": config_hash, "torch": torch.__version__, "semantic_validation": "NOT_PERFORMED",
                    "engineering_pass": profile is not None and len(outcomes) == 1 and outcomes[0]["status"] == "EOS_COMPLETE"}
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
