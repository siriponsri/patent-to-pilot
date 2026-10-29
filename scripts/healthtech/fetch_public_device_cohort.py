"""Acquire a bounded public cardiovascular device--patent development cohort."""
from __future__ import annotations

import argparse
from datetime import date, datetime, timezone
import hashlib
import html as html_lib
import json
import os
from pathlib import Path
import re
import shutil
import sys
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen

from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from patent_to_pilot.healthtech.contracts import canonical_patent_id, content_hash


ABBOTT_DISCLOSURE_URL = "https://www.abbott.com/en-us/patents/legal-notices-patents/patents"
PRODUCTS = (
    {"key": "mitraclip", "label": "MitraClip", "pma_number": "P100009"},
    {"key": "tr iclip".replace(" ", ""), "label": "TriClip", "pma_number": "P230007"},
    {"key": "tendyne", "label": "Tendyne", "pma_number": "P240042"},
)


def _rights_policy_id(source_id: str, source_type: str) -> str:
    """Resolve this builder's source rows to the canonical typed policy IDs."""
    if source_type == "regulatory_record" and source_id.startswith("openfda-pma-"):
        return "openfda-pma-records"
    if source_type == "independent_disclosure" and source_id == "abbott-product-patent-disclosures":
        return "abbott-product-patent-disclosures"
    if source_type == "patent_document" and source_id.startswith("google-patents-"):
        return "google-patents-pages"
    raise ValueError(f"no typed rights policy for source {source_id} ({source_type})")


def _source_registry_row(source: dict[str, object]) -> dict[str, object]:
    """Attach a typed rights-policy ID while preserving the source registry row."""
    row = dict(source)
    row["rights_policy_id"] = _rights_policy_id(
        str(row.get("source_id") or ""),
        str(row.get("source_type") or ""),
    )
    return row


class Accounting:
    def __init__(self, transfer_cap: int, storage_cap: int) -> None:
        self.transfer_cap = transfer_cap
        self.storage_cap = storage_cap
        self.transferred = 0
        self.stored = 0

    def transfer(self, count: int) -> None:
        self.transferred += count
        if self.transferred > self.transfer_cap:
            raise ValueError("cumulative transfer cap exceeded")

    def storage(self, count: int) -> None:
        if count < 0 or self.stored + count > self.storage_cap:
            raise ValueError("cumulative storage cap exceeded")
        self.stored += count


def _fetch(url: str, destination: Path, accounting: Accounting, *, max_file_bytes: int) -> tuple[bytes, str]:
    part = destination.with_name(destination.name + ".part")
    part.unlink(missing_ok=True)
    digest = hashlib.sha256()
    total = 0
    request = Request(url, headers={"User-Agent": "patent-to-pilot-public-case-prep"})
    try:
        with urlopen(request, timeout=60) as response, part.open("wb") as handle:
            declared = response.headers.get("Content-Length")
            if declared and int(declared) > max_file_bytes:
                raise ValueError(f"source exceeds per-file cap: {url}")
            while True:
                chunk = response.read(1024 * 256)
                if not chunk:
                    break
                total += len(chunk)
                if total > max_file_bytes:
                    raise ValueError(f"source exceeds per-file cap: {url}")
                accounting.transfer(len(chunk))
                digest.update(chunk)
                handle.write(chunk)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(part, destination)
        accounting.storage(total)
        return destination.read_bytes(), digest.hexdigest()
    except Exception:
        part.unlink(missing_ok=True)
        raise


def _write_bytes(path: Path, payload: bytes, accounting: Accounting) -> str:
    accounting.storage(len(payload))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    return hashlib.sha256(payload).hexdigest()


def _write_json(path: Path, payload: object, accounting: Accounting) -> tuple[int, str]:
    text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    data = text.encode("utf-8")
    digest = _write_bytes(path, data, accounting)
    return len(data), digest


def _selected_pma_record(rows: list[dict]) -> dict:
    if not rows:
        raise ValueError("PMA query returned no rows")
    return sorted(
        rows,
        key=lambda row: (
            0 if not row.get("supplement_number") else 1,
            str(row.get("decision_date") or "9999-99-99"),
            str(row.get("supplement_number") or ""),
        ),
    )[0]


def _pma_source(record: dict, *, pma_number: str, retrieved: date) -> dict:
    supplement = str(record.get("supplement_number") or "BASE")
    source_id = f"openfda-pma-{pma_number.lower()}-{supplement.lower()}"
    allowed = {
        "pma_number", "supplement_number", "applicant", "generic_name", "trade_name",
        "product_code", "advisory_committee", "advisory_committee_description",
        "decision_date", "decision_code", "date_received", "supplement_reason",
        "supplement_type", "ao_statement", "openfda",
    }
    payload = {key: record[key] for key in sorted(record) if key in allowed}
    return {
        "source_id": source_id,
        "source_type": "regulatory_record",
        "url": f"https://api.fda.gov/device/pma.json?search=pma_number:{pma_number}",
        "revision": "openFDA-last-updated-2026-10-19",
        "retrieved_at_utc": retrieved.isoformat(),
        "jurisdiction": "US",
        "payload": payload,
        "payload_sha256": content_hash(payload),
        "rights": "openFDA/FDA terms and field-specific rights apply; preserve attribution",
        "runtime_allowed": True,
    }


def _product_disclosures(page_html: bytes) -> dict[str, dict[str, object]]:
    soup = BeautifulSoup(page_html, "html.parser")
    items: dict[str, dict[str, object]] = {}
    for product in PRODUCTS:
        item = None
        for candidate in soup.select("abbott-accordion-item"):
            title = candidate.select_one('[slot="title"]')
            title_text = title.get_text(" ", strip=True) if title else ""
            if product["label"].lower() in title_text.lower():
                item = candidate
                break
        if item is None:
            raise ValueError(f"Abbott disclosure section not found: {product['label']}")
        text = item.get_text(" ", strip=True)
        raw_numbers = re.findall(r"(?<!\d)(\d[\d,]{6,10})(?!\d)", text)
        numbers: list[str] = []
        for raw in raw_numbers:
            number = raw.replace(",", "")
            if number not in numbers:
                numbers.append(number)
        if not numbers:
            raise ValueError(f"Abbott disclosure section has no patent numbers: {product['label']}")
        items[product["key"]] = {
            "label": product["label"],
            "pma_number": product["pma_number"],
            "disclosure_text": text,
            "raw_patent_numbers": numbers,
        }
    return items


def _meta(soup: BeautifulSoup, *, name: str | None = None, scheme: str | None = None) -> str | None:
    for tag in soup.find_all("meta"):
        if name is not None and tag.get("name") == name and tag.get("content"):
            return html_lib.unescape(tag["content"]).strip()
        if scheme is not None and tag.get("scheme") == scheme and tag.get("content"):
            return html_lib.unescape(tag["content"]).strip()
    return None


def _patent_document(page_html: bytes, *, canonical: str, url: str, raw_number: str, retrieved: date, raw_sha256: str) -> dict:
    soup = BeautifulSoup(page_html, "html.parser")
    title = _meta(soup, name="DC.title") or ""
    abstract = _meta(soup, name="DC.description") or _meta(soup, name="description") or ""
    claims = "\n".join(node.get_text(" ", strip=True) for node in soup.select(".claim-text"))
    payload = {"title": title, "abstract": abstract, "claims": claims}
    if not title or not abstract:
        raise ValueError(f"patent page lacks title/abstract: {canonical}")
    return {
        "patent_id_raw": raw_number,
        "patent_id_canonical": canonical,
        "document_kind": "US-grant",
        "jurisdiction": "US",
        "title": title,
        "abstract": abstract,
        "claims": claims,
        "text": "\n\n".join(value for value in (title, abstract, claims) if value),
        "source_id": f"google-patents-{canonical.lower()}",
        "source_revision": f"retrieved-{retrieved.isoformat()}",
        "source_url": url,
        "raw_html_sha256": raw_sha256,
        "normalized_sha256": content_hash(payload),
        "source_date": retrieved.isoformat(),
        "company_metadata": "ABBOTT MEDICAL",
        "company_metadata_basis": "Abbott product disclosure page; not an independently verified assignee field",
        "family_id": None,
        "family_source_id": None,
    }


def _fetch_patent(number: str, output: Path, accounting: Accounting, retrieved: date, max_file_bytes: int) -> tuple[dict, dict]:
    raw_number = number
    last_error: Exception | None = None
    for kind in ("B2", "B1"):
        candidate = canonical_patent_id(f"US{number}{kind}")
        url = f"https://patents.google.com/patent/{candidate}/en"
        raw_path = output / "raw" / "patents" / f"{candidate}.html"
        try:
            page_html, raw_sha256 = _fetch(url, raw_path, accounting, max_file_bytes=max_file_bytes)
        except HTTPError as exc:
            last_error = exc
            if exc.code == 404:
                continue
            raise
        return _patent_document(page_html, canonical=candidate, url=url, raw_number=raw_number,
                                retrieved=retrieved, raw_sha256=raw_sha256), {
            "path": raw_path.relative_to(output).as_posix(),
            "bytes": len(page_html),
            "sha256": raw_sha256,
            "url": url,
        }
    raise ValueError(f"no public US grant page found for {number}: {last_error}")


def _write_manifest(output: Path, manifest: dict, accounting: Accounting) -> None:
    before = accounting.stored
    size = 0
    for _ in range(10):
        manifest["accounting"]["manifest_bytes"] = size
        manifest["accounting"]["actual_stored_bytes"] = before + size
        text = json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        next_size = len(text.encode("utf-8"))
        if next_size == size:
            break
        size = next_size
    else:
        raise ValueError("manifest accounting did not converge")
    accounting.storage(size)
    manifest["accounting"]["manifest_bytes"] = size
    manifest["accounting"]["actual_stored_bytes"] = accounting.stored
    text = json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if len(text.encode("utf-8")) != size:
        raise ValueError("manifest accounting changed after finalization")
    (output / "manifest.json").write_bytes(text.encode("utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="fresh ignored output directory")
    parser.add_argument("--max-transfer-bytes", type=int, default=80_000_000)
    parser.add_argument("--max-storage-bytes", type=int, default=140_000_000)
    parser.add_argument("--max-file-bytes", type=int, default=30_000_000)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("output already exists; choose a fresh directory")
    if shutil.disk_usage(args.output.parent.resolve()).free < args.max_storage_bytes:
        parser.error("free disk is below the configured storage cap")
    output = args.output.resolve()
    output.mkdir(parents=True)
    (output / "raw" / "pma").mkdir(parents=True)
    (output / "raw" / "patents").mkdir(parents=True)
    (output / "evaluator").mkdir(parents=True)
    accounting = Accounting(args.max_transfer_bytes, args.max_storage_bytes)
    retrieved_at = datetime.now(timezone.utc)
    retrieved = retrieved_at.date()
    raw_files: list[dict[str, object]] = []
    sources: list[dict[str, object]] = []
    pma_devices: dict[str, dict] = {}
    for product in PRODUCTS:
        pma = product["pma_number"]
        url = f"https://api.fda.gov/device/pma.json?search=pma_number:{quote(pma)}&limit=100"
        raw_path = output / "raw" / "pma" / f"{pma}.json"
        raw_bytes, raw_sha256 = _fetch(url, raw_path, accounting, max_file_bytes=args.max_file_bytes)
        payload = json.loads(raw_bytes.decode("utf-8"))
        rows = payload.get("results") if isinstance(payload, dict) else None
        if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
            raise ValueError(f"PMA response malformed: {pma}")
        selected = _selected_pma_record(rows)
        source = _pma_source(selected, pma_number=pma, retrieved=retrieved)
        sources.append(_source_registry_row(source))
        supplement = str(selected.get("supplement_number") or "BASE")
        query_id = f"HT-DEV-{product['label'].upper()}"
        device_id = f"{pma}:{supplement}"
        trade_name = str(selected.get("trade_name") or product["label"])
        generic_name = str(selected.get("generic_name") or "")
        product_code = str(selected.get("product_code") or "")
        pma_devices[product["key"]] = {
            "query_id": query_id,
            "device_id_raw": f"{trade_name} ({device_id})",
            "device_id_canonical": device_id,
            "pma_number": pma,
            "supplement_number": supplement,
            "company": str(selected.get("applicant") or ""),
            "trade_name": trade_name,
            "generic_name": generic_name,
            "product_code": product_code,
            "technical_description": "; ".join(value for value in (trade_name, generic_name, f"product code {product_code}") if value),
            "features_of_interest": [value for value in (generic_name, product_code) if value],
            "source_id": source["source_id"],
            "evidence_cutoff": retrieved.isoformat(),
        }
        raw_files.append({"path": raw_path.relative_to(output).as_posix(), "bytes": len(raw_bytes), "sha256": raw_sha256, "role": "pma-response"})
    disclosure_path = output / "raw" / "abbott-patents.html"
    disclosure_html, disclosure_sha256 = _fetch(ABBOTT_DISCLOSURE_URL, disclosure_path, accounting, max_file_bytes=args.max_file_bytes)
    disclosure_sections = _product_disclosures(disclosure_html)
    raw_files.append({"path": disclosure_path.relative_to(output).as_posix(), "bytes": len(disclosure_html), "sha256": disclosure_sha256, "role": "product-disclosure-page"})
    disclosure_source = {
        "source_id": "abbott-product-patent-disclosures",
        "source_type": "independent_disclosure",
        "url": ABBOTT_DISCLOSURE_URL,
        "revision": "page-retrieved-" + retrieved.isoformat(),
        "retrieved_at_utc": retrieved_at.isoformat(),
        "jurisdiction": "US",
        "raw_html_sha256": disclosure_sha256,
        "rights": "Public legal notice page; local research evidence only, redistribution and claim-level use remain unresolved.",
        "runtime_allowed": False,
    }
    sources.append(_source_registry_row(disclosure_source))
    all_numbers: list[str] = []
    for section in disclosure_sections.values():
        for number in section["raw_patent_numbers"]:
            if number not in all_numbers:
                all_numbers.append(number)
    patents: list[dict] = []
    patent_files: dict[str, dict] = {}
    for number in all_numbers:
        patent, raw_file = _fetch_patent(number, output, accounting, retrieved, args.max_file_bytes)
        patents.append(patent)
        patent_files[patent["patent_id_canonical"]] = raw_file | {"role": "patent-page"}
        sources.append(_source_registry_row({
            "source_id": patent["source_id"],
            "source_type": "patent_document",
            "url": patent["source_url"],
            "revision": patent["source_revision"],
            "retrieved_at_utc": retrieved_at.isoformat(),
            "jurisdiction": "US",
            "raw_html_sha256": patent["raw_html_sha256"],
            "normalized_sha256": patent["normalized_sha256"],
            "rights": "Public patent page accessed for local research; raw page and extracted text remain local-only.",
            "runtime_allowed": True,
        }))
    patents.sort(key=lambda row: row["patent_id_canonical"])
    references: dict[str, list[str]] = {}
    disclosure_evidence: list[dict] = []
    product_key_by_pma = {value["pma_number"]: key for key, value in pma_devices.items()}
    for section in disclosure_sections.values():
        device = pma_devices[product_key_by_pma[section["pma_number"]]]
        query_id = device["query_id"]
        references[query_id] = []
        for number in section["raw_patent_numbers"]:
            matches = [p for p in patents if p["patent_id_raw"] == number]
            if len(matches) != 1:
                raise ValueError(f"disclosed patent did not resolve uniquely: {section['label']} {number}")
            patent = matches[0]
            references[query_id].append(patent["patent_id_canonical"])
            disclosure_evidence.append({
                "evidence_id": f"DISC-{query_id}-{patent['patent_id_canonical']}",
                "query_id": query_id,
                "patent_id_raw": number,
                "patent_id_canonical": patent["patent_id_canonical"],
                "source_id": disclosure_source["source_id"],
                "locator": f"product:{section['label']}",
                "quoted_span": section["disclosure_text"],
                "evidence_kind": "patent_disclosure",
                "support_basis": "Abbott product disclosure page lists the U.S. patent number under this product; this is a product-level disclosed relationship, not claim-level semantic proof.",
            })
    runtime = {
        "format": "ht-runtime-public-device-cohort-v1",
        "status": "RUNTIME_INPUTS_ONLY_NO_EVALUATOR_LABELS",
        "retrieved_at_utc": retrieved_at.isoformat(),
        "devices": list(pma_devices.values()),
        "patents": [
            {key: patent[key] for key in ("patent_id_raw", "patent_id_canonical", "document_kind", "jurisdiction", "title", "abstract", "claims", "text", "source_id", "source_revision", "source_url", "raw_html_sha256", "normalized_sha256", "source_date", "company_metadata", "company_metadata_basis")}
            for patent in patents
        ],
        "permitted_metadata": ["PMA trade_name", "PMA generic_name", "PMA product_code", "PMA applicant", "patent title/abstract/claims"],
        "runtime_exclusions": ["disclosure references", "evaluator gold/reference links", "family labels", "split answers"],
    }
    references_payload = {
        "format": "ht-evaluator-disclosures-v1",
        "status": "EVALUATOR_ONLY_REFERENCE_RELATIONS",
        "retrieved_at_utc": retrieved_at.isoformat(),
        "references": references,
        "disclosure_evidence": disclosure_evidence,
        "limitations": [
            "These are product-level public disclosure relationships, not independent expert judgments of component-level claim relevance.",
            "Unlisted device--patent pairs remain unjudged and are never recoded as negatives.",
        ],
    }
    source_registry = {
        "format": "ht-source-registry-v1",
        "sources": sorted(sources, key=lambda row: row["source_id"]),
        "separation": "evaluator-only disclosure source is not included in runtime.json",
    }
    device_ids = [device["query_id"] for device in pma_devices.values()]
    patent_sets = {query_id: set(ids) for query_id, ids in references.items()}
    groups: list[list[str]] = []
    remaining = set(device_ids)
    while remaining:
        root = min(remaining)
        group = {root}
        changed = True
        while changed:
            changed = False
            for query_id in sorted(remaining - group):
                if any(patent_sets[query_id] & patent_sets[member] for member in group):
                    group.add(query_id)
                    changed = True
        remaining -= group
        groups.append(sorted(group))
    groups_payload = {
        "format": "ht-device-groups-v1",
        "shared_exact_patent_groups": groups,
        "family_mapping": {"status": "UNAVAILABLE_NOT_ASSUMED", "mapping": {}},
        "company_groups": {"ABBOTT MEDICAL": sorted(device_ids)},
        "overlap_notes": ["All three devices share the Abbott applicant; company-held-out sensitivity is not estimable.", "No family merge is inferred without a sourced family mapping."],
    }
    split_payload = {
        "format": "ht-development-split-v1",
        "assignment_rule": "All eligible disclosed devices remain in development; no final holdout is claimed because the cohort has three devices, one company, and one public disclosure page.",
        "seed": 0,
        "rows": [{"query_id": query_id, "split": "development", "group_id": next(str(i) for i, group in enumerate(groups) if query_id in group)} for query_id in sorted(device_ids)],
        "final_holdout": [],
        "status": "DEVELOPMENT_ONLY_NO_GENERALIZATION_CLAIM",
    }
    data_card = {
        "dataset": "Public Abbott cardiovascular device--patent disclosure development cohort",
        "scope": "Three named cardiovascular devices with one selected openFDA PMA record each and Abbott product-level U.S. patent disclosure lists.",
        "device_count": len(pma_devices),
        "patent_universe_count": len(patents),
        "reference_pair_count": sum(len(ids) for ids in references.values()),
        "selection_rule": "Predeclared PMA identifiers and product names; patent universe is the union of listed patents for the three products.",
        "biases": ["Single applicant and disclosure source", "Product-level disclosure may not identify which component or claim is relevant", "Patent pages and PMA records are retrospective public sources"],
        "absence_of_judgments": "Only listed product disclosures are references; all other pairs are unjudged.",
        "supported_claims": ["Reproducible retrieval over a bounded public disclosure cohort", "Source-linked device and patent metadata"],
        "unsupported_claims": ["Exhaustive patent recall", "Clinical suitability", "FTO", "Patent validity", "Investment merit", "Generalization beyond this development cohort"],
    }
    for relative, payload in (
        ("runtime.json", runtime),
        ("evaluator/references.json", references_payload),
        ("source_registry.json", source_registry),
        ("groups.json", groups_payload),
        ("split_manifest.json", split_payload),
        ("data_card.json", data_card),
    ):
        _write_json(output / relative, payload, accounting)
    manifest = {
        "status": "PUBLIC_DEVICE_DISCLOSURE_COHORT_ACQUIRED",
        "integrity_format": "ht-runtime-integrity-v1",
        "retrieved_at_utc": retrieved_at.isoformat(),
        "products": [product["label"] for product in PRODUCTS],
        "devices": len(pma_devices),
        "patents": len(patents),
        "reference_pairs": sum(len(ids) for ids in references.values()),
        "raw_files": [
            {**item, "size_bytes": int(item["bytes"])}
            for item in raw_files + list(patent_files.values())
        ],
        "source_registry": "source_registry.json",
        "runtime_path": "runtime.json",
        "evaluator_path": "evaluator/references.json",
        "groups_path": "groups.json",
        "split_path": "split_manifest.json",
        "runtime_sha256": content_hash(runtime),
        "source_registry_sha256": content_hash(source_registry),
        "references_sha256": content_hash(references_payload),
        "universe_sha256": content_hash([patent["patent_id_canonical"] for patent in patents]),
        "cohort_sha256": content_hash(device_ids),
        "rights_policy_ids": sorted({str(source["rights_policy_id"]) for source in sources}),
        "accounting": {
            "transfer_cap_bytes": accounting.transfer_cap,
            "storage_cap_bytes": accounting.storage_cap,
            "actual_transferred_bytes": accounting.transferred,
            "actual_stored_bytes_before_manifest": accounting.stored,
            "manifest_bytes": 0,
        },
        "rights": "Metadata and source text are retained locally for research development; raw third-party pages and model weights are excluded from Git.",
        "limitations": data_card["biases"] + data_card["unsupported_claims"],
    }
    _write_manifest(output, manifest, accounting)
    print(json.dumps({"status": manifest["status"], "output": str(output), "devices": len(pma_devices), "patents": len(patents), "pairs": sum(len(ids) for ids in references.values()), "transferred_bytes": accounting.transferred, "stored_bytes": accounting.stored}, ensure_ascii=False))


if __name__ == "__main__":
    main()
