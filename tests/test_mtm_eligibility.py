import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest

from patent_to_pilot.evaluation.mtm_eligibility import audit_eligibility
from patent_to_pilot.evaluation.mtm_staging import stage_metadata
from patent_to_pilot.research.mtm_runtime import InputBoundaryError


def frozen_mask():
    path = Path(__file__).parents[1] / "scripts/healthtech/run_mtm_dense_pool.py"
    spec = importlib.util.spec_from_file_location("frozen_mask_for_audit", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.keep_mask


def query():
    return {"q": {"id": "q", "family_id": "self", "priority": 20100101, "c3": ["A61"]}}


def test_exact_mask_categories_and_denominators():
    corpus = [{"id": "eligible", "visible_from": 20100101, "c3": ["B01"]},
              {"id": "future", "visible_from": 20100102, "c3": ["B01"]},
              {"id": "self", "visible_from": 20000101, "c3": ["A61"]},
              {"id": "representative-shares", "visible_from": 20000101, "c3": ["A61"]},
              {"id": "unknown", "visible_from": None, "c3": ["B01"]},
              {"id": "invalid-date", "visible_from": 20000230, "c3": ["B01"]},
              {"id": "invalid-cpc", "visible_from": 20000101, "c3": None}]
    gold = {"q": {r["id"] for r in corpus} | {"absent"}}
    report = audit_eligibility(query(), gold, corpus, keep_mask=frozen_mask())
    assert report["queries"] == 1 and report["pairs"] == 8
    assert report["pair_classification"] == {"eligible": 1, "ineligible": 4, "indeterminate": 3}
    assert report["overlapping_reasons"] == {
        "absent_from_corpus": 1, "unknown_publication_date": 1, "malformed_publication_date": 1,
        "malformed_cpc3": 1, "publication_after_cutoff": 1, "own_family": 1, "shared_cpc3": 2}
    assert report["queries_dropped"] == 0 and not report["labels_changed"]
    assert report["queries_with_indeterminate_targets"] == 1
    assert report["queries_with_zero_verified_eligible_targets"] == 0
    assert len(gold["q"]) == 8


def test_representative_cpc_mismatch_surfaced_without_relabelling():
    # Fictional gold was selected with cited CPC B01, but representative has A61.
    corpus = [{"id": "target", "visible_from": 20000101, "c3": ["A61"]}]
    report = audit_eligibility(query(), {"q": {"target"}}, corpus, keep_mask=frozen_mask())
    assert report["status"] == "REQUIRES_REVIEW"
    assert report["overlapping_reasons"]["shared_cpc3"] == 1
    assert report["queries_with_zero_verified_eligible_targets"] == 1
    assert report["queries_dropped"] == 0


def test_valid_all_pass_and_duplicate_corpus_rejected():
    corpus = [{"id": "target", "visible_from": 20000101, "c3": []}]
    assert audit_eligibility(query(), {"q": {"target"}}, corpus, keep_mask=frozen_mask())["status"] == "PASS"
    with pytest.raises(InputBoundaryError, match="duplicate corpus"):
        audit_eligibility(query(), {"q": {"target"}}, corpus * 2, keep_mask=frozen_mask())


def test_population_mismatch_fails_before_corpus_access():
    def forbidden():
        raise AssertionError("corpus must not be read")
        yield
    with pytest.raises(InputBoundaryError, match="population"):
        audit_eligibility(query(), {}, forbidden(), keep_mask=frozen_mask())


def test_cli_staged_dev_integration_and_overwrite_refusal(tmp_path):
    source = tmp_path / "synthetic-curator.jsonl"
    source.write_text("\n".join(json.dumps(row) for row in [
        {**query()["q"], "split": "dev", "targets": ["target"]},
        {"id": "tq", "family_id": "tf", "priority": 20190101, "c3": [],
         "split": "test", "targets": ["fictional-sealed-target"]}]) + "\n")
    stage_metadata(source, tmp_path / "runtime", tmp_path / "dev", tmp_path / "protected")
    corpus = tmp_path / "corpus.jsonl"
    corpus.write_text(json.dumps({"id": "target", "visible_from": 20000101, "c3": ["B01"]}) + "\n")
    output = tmp_path / "audit.json"
    command = [sys.executable, str(Path(__file__).parents[1] / "scripts/healthtech/audit_mtm_dev_eligibility.py"),
               "--runtime-dev", str(tmp_path / "runtime/dev"), "--dev-evaluation", str(tmp_path / "dev"),
               "--corpus", str(corpus), "--output", str(output)]
    run = subprocess.run(command, capture_output=True, text=True)
    assert run.returncode == 0, run.stderr
    report = json.loads(output.read_text())
    assert report["status"] == "PASS" and report["pair_classification"]["eligible"] == 1
    assert len(report["inputs_sha256"]["frozen_runner"]) == 64
    assert "fictional-sealed-target" not in run.stdout + output.read_text()
    preserved = output.read_bytes()
    repeated = subprocess.run(command, capture_output=True, text=True)
    assert repeated.returncode != 0 and output.read_bytes() == preserved
    assert "refusing to overwrite" in repeated.stderr
