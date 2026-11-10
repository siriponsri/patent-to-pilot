import json
from pathlib import Path
import subprocess
import sys

import pytest

from patent_to_pilot.evaluation.mtm_ranking_parity import compare_rankings, load_rankings
from patent_to_pilot.research.mtm_runtime import InputBoundaryError
from patent_to_pilot.research.vector_identity import sha256


def bundle(tmp_path, rows, **overrides):
    payload = tmp_path / "rankings.jsonl"
    payload.write_text(''.join(json.dumps(row) + '\n' for row in rows))
    value = {"format": "ptp-mtm-dev-rankings-v1", "split": "dev", "view": "P", "lane": "X",
             "corpus_view": "main", "queries": 1, "sha256": sha256(payload), **overrides}
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps(value))
    return sha256(manifest)


def load(tmp_path, digest):
    return load_rankings(tmp_path, manifest_sha256=digest, query_ids={"q1"}, view="P", lane="X")


def test_exact_parity_keeps_missing_and_empty_denominators():
    result = compare_rankings({"a": ["f1"], "b": []}, {"b": [], "a": ["f1"]},
                              cohort_ids={"a", "b", "missing"}, missing_ids={"missing"})
    assert result["status"] == "EXACT_RANKING_PARITY_PASS"
    assert result["cohort_queries"] == 3
    assert result["available_queries"] == 2
    assert result["predeclared_missing_queries"] == 1
    assert result["both_empty_rankings"] == 1


def test_order_membership_length_and_deep_prefix_changes():
    old = {"a": ["x", "y"], "b": ["z"], "c": [str(i) for i in range(200)]}
    new = {"a": ["y", "x"], "b": [], "c": old["c"][:199] + ["replacement"]}
    result = compare_rankings(old, new, cohort_ids=set(old), missing_ids=set())
    assert result["status"] == "RANKING_PARITY_FAIL"
    assert result["order_only_changes"] == 1
    assert result["membership_changes"] == 2
    assert result["length_changes"] == 1
    assert result["identical_prefix_counts"] == {"20": 1, "100": 1, "200": 0}
    assert "replacement" not in json.dumps(result)


@pytest.mark.parametrize("change", ["test", "lane", "view", "corpus", "count", "unknown", "duplicate_query",
                                     "duplicate_family", "missing", "labels", "depth", "digest"])
def test_invalid_bundles_refused(tmp_path, change):
    rows = [{"query_id": "q1", "families": ["f1"]}]
    overrides = {}
    if change == "test":
        overrides["split"] = "test"
    elif change in ("lane", "view", "corpus", "count"):
        key, value = {"lane": ("lane", "U"), "view": ("view", "T"), "corpus": ("corpus_view", "small"),
                      "count": ("queries", 2)}[change]
        overrides[key] = value
    elif change == "unknown":
        rows[0]["query_id"] = "q2"
    elif change == "duplicate_query":
        rows *= 2
    elif change == "duplicate_family":
        rows[0]["families"] *= 2
    elif change == "missing":
        rows = []
    elif change == "labels":
        rows[0]["targets"] = ["hidden"]
    elif change == "depth":
        rows[0]["families"] = [str(i) for i in range(201)]
    digest = bundle(tmp_path, rows, **overrides)
    if change == "test":
        (tmp_path / "rankings.jsonl").unlink()
    if change == "digest":
        digest = "0" * 64
    with pytest.raises(InputBoundaryError):
        load(tmp_path, digest)


def test_valid_bundle_and_comparator_rejects_silent_omission(tmp_path):
    digest = bundle(tmp_path, [{"query_id": "q1", "families": []}])
    assert load(tmp_path, digest) == {"q1": []}
    with pytest.raises(InputBoundaryError):
        compare_rankings({}, {}, cohort_ids={"q1"}, missing_ids=set())
    with pytest.raises(InputBoundaryError):
        compare_rankings({"q1": ["f", "f"]}, {"q1": ["f", "f"]}, cohort_ids={"q1"}, missing_ids=set())


def test_cli_reports_failure_without_overwrite(tmp_path):
    from test_mtm_bound_runner import bundle as query_bundle
    from test_mtm_preflight import setup_inputs

    inputs = setup_inputs(tmp_path)
    query_root, query_digest = query_bundle(tmp_path)
    old, new = tmp_path / "reference", tmp_path / "candidate"
    old.mkdir()
    new.mkdir()
    old_digest = bundle(old, [{"query_id": "q1", "families": ["f1"]}])
    new_digest = bundle(new, [{"query_id": "q1", "families": ["f2"]}])
    output = tmp_path / "result.json"
    command = [sys.executable, str(Path(__file__).resolve().parents[1] / "scripts/healthtech/compare_mtm_dev_rankings.py"),
               "--metadata-root", str(inputs["metadata_root"]), "--query-root", str(query_root),
               "--reference-root", str(old), "--candidate-root", str(new), "--output", str(output),
               "--metadata-manifest-sha256", sha256(inputs["metadata_root"] / "manifest.json"),
               "--query-manifest-sha256", query_digest, "--reference-manifest-sha256", old_digest,
               "--candidate-manifest-sha256", new_digest, "--lane", "X"]
    first = subprocess.run(command, capture_output=True, text=True)
    assert first.returncode == 1
    result = json.loads(output.read_text())
    assert result["status"] == "RANKING_PARITY_FAIL"
    before = output.read_bytes()
    second = subprocess.run(command, capture_output=True, text=True)
    assert second.returncode != 0 and output.read_bytes() == before
