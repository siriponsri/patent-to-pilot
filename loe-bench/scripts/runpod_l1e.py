"""Generate the frozen L1e messages on one RunPod GPU."""
import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import time

import l1dev_protocol as l1
import l1e_protocol as spec
from runpod_l1dev import verify_model
from loe_bench import l1e_prompt, llm_arm


def run(rows, model_dir, work, config, deadline):
    import torch
    import transformers

    if torch.cuda.device_count() != 1:
        raise ValueError("L1e requires exactly one visible GPU")
    if {"torch": torch.__version__, "transformers": transformers.__version__} != config["runtime"]:
        raise ValueError("runtime differs from L1")
    torch.manual_seed(l1.SEED)
    torch.cuda.set_per_process_memory_fraction(l1.MEMORY_FRACTION, 0)
    torch.cuda.reset_peak_memory_stats()
    started = time.monotonic()
    tokenizer = transformers.AutoTokenizer.from_pretrained(model_dir, local_files_only=True, padding_side="left")
    tokenizer.pad_token = tokenizer.eos_token
    model = transformers.AutoModelForCausalLM.from_pretrained(
        model_dir, torch_dtype=torch.float16, local_files_only=True).cuda().eval()
    model_load = time.monotonic() - started
    start_utc = datetime.now(timezone.utc).isoformat()
    started = time.monotonic()
    count = valid = abstains = first_200_valid = 0
    status = "COMPLETE"
    output = work / "L1E_outputs.jsonl"
    with output.open("x", encoding="utf-8", newline="\n") as stream:
        for offset in range(0, len(rows), l1.BATCH_SIZE):
            if time.time() >= deadline:
                status = "STOP_TIME_CAP"
                break
            batch = rows[offset:offset + l1.BATCH_SIZE]
            prompts = []
            for row in batch:
                system, user = l1e_prompt.build_prompt(row)
                messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
                prompts.append(tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True,
                                                             enable_thinking=False))
            tokens = tokenizer(prompts, return_tensors="pt", padding=True, add_special_tokens=False).to("cuda")
            with torch.inference_mode():
                predicted = model.generate(**tokens, do_sample=False, num_beams=1, max_new_tokens=l1.MAX_NEW_TOKENS,
                                           pad_token_id=tokenizer.eos_token_id)
            texts = tokenizer.batch_decode(predicted[:, tokens.input_ids.shape[1]:], skip_special_tokens=True)
            for row, prompt, raw in zip(batch, prompts, texts, strict=True):
                parsed = llm_arm.parse_response(raw)
                result = {**spec.identity(row), **parsed, "prompt_sha256": sha256(prompt.encode()).hexdigest(),
                          "raw_text": raw}
                stream.write(json.dumps(result, ensure_ascii=False, allow_nan=False) + "\n")
                count += 1
                valid += parsed["valid"]
                abstains += parsed["action"] == llm_arm.ACTIONS[-1]
            stream.flush()
            if count == l1.GATE_ROWS:
                first_200_valid = valid
                print(f"gate {valid}/{count}", flush=True)
                if valid < l1.MINIMUM_VALID:
                    status = "STOP_VALIDITY_GATE"
                    break
            if count % 400 == 0:
                print(f"progress {count}/{len(rows)}; valid {valid}", flush=True)

    elapsed = time.monotonic() - started
    summary = {"status": status, "n_rows": count, "n_planned": len(rows), "valid_json": valid,
               "first_200_valid": first_200_valid, "abstains": abstains, "start_utc": start_utc,
               "end_utc": datetime.now(timezone.utc).isoformat(), "inference_wall_s": elapsed,
               "model_load_s": model_load, "peak_vram_gib": torch.cuda.max_memory_allocated() / 2**30,
               "gpu": torch.cuda.get_device_name(0), "runtime": config["runtime"],
               "input_sha256": config["development_input"]["sha256"],
               "output_sha256": sha256(output.read_bytes()).hexdigest()}
    (work / "L1E_summary.json").write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps(summary), flush=True)
    return 0 if status == "COMPLETE" else 2


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work", required=True, type=Path)
    parser.add_argument("--model", required=True, type=Path)
    parser.add_argument("--deadline", required=True, type=int)
    args = parser.parse_args()
    config = json.loads((args.work / "L1E_FROZEN_CONFIG.json").read_bytes())
    if config["status"] != "FROZEN_FOR_DEVELOPMENT_RUN":
        raise ValueError("use the pre-inference freeze for the runner")
    for name, digest in config["harness_lf_sha256"].items():
        if sha256((args.work / name).read_bytes().replace(b"\r\n", b"\n")).hexdigest() != digest:
            raise ValueError(f"harness digest mismatch: {name}")
    rows = spec.verify_input((args.work / "L1E_inputs.jsonl").read_bytes(), config)
    if time.time() >= args.deadline:
        raise ValueError("deadline reached before model verification")
    verify_model(args.model, config["model"]["files"])
    if time.time() >= args.deadline:
        raise ValueError("deadline reached during model verification")
    print("verified all staged model files", flush=True)
    return run(rows, args.model, args.work, config, args.deadline)


if __name__ == "__main__":
    raise SystemExit(main())
