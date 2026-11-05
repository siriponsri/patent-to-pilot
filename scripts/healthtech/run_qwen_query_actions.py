"""Qwen3-8B acquisition actions (Q1 functional query, Q2 IPC-shift, Q3 pseudo-document) for DAPFAM queries.

Subcommands:
  build     (local)  write label-free query records for a split sample from the private parquet + split file
  generate  (GPU)    run the frozen prompts greedily on the approved V100 and write outputs plus a receipt

Protocol: docs/healthtech/research/ORG_ADAPTIVE_CROSS_DOMAIN_PROTOCOL_DRAFT_20261105_EN.md (draft prompts v0).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import random
import re
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

PROMPT_VERSION = "ptp-org-adaptive-qwen-actions-v1"
CLAIMS_CHAR_LIMIT = 1500
IPC3_PREFIX = re.compile(r"^([A-H][0-9]{2})")
SYSTEM = ("You are a patent prior-art search assistant. You write search text only. "
          "Do not invent patent numbers, citations or product names.")
ACTION_A = (
    "Query patent family\n"
    "Title: {title}\nAbstract: {abstract}\nClaims (truncated): {claims}\nOwn IPC3 codes: {own_ipc3}\n\n"
    "Prior art for this invention may exist in other technical fields that describe the same mechanism "
    "with different vocabulary.\n"
    "1. Write one search query of 60 to 120 words that states the technical problem, the working principle "
    "and the key functional elements in generic engineering terms. Avoid the application domain's jargon "
    "where a generic term exists.\n"
    "2. List up to 3 IPC classes where the same mechanism is plausibly described in another field. Write each "
    "class as exactly three characters: one letter A-H followed by two digits, for example F16, G01 or B01, with "
    "no subclass letter and no group number. Every class MUST differ from the own codes ({own_ipc3}). Prefer "
    "classes from a different IPC section where plausible.\n"
    'Return only JSON: {{"functional_query": "...", "target_ipc3": ["..."]}}'
)
ACTION_B = (
    "Query patent family\n"
    "Title: {title}\nAbstract: {abstract}\nClaims (truncated): {claims}\n\n"
    "Write the abstract (120 to 180 words) of a hypothetical earlier patent from a different technical "
    "field that discloses the same core mechanism, using the vocabulary that field would use. "
    "Return only the abstract text."
)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def build(args: argparse.Namespace) -> int:
    import pyarrow.parquet as pq

    split = json.loads(args.split.read_text(encoding="utf-8"))["assignment"]
    rows = pq.read_table(args.queries_parquet, columns=["query_id", "title_en", "abstract_en", "claims_text",
                                                         "classifications_ipcr_list_first_three_chars_list"]).to_pylist()
    pool = sorted(str(r["query_id"]) for r in rows if split[str(r["query_id"])] == args.split_name)
    if args.sample:
        random.Random(args.seed).shuffle(pool)
        pool = sorted(pool[:args.sample])
    chosen = set(pool)
    records = []
    for row in sorted(rows, key=lambda r: str(r["query_id"])):
        if str(row["query_id"]) in chosen:
            records.append({"id": str(row["query_id"]), "title": " ".join((row["title_en"] or "").split()),
                            "abstract": " ".join((row["abstract_en"] or "").split()),
                            "claims": " ".join((row["claims_text"] or "").split())[:CLAIMS_CHAR_LIMIT],
                            "own_ipc3": sorted(set(row["classifications_ipcr_list_first_three_chars_list"] or []))})
    args.output.write_text("".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in records), encoding="utf-8")
    print(json.dumps({"records": len(records), "split": args.split_name, "sample": args.sample, "seed": args.seed,
                      "sha256": _sha(args.output.read_bytes())}))
    return 0


def parse_action_a(text: str, own_ipc3: list[str]) -> tuple[dict | None, str | None]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        cleaned = cleaned[cleaned.find("{"):]
    start, end = cleaned.find("{"), cleaned.rfind("}")
    if start < 0 or end < start:
        return None, "no JSON object"
    try:
        value = json.loads(cleaned[start:end + 1])
    except json.JSONDecodeError as exc:
        return None, f"json: {exc}"
    query = value.get("functional_query")
    codes = value.get("target_ipc3")
    if not isinstance(query, str) or not query.strip() or not isinstance(codes, list):
        return None, "schema"
    prefixes = [IPC3_PREFIX.match(c.strip().upper()) for c in codes if isinstance(c, str)]
    valid = [m.group(1) for m in prefixes if m]
    valid = [c for c in dict.fromkeys(valid) if c not in set(own_ipc3)][:3]
    return {"functional_query": " ".join(query.split()), "target_ipc3": valid,
            "dropped_ipc3": len(codes) - len(valid)}, None


def generate(args: argparse.Namespace) -> int:
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    from patent_to_pilot.healthtech.local_execution import check_local_window, local_gpu_slot

    records = [json.loads(line) for line in args.input.read_text(encoding="utf-8").splitlines() if line.strip()]
    check_local_window(visible=os.environ.get("CUDA_VISIBLE_DEVICES"))
    out_rows = []
    with local_gpu_slot(args.model_dir):
        load_started = time.perf_counter()
        tokenizer = AutoTokenizer.from_pretrained(args.model_dir, local_files_only=True)
        model = AutoModelForCausalLM.from_pretrained(args.model_dir, local_files_only=True, torch_dtype=torch.float16,
                                                     device_map="cuda:0", low_cpu_mem_usage=True,
                                                     attn_implementation="eager").eval()
        load_seconds = time.perf_counter() - load_started
        torch.cuda.reset_peak_memory_stats()
        for record in records:
            check_local_window()
            fields = {"title": record["title"], "abstract": record["abstract"], "claims": record["claims"],
                      "own_ipc3": ", ".join(record["own_ipc3"]) or "none"}
            row = {"id": record["id"], "prompt_version": PROMPT_VERSION}
            for action, template, limit in (("A", ACTION_A, 320), ("B", ACTION_B, 320)):
                messages = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": template.format(**fields)}]
                encoded = tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True,
                                                        return_tensors="pt", return_dict=True, enable_thinking=False)
                inputs = {k: v.to("cuda:0") for k, v in encoded.items()}
                prompt_tokens = int(inputs["input_ids"].shape[-1])
                started = time.perf_counter()
                with torch.inference_mode():
                    generated = model.generate(**inputs, max_new_tokens=limit, do_sample=False, use_cache=True,
                                               pad_token_id=tokenizer.eos_token_id)
                latency = time.perf_counter() - started
                new_tokens = generated[0, prompt_tokens:]
                text = tokenizer.decode(new_tokens, skip_special_tokens=True).strip()
                entry = {"messages_sha256": _sha(json.dumps(messages, sort_keys=True).encode("utf-8")),
                         "prompt_tokens": prompt_tokens, "output_tokens": int(new_tokens.shape[-1]),
                         "latency_seconds": round(latency, 3), "output_sha256": _sha(text.encode("utf-8")),
                         "truncated": int(new_tokens.shape[-1]) >= limit, "text": text}
                if action == "A":
                    parsed, error = parse_action_a(text, record["own_ipc3"])
                    entry.update({"parsed": parsed, "parse_error": error})
                else:
                    words = len(text.split())
                    entry.update({"parsed": {"pseudo_document": " ".join(text.split())} if words >= 40 else None,
                                  "parse_error": None if words >= 40 else f"too short ({words} words)"})
                row[action] = entry
            out_rows.append(row)
    args.output.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in out_rows), encoding="utf-8")
    calls = [row[a] for row in out_rows for a in ("A", "B")]
    receipt = {
        "status": "PASS" if all(c["parsed"] is not None for c in calls) else "PARTIAL",
        "prompt_version": PROMPT_VERSION, "model_dir": str(args.model_dir),
        "input_sha256": _sha(args.input.read_bytes()), "output_sha256": _sha(args.output.read_bytes()),
        "queries": len(out_rows), "calls": len(calls), "failed_calls": sum(c["parsed"] is None for c in calls),
        "truncated_calls": sum(c["truncated"] for c in calls), "retries": 0,
        "prompt_tokens": sum(c["prompt_tokens"] for c in calls), "output_tokens": sum(c["output_tokens"] for c in calls),
        "generation_seconds": round(sum(c["latency_seconds"] for c in calls), 3),
        "mean_latency_seconds": round(sum(c["latency_seconds"] for c in calls) / max(len(calls), 1), 3),
        "load_seconds": round(load_seconds, 3), "peak_gpu_memory_bytes": int(torch.cuda.max_memory_allocated()),
        "gpu": torch.cuda.get_device_name(0), "torch": torch.__version__, "decoding": "greedy, fp16, eager attention",
        "labels_used": False,
    }
    Path(str(args.output) + ".receipt.json").write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    print(json.dumps(receipt))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    b = sub.add_parser("build")
    b.add_argument("--queries-parquet", type=Path, required=True)
    b.add_argument("--split", type=Path, required=True)
    b.add_argument("--split-name", choices=("dev", "test"), required=True)
    b.add_argument("--sample", type=int)
    b.add_argument("--seed", type=int, default=20261105)
    b.add_argument("--output", type=Path, required=True)
    g = sub.add_parser("generate")
    g.add_argument("--input", type=Path, required=True)
    g.add_argument("--model-dir", type=Path, required=True)
    g.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    return build(args) if args.command == "build" else generate(args)


if __name__ == "__main__":
    raise SystemExit(main())
