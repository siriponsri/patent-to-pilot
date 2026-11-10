"""Audit main/X dev gold with the frozen runtime mask and isolated staged dev inputs.

No test option, no mixed-metadata support, no qrel correction or scoring.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from patent_to_pilot.evaluation.mtm_dev_inputs import load_dev_qrels  # noqa: E402
from patent_to_pilot.evaluation.mtm_eligibility import audit_eligibility  # noqa: E402
from patent_to_pilot.research.mtm_runtime import decode_json, load_dev_metadata  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime-dev", type=Path, required=True)
    parser.add_argument("--dev-evaluation", type=Path, required=True)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit("output exists: refusing to overwrite")
    metadata = load_dev_metadata(args.runtime_dev)
    qrels = load_dev_qrels(args.dev_evaluation, query_ids=set(metadata))
    runner = Path(__file__).with_name("run_mtm_dense_pool.py")
    spec = importlib.util.spec_from_file_location("frozen_mtm_mask", runner)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    digest = hashlib.sha256()

    def rows():
        with args.corpus.open("rb") as handle:
            for line in handle:
                digest.update(line)
                yield decode_json(line)

    report = audit_eligibility(metadata, qrels, rows(), keep_mask=module.keep_mask)
    report["inputs_sha256"] = {
        "corpus": digest.hexdigest(), "frozen_runner": hashlib.sha256(runner.read_bytes()).hexdigest(),
        "runtime_manifest": hashlib.sha256((args.runtime_dev / "manifest.json").read_bytes()).hexdigest(),
        "dev_evaluation_manifest": hashlib.sha256((args.dev_evaluation / "manifest.json").read_bytes()).hexdigest()}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)
        handle.write("\n")
    print(json.dumps({key: report[key] for key in ("status", "queries", "pairs", "pair_classification")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
