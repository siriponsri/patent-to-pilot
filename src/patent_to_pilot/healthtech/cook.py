"""Cook Medical public-cohort adapter for real local HealthTech dossiers.

The adapter reads only the frozen runtime, source registry, pinned raw files,
and reviewed rights matrix. Evaluator references are intentionally excluded;
product-level disclosure evidence is reconstructed from the official Cook PDF.
"""
from __future__ import annotations

from datetime import date, datetime
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
from typing import Any

from patent_to_pilot.healthtech.contracts import (
    AcquisitionBudget,
    DossierVersion,
    EvidenceItem,
    PatentCandidate,
    SourcePayload,
    canonical_patent_id,
    content_hash,
)
from patent_to_pilot.healthtech.engine import DossierInput, PatentInput
from patent_to_pilot.healthtech.rights import attach_rights, load_rights_matrix, select_rights_policy
from patent_to_pilot.healthtech.sources import field_evidence, source_payload
from patent_to_pilot.product.contracts import ProjectBrief
from scripts.healthtech.fetch_cook_zenith_cohort import (
    COOK_DISCLOSURE_SOURCE_ID,
    PRODUCTS,
    _validate_product_rows,
)
from scripts.healthtech.fetch_public_device_cohort import _selected_pma_record


COHORT_FORMAT = "ht-runtime-public-device-cohort-v1"
INTEGRITY_FORMAT = "ht-runtime-integrity-v1"
DEFAULT_RIGHTS_MATRIX = "docs/healthtech/audits/luna-long-run-20261029-cook-expansion-20261029/rights-matrix.json"


class CohortIntegrityError(ValueError):
    """Raised when a frozen Cook runtime cohort does not match its manifest."""


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CohortIntegrityError(f"could not read JSON artifact: {path}") from exc
    if not isinstance(value, dict):
        raise CohortIntegrityError(f"expected JSON object: {path}")
    return value


def _safe_runtime_path(cohort: Path, value: Any, *, label: str) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise CohortIntegrityError(f"{label} must be a nonempty relative path")
    relative = PurePosixPath(value.replace("\\", "/"))
    blocked = {"evaluator", "gold", "reference", "references", "split", "holdout"}
    if relative.is_absolute() or ".." in relative.parts or any(part.lower() in blocked for part in relative.parts):
        raise CohortIntegrityError(f"{label} is outside the runtime boundary: {value}")
    root = cohort.resolve()
    path = (root / Path(*relative.parts)).resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise CohortIntegrityError(f"{label} escapes the cohort root: {value}") from exc
    return path


def _validate_sha256(value: Any, *, label: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[a-f0-9]{64}", value):
        raise CohortIntegrityError(f"{label} must be a lowercase SHA-256")
    return value


def _registry_by_id(registry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    sources = registry.get("sources")
    if not isinstance(sources, list) or not all(isinstance(item, dict) for item in sources):
        raise CohortIntegrityError("source registry is missing sources")
    result: dict[str, dict[str, Any]] = {}
    for item in sources:
        source_id = item.get("source_id")
        if not isinstance(source_id, str) or not source_id:
            raise CohortIntegrityError("source registry contains an invalid source_id")
        if source_id in result:
            raise CohortIntegrityError(f"source registry repeats {source_id}")
        if not isinstance(item.get("rights_policy_id"), str) or not item["rights_policy_id"].strip():
            raise CohortIntegrityError(f"source registry lacks typed rights for {source_id}")
        result[source_id] = item
    return result


def _validate_runtime_integrity(cohort: Path) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, dict[str, Any]]]:
    manifest = _read_json(cohort / "manifest.json")
    if manifest.get("integrity_format") != INTEGRITY_FORMAT:
        raise CohortIntegrityError("manifest is missing the required runtime integrity format")
    runtime_path = _safe_runtime_path(cohort, manifest.get("runtime_path", "runtime.json"), label="runtime_path")
    registry_path = _safe_runtime_path(cohort, manifest.get("source_registry", "source_registry.json"), label="source_registry")
    runtime = _read_json(runtime_path)
    registry = _read_json(registry_path)
    if content_hash(runtime) != _validate_sha256(manifest.get("runtime_sha256"), label="runtime_sha256"):
        raise CohortIntegrityError("runtime JSON hash does not match manifest")
    if content_hash(registry) != _validate_sha256(manifest.get("source_registry_sha256"), label="source_registry_sha256"):
        raise CohortIntegrityError("source registry hash does not match manifest")

    raw_files = manifest.get("raw_files")
    if not isinstance(raw_files, list) or not raw_files:
        raise CohortIntegrityError("manifest raw_files must be a nonempty list")
    raw_by_path: dict[str, dict[str, Any]] = {}
    for index, item in enumerate(raw_files):
        if not isinstance(item, dict):
            raise CohortIntegrityError(f"manifest raw_files[{index}] must be an object")
        raw_path = _safe_runtime_path(cohort, item.get("path"), label=f"raw_files[{index}].path")
        relative = raw_path.relative_to(cohort.resolve()).as_posix()
        if relative in raw_by_path:
            raise CohortIntegrityError(f"manifest raw_files repeats {relative}")
        expected_size = item.get("size_bytes", item.get("bytes"))
        expected_sha = _validate_sha256(item.get("sha256"), label=f"raw_files[{index}].sha256")
        if not isinstance(expected_size, int) or isinstance(expected_size, bool) or expected_size < 0:
            raise CohortIntegrityError(f"manifest raw_files[{index}] has invalid size")
        if not raw_path.is_file():
            raise CohortIntegrityError(f"manifest raw file is missing: {relative}")
        payload = raw_path.read_bytes()
        if len(payload) != expected_size:
            raise CohortIntegrityError(f"raw file size does not match manifest: {relative}")
        if hashlib.sha256(payload).hexdigest() != expected_sha:
            raise CohortIntegrityError(f"raw file hash does not match manifest: {relative}")
        raw_by_path[relative] = {**item, "path": relative, "sha256": expected_sha}

    if runtime.get("format") != COHORT_FORMAT:
        raise CohortIntegrityError("unsupported runtime cohort format")
    devices = runtime.get("devices")
    patents = runtime.get("patents")
    if not isinstance(devices, list) or not all(isinstance(item, dict) for item in devices):
        raise CohortIntegrityError("runtime cohort is missing devices")
    if not isinstance(patents, list) or not all(isinstance(item, dict) for item in patents):
        raise CohortIntegrityError("runtime cohort is missing patents")
    registry_map = _registry_by_id(registry)
    for device in devices:
        query_id = str(device.get("query_id") or "")
        source_id = str(device.get("source_id") or "")
        if not query_id or not source_id:
            raise CohortIntegrityError("runtime device is missing query_id or source_id")
        source = registry_map.get(source_id)
        if source is None or source.get("source_type") != "regulatory_record":
            raise CohortIntegrityError(f"runtime device source is not regulatory: {source_id}")
        pma_number = str(device.get("pma_number") or "")
        if not pma_number or f"raw/pma/{pma_number}.json" not in raw_by_path:
            raise CohortIntegrityError(f"manifest does not pin PMA raw input: {pma_number}")
    patent_ids: set[str] = set()
    for patent in patents:
        canonical = canonical_patent_id(str(patent.get("patent_id_canonical") or ""))
        if canonical in patent_ids:
            raise CohortIntegrityError(f"runtime patents repeat {canonical}")
        patent_ids.add(canonical)
        source_id = str(patent.get("source_id") or "")
        source = registry_map.get(source_id)
        if source is None or source.get("source_type") != "patent_document":
            raise CohortIntegrityError(f"runtime patent source is not a patent document: {source_id}")
        for runtime_field, registry_field in (
            ("source_revision", "revision"),
            ("source_url", "url"),
            ("raw_html_sha256", "raw_html_sha256"),
            ("normalized_sha256", "normalized_sha256"),
        ):
            if patent.get(runtime_field) != source.get(registry_field):
                raise CohortIntegrityError(f"runtime patent {canonical} disagrees with registry field {runtime_field}")
    disclosure = registry_map.get(COOK_DISCLOSURE_SOURCE_ID)
    if disclosure is None or disclosure.get("source_type") != "independent_disclosure":
        raise CohortIntegrityError("source registry is missing the Cook disclosure source")
    disclosure_files = [row for row in raw_by_path.values() if row.get("role") == "patent-marking-pdf"]
    if len(disclosure_files) != 1 or disclosure.get("pdf_sha256") != disclosure_files[0]["sha256"]:
        raise CohortIntegrityError("Cook disclosure PDF is not pinned consistently")
    return manifest, runtime, registry, raw_by_path


def _source_with_metadata(source: SourcePayload, *, locator: str, retrieved_at_utc: str | None, limits: list[str]) -> SourcePayload:
    retrieved_at = datetime.fromisoformat(retrieved_at_utc.replace("Z", "+00:00")) if retrieved_at_utc else None
    record = source.source.model_copy(update={"locator": locator, "retrieved_at": retrieved_at, "limits": limits})
    return source.model_copy(update={"source": record})


def _pma_source(cohort: Path, device: dict[str, Any], registry: dict[str, Any], rights) -> SourcePayload:
    pma_number = str(device["pma_number"])
    raw = _read_json(cohort / "raw" / "pma" / f"{pma_number}.json")
    rows = raw.get("results")
    if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
        raise CohortIntegrityError(f"malformed PMA snapshot: {pma_number}")
    selected = _selected_pma_record(rows)
    allowed = {
        "pma_number", "supplement_number", "applicant", "generic_name", "trade_name",
        "product_code", "advisory_committee", "advisory_committee_description",
        "decision_date", "decision_code", "date_received", "supplement_reason",
        "supplement_type", "ao_statement", "openfda",
    }
    payload = {key: selected[key] for key in sorted(selected) if key in allowed}
    source_id = str(device["source_id"])
    entry = _registry_by_id(registry)[source_id]
    source = source_payload(
        source_id,
        payload,
        uri=str(entry["url"]),
        revision=str(entry["revision"]),
        source_date=date.fromisoformat(str(device["evidence_cutoff"])),
        jurisdiction="US",
        source_type="regulatory_record",
        license_note="Source registry pointer only; intended-use matrix is required and is not a license grant.",
        synthetic=False,
    )
    return _source_with_metadata(
        attach_rights(source, select_rights_policy(
            rights, source_id=source_id, source_type="regulatory_record",
            declared_policy_id=str(entry["rights_policy_id"]),
        )),
        locator=f"openFDA:pma_number={pma_number}",
        retrieved_at_utc=entry.get("retrieved_at_utc"),
        limits=["raw snapshot retained locally", "preserve FDA attribution"],
    )


def _disclosure_source(cohort: Path, registry: dict[str, Any], raw_by_path: dict[str, dict[str, Any]], rights) -> tuple[SourcePayload, dict[str, dict[str, Any]]]:
    pdf_rows = [row for row in raw_by_path.values() if row.get("role") == "patent-marking-pdf"]
    if len(pdf_rows) != 1:
        raise CohortIntegrityError("Cook disclosure PDF is missing or ambiguous")
    pdf_path = cohort / str(pdf_rows[0]["path"])
    sections = _validate_product_rows(pdf_path)
    entry = _registry_by_id(registry)[COOK_DISCLOSURE_SOURCE_ID]
    source = source_payload(
        COOK_DISCLOSURE_SOURCE_ID,
        {"products": sections},
        uri=str(entry["linked_document_url"]),
        revision=str(entry["revision"]),
        source_date=date(2025, 1, 6),
        jurisdiction="US",
        source_type="independent_disclosure",
        license_note="Official Cook product-level patent-marking source used for local research only; redistribution remains blocked.",
        synthetic=False,
    )
    source = _source_with_metadata(
        attach_rights(source, select_rights_policy(
            rights, source_id=COOK_DISCLOSURE_SOURCE_ID, source_type="independent_disclosure",
            declared_policy_id=str(entry["rights_policy_id"]),
        )),
        locator="linked-pdf:US Patents; product rows",
        retrieved_at_utc=entry.get("retrieved_at_utc"),
        limits=[
            "raw page and PDF retained locally",
            "product-level disclosure is not claim-level semantic proof",
            "product display and redistribution BLOCKED_LOCAL",
        ],
    )
    return source, sections


def _patent_inputs(runtime: dict[str, Any], registry: dict[str, Any], rights) -> list[PatentInput]:
    result: list[PatentInput] = []
    registry_map = _registry_by_id(registry)
    for patent in runtime["patents"]:
        canonical = canonical_patent_id(str(patent["patent_id_canonical"]))
        source_id = str(patent["source_id"])
        entry = registry_map[source_id]
        source = source_payload(
            source_id,
            str(patent["text"]),
            uri=str(patent["source_url"]),
            revision=str(patent["source_revision"]),
            source_date=date.fromisoformat(str(patent["source_date"])),
            jurisdiction=str(patent["jurisdiction"]),
            source_type="patent_document",
            license_note="Google-derived patent page used for local research; raw HTML and extracted text remain local-only.",
            synthetic=False,
        )
        source = _source_with_metadata(
            attach_rights(source, select_rights_policy(
                rights, source_id=source_id, source_type="patent_document",
                declared_policy_id=str(entry["rights_policy_id"]),
            )),
            locator=f"disclosure-raw-number:{patent['patent_id_raw']}",
            retrieved_at_utc=entry.get("retrieved_at_utc"),
            limits=[
                f"raw_html_sha256:{patent['raw_html_sha256']}",
                f"normalized_sha256:{patent['normalized_sha256']}",
                "product display and redistribution BLOCKED_LOCAL",
            ],
        )
        result.append(PatentInput(patent_id=canonical, title=str(patent["title"]), source=source))
    return result


def _disclosure_evidence(source: SourcePayload, *, query_id: str, product_key: str, section: dict[str, Any]) -> EvidenceItem:
    field = f"products.{product_key}.raw_patent_numbers"
    raw_numbers = list(section["raw_patent_numbers"])
    return EvidenceItem(
        evidence_id=f"DISC-{query_id}",
        source_id=source.source.source_id,
        source_version=source.source.version_label,
        payload_hash=source.source.sha256,
        locator=f"field:{field}",
        structured_field=field,
        structured_value=raw_numbers,
        evidence_kind="patent_disclosure",
        statement=f"{section['label']} row lists {len(raw_numbers)} U.S. patent numbers.",
        support_basis="Independent Cook product patent-marking PDF; product-level listing only, not claim-level semantic proof.",
        jurisdiction=source.jurisdiction,
        source_date=source.source_date,
        extraction_method="structured_field",
    )


def build_cook_case_inputs(cohort_dir: str | Path, *, rights_matrix_path: str | Path | None = None) -> dict[str, DossierInput]:
    """Build one public-source DossierInput per Cook device without evaluator reads."""
    cohort = Path(cohort_dir)
    _, runtime, registry, raw_by_path = _validate_runtime_integrity(cohort)
    root = Path(__file__).resolve().parents[3]
    matrix_path = Path(rights_matrix_path) if rights_matrix_path else root / DEFAULT_RIGHTS_MATRIX
    if not matrix_path.exists():
        raise ValueError("Cook adapter requires a source-specific rights matrix")
    rights = load_rights_matrix(matrix_path)
    disclosure_source, sections = _disclosure_source(cohort, registry, raw_by_path, rights)
    patents = _patent_inputs(runtime, registry, rights)
    product_by_key = {str(product["key"]): product for product in PRODUCTS}
    cases: dict[str, DossierInput] = {}
    for device in runtime["devices"]:
        query_id = str(device["query_id"])
        key = str(device["device_id_canonical"]).split(":", 1)[-1].lower()
        if key not in product_by_key or key not in sections:
            raise ValueError(f"Cook runtime device has no product row: {query_id}")
        pma_source = _pma_source(cohort, device, registry, rights)
        section = sections[key]
        evidence = [
            field_evidence(pma_source, field, f"FACT-{query_id}-{field}")
            for field in ("pma_number", "generic_name", "applicant", "product_code")
            if field in pma_source.payload
        ]
        evidence.append(_disclosure_evidence(disclosure_source, query_id=query_id, product_key=key, section=section))
        brief = ProjectBrief(
            project_id="healthtech-cook-zenith-dossiers",
            version=1,
            objective="Inspect a public named-device dossier with source-backed product-level patent disclosures.",
            audience="entrepreneur",
            data_class="public",
            language="en",
            theme="formal-light",
        )
        query = {
            "query_id": query_id,
            "brief": brief,
            "device_id_raw": str(device["device_id_raw"]),
            "device_id_canonical": str(device["device_id_canonical"]),
            "selected_comparator_source_id": pma_source.source.source_id,
            "technical_description": str(device["technical_description"]),
            "features_of_interest": [str(item) for item in device.get("features_of_interest", [])],
            "user_questions": ["Which listed patent links remain unresolved at component or claim level?"],
            "company_metadata": {
                "company": str(device.get("company") or "Cook Medical"),
                "regulatory_applicant": str(device.get("regulatory_applicant") or ""),
            },
            "company_source_id": pma_source.source.source_id,
            "jurisdiction": "US",
            "evidence_cutoff": str(device["evidence_cutoff"]),
            "permitted_inputs": [pma_source.source.source_id, disclosure_source.source.source_id],
            "acquisition_budget": AcquisitionBudget(max_search_calls=1, max_returned_candidates=50),
        }
        cases[query_id] = DossierInput(
            query=query,
            sources=[pma_source, disclosure_source],
            patents=patents,
            evidence=evidence,
            policy_id="HT-B0b",
            per_search_limit=50,
        )
    return cases


def disclosed_patent_ids(dossier_input: DossierInput) -> set[str]:
    disclosure = next(item for item in dossier_input.evidence if item.evidence_kind == "patent_disclosure")
    if not isinstance(disclosure.structured_value, list):
        raise ValueError("Cook disclosure evidence must contain raw patent numbers")
    raw_to_canonical = {
        str(patent.source.source.locator).split(":", 1)[1]: canonical_patent_id(patent.patent_id)
        for patent in dossier_input.patents
        if patent.source.source.locator and str(patent.source.source.locator).startswith("disclosure-raw-number:")
    }
    return {raw_to_canonical[str(raw)] for raw in disclosure.structured_value}


def promote_disclosed_links(dossier: DossierVersion, dossier_input: DossierInput) -> DossierVersion:
    """Mark source-backed Cook links without treating them as semantic gold."""
    disclosed_ids = disclosed_patent_ids(dossier_input)
    evidence_id = next(item.evidence_id for item in dossier.evidence if item.evidence_kind == "patent_disclosure")
    existing = {candidate.patent_id_canonical for candidate in dossier.candidates}
    candidates: list[PatentCandidate] = []
    for candidate in dossier.candidates:
        if candidate.patent_id_canonical in disclosed_ids:
            candidate = candidate.model_copy(update={
                "association_status": "disclosed_link",
                "disclosure_evidence_id": evidence_id,
            })
        candidates.append(candidate)
    patents_by_id = {canonical_patent_id(patent.patent_id): patent for patent in dossier_input.patents}
    for patent_id in sorted(disclosed_ids - existing):
        patent = patents_by_id[patent_id]
        candidates.append(PatentCandidate(
            patent_id_raw=patent_id,
            patent_id_canonical=patent_id,
            source_id=patent.source.source.source_id,
            source_revision=patent.source.source.version_label,
            retrieval_action_ids=[f"disclosure-source:{COOK_DISCLOSURE_SOURCE_ID}"],
            scores={"rrf_fixed_k60": 0.0, "disclosure_source": 1.0},
            association_status="disclosed_link",
            disclosure_evidence_id=evidence_id,
        ))
    unresolved = [item for item in dossier.unresolved_items if "no independently checked device-patent disclosure" not in item]
    unresolved.extend([
        "Product-level disclosures do not establish which component or claim is relevant.",
        "Family identity remains unknown unless a separately sourced family mapping is added.",
        "Raw Cook pages/PDF and extracted patent text remain local-only; product display and redistribution are BLOCKED_LOCAL.",
    ])
    return dossier.model_copy(update={"candidates": candidates, "unresolved_items": unresolved})
