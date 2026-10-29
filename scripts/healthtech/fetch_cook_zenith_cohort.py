"""Acquire a bounded Cook Medical Zenith product-marking cohort."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import shutil
import sys
from urllib.parse import quote
from urllib.error import HTTPError

import fitz

_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "src"))

from patent_to_pilot.healthtech.contracts import canonical_patent_id, content_hash
from scripts.healthtech.fetch_public_device_cohort import (
    Accounting,
    _fetch,
    _patent_document,
    _selected_pma_record,
)


COOK_PAGE_URL = "https://www.cookmedical.com/patents/"
COOK_PDF_URL = (
    "https://www.cookmedical.com/wp-content/uploads/2025/01/"
    "US-Patents-List-for-US-website-2025.2.pdf"
)
COOK_DISCLOSURE_SOURCE_ID = "cook-medical-patent-marking"
COOK_RIGHTS_POLICY_ID = "cook-medical-patent-marking"
COOK_COMPANY = "Cook Medical"

PRODUCTS = (
    {
        "key": "zenith-flex-aaa",
        "label": "Zenith Flex AAA Endovascular Graft",
        "display_name": "Zenith Flex AAA Endovascular Graft",
        "pma_number": "P020018",
        "patent_numbers": ["7335224", "7294147"],
    },
    {
        "key": "zenith-renu-converter",
        "label": "Zenith Renu AAA Ancillary Graft Converter",
        "display_name": "Zenith Renu AAA Ancillary Graft Converter",
        "pma_number": "P020018",
        "patent_numbers": ["7335224"],
    },
    {
        "key": "zenith-dissection-stent",
        "label": "Zenith Dissection Endovascular Stent",
        "display_name": "Zenith Dissection Endovascular Stent",
        "pma_number": "P180001",
        "patent_numbers": ["7993383", "9278017"],
    },
)

PMA_ALLOWED = {
    "pma_number", "supplement_number", "applicant", "generic_name", "trade_name",
    "product_code", "advisory_committee", "advisory_committee_description",
    "decision_date", "decision_code", "date_received", "supplement_reason",
    "supplement_type", "ao_statement", "openfda",
}


def _write_json(path: Path, payload: object, accounting: Accounting) -> None:
    data = (json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    accounting.storage(len(data))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def _normalized_text(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def _validate_product_rows(pdf_path: Path) -> dict[str, dict[str, object]]:
    """Validate each predeclared Cook product row against the official PDF."""
    document = fitz.open(pdf_path)
    pages = [page.get_text("text") for page in document]
    rows: dict[str, dict[str, object]] = {}
    for product in PRODUCTS:
        expected_name = _normalized_text(str(product["label"]))
        expected_numbers = [str(value) for value in product["patent_numbers"]]
        matches: list[int] = []
        disclosure_parts: list[str] = []
        for page_number, text in enumerate(pages, start=1):
            if expected_name not in _normalized_text(text):
                continue
            found = {value.replace(",", "") for value in re.findall(r"(?<!\d)(\d[\d,]{6,10})(?!\d)", text)}
            if not set(expected_numbers).issubset(found):
                continue
            matches.append(page_number)
            disclosure_parts.append(text.strip())
        if not matches:
            raise ValueError(
                f"expected Cook patent row not found for {product['label']} "
                f"with patents {expected_numbers}"
            )
        rows[str(product["key"])] = {
            "label": str(product["label"]),
            "display_name": str(product["display_name"]),
            "raw_patent_numbers": expected_numbers,
            "source_locator": "pdf-pages:" + ",".join(str(value) for value in matches),
            "disclosure_text": "\n\n".join(disclosure_parts),
        }
    return rows


def _pma_payload(record: dict) -> dict:
    return {key: record[key] for key in sorted(record) if key in PMA_ALLOWED}


def _fetch_pma(
    pma_number: str,
    output: Path,
    accounting: Accounting,
    retrieved_at: datetime,
    max_file_bytes: int,
) -> tuple[dict, dict, dict]:
    url = f"https://api.fda.gov/device/pma.json?search=pma_number:{quote(pma_number)}&limit=100"
    raw_path = output / "raw" / "pma" / f"{pma_number}.json"
    raw_bytes, raw_sha256 = _fetch(url, raw_path, accounting, max_file_bytes=max_file_bytes)
    response = json.loads(raw_bytes.decode("utf-8"))
    rows = response.get("results") if isinstance(response, dict) else None
    if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
        raise ValueError(f"PMA response malformed: {pma_number}")
    record = _selected_pma_record(rows)
    supplement = str(record.get("supplement_number") or "BASE")
    meta = response.get("meta") if isinstance(response, dict) else None
    last_updated = meta.get("last_updated") if isinstance(meta, dict) else None
    source_id = f"openfda-pma-{pma_number.lower()}-{supplement.lower()}"
    payload = _pma_payload(record)
    source = {
        "source_id": source_id,
        "source_type": "regulatory_record",
        "url": url,
        "revision": f"openfda-meta-last-updated-{last_updated or 'unknown'}",
        "retrieved_at_utc": retrieved_at.isoformat(),
        "jurisdiction": "US",
        "raw_json_sha256": raw_sha256,
        "payload_sha256": content_hash(payload),
        "payload": payload,
        "rights_policy_id": "openfda-pma-records",
        "rights": "openFDA/FDA terms and field-specific rights apply; preserve attribution",
        "runtime_allowed": True,
    }
    raw_file = {
        "path": raw_path.relative_to(output).as_posix(),
        "bytes": len(raw_bytes),
        "sha256": raw_sha256,
        "url": url,
        "role": "pma-response",
    }
    return record, source, raw_file


def _validate_runtime_separation(runtime: dict) -> None:
    runtime_sources = {
        str(device.get("source_id"))
        for device in runtime.get("devices", [])
        if isinstance(device, dict) and device.get("source_id")
    }
    runtime_sources.update(
        str(patent.get("source_id"))
        for patent in runtime.get("patents", [])
        if isinstance(patent, dict) and patent.get("source_id")
    )
    if COOK_DISCLOSURE_SOURCE_ID in runtime_sources:
        raise ValueError("Cook disclosure source leaked into runtime sources")
    forbidden = {"references", "disclosure_evidence", "family_mapping", "split", "final_holdout"}
    leaked = sorted(forbidden.intersection(runtime))
    if leaked:
        raise ValueError(f"runtime evaluator fields leaked: {leaked}")
    exclusions = " ".join(str(value).lower() for value in runtime.get("runtime_exclusions", []))
    for required in ("disclosure", "evaluator", "split"):
        if required not in exclusions:
            raise ValueError(f"runtime_exclusions must mention {required}")


def _fetch_patent(
    number: str,
    output: Path,
    accounting: Accounting,
    retrieved,
    max_file_bytes: int,
) -> tuple[dict, dict]:
    last_error: Exception | None = None
    for kind in ("B2", "B1"):
        canonical = canonical_patent_id(f"US{number}{kind}")
        url = f"https://patents.google.com/patent/{canonical}/en"
        raw_path = output / "raw" / "patents" / f"{canonical}.html"
        try:
            page_html, raw_sha256 = _fetch(url, raw_path, accounting, max_file_bytes=max_file_bytes)
        except HTTPError as exc:
            last_error = exc
            if exc.code == 404:
                continue
            raise
        patent = _patent_document(
            page_html,
            canonical=canonical,
            url=url,
            raw_number=number,
            retrieved=retrieved,
            raw_sha256=raw_sha256,
        )
        patent.update({
            "company_metadata": COOK_COMPANY,
            "company_metadata_basis": "Cook Medical official product patent-marking PDF; not an independently verified assignee field",
        })
        return patent, {
            "path": raw_path.relative_to(output).as_posix(),
            "bytes": len(page_html),
            "sha256": raw_sha256,
            "url": url,
            "role": "patent-page",
        }
    raise ValueError(f"no public US grant page found for {number}: {last_error}")


def _freeze_groups(references: dict[str, list[str]], universe: list[str]) -> tuple[dict, dict, dict]:
    disclosed_sets = {query_id: set(values) for query_id, values in references.items()}
    remaining = set(disclosed_sets)
    groups: list[dict] = []
    while remaining:
        root = min(remaining)
        group = {root}
        changed = True
        while changed:
            changed = False
            for query_id in sorted(remaining - group):
                if any(disclosed_sets[query_id] & disclosed_sets[member] for member in group):
                    group.add(query_id)
                    changed = True
        remaining -= group
        members = sorted(group)
        shared = set(universe)
        for query_id in members:
            shared &= disclosed_sets[query_id]
        groups.append({
            "group_id": "shared-exact-" + content_hash(members)[:12],
            "device_query_ids": members,
            "shared_patent_ids": sorted(shared),
            "basis": "Same canonical patent document appears in Cook Medical product-marking rows.",
            "source_ids": [COOK_DISCLOSURE_SOURCE_ID],
            "family_id": None,
            "family_status": "UNKNOWN_NOT_ASSUMED",
        })
    distractors = {
        query_id: sorted(set(universe) - disclosed_sets[query_id])
        for query_id in sorted(disclosed_sets)
    }
    groups_payload = {
        "format": "ht-group-evidence-v1",
        "status": "DEVELOPMENT_ONLY_FREEZE_NO_HOLDOUT",
        "shared_exact_patent_groups": [group["device_query_ids"] for group in groups],
        "group_evidence": groups,
        "company_groups": [{
            "company": COOK_COMPANY,
            "query_ids": sorted(references),
            "basis": "Cook Medical official patent-marking source, with FDA applicants retained on device rows",
            "source_ids": [COOK_DISCLOSURE_SOURCE_ID],
        }],
        "family_mapping": {"status": "UNKNOWN_NOT_ASSUMED", "mappings": []},
        "overlap_notes": [
            "Zenith Flex AAA and Zenith Renu share exact patent US7335224 in the bounded Cook marking extract.",
            "No family merge is inferred without a sourced family mapping.",
        ],
    }
    split = {
        "format": "ht-development-split-v1",
        "status": "DEVELOPMENT_ONLY_NO_GENERALIZATION_CLAIM",
        "assignment_rule": "All three predeclared Cook product rows remain in development; no final holdout is claimed for this single-company cohort.",
        "seed": 0,
        "rows": [
            {
                "query_id": query_id,
                "split": "development",
                "group_id": next(group["group_id"] for group in groups if query_id in group["device_query_ids"]),
            }
            for query_id in sorted(references)
        ],
        "final_holdout": [],
    }
    return {"by_query": distractors}, groups_payload, split


def _write_manifest(output: Path, manifest: dict, accounting: Accounting) -> None:
    before = accounting.stored
    size = 0
    for _ in range(10):
        manifest["accounting"]["manifest_bytes"] = size
        manifest["accounting"]["actual_stored_bytes"] = before + size
        data = (json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
        next_size = len(data)
        if next_size == size:
            break
        size = next_size
    else:
        raise ValueError("manifest accounting did not converge")
    accounting.storage(size)
    manifest["accounting"]["manifest_bytes"] = size
    manifest["accounting"]["actual_stored_bytes"] = accounting.stored
    data = (json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    if len(data) != size:
        raise ValueError("manifest accounting changed after finalization")
    (output / "manifest.json").write_bytes(data)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--max-transfer-bytes", type=int, default=40_000_000)
    parser.add_argument("--max-storage-bytes", type=int, default=80_000_000)
    parser.add_argument("--max-file-bytes", type=int, default=30_000_000)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("output already exists; choose a fresh directory")
    if shutil.disk_usage(args.output.parent.resolve()).free < args.max_storage_bytes:
        parser.error("free disk is below the configured storage cap")

    output = args.output.resolve()
    (output / "raw" / "pma").mkdir(parents=True)
    (output / "raw" / "patents").mkdir(parents=True)
    (output / "raw" / "disclosure").mkdir(parents=True)
    (output / "evaluator").mkdir(parents=True)
    accounting = Accounting(args.max_transfer_bytes, args.max_storage_bytes)
    retrieved_at = datetime.now(timezone.utc)
    retrieved = retrieved_at.date()
    raw_files: list[dict[str, object]] = []
    regulatory_sources: dict[str, dict] = {}
    records: dict[str, dict] = {}

    for pma_number in sorted({str(product["pma_number"]) for product in PRODUCTS}):
        record, source, raw_file = _fetch_pma(
            pma_number, output, accounting, retrieved_at, args.max_file_bytes
        )
        records[pma_number] = record
        regulatory_sources[str(source["source_id"])] = source
        raw_files.append(raw_file)

    page_path = output / "raw" / "disclosure" / "cook-patents.html"
    page_bytes, page_sha256 = _fetch(COOK_PAGE_URL, page_path, accounting, max_file_bytes=args.max_file_bytes)
    pdf_path = output / "raw" / "disclosure" / "US-Patents-List-for-US-website-2025.2.pdf"
    pdf_bytes, pdf_sha256 = _fetch(COOK_PDF_URL, pdf_path, accounting, max_file_bytes=args.max_file_bytes)
    product_rows = _validate_product_rows(pdf_path)
    raw_files.extend([
        {
            "path": page_path.relative_to(output).as_posix(),
            "bytes": len(page_bytes),
            "sha256": page_sha256,
            "url": COOK_PAGE_URL,
            "role": "patent-marking-page",
        },
        {
            "path": pdf_path.relative_to(output).as_posix(),
            "bytes": len(pdf_bytes),
            "sha256": pdf_sha256,
            "url": COOK_PDF_URL,
            "role": "patent-marking-pdf",
        },
    ])
    disclosure_source = {
        "source_id": COOK_DISCLOSURE_SOURCE_ID,
        "source_type": "independent_disclosure",
        "url": COOK_PAGE_URL,
        "linked_document_url": COOK_PDF_URL,
        "revision": "pdf-updated-2025-01-06-retrieved-" + retrieved.isoformat(),
        "retrieved_at_utc": retrieved_at.isoformat(),
        "jurisdiction": "US",
        "raw_html_sha256": page_sha256,
        "pdf_sha256": pdf_sha256,
        "rights_policy_id": COOK_RIGHTS_POLICY_ID,
        "rights": "Official Cook product-level patent-marking source retained for local research; no redistribution license established.",
        "runtime_allowed": False,
    }

    devices: list[dict] = []
    references: dict[str, list[str]] = {}
    disclosure_evidence: list[dict] = []
    for product in PRODUCTS:
        key = str(product["key"])
        pma_number = str(product["pma_number"])
        record = records[pma_number]
        source_id = next(
            source_id for source_id, source in regulatory_sources.items()
            if str(source["source_id"]).startswith(f"openfda-pma-{pma_number.lower()}-")
        )
        query_id = f"HT-DEV-COOK-{key.upper()}"
        device_id = f"{pma_number}:{key.upper()}"
        devices.append({
            "query_id": query_id,
            "device_id_raw": f"{product['display_name']} ({device_id})",
            "device_id_canonical": device_id,
            "pma_number": pma_number,
            "supplement_number": str(record.get("supplement_number") or "BASE"),
            "company": COOK_COMPANY,
            "regulatory_applicant": str(record.get("applicant") or ""),
            "trade_name": str(product["display_name"]),
            "generic_name": str(record.get("generic_name") or ""),
            "product_code": str(record.get("product_code") or ""),
            "technical_description": "; ".join(value for value in (
                str(product["display_name"]), str(record.get("generic_name") or ""),
                f"product code {record.get('product_code') or ''}",
            ) if value),
            "features_of_interest": [value for value in (
                str(product["display_name"]), str(record.get("generic_name") or ""),
                str(record.get("product_code") or ""),
            ) if value],
            "source_id": source_id,
            "evidence_cutoff": retrieved.isoformat(),
        })

    patents: list[dict] = []
    patent_files: list[dict] = []
    all_numbers = sorted({number for product in PRODUCTS for number in product["patent_numbers"]})
    for number in all_numbers:
        patent, raw_file = _fetch_patent(str(number), output, accounting, retrieved, args.max_file_bytes)
        patents.append(patent)
        patent_files.append(raw_file)
    patents.sort(key=lambda row: row["patent_id_canonical"])
    by_raw = {str(patent["patent_id_raw"]): str(patent["patent_id_canonical"]) for patent in patents}

    for product in PRODUCTS:
        key = str(product["key"])
        row = product_rows[key]
        query_id = f"HT-DEV-COOK-{key.upper()}"
        canonical_ids = [by_raw[number] for number in row["raw_patent_numbers"]]
        references[query_id] = canonical_ids
        disclosure_evidence.append({
            "evidence_id": f"DISC-{query_id}",
            "query_id": query_id,
            "patent_id_raw": list(row["raw_patent_numbers"]),
            "patent_id_canonical": canonical_ids,
            "source_id": COOK_DISCLOSURE_SOURCE_ID,
            "locator": row["source_locator"],
            "quoted_span": row["disclosure_text"],
            "evidence_kind": "patent_disclosure",
            "support_basis": "Cook Medical's official U.S. patent list places these patent numbers on rows for the named Zenith product; product-level documented association only.",
        })

    universe = sorted(patent["patent_id_canonical"] for patent in patents)
    distractors, groups, split = _freeze_groups(references, universe)
    runtime = {
        "format": "ht-runtime-public-device-cohort-v1",
        "status": "RUNTIME_INPUTS_ONLY_NO_EVALUATOR_LABELS",
        "retrieved_at_utc": retrieved_at.isoformat(),
        "devices": devices,
        "patents": [
            {key: patent[key] for key in (
                "patent_id_raw", "patent_id_canonical", "document_kind", "jurisdiction", "title",
                "abstract", "claims", "text", "source_id", "source_revision", "source_url",
                "raw_html_sha256", "normalized_sha256", "source_date", "company_metadata",
                "company_metadata_basis",
            )}
            for patent in patents
        ],
        "permitted_metadata": ["FDA PMA fields", "patent title/abstract/claims", "canonical document IDs"],
        "runtime_exclusions": ["disclosure references", "evaluator gold/reference links", "family labels", "split answers"],
    }
    _validate_runtime_separation(runtime)
    references_payload = {
        "format": "ht-evaluator-disclosures-v1",
        "status": "EVALUATOR_ONLY_REFERENCE_RELATIONS",
        "retrieved_at_utc": retrieved_at.isoformat(),
        "references": references,
        "disclosure_evidence": disclosure_evidence,
        "limitations": [
            "These are product-level patent-marking relationships, not independent expert judgments of component-level claim relevance.",
            "Unlisted device-patent pairs remain unjudged and are never recoded as negatives.",
        ],
    }
    source_registry = {
        "format": "ht-source-registry-v1",
        "separation": "evaluator-only disclosure source is not included in runtime.json",
        "sources": [
            *regulatory_sources.values(),
            disclosure_source,
            *[
                {
                    "source_id": patent["source_id"],
                    "source_type": "patent_document",
                    "url": patent["source_url"],
                    "revision": patent["source_revision"],
                    "retrieved_at_utc": retrieved_at.isoformat(),
                    "jurisdiction": "US",
                    "raw_html_sha256": patent["raw_html_sha256"],
                    "normalized_sha256": patent["normalized_sha256"],
                    "rights_policy_id": "google-patents-pages",
                    "rights": "Google-derived patent page retained for local research; raw HTML and extracted text remain local-only.",
                    "runtime_allowed": True,
                }
                for patent in patents
            ],
        ],
    }
    data_card = {
        "dataset": "Cook Medical Zenith product-marking development cohort",
        "scope": "Three named Cook Medical Zenith rows from the official U.S. patent list, joined to PMA P020018/P180001 and a four-document local patent universe.",
        "selection_rule": "Predeclared Zenith Flex AAA, Zenith Renu AAA Ancillary Graft Converter, and Zenith Dissection Endovascular Stent rows; no retrieval score or evaluator label used.",
        "device_count": len(devices),
        "patent_universe_count": len(universe),
        "reference_pair_count": sum(len(values) for values in references.values()),
        "unjudged_distractor_pair_count": sum(len(values) for values in distractors["by_query"].values()),
        "supported_claims": ["Reproducible local retrieval over a bounded official product-marking cohort", "Source-linked FDA metadata and product-marking locators"],
        "unsupported_claims": ["Exhaustive patent recall", "Claim-level relevance", "Clinical suitability", "FTO", "Patent validity", "Investment merit", "Generalization beyond this development cohort"],
        "rights_boundary": "Local research and offline evaluation only for Cook disclosure and Google-derived patent text; product display and redistribution remain blocked.",
    }
    for relative, payload in (
        ("runtime.json", runtime),
        ("evaluator/references.json", references_payload),
        ("source_registry.json", source_registry),
        ("groups.json", groups),
        ("split_manifest.json", split),
        ("distractors.json", {"format": "ht-unjudged-distractors-v1", "status": "UNJUDGED_NOT_NEGATIVE", **distractors}),
        ("data_card.json", data_card),
    ):
        _write_json(output / relative, payload, accounting)
    manifest = {
        "integrity_format": "ht-runtime-integrity-v1",
        "status": "PUBLIC_COOK_ZENITH_COHORT_ACQUIRED",
        "retrieved_at_utc": retrieved_at.isoformat(),
        "devices": len(devices),
        "patents": len(patents),
        "reference_pairs": sum(len(values) for values in references.values()),
        "unjudged_distractor_pairs": sum(len(values) for values in distractors["by_query"].values()),
        "raw_files": raw_files + patent_files,
        "source_registry": "source_registry.json",
        "runtime_path": "runtime.json",
        "evaluator_path": "evaluator/references.json",
        "groups_path": "groups.json",
        "split_path": "split_manifest.json",
        "distractors_path": "distractors.json",
        "runtime_sha256": content_hash(runtime),
        "references_sha256": content_hash(references_payload),
        "source_registry_sha256": content_hash(source_registry),
        "universe_sha256": content_hash(universe),
        "cohort_sha256": content_hash([device["query_id"] for device in devices]),
        "rights_policy_ids": sorted({str(source["rights_policy_id"]) for source in source_registry["sources"]}),
        "accounting": {
            "transfer_cap_bytes": accounting.transfer_cap,
            "storage_cap_bytes": accounting.storage_cap,
            "actual_transferred_bytes": accounting.transferred,
            "actual_stored_bytes_before_manifest": accounting.stored,
            "manifest_bytes": 0,
        },
        "limitations": data_card["unsupported_claims"] + [
            "Family identity is unknown and not inferred.",
            "The Cook marking list states it may not be all inclusive; unlisted pairs remain unjudged.",
        ],
    }
    _write_manifest(output, manifest, accounting)
    print(json.dumps({
        "status": manifest["status"],
        "output": str(output),
        "devices": len(devices),
        "patents": len(patents),
        "pairs": manifest["reference_pairs"],
        "unjudged_distractor_pairs": manifest["unjudged_distractor_pairs"],
        "transferred_bytes": accounting.transferred,
        "stored_bytes": accounting.stored,
        "provider_calls": 0,
        "paid_cost_usd": 0,
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
