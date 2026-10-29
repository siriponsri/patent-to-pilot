import json
from pathlib import Path

import pytest

from scripts.healthtech.compose_multicompany_cohort import compose_cohort


def _write_parent(root: Path, *, alias: str, company: str, query_id: str, patent_id: str) -> None:
    root.mkdir(parents=True)
    runtime = {
        "format": "ht-runtime-input-v1",
        "status": "PARENT",
        "retrieved_at_utc": "2026-10-29T00:00:00+00:00",
        "devices": [{
            "query_id": query_id,
            "company": company,
            "technical_description": f"{alias} device",
            "features_of_interest": [f"{alias} feature"],
            "source_id": f"openfda-pma-{alias}",
        }],
        "patents": [{
            "patent_id_canonical": patent_id,
            "patent_id_raw": patent_id[2:-2],
            "company_metadata": company.upper(),
            "text": f"{alias} patent text",
        }],
        "permitted_metadata": ["company", "technical_description"],
        "runtime_exclusions": ["disclosure relations", "evaluator references", "split answers"],
    }
    sources = {
        "format": "ht-source-registry-v1",
        "sources": [
            {
                "source_id": f"openfda-pma-{alias}",
                "source_type": "regulatory_record",
                "rights_policy_id": "openfda-pma-records",
                "runtime_allowed": True,
            },
            {
                "source_id": f"{alias}-disclosure",
                "source_type": "independent_disclosure",
                "rights_policy_id": f"{alias}-policy",
                "runtime_allowed": False,
            },
            {
                "source_id": f"google-patents-{patent_id.lower()}",
                "source_type": "patent_document",
                "rights_policy_id": "google-patents-pages",
                "runtime_allowed": True,
            },
        ],
    }
    references = {
        "format": "ht-evaluator-disclosures-v1",
        "references": {query_id: [patent_id]},
        "disclosure_evidence": [{
            "evidence_id": f"DISC-{query_id}",
            "query_id": query_id,
            "patent_id_canonical": [patent_id],
            "source_id": f"{alias}-disclosure",
            "locator": "fixture:row=1",
            "quoted_span": patent_id,
            "support_basis": "authored fixture",
        }],
    }
    groups = {
        "format": "ht-group-evidence-v1",
        "group_evidence": [{
            "group_id": f"shared-exact-{alias}",
            "device_query_ids": [query_id],
            "shared_patent_ids": [patent_id],
            "source_ids": [f"{alias}-disclosure"],
        }],
        "company_groups": [{"company": company, "query_ids": [query_id]}],
        "family_mapping": {"status": "UNKNOWN_NOT_ASSUMED", "mappings": []},
    }
    split = {
        "format": "ht-development-split-v1",
        "rows": [{"query_id": query_id, "split": "development", "group_id": f"shared-exact-{alias}"}],
        "final_holdout": [],
    }
    manifest = {
        "runtime_path": "runtime.json",
        "evaluator_path": "evaluator/references.json",
        "groups_path": "groups.json",
        "source_registry": "source_registry.json",
        "split_path": "split_manifest.json",
        "raw_files": [],
    }
    for path, payload in [
        (root / "runtime.json", runtime),
        (root / "source_registry.json", sources),
        (root / "evaluator" / "references.json", references),
        (root / "groups.json", groups),
        (root / "split_manifest.json", split),
        (root / "manifest.json", manifest),
    ]:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload), encoding="utf-8")


def test_composite_freezes_company_holdout_and_writes_views(tmp_path: Path):
    boston = tmp_path / "boston"
    stryker = tmp_path / "stryker"
    _write_parent(boston, alias="boston", company="Boston Scientific Corp", query_id="Q-B", patent_id="US10000001B2")
    _write_parent(stryker, alias="stryker", company="Stryker Neurovascular", query_id="Q-S", patent_id="US10000002B2")

    output = tmp_path / "composite"
    manifest = compose_cohort(boston_cohort=boston, stryker_cohort=stryker, output=output)

    assert manifest["devices"] == 2
    assert manifest["patents"] == 2
    assert manifest["final_holdout_query_ids"] == ["Q-S"]
    split = json.loads((output / "split_manifest.json").read_text(encoding="utf-8"))
    assert {row["split"] for row in split["rows"]} == {"development", "final_holdout"}
    dev = json.loads((output / "views" / "development" / "runtime.json").read_text(encoding="utf-8"))
    holdout = json.loads((output / "views" / "final_holdout" / "runtime.json").read_text(encoding="utf-8"))
    assert [row["query_id"] for row in dev["devices"]] == ["Q-B"]
    assert [row["query_id"] for row in holdout["devices"]] == ["Q-S"]
    assert len(dev["patents"]) == len(holdout["patents"]) == 2


def test_composite_rejects_untyped_parent_source(tmp_path: Path):
    boston = tmp_path / "boston"
    stryker = tmp_path / "stryker"
    _write_parent(boston, alias="boston", company="Boston Scientific Corp", query_id="Q-B", patent_id="US10000001B2")
    _write_parent(stryker, alias="stryker", company="Stryker Neurovascular", query_id="Q-S", patent_id="US10000002B2")
    registry_path = stryker / "source_registry.json"
    payload = json.loads(registry_path.read_text(encoding="utf-8"))
    payload["sources"][1].pop("rights_policy_id")
    registry_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="typed rights_policy_id"):
        compose_cohort(boston_cohort=boston, stryker_cohort=stryker, output=tmp_path / "composite")


def test_composite_accepts_additional_typed_parent(tmp_path: Path):
    boston = tmp_path / "boston"
    stryker = tmp_path / "stryker"
    cook = tmp_path / "cook"
    _write_parent(boston, alias="boston", company="Boston Scientific Corp", query_id="Q-B", patent_id="US10000001B2")
    _write_parent(stryker, alias="stryker", company="Stryker Neurovascular", query_id="Q-S", patent_id="US10000002B2")
    _write_parent(cook, alias="cook", company="Cook Medical", query_id="Q-C", patent_id="US10000003B2")

    output = tmp_path / "composite"
    manifest = compose_cohort(
        boston_cohort=boston,
        stryker_cohort=stryker,
        output=output,
        additional_cohorts=[("cook", cook)],
    )

    assert manifest["devices"] == 3
    assert manifest["final_holdout_query_ids"] == ["Q-S"]
    assert manifest["development_query_ids"] == ["Q-B", "Q-C"]
    assert any(row["company"] == "Cook Medical" for row in json.loads((output / "groups.json").read_text(encoding="utf-8"))["company_groups"])
