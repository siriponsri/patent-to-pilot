"""Qwen3-8B actions for the cross-industry solution scout feasibility check (dev only).

For each query family:
  P  problem brief  written from title + abstract + the start of the description, without the solution
  F  function       the required function restated in generic terms, written from a brief only (title or P)
  S  solution       a short abstract of a hypothetical patent from another industry, written from a brief only
The F and S actions never see the patent itself, only the brief.

Subcommands:
  build     (local)  write label-free records for one split from the private parquet + split file
  generate  (GPU)    run the frozen prompts greedily; writes one JSON line per query as it goes, then a receipt

Plan: docs/healthtech/research/SOLUTION_SCOUT_FEASIBILITY_PLAN_20261105_EN.md (dev). The test split is built only
for the frozen protocol docs/healthtech/research/SOLUTION_SCOUT_FROZEN_PROTOCOL_20261106_EN.md, which uses P only
(``generate --actions P``).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

PROMPT_VERSION = "ptp-solution-scout-v1"
DESCRIPTION_CHAR_LIMIT = 3000
SYSTEM = ("You help an R&D team search patents for solutions. You write search text only. "
          "Do not invent patent numbers, citations, company or product names.")
PROBLEM = (
    "Patent family\nTitle: {title}\nAbstract: {abstract}\nDescription (start): {description}\n\n"
    "Write the technical problem that an R&D engineer facing this situation would bring to a patent search, "
    "in 40 to 80 words: the need, the operating context and the constraints. Do not describe how this patent "
    "solves it: no mechanism, components, materials or claimed features. Do not mention this patent.\n"
    "Return only the problem text."
)
FUNCTION = (
    "An R&D team describes a technical problem:\n{brief}\n\n"
    "Restate it as the required function in generic engineering terms, so that solutions from other industries "
    "can be found, in 40 to 80 words: the function (verb and object), the physical effect or operating condition "
    "involved, and the constraints. Replace industry-specific terms with generic ones where possible. "
    "Do not propose a specific product.\nReturn only the text."
)
SOLUTION = (
    "An R&D team describes a technical problem:\n{brief}\n\n"
    "Write the abstract (100 to 150 words) of a hypothetical earlier patent from a different industry that "
    "solves the same underlying function, using the vocabulary that industry would use.\nReturn only the abstract."
)
LIMITS = {"P": (25, 120, 200), "F": (25, 120, 200), "S": (60, 220, 300)}  # min words, max words, max new tokens


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _clean(value: str | None) -> str:
    return " ".join((value or "").split())


def parse_text(text: str, action: str) -> tuple[str | None, str | None]:
    """Accept a plain-text answer whose word count is inside the action's bounds."""
    cleaned = _clean(text).strip('"').strip()
    for prefix in ("Problem:", "Function:", "Abstract:"):
        if cleaned.lower().startswith(prefix.lower()):
            cleaned = cleaned[len(prefix):].strip()
    low, high, _ = LIMITS[action]
    words = len(cleaned.split())
    if words < low:
        return None, f"too short ({words} words)"
    if words > high:
        return None, f"too long ({words} words)"
    return cleaned, None


def build(args: argparse.Namespace) -> int:
    import pyarrow.parquet as pq

    split = json.loads(args.split.read_text(encoding="utf-8"))["assignment"]
    rows = pq.read_table(args.queries_parquet, columns=["query_id", "title_en", "abstract_en", "description_en",
                                                         "classifications_ipcr_list_first_three_chars_list"]).to_pylist()
    records = [{"id": str(r["query_id"]), "title": _clean(r["title_en"]), "abstract": _clean(r["abstract_en"]),
                "description": _clean(r["description_en"])[:DESCRIPTION_CHAR_LIMIT],
                "own_ipc3": sorted(set(r["classifications_ipcr_list_first_three_chars_list"] or []))}
               for r in sorted(rows, key=lambda r: str(r["query_id"])) if split[str(r["query_id"])] == args.split_name]
    args.output.write_text("".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in records), encoding="utf-8")
    print(json.dumps({"records": len(records), "split": args.split_name, "sha256": _sha(args.output.read_bytes())}))
    return 0


def generate(args: argparse.Namespace) -> int:
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    from patent_to_pilot.healthtech.local_execution import check_local_window, local_gpu_slot

    records = [json.loads(line) for line in args.input.read_text(encoding="utf-8").splitlines() if line.strip()]
    check_local_window(visible=os.environ.get("CUDA_VISIBLE_DEVICES"))
    calls = []
    with local_gpu_slot(args.model_dir), args.output.open("w", encoding="utf-8") as handle:
        load_started = time.perf_counter()
        tokenizer = AutoTokenizer.from_pretrained(args.model_dir, local_files_only=True)
        model = AutoModelForCausalLM.from_pretrained(args.model_dir, local_files_only=True, torch_dtype=torch.float16,
                                                     device_map="cuda:0", low_cpu_mem_usage=True,
                                                     attn_implementation="eager").eval()
        load_seconds = time.perf_counter() - load_started
        torch.cuda.reset_peak_memory_stats()

        def run(action: str, prompt: str) -> dict:
            messages = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": prompt}]
            encoded = tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True,
                                                    return_tensors="pt", return_dict=True, enable_thinking=False)
            inputs = {k: v.to("cuda:0") for k, v in encoded.items()}
            prompt_tokens = int(inputs["input_ids"].shape[-1])
            limit = LIMITS[action][2]
            started = time.perf_counter()
            with torch.inference_mode():
                generated = model.generate(**inputs, max_new_tokens=limit, do_sample=False, use_cache=True,
                                           pad_token_id=tokenizer.eos_token_id)
            latency = time.perf_counter() - started
            new_tokens = generated[0, prompt_tokens:]
            text = tokenizer.decode(new_tokens, skip_special_tokens=True).strip()
            parsed, error = parse_text(text, action)
            entry = {"messages_sha256": _sha(json.dumps(messages, sort_keys=True).encode("utf-8")),
                     "prompt_tokens": prompt_tokens, "output_tokens": int(new_tokens.shape[-1]),
                     "latency_seconds": round(latency, 3), "output_sha256": _sha(text.encode("utf-8")),
                     "truncated": int(new_tokens.shape[-1]) >= limit, "text": text, "parsed": parsed,
                     "parse_error": error}
            calls.append(entry)
            return entry

        for record in records:
            check_local_window()
            row = {"id": record["id"], "prompt_version": PROMPT_VERSION, "title": record["title"]}
            row["P"] = run("P", PROBLEM.format(title=record["title"], abstract=record["abstract"],
                                               description=record["description"] or "none"))
            briefs = {"T": record["title"], "P": row["P"]["parsed"]} if args.actions == "all" else {}
            for brief_name, brief in briefs.items():
                for action, template in (("F", FUNCTION), ("S", SOLUTION)):
                    key = f"{action}_{brief_name}"
                    row[key] = run(action, template.format(brief=brief)) if brief else None
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
            handle.flush()
    receipt = {
        "status": "PASS" if all(c["parsed"] is not None for c in calls) else "PARTIAL",
        "prompt_version": PROMPT_VERSION, "model_dir": str(args.model_dir),
        "input_sha256": _sha(args.input.read_bytes()), "output_sha256": _sha(args.output.read_bytes()),
        "queries": len(records), "calls": len(calls), "failed_calls": sum(c["parsed"] is None for c in calls),
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
    b.add_argument("--split-name", choices=("dev", "test"), required=True,
                   help="test only after the frozen protocol commit")
    b.add_argument("--output", type=Path, required=True)
    g = sub.add_parser("generate")
    g.add_argument("--input", type=Path, required=True)
    g.add_argument("--model-dir", type=Path, required=True)
    g.add_argument("--output", type=Path, required=True)
    g.add_argument("--actions", choices=("all", "P"), default="all", help="P: problem brief only (frozen test)")
    args = parser.parse_args()
    return build(args) if args.command == "build" else generate(args)


if __name__ == "__main__":
    raise SystemExit(main())
