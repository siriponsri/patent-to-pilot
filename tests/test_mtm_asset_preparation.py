import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from patent_to_pilot.research.mtm_runtime import InputBoundaryError
from patent_to_pilot.research.vector_identity import sha256
from test_mtm_preflight import setup_inputs


def inputs(tmp_path):
    setup = setup_inputs(tmp_path)
    script = Path(__file__).resolve().parents[1] / "scripts/healthtech/prepare_mtm_dev_assets.py"
    spec = importlib.util.spec_from_file_location("prepare_assets_test", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    report = tmp_path / "report.json"
    report.write_text(json.dumps({"identity": setup["trusted_original"]}))
    queries = tmp_path / "source-queries.jsonl"
    queries.write_bytes(b'{"id":"q1", "text":"prefix: original query"}\r\n')
    args = SimpleNamespace(source_corpus=tmp_path / "original.jsonl", dev_queries=queries,
                           metadata_root=setup["metadata_root"], identity_report=report,
                           identity_report_sha256=sha256(report), view="P", expected_missing_count=0,
                           output_root=tmp_path / "assets")
    return module, args


def test_preparation_preserves_query_bytes_and_emits_only_hashes_counts(tmp_path):
    module, args = inputs(tmp_path)
    receipt = module.prepare(args)
    assert receipt["cohort_queries"] == receipt["available_queries"] == 1
    assert receipt["physical_isolation"] == "CURATOR_ATTESTATION_REQUIRED"
    assert (args.output_root / "queries/queries.jsonl").read_bytes() == args.dev_queries.read_bytes()
    assert "original query" not in json.dumps(receipt)
    assert receipt["projection_receipt_sha256"] == sha256(args.output_root / "corpus/projection.json")
    assert (args.output_root / "asset-receipt.json").is_file()
    with pytest.raises(InputBoundaryError):
        module.prepare(args)


@pytest.mark.parametrize("bad", ["test_id", "labels", "identity", "missing_expectation", "corpus"])
def test_refusal_preserves_sources_and_has_no_completion_receipt(tmp_path, bad):
    module, args = inputs(tmp_path)
    if bad == "test_id":
        args.dev_queries.write_text('{"id":"outside-dev","text":"synthetic"}\n')
    elif bad == "labels":
        args.dev_queries.write_text('{"id":"q1","text":"synthetic","targets":["secret"]}\n')
    elif bad == "identity":
        args.identity_report_sha256 = "0" * 64
    elif bad == "missing_expectation":
        args.expected_missing_count = 1
    else:
        args.source_corpus.write_text(args.source_corpus.read_text().replace("first", "changed"))
    before = args.dev_queries.read_bytes()
    with pytest.raises(InputBoundaryError):
        module.prepare(args)
    assert args.dev_queries.read_bytes() == before
    assert not (args.output_root / "asset-receipt.json").exists()
    if bad == "corpus":
        assert args.output_root.exists()  # partial attempt kept for inspection
