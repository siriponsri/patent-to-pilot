from pathlib import Path

import fitz
import hashlib
import json
import pytest

from patent_to_pilot.healthtech.contracts import content_hash
from patent_to_pilot.healthtech.cook import (
    build_cook_case_inputs,
    disclosed_patent_ids,
    promote_disclosed_links,
)
from patent_to_pilot.healthtech.engine import export_markdown, run_dossier
from scripts.healthtech.fetch_cook_zenith_cohort import (
    COOK_DISCLOSURE_SOURCE_ID,
    PRODUCTS,
    _freeze_groups,
    _validate_product_rows,
    _validate_runtime_separation,
)


ROOT = Path(__file__).resolve().parents[1]
RIGHTS_MATRIX = ROOT / "docs/healthtech/audits/luna-long-run-20261029-cook-expansion-20261029/rights-matrix.json"


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_pdf(path: Path, *, include_dissection: bool = True) -> None:
    document = fitz.open()
    page = document.new_page()
    page.insert_text(
        (40, 60),
        "Zenith Renu AAA Ancillary Graft Converter\n7,335,224\n"
        "Zenith Flex AAA Endovascular Graft\n7,335,224; 7,294,147",
    )
    page = document.new_page()
    if include_dissection:
        page.insert_text(
            (40, 60),
            "Zenith Dissection Endovascular Stent\n7,993,383; 9,278,017",
        )
    document.save(path)


def _write_synthetic_cook_cohort(tmp_path: Path) -> Path:
    """Create an authored Cook runtime fixture without evaluator inputs."""
    cohort = tmp_path / "cook-cohort"
    (cohort / "raw" / "pma").mkdir(parents=True)
    (cohort / "raw" / "patents").mkdir(parents=True)
    (cohort / "raw" / "disclosure").mkdir(parents=True)
    (cohort / "evaluator").mkdir()

    pdf_path = cohort / "raw" / "disclosure" / "US-Patents-List-for-US-website-2025.2.pdf"
    _write_pdf(pdf_path)
    html_path = cohort / "raw" / "disclosure" / "cook-patents.html"
    html_path.write_text("Cook patent-marking page fixture", encoding="utf-8")

    pma_records = {
        "P020018": {
            "pma_number": "P020018",
            "supplement_number": None,
            "applicant": "Cook, Inc.",
            "generic_name": "SYSTEM, ENDOVASCULAR GRAFT",
            "trade_name": "ZENITH AAA ENDOVASCULAR GRAFT",
            "product_code": "MIH",
            "decision_date": "2003-05-23",
            "decision_code": "APPR",
        },
        "P180001": {
            "pma_number": "P180001",
            "supplement_number": None,
            "applicant": "Cook, Inc.",
            "generic_name": "STENT, ENDOVASCULAR",
            "trade_name": "ZENITH DISSECTION ENDOVASCULAR STENT",
            "product_code": "MIH",
            "decision_date": "2018-04-20",
            "decision_code": "APPR",
        },
    }
    for pma_number, record in pma_records.items():
        _write_json(cohort / "raw" / "pma" / f"{pma_number}.json", {"results": [record]})

    devices = []
    for product in PRODUCTS:
        key = str(product["key"])
        pma_number = str(product["pma_number"])
        source_id = f"openfda-pma-{pma_number.lower()}-base"
        devices.append({
            "query_id": f"HT-DEV-COOK-{key.upper()}",
            "device_id_raw": f"{product['display_name']} ({pma_number}:{key.upper()})",
            "device_id_canonical": f"{pma_number}:{key.upper()}",
            "pma_number": pma_number,
            "supplement_number": "BASE",
            "company": "Cook Medical",
            "regulatory_applicant": "Cook, Inc.",
            "trade_name": str(product["display_name"]),
            "generic_name": str(pma_records[pma_number]["generic_name"]),
            "product_code": "MIH",
            "technical_description": f"{product['display_name']}; endovascular device",
            "features_of_interest": [str(product["display_name"]), "endovascular", "implant"],
            "source_id": source_id,
            "evidence_cutoff": "2026-10-29",
        })

    raw_patent_numbers = sorted({str(number) for product in PRODUCTS for number in product["patent_numbers"]})
    patents = []
    for raw_number in raw_patent_numbers:
        canonical = f"US{raw_number}B2"
        text = f"Synthetic Cook patent {raw_number}; endovascular implant fixture text."
        raw_html = f"<html><title>{canonical}</title><body>{text}</body></html>".encode()
        raw_html_path = cohort / "raw" / "patents" / f"{canonical}.html"
        raw_html_path.write_bytes(raw_html)
        patents.append({
            "patent_id_raw": raw_number,
            "patent_id_canonical": canonical,
            "document_kind": "US-grant",
            "jurisdiction": "US",
            "title": f"Synthetic endovascular implant {raw_number}",
            "abstract": text,
            "claims": text,
            "text": text,
            "source_id": f"google-patents-{canonical.lower()}",
            "source_revision": "fixture-v1",
            "source_url": f"https://patents.google.com/patent/{canonical}/en",
            "raw_html_sha256": hashlib.sha256(raw_html).hexdigest(),
            "normalized_sha256": hashlib.sha256(text.encode()).hexdigest(),
            "source_date": "2026-10-28",
            "company_metadata": "Cook Medical",
            "company_metadata_basis": "authored synthetic fixture",
        })

    registry_sources = []
    for pma_number in sorted(pma_records):
        raw_path = cohort / "raw" / "pma" / f"{pma_number}.json"
        registry_sources.append({
            "source_id": f"openfda-pma-{pma_number.lower()}-base",
            "source_type": "regulatory_record",
            "url": f"https://api.fda.gov/device/pma.json?search=pma_number:{pma_number}",
            "revision": "fixture-pma-v1",
            "retrieved_at_utc": "2026-10-29T00:00:00+00:00",
            "jurisdiction": "US",
            "rights_policy_id": "openfda-pma-records",
            "runtime_allowed": True,
            "raw_json_sha256": hashlib.sha256(raw_path.read_bytes()).hexdigest(),
        })
    for patent in patents:
        registry_sources.append({
            "source_id": patent["source_id"],
            "source_type": "patent_document",
            "url": patent["source_url"],
            "revision": patent["source_revision"],
            "retrieved_at_utc": "2026-10-29T00:00:00+00:00",
            "jurisdiction": "US",
            "raw_html_sha256": patent["raw_html_sha256"],
            "normalized_sha256": patent["normalized_sha256"],
            "rights_policy_id": "google-patents-pages",
            "runtime_allowed": True,
        })
    registry_sources.append({
        "source_id": COOK_DISCLOSURE_SOURCE_ID,
        "source_type": "independent_disclosure",
        "url": "https://www.cookmedical.com/patents/",
        "linked_document_url": "https://www.cookmedical.com/wp-content/uploads/2025/01/US-Patents-List-for-US-website-2025.2.pdf",
        "revision": "fixture-pdf-v1",
        "retrieved_at_utc": "2026-10-29T00:00:00+00:00",
        "jurisdiction": "US",
        "raw_html_sha256": hashlib.sha256(html_path.read_bytes()).hexdigest(),
        "pdf_sha256": hashlib.sha256(pdf_path.read_bytes()).hexdigest(),
        "rights_policy_id": "cook-medical-patent-marking",
        "runtime_allowed": False,
    })

    runtime = {
        "format": "ht-runtime-public-device-cohort-v1",
        "status": "SYNTHETIC_RUNTIME_FIXTURE",
        "retrieved_at_utc": "2026-10-29T00:00:00+00:00",
        "devices": devices,
        "patents": patents,
        "permitted_metadata": ["FDA PMA fields", "patent title/abstract/claims", "canonical document IDs"],
        "runtime_exclusions": ["disclosure references", "evaluator gold/reference links", "family labels", "split answers"],
    }
    registry = {
        "format": "ht-source-registry-v1",
        "separation": "evaluator-only disclosure source is not included in runtime.json",
        "sources": registry_sources,
    }
    _write_json(cohort / "runtime.json", runtime)
    _write_json(cohort / "source_registry.json", registry)
    raw_files = []
    for path, role in [
        *[(cohort / "raw" / "pma" / f"{pma}.json", "pma-response") for pma in sorted(pma_records)],
        (html_path, "patent-marking-page"),
        (pdf_path, "patent-marking-pdf"),
        *[(cohort / "raw" / "patents" / f"US{number}B2.html", "patent-page") for number in raw_patent_numbers],
    ]:
        payload = path.read_bytes()
        raw_files.append({
            "path": path.relative_to(cohort).as_posix(),
            "size_bytes": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest(),
            "role": role,
        })
    _write_json(cohort / "manifest.json", {
        "integrity_format": "ht-runtime-integrity-v1",
        "status": "SYNTHETIC_COOK_RUNTIME_FIXTURE",
        "runtime_path": "runtime.json",
        "source_registry": "source_registry.json",
        "runtime_sha256": content_hash(runtime),
        "source_registry_sha256": content_hash(registry),
        "raw_files": raw_files,
    })
    (cohort / "evaluator" / "references.json").write_text("evaluator-only fixture; adapter must not read", encoding="utf-8")
    return cohort


def test_cook_pdf_rows_validate_and_preserve_locators(tmp_path: Path):
    pdf_path = tmp_path / "cook.pdf"
    _write_pdf(pdf_path)

    rows = _validate_product_rows(pdf_path)

    assert set(rows) == {str(product["key"]) for product in PRODUCTS}
    assert rows["zenith-flex-aaa"]["raw_patent_numbers"] == ["7335224", "7294147"]
    assert rows["zenith-dissection-stent"]["source_locator"] == "pdf-pages:2"


def test_cook_pdf_rows_reject_missing_product(tmp_path: Path):
    pdf_path = tmp_path / "cook.pdf"
    _write_pdf(pdf_path, include_dissection=False)

    with pytest.raises(ValueError, match="Zenith Dissection"):
        _validate_product_rows(pdf_path)


def test_cook_runtime_separation_rejects_disclosure_leak():
    runtime = {
        "devices": [{"source_id": COOK_DISCLOSURE_SOURCE_ID}],
        "patents": [],
        "runtime_exclusions": ["disclosure", "evaluator", "split"],
    }

    with pytest.raises(ValueError, match="leaked"):
        _validate_runtime_separation(runtime)


def test_cook_exact_patent_overlap_forms_group():
    references = {
        "HT-DEV-COOK-ZENITH-FLEX-AAA": ["US7335224B2", "US7294147B2"],
        "HT-DEV-COOK-ZENITH-RENU-CONVERTER": ["US7335224B2"],
        "HT-DEV-COOK-ZENITH-DISSECTION-STENT": ["US7993383B2", "US9278017B2"],
    }
    _, groups, split = _freeze_groups(references, sorted({value for values in references.values() for value in values}))

    assert sorted(groups["shared_exact_patent_groups"]) == [
        ["HT-DEV-COOK-ZENITH-DISSECTION-STENT"],
        ["HT-DEV-COOK-ZENITH-FLEX-AAA", "HT-DEV-COOK-ZENITH-RENU-CONVERTER"],
    ]
    assert split["final_holdout"] == []


def test_cook_adapter_builds_cases_and_promotes_pdf_disclosures(tmp_path: Path):
    cohort = _write_synthetic_cook_cohort(tmp_path)
    cases = build_cook_case_inputs(cohort, rights_matrix_path=RIGHTS_MATRIX)

    assert sorted(cases) == [
        "HT-DEV-COOK-ZENITH-DISSECTION-STENT",
        "HT-DEV-COOK-ZENITH-FLEX-AAA",
        "HT-DEV-COOK-ZENITH-RENU-CONVERTER",
    ]
    expected = {
        "HT-DEV-COOK-ZENITH-DISSECTION-STENT": {"US7993383B2", "US9278017B2"},
        "HT-DEV-COOK-ZENITH-FLEX-AAA": {"US7335224B2", "US7294147B2"},
        "HT-DEV-COOK-ZENITH-RENU-CONVERTER": {"US7335224B2"},
    }
    for query_id, input_data in cases.items():
        assert len(input_data.patents) == 4
        assert input_data.query.selected_comparator_source_id in input_data.query.permitted_inputs
        assert all(source.rights is not None for source in input_data.sources + [patent.source for patent in input_data.patents])
        assert all("evaluator" not in source.source.uri.lower() for source in input_data.sources)
        disclosure = [item for item in input_data.evidence if item.evidence_kind == "patent_disclosure"]
        assert len(disclosure) == 1
        assert set(disclosure[0].structured_value)  # raw product numbers reconstructed from PDF
        assert disclosed_patent_ids(input_data) == expected[query_id]

        dossier, _, _ = run_dossier(input_data, run_id=f"cook-adapter-{query_id}", code_commit="test")
        linked = promote_disclosed_links(dossier, input_data)
        assert {item.patent_id_canonical for item in linked.candidates if item.association_status == "disclosed_link"} == expected[query_id]
        assert linked.candidates
        assert all(item.source_id in {source.source.source_id for source in linked.sources} for item in linked.candidates)
        assert any("Product-level disclosures" in item for item in linked.unresolved_items)
        with pytest.raises(ValueError, match="product_display blocked"):
            export_markdown(linked, purpose="product_display")


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        ("runtime", "runtime JSON hash"),
        ("runtime_text", "runtime JSON hash"),
        ("raw", "raw file"),
        ("registry", "source registry hash"),
        ("missing", "raw file is missing"),
        ("metadata", "source_registry_sha256"),
    ],
)
def test_cook_adapter_rejects_frozen_cohort_mutations(tmp_path: Path, mutation: str, message: str):
    cohort = _write_synthetic_cook_cohort(tmp_path)
    if mutation == "runtime":
        path = cohort / "runtime.json"
        runtime = json.loads(path.read_text(encoding="utf-8"))
        runtime["devices"][0]["technical_description"] = "MUTATED DEVICE"
        _write_json(path, runtime)
    elif mutation == "runtime_text":
        path = cohort / "runtime.json"
        runtime = json.loads(path.read_text(encoding="utf-8"))
        runtime["patents"][0]["text"] = "MUTATED PATENT TEXT"
        _write_json(path, runtime)
    elif mutation == "raw":
        path = cohort / "raw" / "pma" / "P020018.json"
        path.write_bytes(path.read_bytes() + b"\nmutated")
    elif mutation == "registry":
        path = cohort / "source_registry.json"
        registry = json.loads(path.read_text(encoding="utf-8"))
        registry["sources"][0]["revision"] = "stale-revision"
        _write_json(path, registry)
    elif mutation == "missing":
        (cohort / "raw" / "disclosure" / "US-Patents-List-for-US-website-2025.2.pdf").unlink()
    else:
        path = cohort / "manifest.json"
        manifest = json.loads(path.read_text(encoding="utf-8"))
        manifest.pop("source_registry_sha256")
        _write_json(path, manifest)

    with pytest.raises(ValueError, match=message):
        build_cook_case_inputs(cohort, rights_matrix_path=RIGHTS_MATRIX)
