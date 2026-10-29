from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from patent_to_pilot.healthtech.contracts import content_hash
from patent_to_pilot.healthtech.engine import export_markdown, run_dossier
from patent_to_pilot.healthtech.philips import (
    CohortIntegrityError,
    _validate_product_rows,
    build_philips_case_inputs,
    disclosed_patent_ids,
    promote_disclosed_links,
)
from scripts.healthtech.fetch_philips_cardiovascular_cohort import PRODUCTS


ROOT = Path(__file__).resolve().parents[1]
RIGHTS_MATRIX = ROOT / "docs/healthtech/audits/luna-long-run-20261029-m13-philips-expansion-20261029/rights-matrix.json"


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_synthetic_philips_cohort(tmp_path: Path) -> Path:
    cohort = tmp_path / "philips-cohort"
    (cohort / "raw" / "510k").mkdir(parents=True)
    (cohort / "raw" / "disclosure").mkdir(parents=True)
    (cohort / "raw" / "patents").mkdir(parents=True)

    disclosure_html = "<table>" + "".join(
        "<tr><td>{}</td><td>{}</td></tr>".format(
            product["label"],
            "; ".join(f"{int(number):,}" for number in product["patent_numbers"]),
        )
        for product in PRODUCTS
    ) + "</table>"
    disclosure_path = cohort / "raw" / "disclosure" / "philips-patent-marking.html"
    disclosure_path.write_text(disclosure_html, encoding="utf-8")
    patent_title = "Scoring balloon catheter"
    patent_abstract = "AngioSculpt scoring balloon patent fixture"
    patent_claims = "1. A scoring balloon catheter."
    patent_text = "\n\n".join((patent_title, patent_abstract, patent_claims))
    patent_path = cohort / "raw" / "patents" / "US7686824B2.html"
    patent_path.write_text("<html>synthetic patent page</html>", encoding="utf-8")
    regulatory_payload = {
        "k_number": "K050629",
        "device_name": "ANGIOSCULPT SCORING BALLOON CATHETER",
        "applicant": "Angioscore, Inc.",
        "product_code": "PNO",
        "decision_code": "SESE",
        "decision_date": "2005-09-02",
        "date_received": "2005-03-11",
        "statement_or_summary": "Summary",
        "clearance_type": "Traditional",
        "review_advisory_committee": "CV",
    }
    regulatory_path = cohort / "raw" / "510k" / "K050629.json"
    _write_json(regulatory_path, {"results": [regulatory_payload]})

    device = {
        "query_id": "HT-DEV-PHILIPS-ANGIOSCULPT-SCORING-BALLOON",
        "device_id_raw": "ANGIOSCULPT SCORING BALLOON CATHETER (K050629)",
        "device_id_canonical": "K050629",
        "regulatory_id": "K050629",
        "regulatory_kind": "510k",
        "company": "PHILIPS IMAGE GUIDED THERAPY",
        "regulatory_applicant": "Angioscore, Inc.",
        "trade_name": "ANGIOSCULPT SCORING BALLOON CATHETER",
        "generic_name": "ANGIOSCULPT SCORING BALLOON CATHETER",
        "product_code": "PNO",
        "technical_description": "AngioSculpt scoring balloon catheter; product code PNO",
        "features_of_interest": ["AngioSculpt Scoring Balloon Catheter", "PNO"],
        "source_id": "openfda-510k-k050629",
        "evidence_cutoff": "2026-10-29",
    }
    patent_source_id = "google-patents-us7686824b2"
    runtime_patent = {
        "patent_id_raw": "7686824",
        "patent_id_canonical": "US7686824B2",
        "title": patent_title,
        "text": patent_text,
        "abstract": patent_abstract,
        "claims": patent_claims,
        "source_id": patent_source_id,
        "source_revision": "retrieved-2026-10-29",
        "source_url": "https://patents.google.com/patent/US7686824B2/en",
        "source_date": "2026-10-29",
        "jurisdiction": "US",
        "raw_html_sha256": hashlib.sha256(patent_path.read_bytes()).hexdigest(),
        "normalized_sha256": content_hash({"title": patent_title, "abstract": patent_abstract, "claims": patent_claims}),
    }
    runtime = {
        "format": "ht-runtime-public-device-cohort-v1",
        "status": "PUBLIC_PHILIPS_CARDIOVASCULAR_COHORT_ACQUIRED",
        "retrieved_at_utc": "2026-10-29T13:12:02+00:00",
        "devices": [device],
        "patents": [runtime_patent],
        "permitted_metadata": ["device facts", "patent document metadata"],
        "runtime_exclusions": ["disclosure references", "evaluator gold/reference links", "family labels", "split answers"],
    }
    source_registry = {
        "format": "ht-source-registry-v1",
        "separation": "evaluator-only disclosure source is not included in runtime.json",
        "sources": [
            {
                "source_id": "openfda-510k-k050629",
                "source_type": "regulatory_record",
                "url": "https://api.fda.gov/device/510k.json?search=k_number:K050629&limit=10",
                "revision": "openfda-meta-last-updated-2026-10-19",
                "retrieved_at_utc": "2026-10-29T13:12:02+00:00",
                "jurisdiction": "US",
                "raw_json_sha256": hashlib.sha256(regulatory_path.read_bytes()).hexdigest(),
                "payload_sha256": content_hash(regulatory_payload),
                "rights_policy_id": "openfda-510k-records",
                "runtime_allowed": True,
            },
            {
                "source_id": "philips-cardiovascular-patent-marking",
                "source_type": "independent_disclosure",
                "url": "https://www.philips.com/a-w/about/innovation/ips/contact-and-support/patent-marking",
                "revision": "retrieved-2026-10-29",
                "retrieved_at_utc": "2026-10-29T13:12:02+00:00",
                "jurisdiction": "US",
                "raw_html_sha256": hashlib.sha256(disclosure_path.read_bytes()).hexdigest(),
                "rights_policy_id": "philips-cardiovascular-patent-marking",
                "runtime_allowed": False,
            },
            {
                "source_id": patent_source_id,
                "source_type": "patent_document",
                "url": "https://patents.google.com/patent/US7686824B2/en",
                "revision": "retrieved-2026-10-29",
                "retrieved_at_utc": "2026-10-29T13:12:02+00:00",
                "jurisdiction": "US",
                "raw_html_sha256": runtime_patent["raw_html_sha256"],
                "normalized_sha256": runtime_patent["normalized_sha256"],
                "rights_policy_id": "google-patents-pages",
                "runtime_allowed": True,
            },
        ],
    }
    runtime_path = cohort / "runtime.json"
    registry_path = cohort / "source_registry.json"
    _write_json(runtime_path, runtime)
    _write_json(registry_path, source_registry)
    raw_files = []
    for path, role, url in (
        (regulatory_path, "510k-response", source_registry["sources"][0]["url"]),
        (disclosure_path, "patent-marking-page", source_registry["sources"][1]["url"]),
        (patent_path, "patent-page", source_registry["sources"][2]["url"]),
    ):
        raw_files.append({
            "path": path.relative_to(cohort).as_posix(),
            "bytes": path.stat().st_size,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "role": role,
            "url": url,
        })
    _write_json(
        cohort / "manifest.json",
        {
            "integrity_format": "ht-runtime-integrity-v1",
            "status": "PUBLIC_PHILIPS_CARDIOVASCULAR_COHORT_ACQUIRED",
            "runtime_path": "runtime.json",
            "source_registry": "source_registry.json",
            "runtime_sha256": content_hash(runtime),
            "source_registry_sha256": content_hash(source_registry),
            "raw_files": raw_files,
        },
    )
    return cohort


def test_philips_product_rows_preserve_locators():
    html = "<table>" + "".join(
        "<tr><td>{}</td><td>{}</td></tr>".format(
            product["label"],
            "; ".join(f"{int(number):,}" for number in product["patent_numbers"]),
        )
        for product in PRODUCTS
    ) + "</table>"
    rows = _validate_product_rows(html.encode("utf-8"))
    assert rows["angiosculpt-scoring-balloon"]["raw_patent_numbers"] == ["7686824"]
    assert "html-table:row=0" in rows["angiosculpt-scoring-balloon"]["source_locator"]


def test_philips_adapter_builds_cases_and_promotes_disclosures(tmp_path: Path):
    cohort = _write_synthetic_philips_cohort(tmp_path)
    cases = build_philips_case_inputs(cohort, rights_matrix_path=RIGHTS_MATRIX)

    assert sorted(cases) == ["HT-DEV-PHILIPS-ANGIOSCULPT-SCORING-BALLOON"]
    input_data = cases[next(iter(cases))]
    assert disclosed_patent_ids(input_data) == {"US7686824B2"}
    assert all(source.rights is not None for source in input_data.sources + [patent.source for patent in input_data.patents])
    assert all("evaluator" not in source.source.uri.lower() for source in input_data.sources)

    dossier, _, _ = run_dossier(input_data, run_id="philips-adapter", code_commit="test")
    linked = promote_disclosed_links(dossier, input_data)
    assert {item.patent_id_canonical for item in linked.candidates if item.association_status == "disclosed_link"} == {"US7686824B2"}
    assert any("Product-level disclosures" in item for item in linked.unresolved_items)
    with pytest.raises(ValueError, match="product_display blocked"):
        export_markdown(linked, purpose="product_display")


@pytest.mark.parametrize("mutation", ["runtime_text", "raw", "registry", "manifest"])
def test_philips_adapter_rejects_frozen_cohort_mutations(tmp_path: Path, mutation: str):
    cohort = _write_synthetic_philips_cohort(tmp_path)
    if mutation == "runtime_text":
        path = cohort / "runtime.json"
        runtime = json.loads(path.read_text(encoding="utf-8"))
        runtime["patents"][0]["text"] = "MUTATED PATENT TEXT"
        _write_json(path, runtime)
    elif mutation == "raw":
        path = cohort / "raw" / "disclosure" / "philips-patent-marking.html"
        path.write_bytes(path.read_bytes() + b"\nmutated")
    elif mutation == "registry":
        path = cohort / "source_registry.json"
        registry = json.loads(path.read_text(encoding="utf-8"))
        registry["sources"][2]["revision"] = "stale-revision"
        _write_json(path, registry)
    else:
        path = cohort / "manifest.json"
        manifest = json.loads(path.read_text(encoding="utf-8"))
        manifest["source_registry_sha256"] = "0" * 64
        _write_json(path, manifest)

    with pytest.raises(CohortIntegrityError):
        build_philips_case_inputs(cohort, rights_matrix_path=RIGHTS_MATRIX)
