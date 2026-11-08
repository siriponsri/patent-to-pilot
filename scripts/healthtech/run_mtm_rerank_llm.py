"""MTM dev phase 2, methods-log entry V4: Qwen3-8B pointwise yes/no scores for the baseline lane-X top 30.

For each (query, candidate) pair, one forward pass scores the first answer token: logsumexp of the "yes"/"Yes" logits
minus logsumexp of the "no"/"No" logits. The prompt is one of the frozen variants below (R-neutral "N", R-cross "C"),
with the brief-prompt system message and thinking disabled. The query is the stored query text without the PatEmbed
instruction prefix. The candidate is its title plus the first 200 words of its abstract. Labels are never read.
Writes private raw scores (<output-dir>/llm<prompt>-scores-<name>.jsonl) plus a receipt; the rankings are made by
run_mtm_fusion.py. --limit-pairs runs a throughput smoke test on the first pairs only. Refuses -test names and overwrites.
Methods log: docs/healthtech/research/MEDTECH_TIME_MACHINE_DEV_METHODS_LOG_20261108_EN.md.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

PROMPT_VERSION = "ptp-mtm-rerank-llm-v1"
ABSTRACT_WORDS = 200
PROMPTS = {
    "N": ("Here is a technical problem and a patent.\n\nProblem: {query}\n\nPatent: {candidate}\n\n"
          "Is this patent relevant prior art for the problem? Answer yes or no."),
    "C": ("Here is a technical problem and a patent, which may come from a different technical field.\n\n"
          "Problem: {query}\n\nPatent: {candidate}\n\n"
          "Does the patent disclose a mechanism or technique that could solve this problem, even if it was made for "
          "another field? Answer yes or no."),
}
YES, NO = ("yes", "Yes"), ("no", "No")


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(f"{name}.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 24), b""):
            digest.update(block)
    return digest.hexdigest()


def candidate_text(row: dict) -> str:
    title = " ".join(row["title"].split())
    abstract = " ".join(row["abstract"].split()[:ABSTRACT_WORDS])
    return f"{title}. {abstract}" if title else abstract


def messages(system: str, prompt: str, query: str, candidate: str) -> list[dict]:
    return [{"role": "system", "content": system},
            {"role": "user", "content": PROMPTS[prompt].format(query=query, candidate=candidate)}]


def single_token_ids(tokenizer, words) -> list[int]:
    ids = []
    for word in words:
        encoded = tokenizer.encode(word, add_special_tokens=False)
        if len(encoded) != 1:
            raise SystemExit(f"answer word {word!r} is not a single token")
        ids.append(encoded[0])
    return ids


def yes_no_score(last_logits, yes_ids, no_ids):
    """logsumexp(yes) - logsumexp(no) per row of a (batch, vocab) float tensor."""
    import torch

    return (torch.logsumexp(last_logits[:, yes_ids], dim=-1) - torch.logsumexp(last_logits[:, no_ids], dim=-1))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--queries", type=Path, required=True)
    parser.add_argument("--baseline-dir", type=Path, required=True)
    parser.add_argument("--model-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--name", required=True, help="query view label, e.g. P-dev")
    parser.add_argument("--prompts", default="N,C")
    parser.add_argument("--view", default="main")
    parser.add_argument("--top", type=int, default=30)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--limit-pairs", type=int, default=0, help="smoke test: score only the first N pairs")
    args = parser.parse_args()
    if args.name.endswith("-test"):
        raise SystemExit("phase-2 methods run on dev only")
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    from patent_to_pilot.healthtech.local_execution import check_local_window, local_gpu_slot

    hybrid = _load("run_mtm_hybrid")
    system = _load("run_qwen_scout_actions").SYSTEM
    prompts = args.prompts.split(",")
    outputs = {p: args.output_dir / f"llm{p}-scores-{args.name}.jsonl" for p in prompts}
    receipt_path = args.output_dir / f"receipt-rerank-llm-{args.name}.json"
    if receipt_path.exists() or any(p.exists() for p in outputs.values()):
        raise SystemExit("output exists: refusing to overwrite")
    check_local_window(visible=os.environ.get("CUDA_VISIBLE_DEVICES"))
    queries = {}
    for line in args.queries.read_text(encoding="utf-8").splitlines():
        if line.strip():
            q = json.loads(line)
            queries[q["id"]] = hybrid.strip_prefix(q["text"])
    if any(t.startswith("encode query") for t in queries.values()):
        raise SystemExit("query prefix still present after strip")
    base_path = args.baseline_dir / f"rankings-{args.view}-X-{args.name}.jsonl"
    heads = {}
    for line in base_path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            r = json.loads(line)
            heads[r["query_id"]] = r["families"][: args.top]
    needed = {f for fams in heads.values() for f in fams}
    texts = {}
    with args.corpus.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row["id"] in needed:
                texts[row["id"]] = candidate_text(row)
    pairs = sorted((q, f) for q, fams in heads.items() if q in queries for f in fams)
    if args.limit_pairs:
        pairs = pairs[: args.limit_pairs]
    args.output_dir.mkdir(parents=True, exist_ok=True)
    timings: dict[str, float] = {}
    with local_gpu_slot(args.model_dir):
        tokenizer = AutoTokenizer.from_pretrained(args.model_dir, local_files_only=True)
        tokenizer.padding_side = "left"
        model = AutoModelForCausalLM.from_pretrained(args.model_dir, local_files_only=True, torch_dtype=torch.float16,
                                                     device_map="cuda:0", low_cpu_mem_usage=True,
                                                     attn_implementation="sdpa").eval()
        yes_ids, no_ids = single_token_ids(tokenizer, YES), single_token_ids(tokenizer, NO)
        prompt_tokens = 0
        for p in prompts:
            rendered = [tokenizer.apply_chat_template(messages(system, p, queries[q], texts[f]), tokenize=False,
                                                      add_generation_prompt=True, enable_thinking=False)
                        for q, f in pairs]
            lengths = [len(tokenizer(t, add_special_tokens=False)["input_ids"]) for t in rendered]
            prompt_tokens += sum(lengths)
            order = sorted(range(len(pairs)), key=lambda i: -lengths[i])
            scores = [0.0] * len(pairs)
            started = time.time()
            with torch.inference_mode():
                for start in range(0, len(order), args.batch_size):
                    check_local_window()
                    idx = order[start:start + args.batch_size]
                    enc = tokenizer([rendered[i] for i in idx], return_tensors="pt", padding=True,
                                    add_special_tokens=False).to("cuda:0")
                    last = model(**enc, use_cache=False, logits_to_keep=1).logits[:, -1, :].float()
                    for i, s in zip(idx, yes_no_score(last, yes_ids, no_ids).cpu().tolist()):
                        scores[i] = s
            timings[f"{p}_seconds"] = round(time.time() - started, 3)
            timings[f"{p}_pairs_per_second"] = round(len(pairs) / max(timings[f"{p}_seconds"], 1e-9), 2)
            with outputs[p].open("w", encoding="utf-8") as handle:
                for (q, f), s in zip(pairs, scores):
                    handle.write(json.dumps({"query_id": q, "family": f, "score": s}) + "\n")
        gpu, peak = torch.cuda.get_device_name(0), int(torch.cuda.max_memory_allocated())
    full_pairs = sum(len(f) for q, f in heads.items() if q in queries)
    receipt = {"status": "PASS", "entry": "V4 Qwen3-8B pointwise yes/no", "prompt_version": PROMPT_VERSION,
               "prompts_sha256": {p: hashlib.sha256(PROMPTS[p].encode("utf-8")).hexdigest() for p in prompts},
               "system_sha256": hashlib.sha256(system.encode("utf-8")).hexdigest(),
               "model_dir": str(args.model_dir),
               "weights_sha256": {w.name: _sha256(w) for w in sorted(args.model_dir.glob("*.safetensors"))},
               "answer_token_ids": {"yes": yes_ids, "no": no_ids}, "thinking": False, "dtype": "float16", "attention": "sdpa",
               "candidate_text": f"title. first {ABSTRACT_WORDS} abstract words", "query": "dense instruction prefix stripped",
               "top": args.top, "view": args.view, "lane": "X", "pairs": len(pairs), "full_pairs": full_pairs,
               "smoke": bool(args.limit_pairs), "prompt_tokens": prompt_tokens, "queries": len(heads),
               "inputs_sha256": {p.name: _sha256(p) for p in (args.corpus, args.queries, base_path)},
               "scores_sha256": {p.name: _sha256(p) for p in outputs.values()},
               "timings": timings, "peak_gpu_memory_bytes": peak, "gpu": gpu, "torch": torch.__version__,
               "labels_used": False}
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: receipt[k] for k in ("status", "pairs", "full_pairs", "timings")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
