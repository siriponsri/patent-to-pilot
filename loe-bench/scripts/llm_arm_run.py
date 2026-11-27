"""Remote runner for the T10 LLM arm: JSONL in -> JSONL out. Greedy, seed fixed, one job under the shared GPU lock.

Usage (dr-train): CUDA_VISIBLE_DEVICES=1 python llm_arm_run.py --model DIR --inp rows.jsonl --out out.jsonl --summary s.json
Input rows: {entity, t0, horizon_months, [rule_baseline]}. No outcome labels are read or written.
"""
import argparse
import fcntl
import hashlib
import json
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from loe_bench.llm_arm import build_prompt, parse_response  # noqa: E402

LOCK = ("/home/chaw/patent-to-pilot-jobs/research-product-o1-o4-20261031/models/"
        ".GPU-277ccc57-c3e5-0731-cd49-f4f8695f7089.lock")
SEED = 20261127


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--inp", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--summary", required=True)
    ap.add_argument("--mem-frac", type=float, default=0.12)
    ap.add_argument("--max-new", type=int, default=160)
    ap.add_argument("--limit", type=int, default=20)
    a = ap.parse_args()
    assert os.environ.get("CUDA_VISIBLE_DEVICES") == "1", "V100 only: CUDA_VISIBLE_DEVICES=1"
    import torch
    lockf = open(LOCK, "a")
    t = time.time()
    fcntl.flock(lockf, fcntl.LOCK_EX)
    print("GPU lock acquired after %.1fs" % (time.time() - t), flush=True)
    torch.cuda.set_per_process_memory_fraction(a.mem_frac, 0)
    print("device", torch.cuda.get_device_name(0), "mem_frac", a.mem_frac, flush=True)
    torch.manual_seed(SEED)
    from transformers import AutoModelForCausalLM, AutoTokenizer
    tok = AutoTokenizer.from_pretrained(a.model)
    model = AutoModelForCausalLM.from_pretrained(a.model, torch_dtype=torch.float16).cuda().eval()
    rows = [json.loads(l) for l in open(a.inp, encoding="utf-8") if l.strip()][: a.limit]
    results, lat = [], []
    torch.cuda.reset_peak_memory_stats()
    for r in rows:
        sysm, user = build_prompt(r)
        msgs = [{"role": "system", "content": sysm}, {"role": "user", "content": user}]
        try:
            prompt = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True, enable_thinking=False)
        except TypeError:
            prompt = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
        ids = tok(prompt, return_tensors="pt").to("cuda")
        torch.cuda.synchronize()
        t0 = time.time()
        with torch.no_grad():
            g = model.generate(**ids, do_sample=False, max_new_tokens=a.max_new, pad_token_id=tok.eos_token_id)
        torch.cuda.synchronize()
        dt = time.time() - t0
        text = tok.decode(g[0][ids["input_ids"].shape[1]:], skip_special_tokens=True)
        res = parse_response(text)
        res.update(entity=r["entity"], t0=r["t0"], horizon_months=r["horizon_months"], latency_s=round(dt, 3),
                   prompt_sha256=hashlib.sha256(prompt.encode()).hexdigest(), raw_text=text[:600])
        results.append(res)
        lat.append(dt)
    with open(a.out, "w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    n = len(results)
    summ = {"model_dir": a.model, "n_rows": n, "valid_json_rate": sum(r["valid"] for r in results) / max(n, 1),
            "abstain_rate": sum(r["action"] == "ABSTAIN_REFER_TO_EVALUATOR" for r in results) / max(n, 1),
            "latency_s_mean": sum(lat) / max(n, 1), "latency_s_max": max(lat) if lat else None,
            "peak_vram_gib": torch.cuda.max_memory_allocated() / 2**30, "mem_frac": a.mem_frac,
            "decoding": "greedy, do_sample=False, max_new=%d, seed=%d" % (a.max_new, SEED),
            "torch": torch.__version__, "gpu": torch.cuda.get_device_name(0)}
    import transformers
    summ["transformers"] = transformers.__version__
    json.dump(summ, open(a.summary, "w"), indent=1)
    print(json.dumps(summ), flush=True)


if __name__ == "__main__":
    main()
