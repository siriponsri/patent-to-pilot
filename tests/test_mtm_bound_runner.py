import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from patent_to_pilot.research.mtm_queries import load_dev_queries
from patent_to_pilot.research.mtm_runtime import InputBoundaryError
from patent_to_pilot.research.vector_identity import sha256
from test_mtm_preflight import setup_inputs

ROOT = Path(__file__).resolve().parents[1]


def bundle(tmp_path, rows=None, missing=None, split="dev"):
    root = tmp_path / "queries"
    root.mkdir()
    rows = rows if rows is not None else [{"id": "q1", "text": "literal prefixed query"}]
    payload = root / "queries.jsonl"
    payload.write_text(''.join(json.dumps(row) + '\n' for row in rows))
    manifest = root / "manifest.json"
    manifest.write_text(json.dumps({"format": "ptp-mtm-query-text-v1", "split": split, "view": "P",
                                    "sha256": sha256(payload), "queries": len(rows), "missing_ids": missing or []}))
    return root, sha256(manifest)


def test_missing_query_is_explicit_and_text_unchanged(tmp_path):
    root, digest = bundle(tmp_path, missing=["q2"])
    result = load_dev_queries(root, digest, {"q1", "q2"})
    assert result["rows"][0]["text"] == "literal prefixed query"
    assert result["missing_ids"] == ["q2"]


@pytest.mark.parametrize("kind", ["unknown", "omitted", "overlap", "duplicate", "label", "empty", "hash", "test"])
def test_bad_queries_fail(tmp_path, kind):
    rows = [{"id": "q1", "text": "query"}]
    missing, population = [], {"q1"}
    if kind == "unknown":
        rows[0]["id"] = "unknown"
    elif kind == "omitted":
        population.add("q2")
    elif kind == "overlap":
        missing = ["q1"]
    elif kind == "duplicate":
        rows *= 2
    elif kind == "label":
        rows[0]["targets"] = ["hidden"]
    elif kind == "empty":
        rows[0]["text"] = " "
    root, digest = bundle(tmp_path, rows, missing, "test" if kind == "test" else "dev")
    if kind == "hash":
        digest = "0" * 64
    if kind == "test":
        (root / "queries.jsonl").unlink()  # must reject before opening payload
    with pytest.raises(InputBoundaryError):
        load_dev_queries(root, digest, population)


def runner_setup(tmp_path):
    paths = setup_inputs(tmp_path)
    query_root, query_digest = bundle(tmp_path)
    script = ROOT / "scripts/healthtech/run_mtm_dev_bound.py"
    spec = importlib.util.spec_from_file_location("test_bound_entry", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    identity = paths["trusted_original"]
    identity["model"]["encoder_source_sha256"] = sha256(script.with_name("run_dapfam_dense_pool.py"))
    manifest = tmp_path / "identity.json"
    manifest.write_text(json.dumps(identity))
    args = SimpleNamespace(metadata_root=paths["metadata_root"], query_root=query_root,
                           corpus=paths["corpus"], vectors=paths["vectors"], model_root=paths["model_root"],
                           projection_receipt=paths["projection_receipt"],
                           projection_receipt_sha256=paths["trusted_receipt_sha256"],
                           metadata_manifest_sha256=sha256(paths["metadata_root"] / "manifest.json"),
                           query_manifest_sha256=query_digest, original_identity=manifest,
                           original_identity_sha256=sha256(manifest),
                           runner_source_sha256=sha256(script.with_name("run_mtm_dense_pool.py")),
                           output_dir=tmp_path / "output", batch_size=64)
    return module, args


def test_bad_identity_stops_before_dynamic_runner_import(tmp_path, monkeypatch):
    module, args = runner_setup(tmp_path)
    args.vectors.write_bytes(b"corrupt")
    monkeypatch.setattr(module.importlib.util, "spec_from_file_location",
                        lambda *a: pytest.fail("runner imported before preflight"))
    with pytest.raises((InputBoundaryError, ValueError)):
        module.run(args)
    assert not args.output_dir.exists()


@pytest.mark.parametrize("fail", [False, True])
def test_gate_precedes_frozen_runner_and_preserves_attempt(tmp_path, monkeypatch, fail):
    module, args = runner_setup(tmp_path)
    previous = module.sys.argv
    def main():
        assert (args.output_dir / "bound-preflight.json").exists()
        argv = module.sys.argv
        assert argv[argv.index("--views") + 1] == "main"
        assert argv[argv.index("--name") + 1] == "P-dev"
        assert argv[argv.index("--reuse-vectors") + 1] == str(args.vectors)
        assert "--split" not in argv
        if fail:
            raise RuntimeError("synthetic failure")
        return 0
    monkeypatch.setattr(module.importlib.util, "module_from_spec",
                        lambda spec: SimpleNamespace(main=main))
    # The returned spec loader installs nothing; main above is our synthetic stand-in.
    monkeypatch.setattr(module.importlib.util, "spec_from_file_location",
                        lambda *a: SimpleNamespace(loader=SimpleNamespace(exec_module=lambda value: None)))
    if fail:
        with pytest.raises(RuntimeError, match="synthetic failure"):
            module.run(args)
        receipt = json.loads((args.output_dir / "bound-failure.json").read_text())
        assert receipt["status"] == "RUN_FAILED_OR_INTERRUPTED"
    else:
        assert module.run(args) == 0
        receipt = json.loads((args.output_dir / "bound-outcome.json").read_text())
        assert receipt["ranking_parity"] == "NOT_ASSESSED"
    assert module.sys.argv is previous
    with pytest.raises(InputBoundaryError, match="output exists"):
        module.run(args)
