"""MTM dev phase 2, methods-log entries V4 and V5: fuse reranker scores with dense scores on the baseline X head.

For each query, the head is the first --top families of the frozen lane-X baseline ranking. Each head family gets its
PatEmbed-large MaxP dense score (recomputed from the reused passage vectors, as in the baseline) and the method's raw
score from a private scores file. Both are z-normalised over the head, and fused = lam * z_dense + (1 - lam) * z_method.
The head is reordered by fused score (ties keep the baseline order); later ranks stay unchanged. lam = 1 must reproduce
the baseline head, and the receipt counts the queries where it does. lam = 0 is the method alone. Labels are never read.
Writes <output-dir>/<label>-<lam>/rankings-<view>-X-<name>.jsonl plus a receipt, and refuses -test names and overwrites.
Methods log: docs/healthtech/research/MEDTECH_TIME_MACHINE_DEV_METHODS_LOG_20261108_EN.md.
"""
from __future__ import annotations

import argparse
from functools import lru_cache
import importlib.util
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))


@lru_cache(maxsize=None)
def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(f"{name}.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fuse_head(families: list[str], dense: list[float], method: list[float], lam: float, top: int) -> list[str]:
    """Reorder families[:top] by lam * z(dense) + (1 - lam) * z(method); ties keep the input order."""
    import numpy as np

    hybrid = _load("run_mtm_hybrid")
    head = families[:top]
    if not head:
        return list(families)
    zd = hybrid.zscore(np.asarray(dense[: len(head)], dtype=np.float64))
    zm = hybrid.zscore(np.asarray(method[: len(head)], dtype=np.float64))
    fused = lam * zd + (1 - lam) * zm
    order = sorted(range(len(head)), key=lambda i: (-fused[i], i))
    return [head[i] for i in order] + families[top:]


def read_scores(path: Path) -> dict[tuple[str, str], float]:
    out = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            r = json.loads(line)
            out[(r["query_id"], r["family"])] = float(r["score"])
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--queries", type=Path, required=True, help="dense query file (with the PatEmbed prefix)")
    parser.add_argument("--baseline-dir", type=Path, required=True)
    parser.add_argument("--model-dir", type=Path, required=True)
    parser.add_argument("--vectors", type=Path, required=True)
    parser.add_argument("--scores", required=True, help="label=path[,label=path...] private raw score files")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--name", required=True, help="query view label, e.g. P-dev")
    parser.add_argument("--view", default="main")
    parser.add_argument("--top", type=int, required=True)
    parser.add_argument("--lambdas", default="0.0,0.5,0.6,0.7,0.8,0.9,1.0")
    args = parser.parse_args()
    if args.name.endswith("-test"):
        raise SystemExit("phase-2 methods run on dev only")
    import numpy as np
    import torch

    dense_pool = _load("run_mtm_dense_pool")
    dapfam_dense = dense_pool.dapfam_dense
    labels = dict(item.split("=", 1) for item in args.scores.split(","))
    lambdas = [float(x) for x in args.lambdas.split(",")]
    outputs = {(lab, lam): args.output_dir / f"{lab}-{lam:.1f}" / f"rankings-{args.view}-X-{args.name}.jsonl"
               for lab in labels for lam in lambdas}
    receipt_path = args.output_dir / f"receipt-fusion-{'-'.join(labels)}-{args.name}.json"
    if receipt_path.exists() or any(p.exists() for p in outputs.values()):
        raise SystemExit("output exists: refusing to overwrite")
    if dapfam_dense._sha256(args.model_dir / "model.safetensors") != dapfam_dense.MODEL_SAFETENSORS_SHA256:
        raise SystemExit("PatEmbed-large weight hash mismatch")
    dapfam_dense.check_local_window()
    scores = {lab: read_scores(Path(p)) for lab, p in labels.items()}
    base_path = args.baseline_dir / f"rankings-{args.view}-X-{args.name}.jsonl"
    baseline = [r for r in dapfam_dense._read_jsonl(base_path, None)]
    corpus = dapfam_dense._read_jsonl(args.corpus, None)
    queries = {q["id"]: q["text"] for q in dapfam_dense._read_jsonl(args.queries, None)}
    ids = [r["id"] for r in corpus]
    position = {f: i for i, f in enumerate(ids)}
    owner = []
    for i, row in enumerate(corpus):
        owner += [i] * len(dense_pool.dense_passages(row["title"], row["abstract"], row["claims"]))
    del corpus
    for p in outputs.values():
        p.parent.mkdir(parents=True, exist_ok=True)
    started = time.time()
    lam1_matches, missing_queries = 0, 0
    with dapfam_dense.local_gpu_slot(args.model_dir):
        encoder = dapfam_dense.MeanPoolEncoder(args.model_dir, 64)
        vectors = np.load(args.vectors)
        if vectors.shape != (len(owner), encoder.model.config.hidden_size):
            raise SystemExit("vectors do not match the corpus passages")
        qids = [r["query_id"] for r in baseline]
        qvec = torch.from_numpy(encoder.encode([queries[q] for q in qids])).to("cuda")
        matrix = torch.from_numpy(vectors).to("cuda")
        family_index = torch.tensor(owner, dtype=torch.int64, device="cuda")
        handles = {k: p.open("w", encoding="utf-8") for k, p in outputs.items()}
        try:
            for qi, row in enumerate(baseline):
                q, fams = row["query_id"], row["families"]
                head = fams[: args.top]
                best = torch.full((len(ids),), -float("inf"), device="cuda")
                best.scatter_reduce_(0, family_index, (qvec[qi:qi + 1] @ matrix.T)[0], reduce="amax", include_self=True)
                head_idx = torch.tensor([position[f] for f in head], dtype=torch.int64, device="cuda")
                dense = best[head_idx].cpu().tolist()
                if fuse_head(fams, dense, dense, 1.0, args.top)[: len(head)] == head:
                    lam1_matches += 1
                for lab, table in scores.items():
                    if not all((q, f) in table for f in head):
                        if any((q, f) in table for f in head):
                            raise SystemExit(f"partial scores for query {q} in {lab}")
                        missing_queries += 1
                        ranked = {lam: fams for lam in lambdas}
                    else:
                        method = [table[(q, f)] for f in head]
                        ranked = {lam: fuse_head(fams, dense, method, lam, args.top) for lam in lambdas}
                    for lam, order in ranked.items():
                        handles[(lab, lam)].write(json.dumps({"query_id": q, "families": order}) + "\n")
        finally:
            for handle in handles.values():
                handle.close()
        gpu = torch.cuda.get_device_name(0)
    receipt = {"status": "PASS", "entries": ["V4/V5 dense fusion"], "labels": list(labels), "lambdas": lambdas,
               "top": args.top, "view": args.view, "lane": "X", "normalisation": "per-query z over the baseline head",
               "queries": len(baseline), "lambda1_reproduces_baseline_head": lam1_matches,
               "queries_without_method_scores": missing_queries,
               "inputs_sha256": {p.name: dapfam_dense._sha256(p) for p in
                                 [args.corpus, args.queries, base_path, args.vectors] + [Path(x) for x in labels.values()]},
               "rankings_sha256": {f"{lab}-{lam:.1f}/{p.name}": dapfam_dense._sha256(p) for (lab, lam), p in outputs.items()},
               "seconds": round(time.time() - started, 3), "gpu": gpu, "torch": torch.__version__, "labels_used": False}
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: receipt[k] for k in ("status", "queries", "lambda1_reproduces_baseline_head",
                                              "queries_without_method_scores", "seconds")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
