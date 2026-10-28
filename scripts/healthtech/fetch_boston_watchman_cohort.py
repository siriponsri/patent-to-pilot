"""Acquire a bounded Boston Scientific WATCHMAN development cohort."""
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


PMA_NUMBER = "P130013"
PMA_URL = f"https://api.fda.gov/device/pma.json?search=pma_number:{PMA_NUMBER}&limit=100"
BOSTON_PAGE_URL = "https://www.bostonscientific.com/en-US/patents.html"
BOSTON_PDF_URL = "https://www.bostonscientific.com/content/dam/bostonscientific/corporate/patent-marking-spreadsheet-12nov-2025.pdf"
PRODUCTS = (
    {
        "key": "watchman-flx",
        "label": "WATCHMAN FLX LAAC Device",
        "display_name": "WATCHMAN FLX",
        "patent_numbers": ["9883936", "10463377", "10751158", "11241237", "11413047", "11432809"],
    },
    {
        "key": "watchman-flx-pro",
        "label": "WATCHMAN FLX Pro LAAC Device",
        "display_name": "WATCHMAN FLX Pro",
        "patent_numbers": ["9883936", "10463377", "10751158", "11241237", "11413047", "11432809", "11484320"],
    },
)


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _extract_marking_page(pdf_path: Path) -> tuple[int, str]:
    document = fitz.open(pdf_path)
    for index in range(document.page_count):
        text = document[index].get_text()
        if all(product["label"] in text for product in PRODUCTS):
            return index + 1, text
    raise ValueError("Boston patent-marking PDF does not contain both WATCHMAN rows")


def _validate_product_rows(page_text: str) -> dict[str, dict[str, object]]:
    rows: dict[str, dict[str, object]] = {}
    for product in PRODUCTS:
        label = str(product["label"])
        start = page_text.index(label)
        next_starts = [
            page_text.find(other["label"], start + len(label))
            for other in PRODUCTS if other["label"] != label
        ]
        next_starts.append(page_text.find("Zero Tip Airway Retrieval Basket", start + len(label)))
        end = min((value for value in next_starts if value >= 0), default=len(page_text))
        section = page_text[start:end]
        found = re.findall(r"(?<!\d)(\d{7,8})(?!\d)", section)
        expected = [str(value) for value in product["patent_numbers"]]
        if found[:len(expected)] != expected:
            raise ValueError(f"unexpected Boston patent row for {label}: {found}")
        rows[str(product["key"])] = {
            "label": label,
            "display_name": product["display_name"],
            "raw_patent_numbers": expected,
            "source_locator": "pdf-page:30",
            "disclosure_text": section.strip(),
        }
    return rows


def _pma_payload(record: dict) -> dict:
    allowed = {
        "pma_number", "supplement_number", "applicant", "generic_name", "trade_name",
        "product_code", "advisory_committee", "advisory_committee_description",
        "decision_date", "decision_code", "date_received", "supplement_reason",
        "supplement_type", "ao_statement", "openfda",
    }
    return {key: record[key] for key in sorted(record) if key in allowed}


def _fetch_patent(number: str, output: Path, accounting: Accounting, retrieved, max_file_bytes: int) -> tuple[dict, dict]:
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
            page_html, canonical=canonical, url=url, raw_number=number,
            retrieved=retrieved, raw_sha256=raw_sha256,
        )
        patent.update({
            "company_metadata": "BOSTON SCIENTIFIC CORPORATION",
            "company_metadata_basis": "Boston Scientific virtual patent-marking spreadsheet; not an independently verified assignee field",
        })
        return patent, {
            "path": raw_path.relative_to(output).as_posix(),
            "bytes": len(page_html),
            "sha256": raw_sha256,
            "url": url,
        }
    raise ValueError(f"no public US grant page found for {number}: {last_error}")


def _freeze_groups(references: dict[str, list[str]], universe: list[str], pma_source_id: str) -> tuple[dict, dict, dict]:
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
            "basis": "Same canonical patent document appears in Boston Scientific WATCHMAN product-marking rows.",
            "source_ids": ["boston-watchman-patent-disclosures"],
            "family_id": None,
            "family_status": "UNKNOWN_NOT_ASSUMED",
        })
    distractors = {
        query_id: sorted(set(universe) - disclosed_sets[query_id])
        for query_id in sorted(disclosed_sets)
    }
    group_payload = {
        "format": "ht-group-evidence-v1",
        "status": "DEVELOPMENT_ONLY_FREEZE_NO_HOLDOUT",
        "shared_exact_patent_groups": [group["device_query_ids"] for group in groups],
        "group_evidence": groups,
        "company_groups": [{
            "company": "BOSTON SCIENTIFIC CORP",
            "query_ids": sorted(references),
            "basis": "PMA applicant field",
            "source_ids": [pma_source_id],
        }],
        "family_mapping": {"status": "UNKNOWN_NOT_ASSUMED", "mappings": []},
        "overlap_notes": [
            "WATCHMAN FLX and WATCHMAN FLX Pro share a Boston product-marking source and one PMA family.",
            "No family merge is inferred from shared applicant or document overlap.",
        ],
    }
    split = {
        "format": "ht-development-split-v1",
        "status": "DEVELOPMENT_ONLY_NO_GENERALIZATION_CLAIM",
        "assignment_rule": "Both predeclared Boston WATCHMAN rows remain in development; no final holdout is claimed.",
        "seed": 0,
        "rows": [
            {"query_id": query_id, "split": "development", "group_id": next(group["group_id"] for group in groups if query_id in group["device_query_ids"])}
            for query_id in sorted(references)
        ],
        "final_holdout": [],
    }
    return distractors, group_payload, split


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
    (output / "raw" / "patents").mkdir(parents=True)
    (output / "raw" / "disclosure").mkdir(parents=True)
    (output / "evaluator").mkdir(parents=True)
    accounting = Accounting(args.max_transfer_bytes, args.max_storage_bytes)
    retrieved_at = datetime.now(timezone.utc)
    retrieved = retrieved_at.date()
    raw_files: list[dict[str, object]] = []

    pma_path = output / "raw" / "pma" / f"{PMA_NUMBER}.json"
    pma_bytes, pma_sha256 = _fetch(PMA_URL, pma_path, accounting, max_file_bytes=args.max_file_bytes)
    rows = json.loads(pma_bytes.decode("utf-8")).get("results")
    if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
        raise ValueError("PMA response malformed")
    selected_pma = _selected_pma_record(rows)
    supplement = str(selected_pma.get("supplement_number") or "BASE")
    pma_source_id = f"openfda-pma-{PMA_NUMBER.lower()}-{supplement.lower()}"
    pma_payload = _pma_payload(selected_pma)
    raw_files.append({"path": pma_path.relative_to(output).as_posix(), "bytes": len(pma_bytes), "sha256": pma_sha256, "role": "pma-response"})

    page_path = output / "raw" / "disclosure" / "boston-patents.html"
    page_bytes, page_sha256 = _fetch(BOSTON_PAGE_URL, page_path, accounting, max_file_bytes=args.max_file_bytes)
    pdf_path = output / "raw" / "disclosure" / "patent-marking-spreadsheet-12nov-2025.pdf"
    pdf_bytes, pdf_sha256 = _fetch(BOSTON_PDF_URL, pdf_path, accounting, max_file_bytes=args.max_file_bytes)
    marking_page, page_text = _extract_marking_page(pdf_path)
    if marking_page != 30:
        raise ValueError(f"expected WATCHMAN marking page 30, found {marking_page}")
    product_rows = _validate_product_rows(page_text)
    raw_files.extend([
        {"path": page_path.relative_to(output).as_posix(), "bytes": len(page_bytes), "sha256": page_sha256, "role": "virtual-patent-marking-page"},
        {"path": pdf_path.relative_to(output).as_posix(), "bytes": len(pdf_bytes), "sha256": pdf_sha256, "role": "patent-marking-spreadsheet"},
    ])

    patents: list[dict] = []
    patent_files: list[dict] = []
    all_numbers = sorted({number for product in PRODUCTS for number in product["patent_numbers"]})
    for number in all_numbers:
        patent, raw_file = _fetch_patent(number, output, accounting, retrieved, args.max_file_bytes)
        patents.append(patent)
        patent_files.append(raw_file | {"role": "patent-page"})
    patents.sort(key=lambda row: row["patent_id_canonical"])
    by_raw = {str(patent["patent_id_raw"]): str(patent["patent_id_canonical"]) for patent in patents}

    devices = []
    references: dict[str, list[str]] = {}
    disclosure_evidence: list[dict] = []
    for product in PRODUCTS:
        row = product_rows[str(product["key"])]
        query_id = f"HT-DEV-{str(product['key']).upper()}"
        device_id = f"{PMA_NUMBER}:{str(product['key']).upper()}"
        devices.append({
            "query_id": query_id,
            "device_id_raw": f"{row['display_name']} ({PMA_NUMBER})",
            "device_id_canonical": device_id,
            "pma_number": PMA_NUMBER,
            "supplement_number": supplement,
            "company": str(selected_pma.get("applicant") or "Boston Scientific Corp"),
            "trade_name": str(row["display_name"]),
            "generic_name": str(selected_pma.get("generic_name") or "System, appendage closure, left atrial"),
            "product_code": str(selected_pma.get("product_code") or "NGV"),
            "technical_description": f"{row['display_name']}; {selected_pma.get('generic_name', '')}; product code {selected_pma.get('product_code', '')}",
            "features_of_interest": [str(row["display_name"]), str(selected_pma.get("generic_name") or ""), str(selected_pma.get("product_code") or "NGV")],
            "source_id": pma_source_id,
            "evidence_cutoff": retrieved.isoformat(),
        })
        canonical_ids = [by_raw[number] for number in row["raw_patent_numbers"]]
        references[query_id] = canonical_ids
        disclosure_evidence.append({
            "evidence_id": f"DISC-{query_id}",
            "query_id": query_id,
            "patent_id_raw": list(row["raw_patent_numbers"]),
            "patent_id_canonical": canonical_ids,
            "source_id": "boston-watchman-patent-disclosures",
            "locator": row["source_locator"],
            "quoted_span": row["disclosure_text"],
            "evidence_kind": "patent_disclosure",
            "support_basis": "Boston Scientific virtual patent-marking spreadsheet lists these U.S. patent numbers under the named WATCHMAN product row; product-level documented association only.",
        })

    universe = sorted(patent["patent_id_canonical"] for patent in patents)
    distractors, groups, split = _freeze_groups(references, universe, pma_source_id)
    runtime = {
        "format": "ht-runtime-public-device-cohort-v1",
        "status": "RUNTIME_INPUTS_ONLY_NO_EVALUATOR_LABELS",
        "retrieved_at_utc": retrieved_at.isoformat(),
        "devices": devices,
        "patents": [
            {key: patent[key] for key in ("patent_id_raw", "patent_id_canonical", "document_kind", "jurisdiction", "title", "abstract", "claims", "text", "source_id", "source_revision", "source_url", "raw_html_sha256", "normalized_sha256", "source_date", "company_metadata", "company_metadata_basis")}
            for patent in patents
        ],
        "permitted_metadata": ["PMA facts", "Boston product-marking row", "patent title/abstract/claims"],
        "runtime_exclusions": ["disclosure references", "evaluator gold/reference links", "family labels", "split answers"],
    }
    references_payload = {
        "format": "ht-evaluator-disclosures-v1",
        "status": "EVALUATOR_ONLY_REFERENCE_RELATIONS",
        "retrieved_at_utc": retrieved_at.isoformat(),
        "references": references,
        "disclosure_evidence": disclosure_evidence,
        "limitations": [
            "These are product-level virtual patent-marking relationships, not independent expert judgments of component-level claim relevance.",
            "Unlisted device-patent pairs remain unjudged and are never recoded as negatives.",
        ],
    }
    source_registry = {
        "format": "ht-source-registry-v1",
        "separation": "evaluator-only disclosure source is not included in runtime.json",
        "sources": [
            {
                "source_id": pma_source_id,
                "source_type": "regulatory_record",
                "url": PMA_URL,
                "revision": "openFDA-last-updated-2026-10-19",
                "retrieved_at_utc": retrieved_at.isoformat(),
                "jurisdiction": "US",
                "raw_json_sha256": pma_sha256,
                "rights_policy_id": "openfda-pma-records",
                "runtime_allowed": True,
            },
            {
                "source_id": "boston-watchman-patent-disclosures",
                "source_type": "independent_disclosure",
                "url": BOSTON_PDF_URL,
                "revision": "pdf-12nov-2025-retrieved-2026-10-28",
                "retrieved_at_utc": retrieved_at.isoformat(),
                "jurisdiction": "US",
                "raw_html_sha256": page_sha256,
                "pdf_sha256": pdf_sha256,
                "pdf_page": marking_page,
                "rights_policy_id": "boston-scientific-virtual-patent-marking",
                "rights": "Official product-level patent-marking source retained for local research; no redistribution license established.",
                "runtime_allowed": False,
            },
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
        "dataset": "Boston Scientific WATCHMAN product-marking development cohort",
        "scope": "Two named Boston Scientific WATCHMAN rows from the official virtual patent-marking spreadsheet, joined to PMA P130013 and a seven-document local patent universe.",
        "selection_rule": "Predeclared WATCHMAN FLX and WATCHMAN FLX Pro rows on the official Boston Scientific 12 November 2025 patent-marking spreadsheet; no retrieval score or evaluator label used.",
        "device_count": len(devices),
        "patent_universe_count": len(universe),
        "reference_pair_count": sum(len(values) for values in references.values()),
        "unjudged_distractor_pair_count": sum(len(values) for values in distractors.values()),
        "supported_claims": ["Reproducible local retrieval over a bounded official product-marking cohort", "Source-linked PMA and product-marking metadata"],
        "unsupported_claims": ["Exhaustive patent recall", "Claim-level relevance", "Clinical suitability", "FTO", "Patent validity", "Investment merit", "Generalization beyond this development cohort"],
        "rights_boundary": "Local research and offline evaluation only for Boston disclosure and Google-derived patent text; product display and redistribution remain blocked.",
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
        _write_json(output / relative, payload)
    manifest = {
        "status": "PUBLIC_BOSTON_WATCHMAN_COHORT_ACQUIRED",
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
        "rights_policy_ids": ["openfda-pma-records", "boston-scientific-virtual-patent-marking", "google-patents-pages"],
        "accounting": {
            "transfer_cap_bytes": accounting.transfer_cap,
            "storage_cap_bytes": accounting.storage_cap,
            "actual_transferred_bytes": accounting.transferred,
            "actual_stored_bytes": accounting.stored,
        },
        "limitations": data_card["unsupported_claims"] + [
            "One applicant and one PMA family; no company-held-out sensitivity is estimable.",
            "Family identity is unknown and not inferred.",
        ],
    }
    _write_json(output / "manifest.json", manifest)
    print(json.dumps({
        "status": manifest["status"],
        "output": str(output),
        "devices": len(devices),
        "patents": len(patents),
        "pairs": manifest["reference_pairs"],
        "unjudged_distractor_pairs": manifest["unjudged_distractor_pairs"],
        "provider_calls": 0,
        "paid_cost_usd": 0,
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
