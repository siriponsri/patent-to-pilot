"""Probe the actual Abbott builder against a frozen local cohort copy."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _copy_input_file(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cohort", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[5]
    sys.path[:0] = [str(root / "src"), str(root)]
    from patent_to_pilot.healthtech.abbott import build_abbott_case_inputs

    if args.output.exists():
        parser.error("output already exists; choose a fresh directory")
    args.output.mkdir(parents=True)
    local = args.output / "local-copy"
    shutil.copytree(args.cohort / "raw", local / "raw")
    for name in ("runtime.json", "source_registry.json", "manifest.json"):
        _copy_input_file(args.cohort / name, local / name)

    baseline_manifest_hash = _sha256(local / "manifest.json")
    results: dict[str, dict] = {}

    try:
        cases = build_abbott_case_inputs(local)
        results["valid_frozen_copy"] = {
            "status": "PASS",
            "case_count": len(cases),
            "patents_per_case": {key: len(value.patents) for key, value in cases.items()},
            "evaluator_directory_copied": (local / "evaluator").exists(),
        }
    except Exception as exc:  # pragma: no cover - probe reports the failure
        results["valid_frozen_copy"] = {
            "status": "FAIL",
            "error_type": type(exc).__name__,
            "error": str(exc),
        }

    mutations = [
        ("runtime_mutation", local / "runtime.json", "runtime"),
        ("raw_consumed_file_mutation", local / "raw" / "pma" / "P100009.json", "raw"),
        ("registry_revision_mutation", local / "source_registry.json", "registry"),
        ("malformed_integrity_metadata", local / "manifest.json", "manifest"),
    ]
    for name, path, kind in mutations:
        original = path.read_bytes()
        try:
            if kind == "runtime":
                payload = json.loads(original.decode("utf-8"))
                payload["patents"][0]["text"] += " PROBE_MUTATION"
                path.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
            elif kind == "raw":
                path.write_bytes(original + b"\nPROBE_MUTATION")
            elif kind == "registry":
                payload = json.loads(original.decode("utf-8"))
                payload["sources"][0]["revision"] = "probe-stale-revision"
                path.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
            else:
                payload = json.loads(original.decode("utf-8"))
                payload.pop("source_registry_sha256", None)
                path.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
            try:
                build_abbott_case_inputs(local)
            except Exception as exc:
                results[name] = {
                    "status": "PASS_REJECTED",
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                }
            else:
                results[name] = {"status": "FAIL_ACCEPTED"}
        finally:
            path.write_bytes(original)

    summary = {
        "format": "ht-abbott-frozen-integrity-probe-v1",
        "cohort": str(args.cohort),
        "manifest_sha256_before_mutation": baseline_manifest_hash,
        "evaluator_directory_copied": (local / "evaluator").exists(),
        "results": results,
        "network_calls": 0,
        "provider_calls": 0,
        "original_cohort_modified": False,
    }
    (args.output / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
