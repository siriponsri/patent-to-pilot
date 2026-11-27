"""Run the pinned E4b model on one GPU using only verified L1DEV inputs."""
import argparse
from datetime import datetime, timezone
from hashlib import file_digest, sha256
import json
from pathlib import Path
import sys
import time

import l1dev_protocol as spec
from loe_bench.llm_arm import build_prompt, parse_response


def verify_model(model, files):
    for item in files:
        path = model / item["name"]
        if path.stat().st_size != item["bytes"]:
            raise ValueError(f"model size mismatch: {path.name}")
        with path.open("rb") as source:
            if file_digest(source, "sha256").hexdigest() != item["sha256"]:
                raise ValueError(f"model digest mismatch: {path.name}")


def run(inputs, model_dir, work, plan, deadline):
    import torch
    import transformers

    if torch.cuda.device_count() != 1:
        raise ValueError("L1DEV requires exactly one visible GPU")
    if {"torch": torch.__version__, "transformers": transformers.__version__} != plan["runtime"]:
        raise ValueError("runtime differs from the pinned E4b environment")
    torch.manual_seed(spec.SEED)
    torch.cuda.set_per_process_memory_fraction(spec.MEMORY_FRACTION, 0)
    torch.cuda.reset_peak_memory_stats()
    started = time.monotonic()
    tokenizer = transformers.AutoTokenizer.from_pretrained(model_dir, local_files_only=True, padding_side="left")
    tokenizer.pad_token = tokenizer.eos_token
    model = transformers.AutoModelForCausalLM.from_pretrained(
        model_dir, torch_dtype=torch.float16, local_files_only=True).cuda().eval()
    load_seconds = time.monotonic() - started
    start_utc = datetime.now(timezone.utc).isoformat()
    inference_start = time.monotonic()
    status = "COMPLETE"
    count = valid = abstains = first_200_valid = 0
    output = work / "L1DEV_outputs.jsonl"
    with output.open("x", encoding="utf-8", newline="\n") as stream:
        for offset in range(0, len(inputs), spec.BATCH_SIZE):
            if time.time() >= deadline:
                status = "STOP_TIME_CAP"
                break
            batch = inputs[offset:offset + spec.BATCH_SIZE]
            prompts = []
            for row in batch:
                system, message = build_prompt(row)
                messages = [{"role": "system", "content": system}, {"role": "user", "content": message}]
                prompts.append(tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True,
                                                             enable_thinking=False))
            tokens = tokenizer(prompts, return_tensors="pt", padding=True, add_special_tokens=False).to("cuda")
            with torch.inference_mode():
                predicted = model.generate(**tokens, do_sample=False, num_beams=1,
                                           max_new_tokens=spec.MAX_NEW_TOKENS, pad_token_id=tokenizer.eos_token_id)
            texts = tokenizer.batch_decode(predicted[:, tokens.input_ids.shape[1]:], skip_special_tokens=True)
            for row, prompt, raw in zip(batch, prompts, texts, strict=True):
                parsed = parse_response(raw)
                record = {**row, **parsed, "prompt_sha256": sha256(prompt.encode()).hexdigest(), "raw_text": raw}
                stream.write(json.dumps(record, ensure_ascii=False, allow_nan=False) + "\n")
                count += 1
                valid += parsed["valid"]
                abstains += parsed["action"] == "ABSTAIN_REFER_TO_EVALUATOR"
            stream.flush()
            if count == spec.GATE_ROWS:
                first_200_valid = valid
                print(f"gate {valid}/{count}", flush=True)
                if valid < spec.MINIMUM_VALID:
                    status = "STOP_VALIDITY_GATE"
                    break
            if count % 400 == 0:
                print(f"progress {count}/{len(inputs)}; valid {valid}", flush=True)

    wall = time.monotonic() - inference_start
    with output.open("rb") as stream:
        digest = file_digest(stream, "sha256").hexdigest()
    summary = {"status": status, "n_rows": count, "n_planned": len(inputs), "valid_json": valid,
               "first_200_valid": first_200_valid, "abstains": abstains,
               "inference_started_utc": start_utc, "inference_finished_utc": datetime.now(timezone.utc).isoformat(),
               "inference_wall_s": wall, "rows_per_s": count / wall, "model_load_s": load_seconds,
               "input_sha256": plan["development_input"]["sha256"], "output_sha256": digest,
               "peak_vram_gib": torch.cuda.max_memory_allocated() / 2**30, "gpu": torch.cuda.get_device_name(0),
               "torch": torch.__version__, "transformers": transformers.__version__}
    (work / "L1DEV_summary.json").write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps(summary), flush=True)
    return 0 if status == "COMPLETE" else 2


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work", required=True, type=Path)
    parser.add_argument("--model", required=True, type=Path)
    parser.add_argument("--deadline", required=True, type=int, help="UTC epoch beyond which inference ends")
    args = parser.parse_args()
    config_path = args.work / "L1_FROZEN_CONFIG.json"
    config = json.loads(config_path.read_bytes())
    data = (args.work / "L1DEV_inputs.jsonl").read_bytes()
    rows = spec.validate_input(data, config["development_input"]["sha256"])
    if args.deadline <= time.time():
        raise ValueError("time cap reached before model verification")
    for name, digest in config["harness_lf_sha256"].items():
        if sha256((args.work / name).read_bytes().replace(b"\r\n", b"\n")).hexdigest() != digest:
            raise ValueError(f"harness digest mismatch: {name}")
    if spec.GATE_ROWS % spec.BATCH_SIZE:
        raise ValueError("batch size must reach the validity gate exactly")
    verify_model(args.model, config["model"]["files"])
    if time.time() >= args.deadline:
        raise ValueError("time cap reached during model verification")
    print("verified all staged model files", flush=True)
    return run(rows, args.model, args.work, config, args.deadline)


if __name__ == "__main__":
    sys.exit(main())
