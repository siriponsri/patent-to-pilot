"""Fetch a bounded set of public openFDA 510(k) records into local case inputs."""
from __future__ import annotations

import argparse
from datetime import date, datetime, timezone
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
from urllib.parse import quote
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from patent_to_pilot.healthtech.engine import DossierInput
from patent_to_pilot.healthtech.sources import field_evidence, normalize_510k_record


ALLOWED_FIELDS = {"k_number", "device_name", "applicant", "product_code", "decision_code",
                  "decision_date", "date_received", "statement_or_summary", "clearance_type",
                  "review_advisory_committee"}


@dataclass
class AcquisitionAccounting:
    transfer_cap_bytes: int
    storage_cap_bytes: int
    transferred_bytes: int = 0
    stored_bytes: int = 0

    def record_transfer(self, count: int) -> None:
        self.transferred_bytes += count
        if self.transferred_bytes > self.transfer_cap_bytes:
            raise ValueError(
                f"cumulative transfer cap exceeded: {self.transferred_bytes} > {self.transfer_cap_bytes}"
            )

    def reserve_storage(self, count: int) -> None:
        if count < 0:
            raise ValueError("storage reservation must be nonnegative")
        if self.stored_bytes + count > self.storage_cap_bytes:
            raise ValueError(
                f"cumulative storage cap exceeded: {self.stored_bytes + count} > {self.storage_cap_bytes}"
            )

    def record_storage(self, count: int) -> None:
        self.reserve_storage(count)
        self.stored_bytes += count


def _download(url: str, destination: Path, max_bytes: int, accounting: AcquisitionAccounting) -> tuple[dict, str, int]:
    request = Request(url, headers={"User-Agent": "patent-to-pilot-public-case-prep"})
    digest = hashlib.sha256()
    total = 0
    part_path = destination.with_name(destination.name + ".part")
    part_path.unlink(missing_ok=True)
    try:
        with urlopen(request, timeout=30) as response, part_path.open("wb") as handle:
            declared = response.headers.get("Content-Length")
            if declared and int(declared) > max_bytes:
                raise ValueError(f"response exceeds per-file transfer cap: {declared} > {max_bytes}")
            while True:
                chunk = response.read(64 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                accounting.record_transfer(len(chunk))
                if total > max_bytes:
                    raise ValueError("response exceeds per-file transfer cap")
                handle.write(chunk)
                digest.update(chunk)
            handle.flush()
            os.fsync(handle.fileno())
        payload = json.loads(part_path.read_text(encoding="utf-8"))
        accounting.reserve_storage(part_path.stat().st_size)
        os.replace(part_path, destination)
        accounting.record_storage(destination.stat().st_size)
        return payload, digest.hexdigest(), total
    except Exception:
        part_path.unlink(missing_ok=True)
        raise


def _input_for(record: dict, source, *, retrieved: date, language: str) -> dict:
    k_number = record["k_number"]
    device_name = record["device_name"]
    applicant = record.get("applicant")
    product_code = record.get("product_code")
    evidence = [field_evidence(source, field, f"{k_number}-{field}").model_dump(mode="json")
                for field in ("k_number", "device_name", "applicant", "product_code", "decision_code",
                              "decision_date", "date_received")
                if isinstance(source.payload, dict) and field in source.payload]
    features = [product_code] if isinstance(product_code, str) and product_code else []
    query = {
        "query_id": f"HT-PUBLIC-{k_number}",
        "brief": {
            "project_id": f"ht-public-{k_number.lower()}",
            "version": 1,
            "objective": f"Prepare a public-source evidence dossier for named device record {k_number}.",
            "audience": "entrepreneur",
            "data_class": "public",
            "language": language,
            "theme": "formal-light",
        },
        "device_id_raw": f"{device_name} ({k_number})",
        "device_id_canonical": k_number,
        "selected_comparator_source_id": source.source.source_id,
        "technical_description": device_name,
        "features_of_interest": features,
        "user_questions": [
            "Request independent device–patent disclosure evidence before interpreting any candidate.",
            "Treat the regulatory record as a source fact, not as clinical endorsement or patent linkage.",
        ],
        "company_metadata": {"applicant": applicant} if isinstance(applicant, str) and applicant else {},
        "company_source_id": source.source.source_id if isinstance(applicant, str) and applicant else None,
        "jurisdiction": "US",
        "evidence_cutoff": str(retrieved),
        "permitted_inputs": [source.source.source_id],
        "acquisition_budget": {"max_search_calls": 1, "max_returned_candidates": 20, "accounting": "offline_counts"},
    }
    payload = {
        "query": query,
        "sources": [source.model_dump(mode="json")],
        "patents": [],
        "evidence": evidence,
        "policy_id": "HT-B0b",
        "per_search_limit": 20,
    }
    DossierInput.model_validate(payload)
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--k-number", action="append", required=True, help="one or more K/denovo identifiers")
    parser.add_argument("--output", type=Path, required=True, help="fresh output directory")
    parser.add_argument("--language", choices=("en", "th"), default="en")
    parser.add_argument("--max-transfer-bytes", type=int, default=10_000_000)
    parser.add_argument("--max-storage-bytes", type=int, default=50_000_000)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("output already exists; select a fresh directory")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if shutil.disk_usage(args.output.parent.resolve()).free < args.max_storage_bytes:
        parser.error("free disk is below the configured storage cap")
    args.output.mkdir(parents=True)
    raw_dir = args.output / "raw"
    input_dir = args.output / "inputs"
    raw_dir.mkdir()
    input_dir.mkdir()
    accounting = AcquisitionAccounting(args.max_transfer_bytes * len(args.k_number), args.max_storage_bytes)
    retrieved_at = datetime.now(timezone.utc)
    retrieved_date = retrieved_at.date()
    records = []
    for raw_k in args.k_number:
        k_number = raw_k.upper().strip()
        if not k_number.startswith("K"):
            parser.error(f"unsupported 510(k) identifier: {raw_k}")
        url = f"https://api.fda.gov/device/510k.json?search=k_number:{quote(k_number)}&limit=1"
        raw_path = raw_dir / f"{k_number}.json"
        raw_response, raw_sha256, raw_bytes = _download(url, raw_path, args.max_transfer_bytes, accounting)
        results = raw_response.get("results") if isinstance(raw_response, dict) else None
        if not isinstance(results, list) or len(results) != 1 or not isinstance(results[0], dict):
            raise ValueError(f"openFDA returned no unique record for {k_number}")
        record = results[0]
        source_id = f"openfda-510k-{k_number.lower()}"
        source = normalize_510k_record(record, source_id=source_id, snapshot_revision=f"openfda-retrieved-{retrieved_date}", retrieved_date=retrieved_date)
        input_path = input_dir / f"{k_number}.json"
        input_payload = _input_for(record, source, retrieved=retrieved_date, language=args.language)
        normalized_text = json.dumps(input_payload, ensure_ascii=False, indent=2) + "\n"
        normalized_bytes = len(normalized_text.encode("utf-8"))
        accounting.record_storage(normalized_bytes)
        input_path.write_bytes(normalized_text.encode("utf-8"))
        records.append({
            "k_number": k_number,
            "request_url": url,
            "raw_path": str(raw_path),
            "raw_bytes": raw_bytes,
            "raw_sha256": raw_sha256,
            "normalized_bytes": normalized_bytes,
            "normalized_sha256": source.source.sha256,
            "normalized_fields": sorted(source.payload.keys()),
            "excluded_fields": sorted(set(record) - ALLOWED_FIELDS),
            "rights": "openFDA/FDA terms and field-specific rights apply; preserve attribution",
            "input_path": str(input_path),
        })
    manifest = {
        "status": "PUBLIC_SOURCE_SNAPSHOT_PREPARED",
        "source": "openFDA 510(k)",
        "retrieved_at_utc": retrieved_at.isoformat(),
        "transfer_cap_bytes": args.max_transfer_bytes,
        "storage_cap_bytes": args.max_storage_bytes,
        "records": records,
        "limitations": [
            "Selected 510(k) records are regulatory source facts only; they do not establish clinical suitability, approval beyond the source code, FTO, patent validity, or device–patent disclosure.",
            "No patent corpus was acquired in this batch; dossier retrieval therefore reports an explicit unresolved candidate gap.",
            "Raw third-party responses remain in local ignored output and are not intended for Git publication.",
        ],
        "accounting": {
            "transfer_cap_bytes": accounting.transfer_cap_bytes,
            "storage_cap_bytes": accounting.storage_cap_bytes,
            "actual_transferred_bytes": accounting.transferred_bytes,
            "actual_stored_bytes_before_manifest": accounting.stored_bytes,
            "manifest_bytes": 0,
        },
    }
    stored_before_manifest = accounting.stored_bytes
    manifest_bytes = 0
    manifest_text = ""
    for _ in range(10):
        manifest["accounting"]["manifest_bytes"] = manifest_bytes
        manifest["accounting"]["actual_stored_bytes"] = stored_before_manifest + manifest_bytes
        manifest_text = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
        next_manifest_bytes = len(manifest_text.encode("utf-8"))
        if next_manifest_bytes == manifest_bytes:
            break
        manifest_bytes = next_manifest_bytes
    else:
        raise ValueError("manifest accounting did not reach a stable byte count")
    accounting.record_storage(manifest_bytes)
    manifest["accounting"]["manifest_bytes"] = manifest_bytes
    manifest["accounting"]["actual_stored_bytes"] = accounting.stored_bytes
    manifest_text = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    if len(manifest_text.encode("utf-8")) != manifest_bytes:
        raise ValueError("manifest byte accounting changed after finalization")
    (args.output / "manifest.json").write_bytes(manifest_text.encode("utf-8"))
    print(json.dumps({"status": manifest["status"], "output": str(args.output), "records": len(records), "raw_bytes": sum(item["raw_bytes"] for item in records), "provider_calls": 0, "paid_cost_usd": 0}, ensure_ascii=False))


if __name__ == "__main__":
    main()
