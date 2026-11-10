"""Synthetic-only boundary tests. No real benchmark files are accessed."""
import hashlib
import json
from pathlib import Path

import pytest

from patent_to_pilot.evaluation.mtm_dev_inputs import load_dev_qrels
from patent_to_pilot.evaluation.mtm_staging import stage_metadata
from patent_to_pilot.research.mtm_runtime import InputBoundaryError, load_dev_metadata, validate_metadata


def source_rows():
    return [
        {"id": "dev-one", "family_id": "query-one", "priority": 20100101,
         "c3": ["A61"], "split": "dev", "targets": ["dev-positive"]},
        {"id": "dev-two", "family_id": "query-two", "priority": 20110228,
         "c3": [], "split": "dev", "targets": ["other-positive"]},
        {"id": "test-one", "family_id": "query-three", "priority": 20190101,
         "c3": ["G06"], "split": "test", "targets": ["SYNTHETIC_PROTECTED_SENTINEL"]},
    ]


def stage(tmp_path, rows=None):
    source = tmp_path / "curator-source.jsonl"
    source.write_text("".join(json.dumps(r) + "\n" for r in (source_rows() if rows is None else rows)), encoding="utf-8")
    runtime, dev, protected = (tmp_path / n for n in ("runtime", "dev-evaluation", "protected"))
    receipt = stage_metadata(source, runtime, dev, protected)
    return runtime, dev, protected, receipt


def replace_payload(root, rows, filename="metadata.jsonl"):
    raw = "".join(json.dumps(r) + "\n" for r in rows).encode()
    (root / filename).write_bytes(raw)
    manifest = json.loads((root / "manifest.json").read_text())
    manifest.update(sha256=hashlib.sha256(raw).hexdigest(), queries=len(rows))
    (root / "manifest.json").write_text(json.dumps(manifest))


def test_staging_preserves_population_and_separates_payloads(tmp_path):
    runtime, dev, protected, receipt = stage(tmp_path)
    meta = load_dev_metadata(runtime / "dev")
    assert set(meta) == {"dev-one", "dev-two"}
    assert load_dev_qrels(dev, query_ids=set(meta)) == {
        "dev-one": {"dev-positive"}, "dev-two": {"other-positive"}}
    for path in runtime.rglob("*"):
        if path.is_file():
            assert b"targets" not in path.read_bytes()
            assert b"positive" not in path.read_bytes()
            assert b"SYNTHETIC_PROTECTED_SENTINEL" not in path.read_bytes()
    assert b"SYNTHETIC_PROTECTED_SENTINEL" in (protected / "qrels.jsonl").read_bytes()
    assert receipt["physical_isolation"] == "CURATOR_ATTESTATION_REQUIRED"
    assert receipt["status"] != "PASS"


@pytest.mark.parametrize("change", [
    {"targets": ["SYNTHETIC_PROTECTED_SENTINEL"]},
    {"c3": [{"targets": ["SYNTHETIC_PROTECTED_SENTINEL"]}]},
    {"family_id": {"targets": ["SYNTHETIC_PROTECTED_SENTINEL"]}},
    {"priority": True}, {"priority": "20100101"}, {"priority": 20100230},
    {"c3": ["A61B"]}, {"c3": ["A61", "A61"]}, {"sets": ["target"]},
])
def test_allowlist_rejects_nested_labels_types_and_roles(change):
    row = {"id": "q", "family_id": "f", "priority": 20100101, "c3": ["A61"]}
    with pytest.raises(InputBoundaryError) as exc:
        validate_metadata({**row, **change})
    assert "SYNTHETIC_PROTECTED_SENTINEL" not in str(exc.value)


def test_tampered_and_rehashed_label_payload_still_rejected(tmp_path):
    runtime, _, _, _ = stage(tmp_path)
    root = runtime / "dev"
    rows = [json.loads(line) for line in (root / "metadata.jsonl").read_text().splitlines()]
    rows[0]["targets"] = ["forbidden"]
    replace_payload(root, rows)
    with pytest.raises(InputBoundaryError, match="fields"):
        load_dev_metadata(root)


def test_content_hash_mismatch(tmp_path):
    runtime, _, _, _ = stage(tmp_path)
    path = runtime / "dev" / "metadata.jsonl"
    path.write_bytes(path.read_bytes() + b"\n")
    with pytest.raises(InputBoundaryError, match="hash"):
        load_dev_metadata(path.parent)


def test_protected_manifest_rejected_before_payload_open(tmp_path, monkeypatch):
    runtime, _, protected, _ = stage(tmp_path)
    original = Path.read_bytes
    opened = []

    def watched(path):
        opened.append(path.name)
        assert path.name not in {"metadata.jsonl", "qrels.jsonl"}
        return original(path)

    monkeypatch.setattr(Path, "read_bytes", watched)
    with pytest.raises(InputBoundaryError, match="development"):
        load_dev_metadata(runtime / "test")
    with pytest.raises(InputBoundaryError, match="development"):
        load_dev_qrels(protected, query_ids={"test-one"})
    assert opened == ["manifest.json", "manifest.json"]


def test_manifest_cannot_redirect_to_protected_file(tmp_path):
    runtime, _, _, _ = stage(tmp_path)
    path = runtime / "dev" / "manifest.json"
    manifest = json.loads(path.read_text())
    manifest["path"] = "../../protected/qrels.jsonl"
    path.write_text(json.dumps(manifest))
    with pytest.raises(InputBoundaryError, match="fields"):
        load_dev_metadata(path.parent)


def test_query_denominator_mismatch_and_duplicates_rejected(tmp_path):
    runtime, dev, _, _ = stage(tmp_path)
    with pytest.raises(InputBoundaryError, match="population"):
        load_dev_qrels(dev, query_ids={"dev-one"})
    meta = list(load_dev_metadata(runtime / "dev").values())
    replace_payload(runtime / "dev", [meta[0], meta[0]])
    with pytest.raises(InputBoundaryError, match="duplicate"):
        load_dev_metadata(runtime / "dev")


def test_staging_rejects_cross_split_family_without_writing(tmp_path):
    rows = source_rows()
    rows[-1]["family_id"] = rows[0]["family_id"]
    with pytest.raises(InputBoundaryError, match="cross-split"):
        stage(tmp_path, rows)
    assert not (tmp_path / "runtime").exists()
    assert not (tmp_path / "protected").exists()


def test_staging_rejects_nested_destinations_and_overwrite(tmp_path):
    runtime, dev, protected, _ = stage(tmp_path)
    source = tmp_path / "curator-source.jsonl"
    before = (protected / "qrels.jsonl").read_bytes()
    with pytest.raises(InputBoundaryError, match="exists"):
        stage_metadata(source, runtime, dev, protected)
    with pytest.raises(InputBoundaryError, match="disjoint"):
        stage_metadata(source, tmp_path / "new", tmp_path / "new" / "dev", tmp_path / "p2")
    assert (protected / "qrels.jsonl").read_bytes() == before


def test_duplicate_json_keys_rejected(tmp_path):
    runtime, _, _, _ = stage(tmp_path)
    path = runtime / "dev" / "manifest.json"
    path.write_text('{"split":"test","split":"dev"}')
    with pytest.raises(InputBoundaryError, match="duplicate JSON"):
        load_dev_metadata(path.parent)


def test_runtime_module_has_no_evaluator_imports():
    import ast
    import patent_to_pilot.research.mtm_runtime as runtime

    tree = ast.parse(Path(runtime.__file__).read_text())
    imports = [n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)]
    assert not any("evaluation" in (module or "") for module in imports)


def test_staged_metadata_preserves_frozen_mask_outputs(tmp_path):
    import numpy as np

    runtime, _, _, _ = stage(tmp_path)
    meta = load_dev_metadata(runtime / "dev")
    # Exercise the exact frozen helper, without importing any runner/GPU model.
    source = (Path(__file__).parents[1] / "scripts/healthtech/run_mtm_dense_pool.py").read_text()
    namespace = {}
    exec(source[source.index("def keep_mask"):source.index("def main")], namespace)
    keep = namespace["keep_mask"]
    visible = [20000101, 20150101, 20090101, 20100101]
    for row in source_rows()[:2]:
        for lane in ("U", "X"):
            for view in ([True] * 4, [True, False, True, False]):
                prior = keep(visible, row["priority"], 0, view, [2], lane)
                staged = keep(visible, meta[row["id"]]["priority"], 0, view, [2], lane)
                assert np.array_equal(prior, staged)
