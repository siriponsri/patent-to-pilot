"""Offline current-head M1 rights and frozen-cohort probes.

The script uses authored synthetic data plus a local copy of the frozen Abbott
cohort. It never prints or persists restricted raw payloads in the audit record.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import socket
import sys


parser = argparse.ArgumentParser()
parser.add_argument("snapshot", type=Path)
parser.add_argument("local_cohort", type=Path)
parser.add_argument("scratch_output", type=Path)
parser.add_argument("audit_summary", type=Path)
parser.add_argument("--source-commit", required=True)
args = parser.parse_args()

root = args.snapshot.resolve()
local_cohort = args.local_cohort.resolve()
scratch_output = args.scratch_output.resolve()
audit_summary = args.audit_summary.resolve()
scratch_output.mkdir(parents=True, exist_ok=False)
audit_summary.parent.mkdir(parents=True, exist_ok=True)

sys.dont_write_bytecode = True
sys.path[:0] = [str(root / "src"), str(root)]
network_attempts: list[str] = []


def deny_network(*_args, **_kwargs):
    network_attempts.append("blocked")
    raise RuntimeError("current-head audit network guard")


socket.socket.connect = deny_network
socket.socket.connect_ex = deny_network
socket.create_connection = deny_network
socket.getaddrinfo = deny_network

spec = importlib.util.spec_from_file_location("fixture_helpers", root / "tests/test_healthtech_repairs.py")
if spec is None or spec.loader is None:
    raise RuntimeError("could not load authored test helpers")
helpers = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helpers)

from patent_to_pilot.healthtech.abbott import build_abbott_case_inputs
from patent_to_pilot.healthtech.engine import DossierInput, export_markdown, run_dossier, serialize_dossier
from patent_to_pilot.healthtech.sources import field_evidence


def read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def expected_rejection(fn, expected_fragment: str) -> dict[str, object]:
    try:
        fn()
    except Exception as exc:  # noqa: BLE001 - probe records the concrete failure boundary
        message = str(exc).replace(str(scratch_output), "<scratch-output>")
        return {
            "status": "PASS" if expected_fragment in message else "FAIL",
            "rejected": True,
            "error_type": type(exc).__name__,
            "message": message[:300],
        }
    return {"status": "FAIL", "rejected": False, "message": "mutation was accepted"}


synthetic = helpers._write_synthetic_abbott_cohort(scratch_output / "synthetic-cohort")
synthetic_case = next(iter(build_abbott_case_inputs(synthetic).values()))
pma_source = next(source for source in synthetic_case.sources if source.source.source_type == "regulatory_record")
pma_source = pma_source.model_copy(
    update={"rights": pma_source.rights.model_copy(update={"displayable_fields": ["trade_name"]})}
)
synthetic_query = synthetic_case.query.model_copy(update={"permitted_inputs": [pma_source.source.source_id]})
synthetic_input = DossierInput(
    query=synthetic_query,
    sources=[pma_source],
    patents=[],
    evidence=[field_evidence(pma_source, "openfda", "AUDIT-RESTRICTED-OPENFDA")],
)
synthetic_dossier, _, _ = run_dossier(
    synthetic_input,
    run_id="current-head-rights-probe",
    code_commit=args.source_commit,
)
restricted_value = pma_source.payload["openfda"]["device_name"]
synthetic_external = serialize_dossier(synthetic_dossier, purpose="redistribution")
synthetic_markdown = export_markdown(synthetic_dossier, purpose="product_display")
synthetic_rights = {
    "status": "PASS" if (
        restricted_value not in synthetic_markdown
        and restricted_value not in json.dumps(synthetic_external, ensure_ascii=False)
        and synthetic_external["sources"][0]["payload"] == {"trade_name": "MitraClip"}
    ) else "FAIL",
    "restricted_value_excluded": restricted_value not in synthetic_markdown
    and restricted_value not in json.dumps(synthetic_external, ensure_ascii=False),
    "projected_payload_keys": sorted(synthetic_external["sources"][0]["payload"]),
    "local_payload_keys": sorted(synthetic_dossier.sources[0].payload),
}

synthetic_runtime_path = synthetic / "runtime.json"
synthetic_runtime = read_json(synthetic_runtime_path)
assert isinstance(synthetic_runtime, dict)
synthetic_runtime["patents"][0]["text"] = "MUTATED PATENT TEXT"
write_json(synthetic_runtime_path, synthetic_runtime)
synthetic_mutation = expected_rejection(
    lambda: build_abbott_case_inputs(synthetic),
    "runtime JSON hash",
)

real_copy = scratch_output / "real-cohort-copy"
real_copy.mkdir(parents=True)
manifest = read_json(local_cohort / "manifest.json")
assert isinstance(manifest, dict)
copy_records: list[dict[str, object]] = []
for relative in ("manifest.json", "runtime.json", str(manifest["source_registry"])):
    source_path = local_cohort / relative
    destination = real_copy / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source_path, destination)
    copy_records.append({"path": relative, "bytes": destination.stat().st_size, "sha256": digest(destination)})
for raw_file in manifest["raw_files"]:
    relative = str(raw_file["path"])
    source_path = local_cohort / relative
    destination = real_copy / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source_path, destination)
    copy_records.append({"path": relative, "bytes": destination.stat().st_size, "sha256": digest(destination)})

real_before = build_abbott_case_inputs(real_copy)
real_runtime_path = real_copy / str(manifest["runtime_path"])
real_runtime = read_json(real_runtime_path)
assert isinstance(real_runtime, dict)
real_runtime["patents"][0]["text"] = "MUTATED PATENT TEXT"
write_json(real_runtime_path, real_runtime)
real_mutation = expected_rejection(
    lambda: build_abbott_case_inputs(real_copy),
    "runtime JSON hash",
)

summary = {
    "format": "ht-m1-current-head-reproduction-v1",
    "status": "PASS" if all(
        item["status"] == "PASS"
        for item in (synthetic_rights, synthetic_mutation, real_mutation)
    ) else "FAIL",
    "source_commit": args.source_commit,
    "synthetic": {
        "rights_projection": synthetic_rights,
        "runtime_patent_text_mutation": synthetic_mutation,
    },
    "real_manifest": {
        "cohort_label": "local frozen Abbott development copy",
        "manifest_integrity_format": manifest.get("integrity_format"),
        "raw_files_declared": len(manifest["raw_files"]),
        "files_copied": len(copy_records),
        "copied_bytes": sum(int(item["bytes"]) for item in copy_records),
        "copied_file_hashes": copy_records,
        "baseline_case_count": len(real_before),
        "baseline_patents_per_case": {key: len(value.patents) for key, value in real_before.items()},
        "runtime_patent_text_mutation": real_mutation,
    },
    "network_attempts_blocked": len(network_attempts),
    "remote_provider_calls": 0,
    "neural_model_calls": 0,
    "restricted_raw_payloads_persisted_in_audit": False,
}
write_json(audit_summary, summary)
print(json.dumps(summary, indent=2))
if summary["status"] != "PASS":
    raise SystemExit(1)
