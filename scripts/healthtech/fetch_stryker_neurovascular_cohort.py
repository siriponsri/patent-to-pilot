"""Acquire a bounded Stryker Neurovascular product-marking cohort."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import shutil
import sys
from urllib.error import HTTPError
from urllib.parse import quote

from bs4 import BeautifulSoup

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


STRYKER_PAGE_URL = (
    "https://www.stryker.com/us/en/about/patents/"
    "neurovascular-intervention-patents.html"
)

PRODUCTS = (
    {
        "key": "neuroform-atlas",
        "label": "NeuroForm Atlas Stent System",
        "display_name": "NeuroForm Atlas Stent System",
        "regulatory_kind": "pma",
        "regulatory_id": "P180031",
        "patent_numbers": ["7037330"],
    },
    {
        "key": "target-xl-360-soft",
        "label": "Target XL 360 Soft Detachable Coils",
        "display_name": "Target XL 360 Soft Detachable Coils",
        "regulatory_kind": "510k",
        "regulatory_id": "K252694",
        "patent_numbers": ["8202292", "9055948", "9265504", "9314250", "9504475"],
    },
    {
        "key": "trevo-provue",
        "label": "Trevo ProVue Retrievers",
        "display_name": "Trevo ProVue Retrievers",
        "regulatory_kind": "510k",
        "regulatory_id": "K223305",
        "patent_numbers": [
            "8357179",
            "8529596",
            "8795317",
            "8795345",
            "9044263",
            "9072537",
            "9700331",
        ],
    },
)

PMA_ALLOWED = {
    "pma_number", "supplement_number", "applicant", "generic_name", "trade_name",
    "product_code", "advisory_committee", "advisory_committee_description",
    "decision_date", "decision_code", "date_received", "supplement_reason",
    "supplement_type", "ao_statement", "openfda",
}
K510_ALLOWED = {
    "k_number", "device_name", "applicant", "product_code", "decision_code",
    "decision_date", "date_received", "statement_or_summary", "clearance_type",
    "review_advisory_committee",
}


def _write_json(path: Path, payload: object, accounting: Accounting) -> None:
    data = (json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    accounting.storage(len(data))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def _normalized_product_name(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def _validate_product_rows(page_html: bytes) -> dict[str, dict[str, object]]:
    """Extract and validate the three predeclared rows from the Stryker table."""
    soup = BeautifulSoup(page_html, "html.parser")
    rows: dict[str, dict[str, object]] = {}
    table_rows = soup.select("table tr")
    for product in PRODUCTS:
        matches: list[tuple[int, list[str]]] = []
        expected_name = _normalized_product_name(str(product["label"]))
        for index, row in enumerate(table_rows):
            cells = [cell.get_text(" ", strip=True) for cell in row.find_all("td")]
            if len(cells) >= 4 and _normalized_product_name(cells[1]) == expected_name:
                matches.append((index, cells))
        if len(matches) != 1:
            raise ValueError(f"expected one Stryker patent row for {product['label']}, found {len(matches)}")
        row_index, cells = matches[0]
        found = [value.replace(",", "") for value in re.findall(r"(?<!\d)(\d[\d,]{6,10})(?!\d)", cells[3])]
        expected = [str(value) for value in product["patent_numbers"]]
        if found != expected:
            raise ValueError(f"unexpected Stryker patent row for {product['label']}: {found}")
        rows[str(product["key"])] = {
            "label": str(product["label"]),
            "display_name": str(product["display_name"]),
            "raw_patent_numbers": expected,
            "source_locator": f"html-table:row={row_index};product={cells[1]}",
            "disclosure_text": " | ".join(cells),
        }
    return rows


def _pma_payload(record: dict) -> dict:
    return {key: record[key] for key in sorted(record) if key in PMA_ALLOWED}


def _510k_payload(record: dict) -> dict:
    return {key: record[key] for key in sorted(record) if key in K510_ALLOWED}


def _source_policy_id(regulatory_kind: str) -> str:
    if regulatory_kind == "pma":
        return "openfda-pma-records"
    if regulatory_kind == "510k":
        return "openfda-510k-records"
    raise ValueError(f"unsupported regulatory kind: {regulatory_kind}")


def _validate_runtime_separation(runtime: dict, disclosure_source_id: str) -> None:
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
    if disclosure_source_id in runtime_sources:
        raise ValueError("evaluator disclosure source leaked into runtime sources")
    forbidden = {"references", "disclosure_evidence", "family_mapping", "split", "final_holdout"}
    leaked = sorted(forbidden.intersection(runtime))
    if leaked:
        raise ValueError(f"evaluator fields leaked into runtime: {leaked}")
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
            "company_metadata": "STRYKER NEUROVASCULAR",
            "company_metadata_basis": "Stryker product-marking page; not an independently verified assignee field",
        })
        return patent, {
            "path": raw_path.relative_to(output).as_posix(),
            "bytes": len(page_html),
            "sha256": raw_sha256,
            "url": url,
        }
    raise ValueError(f"no public US grant page found for {number}: {last_error}")


def _fetch_regulatory(
    product: dict[str, object],
    output: Path,
    accounting: Accounting,
    retrieved_at: datetime,
    max_file_bytes: int,
) -> tuple[dict, dict, dict]:
    kind = str(product["regulatory_kind"])
    identifier = str(product["regulatory_id"])
    if kind == "pma":
        url = f"https://api.fda.gov/device/pma.json?search=pma_number:{quote(identifier)}&limit=100"
        raw_path = output / "raw" / "pma" / f"{identifier}.json"
    elif kind == "510k":
        url = f"https://api.fda.gov/device/510k.json?search=k_number:{quote(identifier)}&limit=10"
        raw_path = output / "raw" / "510k" / f"{identifier}.json"
    else:
        raise ValueError(f"unsupported regulatory kind: {kind}")
    raw_bytes, raw_sha256 = _fetch(url, raw_path, accounting, max_file_bytes=max_file_bytes)
    response = json.loads(raw_bytes.decode("utf-8"))
    rows = response.get("results") if isinstance(response, dict) else None
    if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
        raise ValueError(f"regulatory response malformed: {identifier}")
    if kind == "pma":
        record = _selected_pma_record(rows)
        supplement = str(record.get("supplement_number") or "BASE")
        source_id = f"openfda-pma-{identifier.lower()}-{supplement.lower()}"
        payload = _pma_payload(record)
        device_id = f"{identifier}:{supplement}"
        trade_name = str(record.get("trade_name") or product["display_name"])
        generic_name = str(record.get("generic_name") or "")
        product_code = str(record.get("product_code") or "")
    else:
        if len(rows) != 1:
            raise ValueError(f"expected one 510(k) record: {identifier}")
        record = rows[0]
        source_id = f"openfda-510k-{identifier.lower()}"
        payload = _510k_payload(record)
        device_id = identifier
        trade_name = str(record.get("device_name") or product["display_name"])
        generic_name = str(record.get("device_name") or "")
        product_code = str(record.get("product_code") or "")
    meta = response.get("meta") if isinstance(response, dict) else None
    last_updated = meta.get("last_updated") if isinstance(meta, dict) else None
    revision = f"openfda-meta-last-updated-{last_updated or 'unknown'}"
    source = {
        "source_id": source_id,
        "source_type": "regulatory_record",
        "url": url,
        "revision": revision,
        "retrieved_at_utc": retrieved_at.isoformat(),
        "jurisdiction": "US",
        "raw_json_sha256": raw_sha256,
        "payload_sha256": content_hash(payload),
        "payload": payload,
        "rights_policy_id": _source_policy_id(kind),
        "rights": "openFDA/FDA terms and field-specific rights apply; preserve attribution",
        "runtime_allowed": True,
    }
    device = {
        "query_id": f"HT-DEV-{str(product['key']).upper()}",
        "device_id_raw": f"{trade_name} ({device_id})",
        "device_id_canonical": device_id,
        "regulatory_id": identifier,
        "regulatory_kind": kind,
        "supplement_number": str(record.get("supplement_number") or "BASE") if kind == "pma" else None,
        "company": str(record.get("applicant") or "Stryker Neurovascular"),
        "trade_name": trade_name,
        "generic_name": generic_name,
        "product_code": product_code,
        "technical_description": "; ".join(value for value in (trade_name, generic_name, f"product code {product_code}") if value),
        "features_of_interest": [value for value in (str(product["display_name"]), generic_name, product_code) if value],
        "source_id": source_id,
        "evidence_cutoff": retrieved_at.date().isoformat(),
    }
    raw_file = {
        "path": raw_path.relative_to(output).as_posix(),
        "bytes": len(raw_bytes),
        "sha256": raw_sha256,
        "url": url,
        "role": f"{kind}-response",
    }
    return device, source, raw_file


def _freeze_groups(references: dict[str, list[str]], universe: list[str], source_ids: list[str]) -> tuple[dict, dict, dict]:
    groups = []
    for query_id in sorted(references):
        groups.append({
            "group_id": "shared-exact-" + content_hash([query_id])[:12],
            "device_query_ids": [query_id],
            "shared_patent_ids": sorted(references[query_id]),
            "basis": "No disclosed patent overlap across the three predeclared Stryker product rows.",
            "source_ids": ["stryker-neurovascular-patent-marking"],
            "family_id": None,
            "family_status": "UNKNOWN_NOT_ASSUMED",
        })
    distractors = {
        query_id: sorted(set(universe) - set(values))
        for query_id, values in sorted(references.items())
    }
    group_payload = {
        "format": "ht-group-evidence-v1",
        "status": "DEVELOPMENT_ONLY_FREEZE_NO_HOLDOUT",
        "shared_exact_patent_groups": [group["device_query_ids"] for group in groups],
        "group_evidence": groups,
        "company_groups": [{
            "company": "STRYKER NEUROVASCULAR",
            "query_ids": sorted(references),
            "basis": "FDA applicant fields",
            "source_ids": source_ids,
        }],
        "family_mapping": {"status": "UNKNOWN_NOT_ASSUMED", "mappings": []},
        "overlap_notes": [
            "The three Stryker rows have no shared exact patent document in this bounded marking extract.",
            "All rows share one applicant/company, so company-held-out sensitivity is not estimable.",
            "No family merge is inferred without a sourced family mapping.",
        ],
    }
    split = {
        "format": "ht-development-split-v1",
        "status": "DEVELOPMENT_ONLY_NO_GENERALIZATION_CLAIM",
        "assignment_rule": "All three predeclared Stryker rows remain in development; no final holdout is claimed for this single-company cohort.",
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
    return distractors, group_payload, split


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
        parser.error("free disk is below configured storage cap")

    output = args.output.resolve()
    (output / "raw" / "pma").mkdir(parents=True)
    (output / "raw" / "510k").mkdir(parents=True)
    (output / "raw" / "patents").mkdir(parents=True)
    (output / "raw" / "disclosure").mkdir(parents=True)
    (output / "evaluator").mkdir(parents=True)
    accounting = Accounting(args.max_transfer_bytes, args.max_storage_bytes)
    retrieved_at = datetime.now(timezone.utc)
    retrieved = retrieved_at.date()
    raw_files: list[dict[str, object]] = []
    devices: list[dict] = []
    regulatory_sources: list[dict] = []
    regulatory_source_ids: list[str] = []
    for product in PRODUCTS:
        device, source, raw_file = _fetch_regulatory(
            product, output, accounting, retrieved_at, args.max_file_bytes
        )
        devices.append(device)
        regulatory_sources.append(source)
        regulatory_source_ids.append(str(source["source_id"]))
        raw_files.append(raw_file)

    disclosure_path = output / "raw" / "disclosure" / "stryker-neurovascular-intervention-patents.html"
    page_bytes, page_sha256 = _fetch(
        STRYKER_PAGE_URL,
        disclosure_path,
        accounting,
        max_file_bytes=args.max_file_bytes,
    )
    product_rows = _validate_product_rows(page_bytes)
    raw_files.append({
        "path": disclosure_path.relative_to(output).as_posix(),
        "bytes": len(page_bytes),
        "sha256": page_sha256,
        "url": STRYKER_PAGE_URL,
        "role": "product-patent-marking-page",
    })
    disclosure_source = {
        "source_id": "stryker-neurovascular-patent-marking",
        "source_type": "independent_disclosure",
        "url": STRYKER_PAGE_URL,
        "revision": "page-retrieved-" + retrieved.isoformat(),
        "retrieved_at_utc": retrieved_at.isoformat(),
        "jurisdiction": "US",
        "raw_html_sha256": page_sha256,
        "rights_policy_id": "stryker-neurovascular-product-marking",
        "rights": "Official product-level patent-marking source retained for local research; no redistribution license established.",
        "runtime_allowed": False,
    }

    patents: list[dict] = []
    patent_files: list[dict] = []
    all_numbers = sorted({number for product in PRODUCTS for number in product["patent_numbers"]})
    for number in all_numbers:
        patent, raw_file = _fetch_patent(str(number), output, accounting, retrieved, args.max_file_bytes)
        patents.append(patent)
        patent_files.append(raw_file | {"role": "patent-page"})
    patents.sort(key=lambda row: row["patent_id_canonical"])
    by_raw = {str(patent["patent_id_raw"]): str(patent["patent_id_canonical"]) for patent in patents}

    references: dict[str, list[str]] = {}
    disclosure_evidence: list[dict] = []
    for product in PRODUCTS:
        row = product_rows[str(product["key"])]
        query_id = f"HT-DEV-{str(product['key']).upper()}"
        canonical_ids = [by_raw[number] for number in row["raw_patent_numbers"]]
        references[query_id] = canonical_ids
        disclosure_evidence.extend({
            "evidence_id": f"DISC-{query_id}-{canonical}",
            "query_id": query_id,
            "patent_id_raw": raw_number,
            "patent_id_canonical": canonical,
            "source_id": disclosure_source["source_id"],
            "locator": row["source_locator"],
            "quoted_span": row["disclosure_text"],
            "evidence_kind": "patent_disclosure",
            "support_basis": "Stryker product-marking page lists the U.S. patent number on the named product row; product-level documented association only.",
        } for raw_number, canonical in zip(row["raw_patent_numbers"], canonical_ids))

    universe = sorted(patent["patent_id_canonical"] for patent in patents)
    distractors, groups, split = _freeze_groups(references, universe, regulatory_source_ids)
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
        "permitted_metadata": [
            "FDA PMA/510(k) fields", "patent title/abstract/claims", "canonical document IDs",
        ],
        "runtime_exclusions": [
            "disclosure references", "evaluator gold/reference links", "family labels", "split answers",
        ],
    }
    _validate_runtime_separation(runtime, str(disclosure_source["source_id"]))
    references_payload = {
        "format": "ht-evaluator-disclosures-v1",
        "status": "EVALUATOR_ONLY_REFERENCE_RELATIONS",
        "retrieved_at_utc": retrieved_at.isoformat(),
        "references": references,
        "disclosure_evidence": disclosure_evidence,
        "limitations": [
            "These are product-level public disclosure relationships, not independent expert judgments of component-level claim relevance.",
            "Unlisted device-patent pairs remain unjudged and are never recoded as negatives.",
        ],
    }
    source_registry = {
        "format": "ht-source-registry-v1",
        "separation": "evaluator-only disclosure source is not included in runtime.json",
        "sources": [
            *regulatory_sources,
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
        "dataset": "Stryker Neurovascular product-marking development cohort",
        "scope": "Three named Stryker Neurovascular rows from the official U.S. neurovascular intervention patent-marking page, joined to one PMA, two 510(k) records, and a thirteen-document local patent universe.",
        "selection_rule": "Predeclared NeuroForm Atlas, Target XL 360 Soft, and Trevo ProVue rows; no retrieval score or evaluator label used.",
        "device_count": len(devices),
        "patent_universe_count": len(universe),
        "reference_pair_count": sum(len(values) for values in references.values()),
        "unjudged_distractor_pair_count": sum(len(values) for values in distractors.values()),
        "supported_claims": [
            "Reproducible local retrieval over a bounded official product-marking cohort",
            "Source-linked FDA metadata and product-marking locators",
        ],
        "unsupported_claims": [
            "Exhaustive patent recall", "Claim-level relevance", "Clinical suitability", "FTO",
            "Patent validity", "Investment merit", "Generalization beyond this development cohort",
        ],
        "rights_boundary": "Local research and offline evaluation only for Stryker disclosure and Google-derived patent text; product display and redistribution remain blocked.",
    }
    for relative, payload in (
        ("runtime.json", runtime),
        ("evaluator/references.json", references_payload),
        ("source_registry.json", source_registry),
        ("groups.json", groups),
        ("split_manifest.json", split),
        ("distractors.json", {"format": "ht-unjudged-distractors-v1", "status": "UNJUDGED_NOT_NEGATIVE", "by_query": distractors}),
        ("data_card.json", data_card),
    ):
        _write_json(output / relative, payload, accounting)
    manifest = {
        "status": "PUBLIC_STRYKER_NEUROVASCULAR_COHORT_ACQUIRED",
        "retrieved_at_utc": retrieved_at.isoformat(),
        "devices": len(devices),
        "patents": len(patents),
        "reference_pairs": sum(len(values) for values in references.values()),
        "unjudged_distractor_pairs": sum(len(values) for values in distractors.values()),
        "raw_files": raw_files + patent_files,
        "source_registry": "source_registry.json",
        "runtime_path": "runtime.json",
        "evaluator_path": "evaluator/references.json",
        "groups_path": "groups.json",
        "split_path": "split_manifest.json",
        "distractors_path": "distractors.json",
        "runtime_sha256": content_hash(runtime),
        "references_sha256": content_hash(references_payload),
        "universe_sha256": content_hash(universe),
        "cohort_sha256": content_hash([device["query_id"] for device in devices]),
        "source_registry_sha256": content_hash(source_registry),
        "rights_policy_ids": [
            "openfda-pma-records", "openfda-510k-records", "stryker-neurovascular-product-marking",
            "google-patents-pages",
        ],
        "accounting": {
            "transfer_cap_bytes": accounting.transfer_cap,
            "storage_cap_bytes": accounting.storage_cap,
            "actual_transferred_bytes": accounting.transferred,
            "actual_stored_bytes_before_manifest": accounting.stored,
            "manifest_bytes": 0,
        },
        "limitations": data_card["unsupported_claims"] + [
            "One applicant/company; company-held-out sensitivity is not estimable.",
            "Family identity is unknown and not inferred.",
            "The Stryker marking page is product-level disclosure, not claim-level semantic gold.",
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
