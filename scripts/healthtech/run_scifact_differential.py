"""Compare the local SciFact wrapper with the pinned upstream evaluator."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import types
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from patent_to_pilot.evaluation.healthtech.scifact import (
    SciFactDocument,
    evaluate_predictions,
    load_gold_claims,
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_official(official_root: Path) -> tuple[Any, Any, dict[str, str]]:
    """Load upstream modules without installing their legacy dependency set."""
    metrics_path = official_root / "verisci" / "evaluate" / "lib" / "metrics.py"
    data_path = official_root / "verisci" / "evaluate" / "lib" / "data.py"
    required = {"metrics": metrics_path, "data": data_path}
    missing = [str(path) for path in required.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError("missing pinned official evaluator files: " + ", ".join(missing))

    # Upstream metrics imports pandas only for warning display and DataFrame
    # construction. Direct metric functions do not need a pandas installation.
    pandas_stub = types.ModuleType("pandas")
    pandas_stub.DataFrame = lambda rows: rows
    sys.modules.setdefault("pandas", pandas_stub)

    package = types.ModuleType("official_scifact")
    package.__path__ = []
    lib_package = types.ModuleType("official_scifact.lib")
    lib_package.__path__ = []
    sys.modules[package.__name__] = package
    sys.modules[lib_package.__name__] = lib_package

    data_spec = importlib.util.spec_from_file_location("official_scifact.lib.data", data_path)
    if data_spec is None or data_spec.loader is None:
        raise RuntimeError("could not load pinned official data module")
    data_module = importlib.util.module_from_spec(data_spec)
    sys.modules[data_spec.name] = data_module
    data_spec.loader.exec_module(data_module)

    metrics_spec = importlib.util.spec_from_file_location("official_scifact.lib.metrics", metrics_path)
    if metrics_spec is None or metrics_spec.loader is None:
        raise RuntimeError("could not load pinned official metrics module")
    metrics_module = importlib.util.module_from_spec(metrics_spec)
    sys.modules[metrics_spec.name] = metrics_module
    metrics_spec.loader.exec_module(metrics_module)
    return data_module, metrics_module, {name: _sha256(path) for name, path in required.items()}


def _official_metrics(data_module: Any, metrics_module: Any, root: Path, case: dict[str, Any]) -> dict[str, dict[str, float]]:
    corpus_path = root / "corpus.jsonl"
    gold_path = root / "gold.jsonl"
    prediction_path = root / "prediction.jsonl"
    corpus_path.write_text("\n".join(json.dumps(row) for row in case["corpus"]) + "\n", encoding="utf-8")
    gold_path.write_text("\n".join(json.dumps(row) for row in case["gold"]) + "\n", encoding="utf-8")
    prediction_path.write_text("\n".join(json.dumps(row) for row in case["prediction"]) + "\n", encoding="utf-8")
    gold = data_module.GoldDataset(str(corpus_path), str(gold_path))
    predictions = data_module.PredictedDataset(gold, str(prediction_path))
    abstract = metrics_module.Counter()
    sentence = metrics_module.Counter()
    for prediction in predictions:
        gold_claim = gold.get_claim(prediction.claim_id)
        metrics_module.update_counts_abstract(prediction, gold_claim, abstract)
        metrics_module.update_counts_sentence(prediction, gold_claim, sentence)
    return {
        "abstract_label_only": metrics_module.compute_f1(abstract, "label_only"),
        "abstract_rationalized": metrics_module.compute_f1(abstract, "rationalized"),
        "sentence_selection": metrics_module.compute_f1(sentence, "selection"),
        "sentence_label": metrics_module.compute_f1(sentence, "label"),
    }


def _local_metrics(root: Path, case: dict[str, Any]) -> dict[str, Any]:
    corpus_rows = {str(row["doc_id"]): SciFactDocument(str(row["doc_id"]), row["title"], tuple(row["abstract"]), bool(row.get("structured", False))) for row in case["corpus"]}
    gold_path = root / "gold.jsonl"
    gold_path.write_text("\n".join(json.dumps(row) for row in case["gold"]) + "\n", encoding="utf-8")
    return evaluate_predictions(load_gold_claims(gold_path), case["prediction"], corpus=corpus_rows)


def _cases() -> list[dict[str, Any]]:
    corpus = [
        {"doc_id": 10, "title": "Ten", "abstract": ["zero", "one", "two"]},
        {"doc_id": 11, "title": "Eleven", "abstract": ["zero", "one", "two", "three"]},
        {"doc_id": 15, "title": "Fifteen", "abstract": ["zero", "one", "two", "three", "four"]},
        {"doc_id": 16, "title": "Sixteen", "abstract": ["zero", "one", "two", "three", "four", "five"]},
    ]
    return [
        {
            "name": "exact_single_rationale",
            "corpus": corpus,
            "gold": [{"id": 1, "claim": "Claim", "cited_doc_ids": [10], "evidence": {"10": [{"label": "SUPPORT", "sentences": [0]}]}}],
            "prediction": [{"id": 1, "evidence": {"10": {"label": "SUPPORT", "sentences": [0]}}}],
        },
        {
            "name": "partial_and_false_document",
            "corpus": corpus,
            "gold": [{"id": 52, "claim": "Claim", "cited_doc_ids": [11, 15], "evidence": {"11": [{"label": "SUPPORT", "sentences": [0, 1]}, {"label": "SUPPORT", "sentences": [2]}], "15": [{"label": "SUPPORT", "sentences": [4]}]}}],
            "prediction": [{"id": 52, "evidence": {"11": {"label": "SUPPORT", "sentences": [1, 2, 3]}, "16": {"label": "CONTRADICT", "sentences": [4, 5]}}}],
        },
        {
            "name": "wrong_label_and_empty_evidence",
            "corpus": corpus,
            "gold": [{"id": 7, "claim": "Claim", "cited_doc_ids": [10], "evidence": {"10": [{"label": "SUPPORT", "sentences": [0]}]}}],
            "prediction": [{"id": 7, "evidence": {"10": {"label": "CONTRADICT", "sentences": []}}}],
        },
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--official-root", type=Path, required=True, help="directory containing verisci/evaluate/lib/{data,metrics}.py")
    parser.add_argument("--output", type=Path, required=True, help="fresh receipt path")
    args = parser.parse_args()
    if args.output.exists():
        parser.error("output already exists; select a fresh receipt path")
    data_module, metrics_module, file_hashes = _load_official(args.official_root)
    cases: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="ptp-scifact-differential-") as temp_dir:
        root = Path(temp_dir)
        for case in _cases():
            official = _official_metrics(data_module, metrics_module, root, case)
            local = _local_metrics(root, case)
            comparison = {
                key: {"official": official[key], "local": local[key], "equal": official[key] == local[key]}
                for key in official
            }
            cases.append({"name": case["name"], "comparison": comparison, "parity": all(row["equal"] for row in comparison.values())})
    receipt = {
        "status": "PASS" if all(case["parity"] for case in cases) else "FAIL",
        "official_revision": "68b98a56d93e0f9da0d2aab4e6c3294699a0f72e",
        "official_source": "https://github.com/allenai/scifact",
        "official_files": file_hashes,
        "cases": cases,
        "limitations": [
            "This differential covers valid prediction semantics only; local strict wrapper validation is intentionally stricter than upstream parsing.",
            "The upstream evaluator does not reject unexpected claim IDs, duplicate sentence IDs, or out-of-range sentences; those are local contract guards.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": receipt["status"], "output": str(args.output), "cases": len(cases)}, ensure_ascii=False))
    if receipt["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
