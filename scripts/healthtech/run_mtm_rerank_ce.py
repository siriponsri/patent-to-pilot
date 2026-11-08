"""MTM dev phase 1, methods-log entry V3: zero-shot cross-encoder rerank of the baseline lane-X top 100.

Model: BAAI/bge-reranker-v2-m3 (Apache-2.0), loaded from a local directory. The weight sha256 and the revision go in
the receipt. Each pair is (query text, candidate "title. abstract"), max length 512 tokens, fp16, scored by the
single logit. The top --top families are reordered by score, with ties keeping the baseline order. Later ranks stay
unchanged, so hit@100 equals the baseline when --top is 100. Labels are never read. Writes
<output-dir>/rankings-<view>-X-<name>.jsonl plus a receipt, and refuses to overwrite.
Methods log: docs/healthtech/research/MEDTECH_TIME_MACHINE_DEV_METHODS_LOG_20261108_EN.md.
Phase 1b (V3b): the PatEmbed instruction prefix is stripped from the query text, and --scores-out writes the raw score of
every pair (private; used by V5). The phase-1 code without the strip is at commit 2feec03 (defective).
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import re
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

SPACE = re.compile(r"\s+")


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(f"{name}.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def query_text(text: str) -> str:
    return _load("run_mtm_hybrid").strip_prefix(text)


def candidate_text(row: dict) -> str:
    title, abstract = SPACE.sub(" ", row["title"]).strip(), SPACE.sub(" ", row["abstract"]).strip()
    return f"{title}. {abstract}" if title else abstract


def rerank(families: list[str], scores: dict[str, float], top: int) -> list[str]:
    """Reorder the first `top` families by score (ties keep the input order); keep the rest unchanged."""
    head = families[:top]
    order = sorted(range(len(head)), key=lambda i: (-scores[head[i]], i))
    return [head[i] for i in order] + families[top:]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--queries", type=Path, required=True)
    parser.add_argument("--baseline-dir", type=Path, required=True)
    parser.add_argument("--model-dir", type=Path, required=True)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--name", required=True, help="query view label, e.g. P-dev")
    parser.add_argument("--views", default="main")
    parser.add_argument("--top", type=int, default=100)
    parser.add_argument("--max-length", type=int, default=512)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--scores-out", type=Path, required=True, help="private jsonl of raw pair scores")
    args = parser.parse_args()
    if args.name.endswith("-test"):
        raise SystemExit("phase-1 methods run on dev only")
    import torch
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    spec = importlib.util.spec_from_file_location("dapfam_dense", Path(__file__).with_name("run_dapfam_dense_pool.py"))
    dapfam_dense = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(dapfam_dense)
    views = args.views.split(",")
    outputs = {v: args.output_dir / f"rankings-{v}-X-{args.name}.jsonl" for v in views}
    receipt_path = args.output_dir / f"receipt-rerank-ce-{args.name}.json"
    if receipt_path.exists() or args.scores_out.exists() or any(p.exists() for p in outputs.values()):
        raise SystemExit("output exists: refusing to overwrite")
    dapfam_dense.check_local_window()
    queries = {q["id"]: query_text(q["text"]) for q in dapfam_dense._read_jsonl(args.queries, None)}
    if any(t.startswith("encode query") for t in queries.values()):
        raise SystemExit("query prefix still present after strip")
    baseline = {}
    for v in views:
        path = args.baseline_dir / f"rankings-{v}-X-{args.name}.jsonl"
        baseline[v] = {r["query_id"]: r["families"] for r in dapfam_dense._read_jsonl(path, None)}
    needed = {f for ranks in baseline.values() for fams in ranks.values() for f in fams[: args.top]}
    texts = {}
    with args.corpus.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row["id"] in needed:
                texts[row["id"]] = candidate_text(row)
    pairs = sorted({(q, f) for ranks in baseline.values() for q, fams in ranks.items() for f in fams[: args.top]})
    weights = sorted(args.model_dir.glob("*.safetensors"))
    args.output_dir.mkdir(parents=True, exist_ok=True)
    scores: dict[tuple[str, str], float] = {}
    with dapfam_dense.local_gpu_slot(args.model_dir):
        tokenizer = AutoTokenizer.from_pretrained(args.model_dir)
        model = AutoModelForSequenceClassification.from_pretrained(args.model_dir, torch_dtype=torch.float16).to("cuda").eval()
        started = time.time()
        with torch.inference_mode():
            for start in range(0, len(pairs), args.batch_size):
                batch = pairs[start:start + args.batch_size]
                enc = tokenizer([queries[q] for q, _ in batch], [texts[f] for _, f in batch], padding=True,
                                truncation=True, max_length=args.max_length, return_tensors="pt").to("cuda")
                logits = model(**enc).logits.view(-1).float().cpu().tolist()
                scores.update(zip(batch, logits))
        seconds = round(time.time() - started, 3)
        gpu = torch.cuda.get_device_name(0)
    with args.scores_out.open("w", encoding="utf-8") as handle:
        for (q, f), value in sorted(scores.items()):
            handle.write(json.dumps({"query_id": q, "family": f, "score": value}) + "\n")
    for v, path in outputs.items():
        with path.open("w", encoding="utf-8") as handle:
            for q, fams in baseline[v].items():
                ranked = rerank(fams, {f: scores[(q, f)] for f in fams[: args.top]}, args.top)
                handle.write(json.dumps({"query_id": q, "families": ranked}) + "\n")
    receipt = {"status": "PASS", "entry": "V3b zero-shot cross-encoder, prefix stripped", "model": "BAAI/bge-reranker-v2-m3",
               "revision": args.revision, "weights_sha256": {p.name: dapfam_dense._sha256(p) for p in weights},
               "top": args.top, "max_length": args.max_length, "dtype": "float16", "candidate_text": "title. abstract",
               "query": "dense instruction prefix stripped", "scores_sha256": dapfam_dense._sha256(args.scores_out),
               "pairs": len(pairs), "queries": len(queries), "views": views, "lane": "X",
               "inputs_sha256": {p.name: dapfam_dense._sha256(p) for p in
                                 [args.corpus, args.queries] + [args.baseline_dir / f"rankings-{v}-X-{args.name}.jsonl" for v in views]},
               "rankings_sha256": {p.name: dapfam_dense._sha256(p) for p in outputs.values()},
               "timings": {"scoring_seconds": seconds, "pairs_per_second": round(len(pairs) / seconds, 1) if seconds else None},
               "gpu": gpu, "torch": torch.__version__, "labels_used": False}
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: receipt[k] for k in ("status", "pairs", "timings")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
