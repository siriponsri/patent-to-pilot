from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from scripts.healthtech.analyze_family_frontier import analyze_family_frontier
from scripts.healthtech.analyze_family_groups import analyze
from scripts.healthtech.build_google_family_mapping import build_mapping, parse_google_family_id


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_fixture_cohort(root: Path, *, family_id: str = "12345") -> Path:
    cohort = root / "cohort"
    raw = cohort / "raw" / "patents"
    raw.mkdir(parents=True)
    html = f"<html><section itemprop=\"family\" itemscope><h2>ID={family_id}</h2></section></html>"
    raw_path = raw / "US1234567B2.html"
    raw_path.write_text(html, encoding="utf-8")
    raw_sha = hashlib.sha256(raw_path.read_bytes()).hexdigest()
    _write_json(cohort / "runtime.json", {
        "devices": [],
        "patents": [{"patent_id_canonical": "US1234567B2", "source_id": "google-patents-us1234567b2"}],
    })
    _write_json(cohort / "source_registry.json", {
        "sources": [{
            "source_id": "google-patents-us1234567b2",
            "source_type": "patent_document",
            "rights_policy_id": "google-patents-pages",
            "url": "https://patents.google.com/patent/US1234567B2/en",
            "revision": "fixture-v1",
            "raw_html_sha256": raw_sha,
        }]
    })
    _write_json(cohort / "manifest.json", {
        "runtime_path": "runtime.json",
        "source_registry": "source_registry.json",
        "raw_files": [{
            "path": "raw/patents/US1234567B2.html",
            "size_bytes": raw_path.stat().st_size,
            "sha256": raw_sha,
        }],
    })
    return cohort


def test_parse_google_family_id_requires_explicit_family_section():
    assert parse_google_family_id('<section itemprop="family"><h2>ID=77</h2></section>') == "google-docdb-77"
    with pytest.raises(ValueError, match="family section"):
        parse_google_family_id("<html></html>")


def test_build_mapping_hashes_source_and_keeps_evaluator_out(tmp_path):
    cohort = _write_fixture_cohort(tmp_path)
    payload = build_mapping([cohort])
    assert payload["status"] == "SOURCED_LOCAL_EVALUATOR_MAPPING"
    assert payload["counts"] == {"patents_mapped": 1, "families_observed": 1, "unmapped_patents": 0}
    assert payload["mappings"][0]["family_id"] == "google-docdb-12345"
    serialized = json.dumps(payload).lower()
    assert "evaluator_path" not in serialized
    assert "disclosure_evidence" not in serialized
    assert "references" not in serialized


def test_build_mapping_rejects_raw_hash_mutation(tmp_path):
    cohort = _write_fixture_cohort(tmp_path)
    raw_path = cohort / "raw" / "patents" / "US1234567B2.html"
    raw_path.write_text(raw_path.read_text(encoding="utf-8") + "mutated", encoding="utf-8")
    with pytest.raises(ValueError, match="hash/size mismatch"):
        build_mapping([cohort])


def test_family_group_analysis_merges_only_sourced_family_links(tmp_path):
    references = tmp_path / "references.json"
    groups = tmp_path / "groups.json"
    mapping = tmp_path / "mapping.json"
    _write_json(references, {"references": {"q1": ["US1234567B2"], "q2": ["US7654321B2"]}})
    _write_json(groups, {"shared_exact_patent_groups": [["q1"], ["q2"]]})
    _write_json(mapping, {"status": "SOURCED_LOCAL_EVALUATOR_MAPPING", "mapping_sha256": "a" * 64, "mappings": [
        {"patent_id_canonical": "US1234567B2", "family_id": "google-docdb-1"},
        {"patent_id_canonical": "US7654321B2", "family_id": "google-docdb-1"},
    ]})
    report = analyze(references, groups, mapping)
    assert report["counts"]["family_aware_group_count"] == 1
    assert report["counts"]["family_merged_exact_group_count"] == 1


def test_family_frontier_reprojects_metrics_without_changing_exact_rows(tmp_path):
    references = tmp_path / "references.json"
    mapping = tmp_path / "mapping.json"
    baseline = tmp_path / "baseline"
    _write_json(references, {"references": {"q1": ["US1234567B2"], "q2": ["US7654321B2"]}})
    _write_json(mapping, {"status": "SOURCED_LOCAL_EVALUATOR_MAPPING", "mapping_sha256": "b" * 64, "mappings": [
        {"patent_id_canonical": "US1234567B2", "family_id": "google-docdb-1"},
        {"patent_id_canonical": "US7654321B2", "family_id": "google-docdb-1"},
    ]})
    _write_json(baseline / "receipt.json", {"status": "REAL_PUBLIC_DEVELOPMENT_RUN"})
    _write_json(baseline / "per_device_group_results.json", {
        "HT-B0a": {"by_k": {"20": {
            "k": 20,
            "macro_known_link_recall": 0.5,
            "micro_known_link_recall": 0.5,
            "per_query": [
                {"query_id": "q1", "known_recall": 1.0},
                {"query_id": "q2", "known_recall": 0.0},
            ],
            "group_results": [{"group_id": "0", "query_ids": ["q1"]}, {"group_id": "1", "query_ids": ["q2"]}],
        }}},
    })
    _write_json(baseline / "frontier_diagnostics.json", {
        "primary_k": 20,
        "quality_resource_frontier": {"rows": [{
            "method": "HT-B0a",
            "prefix": 1,
            "scheduled_query_count": 2,
            "reached_query_count": 2,
            "failed_query_count": 0,
            "not_realized_query_count": 0,
            "macro_known_link_recall_at_20_all_devices": 0.5,
            "micro_known_link_recall_at_20": 0.5,
            "per_query": [
                {"query_id": "q1", "known_recall_at_k": 1.0, "status": "completed"},
                {"query_id": "q2", "known_recall_at_k": 0.0, "status": "completed"},
            ],
        }]},
    })
    report = analyze_family_frontier(
        baseline_dir=baseline,
        references_path=references,
        family_mapping_path=mapping,
        split="development",
    )
    assert report["counts"]["exact_group_count"] == 2
    assert report["counts"]["family_aware_group_count"] == 1
    assert report["counts"]["family_merged_exact_group_count"] == 1
    assert len(report["by_method_and_k"]["HT-B0a"]["20"]["exact_group_results"]) == 2
    assert len(report["by_method_and_k"]["HT-B0a"]["20"]["family_group_results"]) == 1
    assert len(report["frontier_rows"][0]["family_group_results"]) == 1
    assert report["uncertainty"]["status"] == "NOT_ESTIMABLE"
