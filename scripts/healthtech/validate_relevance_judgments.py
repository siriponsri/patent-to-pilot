"""Validate a semantic relevance-judgment manifest against a runtime cohort."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from patent_to_pilot.evaluation.healthtech.judgments import validate_relevance_judgment_manifest
from patent_to_pilot.evaluation.healthtech.local_retrieval import validate_runtime_payload


def _read_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--runtime", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("output already exists; choose a fresh path")
    runtime = _read_json(args.runtime)
    devices, patents = validate_runtime_payload(runtime)
    report = validate_relevance_judgment_manifest(
        _read_json(args.manifest),
        runtime_query_ids=[device.query_id for device in devices],
        runtime_universe=[patent.patent_id_canonical for patent in patents],
        runtime_sha256=hashlib.sha256(args.runtime.read_bytes()).hexdigest(),
    )
    report.update({
        "manifest_path": str(args.manifest),
        "manifest_sha256": hashlib.sha256(args.manifest.read_bytes()).hexdigest(),
        "runtime_path": str(args.runtime),
        "runtime_sha256": hashlib.sha256(args.runtime.read_bytes()).hexdigest(),
    })
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "output": str(args.output), "judged_pair_count": report["judged_pair_count"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
