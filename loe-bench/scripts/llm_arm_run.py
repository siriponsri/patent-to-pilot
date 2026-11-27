"""Remote runner for the T10 LLM arm: JSONL in -> JSONL out. Greedy, seed fixed, one job under the shared GPU lock.

Usage (dr-train): CUDA_VISIBLE_DEVICES=1 python llm_arm_run.py --model DIR --inp rows.jsonl --out out.jsonl --summary s.json
Input rows: {entity, t0, horizon_months, [rule_baseline]}. No outcome labels are read or written.
On a dedicated one-GPU RunPod pod, pass --runpod. For the E4b smoke, pass --min-valid-rate 0.90.
"""
import argparse
import fcntl
import hashlib
import json
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from loe_bench.llm_arm import ALLOWED_FEATURES, build_prompt, parse_response  # noqa: E402

LOCK = ("/home/chaw/patent-to-pilot-jobs/research-product-o1-o4-20261031/models/"
        ".GPU-277ccc57-c3e5-0731-cd49-f4f8695f7089.lock")
SEED = 20261127


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--inp", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--summary", required=True)
    ap.add_argument("--runpod", action="store_true")
    ap.add_argument("--mem-frac", type=float)
    ap.add_argument("--max-new", type=int, default=160)
    ap.add_argument("--limit", type=int, default=20)
    ap.add_argument("--min-valid-rate", type=float)
    a = ap.parse_args()
    if a.mem_frac is None:
        a.mem_frac = 0.90 if a.runpod else 0.12
    if not 0 < a.mem_frac <= 1 or a.limit < 1 or a.max_new < 1:
        ap.error("require a memory fraction in (0, 1] and positive row and token limits")
    if a.min_valid_rate is not None and not 0 <= a.min_valid_rate <= 1:
        ap.error("minimum valid rate must be in [0, 1]")
    if not a.runpod and os.environ.get("CUDA_VISIBLE_DEVICES") != "1":
        ap.error("V100 only: CUDA_VISIBLE_DEVICES=1")
    with open(a.inp, encoding="utf-8") as source:
        from itertools import islice
        rows = [json.loads(line) for line in islice((line for line in source if line.strip()), a.limit)]
    if not rows:
        ap.error("input has no rows")
    allowed = {"entity", "t0", "horizon_months", *ALLOWED_FEATURES}
    if a.runpod and any(not isinstance(row, dict) or row.keys() - allowed for row in rows):
        ap.error("RunPod input must contain only label-free forecast fields")
    prompts = [build_prompt(row) for row in rows]
    import torch
    if a.runpod and torch.cuda.device_count() != 1:
        ap.error("RunPod requires exactly one visible GPU")
    with open("/tmp/loe-bench-runpod-gpu.lock" if a.runpod else LOCK, "a") as lock:
        t = time.monotonic()
        fcntl.flock(lock, fcntl.LOCK_EX)
        print("GPU lock acquired after %.1fs" % (time.monotonic() - t), flush=True)
        return run(a, rows, prompts, torch)


def run(a, rows, prompts, torch):
    torch.cuda.set_per_process_memory_fraction(a.mem_frac, 0)
    print("device", torch.cuda.get_device_name(0), "mem_frac", a.mem_frac, flush=True)
    torch.manual_seed(SEED)
    from transformers import AutoModelForCausalLM, AutoTokenizer
    torch.cuda.reset_peak_memory_stats()
    started = time.monotonic()
    tok = AutoTokenizer.from_pretrained(a.model, local_files_only=a.runpod)
    model = AutoModelForCausalLM.from_pretrained(
        a.model, torch_dtype=torch.float16, local_files_only=a.runpod,
    ).cuda().eval()
    load_seconds = time.monotonic() - started
    results, lat = [], []
    valid_count = 0
    stopped_early = False
    for r, (sysm, user) in zip(rows, prompts):
        t0 = time.monotonic()
        msgs = [{"role": "system", "content": sysm}, {"role": "user", "content": user}]
        try:
            prompt = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True, enable_thinking=False)
        except TypeError:
            prompt = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
        ids = tok(prompt, return_tensors="pt", add_special_tokens=False).to("cuda")
        with torch.no_grad():
            g = model.generate(**ids, do_sample=False, max_new_tokens=a.max_new, pad_token_id=tok.eos_token_id)
        torch.cuda.synchronize()
        text = tok.decode(g[0][ids["input_ids"].shape[1]:], skip_special_tokens=True)
        res = parse_response(text)
        dt = time.monotonic() - t0
        res.update(entity=r["entity"], t0=r["t0"], horizon_months=r["horizon_months"], latency_s=round(dt, 3),
                   prompt_sha256=hashlib.sha256(prompt.encode()).hexdigest(), raw_text=text[:600])
        results.append(res)
        lat.append(dt)
        valid_count += res["valid"]
        if a.min_valid_rate is not None and valid_count / len(results) < a.min_valid_rate:
            stopped_early = True
            break
    with open(a.out, "w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    n = len(results)
    summ = {"model_dir": a.model, "n_rows": n, "n_planned": len(rows), "valid_json_rate": valid_count / n,
            "stopped_below_min_valid_rate": stopped_early, "model_load_s": load_seconds,
            "abstain_rate": sum(r["action"] == "ABSTAIN_REFER_TO_EVALUATOR" for r in results) / max(n, 1),
            "latency_s_mean": sum(lat) / max(n, 1), "latency_s_max": max(lat) if lat else None,
            "peak_vram_gib": torch.cuda.max_memory_allocated() / 2**30,
            "peak_reserved_vram_gib": torch.cuda.max_memory_reserved() / 2**30, "mem_frac": a.mem_frac,
            "decoding": "greedy, do_sample=False, max_new=%d, seed=%d" % (a.max_new, SEED),
            "torch": torch.__version__, "gpu": torch.cuda.get_device_name(0)}
    import transformers
    summ["transformers"] = transformers.__version__
    with open(a.summary, "w", encoding="utf-8") as summary:
        json.dump(summ, summary, indent=1)
    print(json.dumps(summ), flush=True)
    return 2 if stopped_early else 0


if __name__ == "__main__":
    sys.exit(main())
