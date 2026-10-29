"""Offline current-head M1 closure probes.

This probe uses authored synthetic fixtures plus a disposable copy of the
frozen Abbott cohort. It records hashes, counts, and error classes only; it
does not persist restricted raw payloads or evaluator relations.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import socket
import sys
from unittest.mock import patch


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
    raise RuntimeError("m1 closure audit network guard")


socket.socket.connect = deny_network
socket.socket.connect_ex = deny_network
socket.create_connection = deny_network
socket.getaddrinfo = deny_network

spec = importlib.util.spec_from_file_location("fixture_helpers", root / "tests/test_healthtech_repairs.py")
if spec is None or spec.loader is None:
    raise RuntimeError("could not load authored test helpers")
helpers = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helpers)

from patent_to_pilot.evaluation.healthtech import provenance as provenance_module
from patent_to_pilot.evaluation.healthtech.provenance import verify_cohort_provenance
from patent_to_pilot.healthtech.abbott import build_abbott_case_inputs
from patent_to_pilot.healthtech.contracts import SourceRights
from patent_to_pilot.healthtech.engine import DossierInput, export_markdown, run_dossier, serialize_dossier
from patent_to_pilot.healthtech.history import source_view
from patent_to_pilot.healthtech.sources import field_evidence


def read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rejection(fn, expected_fragment: str) -> dict[str, object]:
    try:
        fn()
    except Exception as exc:  # noqa: BLE001 - receipt records the boundary
        message = str(exc).replace(str(scratch_output), "<scratch-output>")
        return {
            "status": "PASS" if expected_fragment in message else "FAIL",
            "rejected": True,
            "error_type": type(exc).__name__,
            "message": message[:300],
        }
    return {"status": "FAIL", "rejected": False, "message": "mutation was accepted"}


def policy_fixture(*, rights_id: str, source_types: list[str], prefixes: list[str]) -> SourceRights:
    return SourceRights(
        rights_id=rights_id,
        source_id_prefixes=prefixes,
        source_types=source_types,
        basis_url="urn:synthetic:rights",
        checked_date="2026-10-29",
        basis_revision="fixture-v1",
        basis_sha256="a" * 64,
        clause_locator="fixture",
        clause="fixture",
        interpretation="fixture",
        acquisition="ALLOWED",
        local_evaluation="ALLOWED_LOCAL_RESEARCH",
        product_display="BLOCKED_LOCAL",
        redistribution="BLOCKED_LOCAL",
    )


synthetic_root = scratch_output / "synthetic"
abbott_fixture = helpers._write_synthetic_abbott_cohort(synthetic_root)
case = next(iter(build_abbott_case_inputs(abbott_fixture).values()))
pma = next(source for source in case.sources if source.source.source_type == "regulatory_record")
pma = pma.model_copy(update={
    "rights": pma.rights.model_copy(update={
        "product_display": "ALLOWED",
        "redistribution": "ALLOWED",
        "displayable_fields": ["trade_name"],
    })
})
query = case.query.model_copy(update={"permitted_inputs": [pma.source.source_id]})
secret = "restricted-nested-MitraClip"
encoded_secret = base64.b64encode(secret.encode("utf-8")).decode("ascii")
structured = field_evidence(pma, "trade_name", "AUDIT-STRUCTURED").model_copy(update={
    "statement": secret,
    "structured_value": secret,
})
literal = field_evidence(pma, "trade_name", "AUDIT-LITERAL").model_copy(update={
    "locator": "chars:0:128",
    "quoted_span": f"quote={secret}; encoded={encoded_secret}",
    "structured_field": None,
    "structured_value": None,
    "extraction_method": "literal_span",
    "statement": f"statement={secret}; encoded={encoded_secret}",
})
restricted_nested = field_evidence(pma, "openfda", "AUDIT-NESTED").model_copy(update={
    "statement": "openfda: restricted-nested-MitraClip",
    "structured_value": {"device_name": secret},
})
data = DossierInput(
    query=query,
    sources=[pma],
    patents=[],
    evidence=[field_evidence(pma, "trade_name", "AUDIT-TRADE"), field_evidence(pma, "openfda", "AUDIT-NESTED")],
)
dossier, _, _ = run_dossier(data, run_id="m1-closure-rights", code_commit=args.source_commit)
dossier = dossier.model_copy(update={
    "evidence": dossier.evidence + [structured, literal, restricted_nested],
})
local_markdown = export_markdown(dossier, language="en")
external_markdown = export_markdown(dossier, language="en", purpose="product_display")
external_json = serialize_dossier(dossier, purpose="redistribution")
external_json_text = json.dumps(external_json, ensure_ascii=False, sort_keys=True)
external_source = source_view(dossier, pma.source.source_id, purpose="product_display")
rights_projection_checks = {
    "status": "PASS" if all([
        secret in local_markdown,
        encoded_secret in local_markdown,
        secret not in external_markdown,
        encoded_secret not in external_markdown,
        secret not in external_json_text,
        encoded_secret not in external_json_text,
        secret not in json.dumps(external_source, ensure_ascii=False),
        external_json["sources"][0]["payload"] == {"trade_name": "MitraClip"},
        external_source["payload"] == {"trade_name": "MitraClip"},
        all(item["evidence_id"] != "AUDIT-LITERAL" for item in external_json["evidence"]),
        all(item["evidence_id"] != "AUDIT-NESTED" for item in external_json["evidence"]),
    ]) else "FAIL",
    "local_retains_secret": secret in local_markdown and encoded_secret in local_markdown,
    "external_markdown_excludes_secret": secret not in external_markdown and encoded_secret not in external_markdown,
    "external_json_excludes_secret": secret not in external_json_text and encoded_secret not in external_json_text,
    "external_source_view_excludes_secret": secret not in json.dumps(external_source, ensure_ascii=False),
    "projected_payload": external_json["sources"][0]["payload"],
    "external_evidence_ids": [item["evidence_id"] for item in external_json["evidence"]],
}

synthetic_runtime = read_json(abbott_fixture / "runtime.json")
assert isinstance(synthetic_runtime, dict)
synthetic_runtime["patents"][0]["text"] = "MUTATED PATENT TEXT"
write_json(abbott_fixture / "runtime.json", synthetic_runtime)
synthetic_runtime_mutation = rejection(
    lambda: build_abbott_case_inputs(abbott_fixture),
    "runtime JSON hash",
)

typed_root = scratch_output / "typed"
typed = helpers._write_synthetic_provenance_cohort(typed_root, typed_rights=True)
registry_path = typed / "source_registry.json"
baseline_registry = read_json(registry_path)
assert isinstance(baseline_registry, dict)


def typed_case(policy_id: object) -> dict[str, object]:
    payload = json.loads(json.dumps(baseline_registry))
    payload["sources"][0]["rights_policy_id"] = policy_id
    write_json(registry_path, payload)
    try:
        report = verify_cohort_provenance(typed)
        return {
            "status": report["status"],
            "rights_binding": report["rights_binding"],
            "resolved_policy_ids": report["rights_policy_ids"],
            "unresolved_policy_ids": report["unresolved_rights_policy_ids"],
        }
    finally:
        write_json(registry_path, baseline_registry)


typed_cases = {
    "unknown": typed_case("unknown-policy"),
    "blank": typed_case(""),
    "mismatched": typed_case("google-patents-pages"),
}
ambiguous_policies = {
    "first": policy_fixture(
        rights_id="shared-policy-id",
        source_types=["independent_disclosure"],
        prefixes=["abbott-product-"],
    ),
    "second": policy_fixture(
        rights_id="shared-policy-id",
        source_types=["independent_disclosure"],
        prefixes=["abbott-product-"],
    ),
}
ambiguous = {}
with patch.object(provenance_module, "load_rights_matrix", return_value=ambiguous_policies):
    ambiguous["report"] = typed_case("shared-policy-id")
typed_policy_checks = {
    "status": "PASS" if (
        all(
            report["status"] == "PASS_WITH_UNRESOLVED_RIGHTS"
            and report["rights_binding"] == "UNRESOLVED_TYPED_POLICY"
            and report["resolved_policy_ids"] == []
            for report in typed_cases.values()
        )
        and ambiguous["report"]["status"] == "PASS_WITH_UNRESOLVED_RIGHTS"
        and ambiguous["report"]["rights_binding"] == "UNRESOLVED_TYPED_POLICY"
    ) else "FAIL",
    "cases": typed_cases,
    "ambiguous": ambiguous,
}

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
real_mutation = rejection(lambda: build_abbott_case_inputs(real_copy), "runtime JSON hash")

summary = {
    "format": "ht-m1-closure-reproduction-v1",
    "status": "PASS" if all(item["status"] == "PASS" for item in (
        rights_projection_checks, synthetic_runtime_mutation, typed_policy_checks, real_mutation,
    )) else "FAIL",
    "source_commit": args.source_commit,
    "fixture_import": "tests/test_healthtech_repairs.py",
    "rights_projection": rights_projection_checks,
    "synthetic_runtime_mutation": synthetic_runtime_mutation,
    "typed_policy": typed_policy_checks,
    "real_manifest": {
        "cohort_label": "local frozen Abbott development copy",
        "manifest_integrity_format": manifest.get("integrity_format"),
        "raw_files_declared": len(manifest["raw_files"]),
        "files_copied": len(copy_records),
        "copied_bytes": sum(int(item["bytes"]) for item in copy_records),
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
print(json.dumps(summary, indent=2, sort_keys=True))
if summary["status"] != "PASS":
    raise SystemExit(1)
