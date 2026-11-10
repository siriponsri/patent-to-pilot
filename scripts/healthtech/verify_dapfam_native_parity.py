"""Synthetic-only differential checks against pinned MTEB source and pytrec_eval.

No benchmark downloader. Source cache must contain the exact reviewed public
files. Only hash-pinned, selected functions execute, with a synthetic dataset
stub. This verifies loader/metric semantics, not a full MTEB/model run.
"""
import argparse
import ast
from collections import defaultdict
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
import sys
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from patent_to_pilot.evaluation.dapfam_native import (  # noqa: E402
    DATASET_REVISION, MTEB_REVISION, evaluate_native_dev, native_dev_task,
)

SOURCE_HASHES = {
    "mteb__tasks__retrieval__eng__dapfam_patent_retrieval.py":
        "8bcd06495193bc9f0ec85ec804ca506912e56ff6f261dce67628b2483c74afc5",
    "mteb___evaluators__retrieval_metrics.py":
        "e1438f788f846464f81c5a6317c37a43686bc881dff72c64af69f61e9efb3b1a",
    "mteb__abstasks__retrieval.py":
        "c3cfe12420c22ebd8e67e44ee00d42f3a6b33c9fea4fe7c5f49590d5f0c1258d",
}


def pinned_function(cache, filename, name, namespace):
    raw = (cache / filename).read_bytes()
    if hashlib.sha256(raw).hexdigest() != SOURCE_HASHES[filename]:
        raise ValueError("public source hash mismatch")
    functions = [n for n in ast.walk(ast.parse(raw)) if isinstance(n, ast.FunctionDef) and n.name == name]
    if len(functions) != 1:
        raise ValueError("pinned function ambiguous")
    tree = ast.Module(body=[ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0),
                            functions[0]], type_ignores=[])
    exec(compile(ast.fix_missing_locations(tree), filename, "exec"), namespace)
    return namespace[name]


class SyntheticQueries:
    def __init__(self, ids):
        self.ids = ids

    def __getitem__(self, key):
        assert key == "id"
        return self.ids

    def select(self, indices):
        return SyntheticQueries([self.ids[i] for i in indices])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-cache", type=Path, required=True)
    parser.add_argument("--backend-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit("output exists: refusing to overwrite")
    sys.path.insert(0, str(args.backend_dir.resolve()))
    import pytrec_eval

    if version("pytrec-eval-terrier") != "0.5.11":
        raise ValueError("unreviewed metric backend version")
    corpus = [{"relevant_id": f, "title_en": f + " title", "abstract_en": "abstract", "claims_text": "claims"}
              for f in ("A", "B", "C")]
    queries = [{"query_id": q, "title_en": "title", "abstract_en": "abstract", "claims_text": "not a TA input"}
               for q in ("q1", "q2", "q3")]
    relations = [{"query_id": q, "relevant_id": d, "relevance_score": s, "domain_rel": p}
                 for q, d, s, p in [("q1", "A", 2, "IN"), ("q1", "B", 3, "OUT"),
                                     ("q2", "B", 1, "OUT"), ("q3", "C", 0, "OUT")]]
    calls = []

    def synthetic_dataset(path, config, *, split, revision):
        assert path == "synthetic-only" and split == "train" and revision == DATASET_REVISION
        calls.append(config)
        return {"corpus": corpus, "queries": queries, "relations": relations}[config]

    load = pinned_function(args.source_cache, "mteb__tasks__retrieval__eng__dapfam_patent_retrieval.py",
                           "load_data", {"load_dataset": synthetic_dataset})
    parse = pinned_function(args.source_cache, "mteb___evaluators__retrieval_metrics.py",
                            "parse_metrics_from_scores", {"defaultdict": defaultdict})
    filter_queries = pinned_function(args.source_cache, "mteb__abstasks__retrieval.py",
                                     "_filter_queries_without_positives", {})
    rankings = {"q1": ["A", "C", "B"], "q2": ["B", "C", "A"]}
    metrics = {m + ".1,3,100" for m in ("ndcg_cut", "map_cut", "recall", "P", "success")}
    checks = []
    for partition in ("ALL", "IN", "OUT"):
        native = SimpleNamespace(domain_filter=None if partition == "ALL" else partition,
                                 query_fields=["title_en", "abstract_en"],
                                 corpus_fields=["title_en", "abstract_en", "claims_text"],
                                 metadata=SimpleNamespace(dataset={"path": "synthetic-only", "revision": DATASET_REVISION},
                                                          eval_splits=["train"]))
        c, q, g = load(native)
        ours = native_dev_task(corpus, queries, relations, partition=partition)
        assert c["train"] == ours["corpus"] and q["train"] == ours["queries"] and g["train"] == ours["qrels"]
        kept, selected = filter_queries(g["train"], SyntheticQueries(list(q["train"])))
        assert set(selected.ids) == set(ours["qrels"]) == set(kept)
        evaluator = pytrec_eval.RelevanceEvaluator(g["train"], metrics)
        for mode in ("complete", "missing", "empty", "all_missing"):
            candidate = dict(rankings)
            if mode == "missing":
                candidate.pop("q2")
            elif mode == "empty":
                candidate["q2"] = []
            elif mode == "all_missing":
                candidate = {}
            # Complete the eligible population explicitly, never drop failures.
            backend_input = {qid: {pid: float(len(candidate.get(qid, [])) - rank)
                                    for rank, pid in enumerate(candidate.get(qid, []))} for qid in kept}
            scores = evaluator.evaluate(backend_input)
            ndcg, _, recall, *_ = parse(scores, [1, 3, 100])
            observed = evaluate_native_dev(ours, candidate, cutoffs=(1, 3, 100))
            assert observed["metrics"] == {**ndcg, **recall}
            assert observed["queries"] == len(scores) == len(kept)
            checks.append({"partition": partition, "mode": mode, "queries": len(kept), "status": "PASS"})
    assert calls == ["corpus", "queries", "relations"] * 3
    raw_evaluator = pytrec_eval.RelevanceEvaluator({"q1": {"B": 1}, "q2": {"B": 1}}, metrics)
    raw_missing = raw_evaluator.evaluate({"q1": {"B": 1.0}})
    assert set(raw_missing) == {"q1"}
    result = {"status": "PASS_SYNTHETIC_DIFFERENTIAL", "mteb_revision": MTEB_REVISION,
              "dataset_revision": DATASET_REVISION, "source_sha256": SOURCE_HASHES,
              "backend": "pytrec-eval-terrier==0.5.11", "checks": checks,
              "raw_backend_missing_query_omitted": True, "wrapper_missing_query_scores_zero": True,
              "benchmark_rows_loaded": 0, "protected_label_access": False,
              "full_mteb_run": "NOT_RUN", "published_result_replication": "NOT_RUN",
              "scope": "native TA/TAC loader, positive-query filtering, binary NDCG/recall and denominator guard"}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2)
        handle.write("\n")
    print(json.dumps({"status": result["status"], "differential_cases": len(checks)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
