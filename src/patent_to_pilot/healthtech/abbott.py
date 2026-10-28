"""Deterministic adapter for the local Abbott public-device cohort.

This module reads only normalized runtime records, source metadata, and raw
public source snapshots. It never reads evaluator reference relations.
"""
from __future__ import annotations

from datetime import date, datetime, timezone
import json
from pathlib import Path
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
from scripts.healthtech.fetch_public_device_cohort import PRODUCTS, _product_disclosures, _selected_pma_record


DISCLOSURE_SOURCE_ID = "abbott-product-patent-disclosures"
COHORT_FORMAT = "ht-runtime-public-device-cohort-v1"


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _source_with_metadata(
    source: SourcePayload,
    *,
    locator: str | None,
    retrieved_at_utc: str | None,
    limits: list[str],
) -> SourcePayload:
    retrieved_at = datetime.fromisoformat(retrieved_at_utc.replace("Z", "+00:00")) if retrieved_at_utc else None
    record = source.source.model_copy(update={
        "locator": locator,
        "retrieved_at": retrieved_at,
        "limits": limits,
    })
    return source.model_copy(update={"source": record})


def _registry_by_id(registry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    sources = registry.get("sources")
    if not isinstance(sources, list) or not all(isinstance(item, dict) for item in sources):
        raise ValueError("source registry is missing sources")
    return {str(item["source_id"]): item for item in sources}


def _pma_source(cohort: Path, device: dict[str, Any], registry: dict[str, Any], rights) -> SourcePayload:
    pma_number = str(device["pma_number"])
    raw_path = cohort / "raw" / "pma" / f"{pma_number}.json"
    raw_payload = _read_json(raw_path)
    rows = raw_payload.get("results")
    if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
        raise ValueError(f"malformed PMA snapshot: {raw_path}")
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
            rights, source_id=source_id, source_type=source.source.source_type
        )),
        locator=f"openFDA:pma_number={pma_number}",
        retrieved_at_utc=entry.get("retrieved_at_utc"),
        limits=["raw snapshot retained locally", "preserve FDA attribution"],
    )


def _disclosure_source(cohort: Path, registry: dict[str, Any], rights) -> tuple[SourcePayload, dict[str, dict[str, Any]]]:
    raw_path = cohort / "raw" / "abbott-patents.html"
    html = raw_path.read_bytes()
    sections = _product_disclosures(html)
    payload = {"products": sections}
    entry = _registry_by_id(registry)[DISCLOSURE_SOURCE_ID]
    source = source_payload(
        DISCLOSURE_SOURCE_ID,
        payload,
        uri=str(entry["url"]),
        revision=str(entry["revision"]),
        source_date=date.fromisoformat(str(entry["revision"]).split("page-retrieved-", 1)[1]),
        jurisdiction="US",
        source_type="independent_disclosure",
        license_note="Product-level public disclosure used for local research only; claim-level use and redistribution remain unresolved.",
        synthetic=False,
    )
    source = _source_with_metadata(
        attach_rights(source, select_rights_policy(
            rights, source_id=DISCLOSURE_SOURCE_ID, source_type=source.source.source_type
        )),
        locator="product-sections:Abbott patent legal notice",
        retrieved_at_utc=entry.get("retrieved_at_utc"),
        limits=[
            "raw HTML retained locally",
            "product-level disclosure is not claim-level semantic proof",
            "product display and redistribution BLOCKED_LOCAL pending rights review",
        ],
    )
    return source, sections


def _patent_inputs(cohort: Path, runtime: dict[str, Any], registry: dict[str, Any], rights) -> list[PatentInput]:
    patents = runtime.get("patents")
    if not isinstance(patents, list) or not all(isinstance(item, dict) for item in patents):
        raise ValueError("runtime cohort is missing patents")
    registry_map = _registry_by_id(registry)
    inputs: list[PatentInput] = []
    for patent in patents:
        canonical = canonical_patent_id(str(patent["patent_id_canonical"]))
        source_id = str(patent["source_id"])
        entry = registry_map[source_id]
        raw_number = str(patent["patent_id_raw"])
        payload = str(patent["text"])
        source = source_payload(
            source_id,
            payload,
            uri=str(patent["source_url"]),
            revision=str(patent["source_revision"]),
            source_date=date.fromisoformat(str(patent["source_date"])),
            jurisdiction=str(patent["jurisdiction"]),
            source_type="patent_document",
            license_note="Public patent page used for local research; raw page and extracted text remain local-only.",
            synthetic=False,
        )
        source = _source_with_metadata(
            attach_rights(source, select_rights_policy(
                rights, source_id=source_id, source_type=source.source.source_type
            )),
            locator=f"disclosure-raw-number:{raw_number}",
            retrieved_at_utc=entry.get("retrieved_at_utc"),
            limits=[
                f"raw_html_sha256:{patent['raw_html_sha256']}",
                f"normalized_sha256:{patent['normalized_sha256']}",
                "product display and redistribution BLOCKED_LOCAL pending rights review",
            ],
        )
        inputs.append(PatentInput(patent_id=canonical, title=str(patent["title"]), source=source))
    return inputs


def _disclosure_evidence(
    source: SourcePayload,
    *,
    query_id: str,
    product_key: str,
    section: dict[str, Any],
) -> EvidenceItem:
    field = f"products.{product_key}.raw_patent_numbers"
    raw_numbers = list(section["raw_patent_numbers"])
    return EvidenceItem(
        evidence_id=f"DISC-{query_id}",
        source_id=source.source.source_id,
        source_version=source.source.version_label,
        payload_hash=source.source.sha256 or content_hash(source.payload),
        locator=f"field:{field}",
        structured_field=field,
        structured_value=raw_numbers,
        evidence_kind="patent_disclosure",
        statement=f"{section['label']} section lists {len(raw_numbers)} U.S. patent numbers.",
        support_basis="Independent Abbott product patent disclosure page; product-level listing only, not claim-level semantic proof.",
        jurisdiction=source.jurisdiction,
        source_date=source.source_date,
        extraction_method="structured_field",
    )


def _product_for_device(device: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    for product in PRODUCTS:
        if product["pma_number"] == device["pma_number"]:
            return str(product["key"]), product
    raise ValueError(f"unknown product mapping for {device['pma_number']}")


def _search_description(device: dict[str, Any]) -> str:
    """Use a concise, source-derived lexical anchor for the BM25 baseline."""
    generic = str(device["generic_name"]).lower()
    if "tricuspid" in generic:
        return "tricuspid valve"
    if "mitral" in generic:
        return "mitral valve"
    return " ".join(generic.split()[:2])


def build_abbott_case_inputs(
    cohort_dir: str | Path, *, rights_matrix_path: str | Path | None = None
) -> dict[str, DossierInput]:
    """Build one public-source DossierInput per Abbott device without evaluator reads."""
    cohort = Path(cohort_dir)
    runtime = _read_json(cohort / "runtime.json")
    registry = _read_json(cohort / "source_registry.json")
    if runtime.get("format") != COHORT_FORMAT:
        raise ValueError("unsupported runtime cohort format")
    devices = runtime.get("devices")
    if not isinstance(devices, list) or not all(isinstance(item, dict) for item in devices):
        raise ValueError("runtime cohort is missing devices")
    root = Path(__file__).resolve().parents[3]
    default_paths = [
        root / "docs/healthtech/audits/luna-patent-dossiers-20261028-rights-cohort/rights-matrix.json",
        root / "docs/healthtech/audits/luna-patent-dossiers-20261028-atomic/rights-matrix.json",
    ]
    matrix_path = Path(rights_matrix_path) if rights_matrix_path else next(
        (path for path in default_paths if path.exists()), None
    )
    if matrix_path is None:
        raise ValueError("Abbott adapter requires a source-specific rights matrix")
    rights = load_rights_matrix(matrix_path)
    disclosure_source, disclosure_sections = _disclosure_source(cohort, registry, rights)
    patents = _patent_inputs(cohort, runtime, registry, rights)
    by_patent_raw = {
        str(item["patent_id_raw"]): canonical_patent_id(str(item["patent_id_canonical"]))
        for item in runtime["patents"]
    }
    cases: dict[str, DossierInput] = {}
    for device in devices:
        product_key, product = _product_for_device(device)
        pma_source = _pma_source(cohort, device, registry, rights)
        query_id = str(device["query_id"])
        section = disclosure_sections[product_key]
        disclosed_ids = [by_patent_raw[str(raw)] for raw in section["raw_patent_numbers"]]
        evidence = [
            field_evidence(pma_source, field, f"FACT-{query_id}-{field}")
            for field in ("pma_number", "trade_name", "generic_name", "applicant")
            if field in pma_source.payload
        ]
        evidence.append(_disclosure_evidence(
            disclosure_source,
            query_id=query_id,
            product_key=product_key,
            section=section,
        ))
        brief = ProjectBrief(
            project_id="healthtech-abbott-patent-dossiers",
            version=1,
            objective="Inspect a public named-device dossier with independently disclosed patent links.",
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
            "technical_description": _search_description(device),
            "features_of_interest": [str(item) for item in device["features_of_interest"]],
            "user_questions": ["Which listed patent links remain unresolved at component or claim level?"],
            "company_metadata": {"applicant": str(device["company"])},
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
    """Recover disclosed canonical IDs from the input evidence and patent sources."""
    disclosure = next(e for e in dossier_input.evidence if e.evidence_kind == "patent_disclosure")
    if not isinstance(disclosure.structured_value, list):
        raise ValueError("disclosure evidence must contain raw patent numbers")
    raw_to_canonical = {
        str(patent.source.source.locator).split(":", 1)[1]: canonical_patent_id(patent.patent_id)
        for patent in dossier_input.patents
        if patent.source.source.locator and str(patent.source.source.locator).startswith("disclosure-raw-number:")
    }
    return {raw_to_canonical[str(raw)] for raw in disclosure.structured_value}


def promote_disclosed_links(dossier: DossierVersion, dossier_input: DossierInput) -> DossierVersion:
    """Annotate ranked candidates and append evidence-only disclosed links."""
    disclosed_ids = disclosed_patent_ids(dossier_input)
    evidence_id = next(e.evidence_id for e in dossier.evidence if e.evidence_kind == "patent_disclosure")
    existing = {candidate.patent_id_canonical for candidate in dossier.candidates}
    candidates: list[PatentCandidate] = []
    for candidate in dossier.candidates:
        if candidate.patent_id_canonical in disclosed_ids:
            candidate = candidate.model_copy(update={
                "association_status": "disclosed_link",
                "disclosure_evidence_id": evidence_id,
            })
        candidates.append(candidate)
    sources = {source.source.source_id: source for source in dossier.sources}
    patents_by_id = {canonical_patent_id(patent.patent_id): patent for patent in dossier_input.patents}
    for patent_id in sorted(disclosed_ids - existing):
        patent = patents_by_id[patent_id]
        candidates.append(PatentCandidate(
            patent_id_raw=patent_id,
            patent_id_canonical=patent_id,
            source_id=patent.source.source.source_id,
            source_revision=patent.source.source.version_label,
            retrieval_action_ids=[f"disclosure-source:{DISCLOSURE_SOURCE_ID}"],
            scores={"rrf_fixed_k60": 0.0, "disclosure_source": 1.0},
            association_status="disclosed_link",
            disclosure_evidence_id=evidence_id,
        ))
    unresolved = [
        item for item in dossier.unresolved_items
        if "no independently checked device-patent disclosure" not in item
    ]
    unresolved.extend([
        "Product-level disclosures do not establish which component or claim is relevant.",
        "Family identity remains unknown unless a separately sourced family mapping is added.",
        "Raw third-party pages and extracted text remain local-only; product display and redistribution are BLOCKED_LOCAL.",
    ])
    return dossier.model_copy(update={"candidates": candidates, "unresolved_items": unresolved})


def build_abbott_development_protocol(cohort_dir: str | Path) -> dict[str, Any]:
    """Freeze a development-only universe, distractor rule, groups, and split."""
    cohort = Path(cohort_dir)
    runtime = _read_json(cohort / "runtime.json")
    registry = _read_json(cohort / "source_registry.json")
    cases = build_abbott_case_inputs(cohort)
    universe = sorted(canonical_patent_id(str(item["patent_id_canonical"])) for item in runtime["patents"])
    disclosed_by_query = {query_id: sorted(disclosed_patent_ids(case)) for query_id, case in sorted(cases.items())}
    distractors_by_query = {
        query_id: [patent_id for patent_id in universe if patent_id not in disclosed]
        for query_id, disclosed in disclosed_by_query.items()
    }
    groups: list[set[str]] = []
    remaining = set(disclosed_by_query)
    while remaining:
        root = min(remaining)
        group = {root}
        changed = True
        while changed:
            changed = False
            for query_id in sorted(remaining - group):
                if any(set(disclosed_by_query[query_id]) & set(disclosed_by_query[member]) for member in group):
                    group.add(query_id)
                    changed = True
        remaining -= group
        groups.append(group)
    group_evidence = []
    for group in sorted(groups, key=lambda values: sorted(values)):
        members = sorted(group)
        shared = set(universe)
        for query_id in members:
            shared &= set(disclosed_by_query[query_id])
        group_id = "shared-exact-" + content_hash(members)[:12]
        group_evidence.append({
            "group_id": group_id,
            "device_query_ids": members,
            "shared_patent_ids": sorted(shared),
            "basis": "Same canonical patent document appears in independently parsed Abbott product disclosure sections.",
            "source_ids": [DISCLOSURE_SOURCE_ID],
            "family_id": None,
            "family_status": "UNKNOWN_NOT_ASSUMED",
        })
    company_groups: dict[str, list[str]] = {}
    for query_id, case in sorted(cases.items()):
        pma = next(source for source in case.sources if source.source.source_id == case.query.selected_comparator_source_id)
        company = str(pma.payload.get("applicant", "UNKNOWN")) if isinstance(pma.payload, dict) else "UNKNOWN"
        company_groups.setdefault(company, []).append(query_id)
    registry_map = _registry_by_id(registry)
    return {
        "format": "ht-development-protocol-v1",
        "status": "DEVELOPMENT_ONLY_FREEZE_NO_HOLDOUT",
        "frozen_at_utc": datetime.now(timezone.utc).isoformat(),
        "selection_rule": "Predeclared Abbott PMA devices plus every canonical patent document in the frozen runtime universe.",
        "distractor_rule": "For each device, every universe patent not listed in that device's independently parsed product disclosure is an unjudged distractor, never a negative.",
        "eligible_query_ids": sorted(cases),
        "evidence_cutoffs": {query_id: case.query.evidence_cutoff.isoformat() for query_id, case in sorted(cases.items())},
        "universe": universe,
        "disclosed_by_query": disclosed_by_query,
        "distractors_by_query": distractors_by_query,
        "counts": {
            "eligible_devices": len(cases),
            "universe_patents": len(universe),
            "disclosed_pairs": sum(len(values) for values in disclosed_by_query.values()),
            "unjudged_distractor_pairs": sum(len(values) for values in distractors_by_query.values()),
        },
        "groups": {
            "shared_exact_patent_groups": group_evidence,
            "company_groups": [
                {"company": company, "query_ids": sorted(query_ids), "basis": "PMA applicant field", "source_ids": [cases[query_ids[0]].query.selected_comparator_source_id]}
                for company, query_ids in sorted(company_groups.items())
            ],
            "family_mapping": {"status": "UNKNOWN_NOT_ASSUMED", "mappings": []},
        },
        "split": {
            "assignment_rule": "All eligible devices remain in development; no final holdout is claimed for this three-device single-company slice.",
            "rows": [
                {"query_id": query_id, "split": "development", "group_id": next(item["group_id"] for item in group_evidence if query_id in item["device_query_ids"])}
                for query_id in sorted(cases)
            ],
            "final_holdout": [],
        },
        "source_refs": {
            "runtime_sha256": content_hash(runtime),
            "source_registry_sha256": content_hash(registry),
            "disclosure_source_id": DISCLOSURE_SOURCE_ID,
            "disclosure_raw_html_sha256": registry_map[DISCLOSURE_SOURCE_ID].get("raw_html_sha256"),
        },
        "resource_policy": {
            "provider_calls": 0,
            "paid_cost_usd": 0,
            "method": "HT-B0b local lexical baseline",
            "max_search_calls_per_device": 1,
            "max_returned_candidates_per_device": 50,
        },
        "limitations": [
            "Product-level disclosure is not component-level semantic relevance or claim construction.",
            "Unlisted pairs remain unjudged; the distractor list is not a negative-label set.",
            "Family identity is unknown and is not inferred from shared applicant or document overlap.",
            "No final holdout or generalization claim is supported.",
        ],
    }
