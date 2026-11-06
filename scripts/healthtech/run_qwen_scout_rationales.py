"""Record Qwen3-8B transfer rationales for the Solution Scout public demo (HUPD, CC BY-SA 4.0).

Subcommands:
  build     (local, CPU venv)  live-search each authored demo brief; keep the own-field top
            ``--own`` and the other-fields top ``--other`` candidates with their source text
  generate  (GPU)  one greedy call per candidate; JSON answer with quotes copied from the text;
            one line per call, written as it goes; no retries; then a receipt
  book      (local)  turn generated rows into a rationale book (``ptp-scout-rationales-v1``) for
            the scout service. Quote checks are recomputed by the service, never taken from here.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

PROMPT_VERSION = "ptp-scout-rationale-v0"
MAX_NEW_TOKENS = 400
SYSTEM = ("You help an R&D team judge whether an existing patent document could help solve their problem. "
          "Base every statement only on the document text given. Do not invent facts, patent numbers, "
          "companies or products.")
RATIONALE = (
    "Problem brief from the R&D team:\n{brief}\n\n"
    "Patent document ({lane_label}):\n{text}\n\n"
    "Answer in JSON with exactly these keys:\n"
    "\"what_it_does\": one or two sentences (at most 50 words) on what this document's invention does.\n"
    "\"transferable_mechanism\": one or two sentences (at most 60 words) on the mechanism or principle that "
    "might transfer to the team's problem, or \"No clear transferable mechanism.\" if there is none.\n"
    "\"quotes\": a list of 1 to 3 passages copied word for word from the document text above (each 8 to 40 "
    "words) that support your answer. Copy them exactly; do not paraphrase or join separate sentences.\n"
    "Return only the JSON object."
)
LANE_LABEL = {"own_field": "from the team's own field", "other_fields": "from another field"}


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def parse_rationale(text: str) -> tuple[dict | None, str | None]:
    match = re.search(r"\{.*\}", text, flags=re.S)
    if not match:
        return None, "no JSON object"
    try:
        value = json.loads(match.group(0))
    except json.JSONDecodeError:
        return None, "invalid JSON"
    if not isinstance(value, dict) or set(value) != {"what_it_does", "transferable_mechanism", "quotes"}:
        return None, "wrong keys"
    quotes = value["quotes"]
    if not isinstance(quotes, list) or not 1 <= len(quotes) <= 3 or not all(isinstance(q, str) and q.strip()
                                                                          for q in quotes):
        return None, "quotes must be 1-3 strings"
    what, mechanism = " ".join(str(value["what_it_does"]).split()), " ".join(str(value["transferable_mechanism"]).split())
    if not what or not mechanism or len(what) > 600 or len(mechanism) > 600:
        return None, "summary fields empty or longer than 600 characters"
    return {"what_it_does": what, "transferable_mechanism": mechanism, "quotes": [q.strip() for q in quotes]}, None


def build(args: argparse.Namespace) -> int:
    from patent_to_pilot.healthtech.scout import normalize_ipc3, partition_by_field
    from patent_to_pilot.healthtech.scout_live import LiveIndex

    index = LiveIndex.load(args.data_dir, args.model_dir)
    briefs = json.loads(args.briefs.read_text(encoding="utf-8"))["briefs"]
    rows = []
    for brief in briefs:
        own_ipc3 = list(normalize_ipc3(brief["own_ipc3"]))
        ranking, _, _ = index.search(brief["text"])
        ranked = [family for family, _ in ranking]
        family_ipc3 = {family: index.rows[index.by_id[family]].get("ipc3", []) for family in ranked}
        own, other = partition_by_field(ranked, family_ipc3, own_ipc3)
        for lane, families in (("own_field", own[:args.own]), ("other_fields", other[:args.other])):
            for rank, family in enumerate(families, 1):
                rows.append({"brief_id": brief["brief_id"], "brief_text": brief["text"], "own_ipc3": own_ipc3,
                             "family_id": family, "lane": lane, "rank_in_lane": rank,
                             "source_text": index.family(family)["source_text"]})
    args.output.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    print(json.dumps({"briefs": len(briefs), "candidates": len(rows), "corpus_sha256": index.corpus_sha256,
                      "output_sha256": _sha(args.output.read_bytes())}))
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
        for record in records:
            check_local_window()
            messages = [{"role": "system", "content": SYSTEM},
                        {"role": "user", "content": RATIONALE.format(brief=record["brief_text"],
                                                                     lane_label=LANE_LABEL[record["lane"]],
                                                                     text=record["source_text"])}]
            encoded = tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True,
                                                    return_tensors="pt", return_dict=True, enable_thinking=False)
            inputs = {k: v.to("cuda:0") for k, v in encoded.items()}
            prompt_tokens = int(inputs["input_ids"].shape[-1])
            started = time.perf_counter()
            with torch.inference_mode():
                generated = model.generate(**inputs, max_new_tokens=MAX_NEW_TOKENS, do_sample=False, use_cache=True,
                                           pad_token_id=tokenizer.eos_token_id)
            latency = time.perf_counter() - started
            new_tokens = generated[0, prompt_tokens:]
            text = tokenizer.decode(new_tokens, skip_special_tokens=True).strip()
            parsed, error = parse_rationale(text)
            entry = {"brief_id": record["brief_id"], "family_id": record["family_id"], "lane": record["lane"],
                     "prompt_version": PROMPT_VERSION,
                     "messages_sha256": _sha(json.dumps(messages, sort_keys=True).encode("utf-8")),
                     "prompt_tokens": prompt_tokens, "output_tokens": int(new_tokens.shape[-1]),
                     "latency_seconds": round(latency, 3), "output_sha256": _sha(text.encode("utf-8")),
                     "truncated": int(new_tokens.shape[-1]) >= MAX_NEW_TOKENS, "text": text, "parsed": parsed,
                     "parse_error": error}
            calls.append(entry)
            handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
            handle.flush()
    receipt = {
        "status": "PASS" if all(c["parsed"] is not None for c in calls) else "PARTIAL",
        "prompt_version": PROMPT_VERSION, "model_dir": str(args.model_dir),
        "input_sha256": _sha(args.input.read_bytes()), "output_sha256": _sha(args.output.read_bytes()),
        "calls": len(calls), "failed_calls": sum(c["parsed"] is None for c in calls),
        "truncated_calls": sum(c["truncated"] for c in calls), "retries": 0,
        "prompt_tokens": sum(c["prompt_tokens"] for c in calls), "output_tokens": sum(c["output_tokens"] for c in calls),
        "generation_seconds": round(sum(c["latency_seconds"] for c in calls), 3),
        "mean_latency_seconds": round(sum(c["latency_seconds"] for c in calls) / max(len(calls), 1), 3),
        "load_seconds": round(load_seconds, 3), "peak_gpu_memory_bytes": int(torch.cuda.max_memory_allocated()),
        "gpu": torch.cuda.get_device_name(0), "torch": torch.__version__, "decoding": "greedy, fp16, eager attention",
    }
    Path(str(args.output) + ".receipt.json").write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    print(json.dumps(receipt))
    return 0


def book(args: argparse.Namespace) -> int:
    briefs = {b["brief_id"]: b for b in json.loads(args.briefs.read_text(encoding="utf-8"))["briefs"]}
    rows = [json.loads(line) for line in args.generated.read_text(encoding="utf-8").splitlines() if line.strip()]
    receipt = json.loads(Path(str(args.generated) + ".receipt.json").read_text(encoding="utf-8"))
    entries = [{"brief_text": briefs[r["brief_id"]]["text"], "own_ipc3": sorted(briefs[r["brief_id"]]["own_ipc3"]),
                "family_id": r["family_id"], "model": "Qwen/Qwen3-8B", "model_revision": args.model_revision,
                "prompt_version": r["prompt_version"], "prompt_tokens": r["prompt_tokens"],
                "output_tokens": r["output_tokens"], "latency_seconds": r["latency_seconds"], **r["parsed"]}
               for r in rows if r["parsed"] is not None]
    value = {"format": "ptp-scout-rationales-v1", "corpus_sha256": args.corpus_sha256,
             "generated_sha256": _sha(args.generated.read_bytes()), "generation_receipt": receipt,
             "rationales": entries}
    args.output.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"rationales": len(entries), "failed": len(rows) - len(entries)}))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    b = sub.add_parser("build")
    b.add_argument("--data-dir", type=Path, required=True)
    b.add_argument("--model-dir", type=Path, required=True)
    b.add_argument("--briefs", type=Path, required=True)
    b.add_argument("--own", type=int, default=2)
    b.add_argument("--other", type=int, default=5)
    b.add_argument("--output", type=Path, required=True)
    g = sub.add_parser("generate")
    g.add_argument("--input", type=Path, required=True)
    g.add_argument("--model-dir", type=Path, required=True)
    g.add_argument("--output", type=Path, required=True)
    k = sub.add_parser("book")
    k.add_argument("--briefs", type=Path, required=True)
    k.add_argument("--generated", type=Path, required=True)
    k.add_argument("--corpus-sha256", required=True)
    k.add_argument("--model-revision", required=True)
    k.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    return {"build": build, "generate": generate, "book": book}[args.command](args)


if __name__ == "__main__":
    raise SystemExit(main())
