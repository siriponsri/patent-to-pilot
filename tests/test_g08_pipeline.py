import io
import json
from pathlib import Path

import pytest

from patent_to_pilot.extraction.interfaces import ExtractionRequest, LexicalExtractor, ModelExtractionAdapter
from patent_to_pilot.ingestion.pls import PLSIngester, PatentDocument
from patent_to_pilot.retrieval.fts import FTSIndex

ROOT = Path(__file__).parents[1]
# Project-authored CSV-shaped fixture: no external download or scientific claim.
PLS = ROOT / "tests" / "fixtures" / "legacy_pls.csv"


def test_streaming_pls_sample_preserves_locator_and_unknown_date():
    stream = io.StringIO()
    count = PLSIngester().ingest_to_stream(PLS, stream, "PLS-AUTHORED-FIXTURE", "authored-v1", max_rows=3)
    lines = stream.getvalue().splitlines()
    assert count == 3 and len(lines) == 3
    assert all('"publication_date_status":"unknown_not_in_source"' in line for line in lines)
    assert all("#row=" in line for line in lines)


def test_fts_search_filter_and_lexical_extraction(tmp_path):
    normalized = tmp_path / "atazanavir.jsonl"
    report = PLSIngester().ingest_jsonl(PLS, normalized, "PLS-AUTHORED-FIXTURE", "authored-v1", max_rows=20)
    assert report.rows_written == 20
    index = FTSIndex(tmp_path / "index.sqlite")
    assert index.add_jsonl(normalized) == 20
    hits = index.search("aryl piperazines", limit=3, source_id="PLS-AUTHORED-FIXTURE")
    assert hits and all(hit.source_id == "PLS-AUTHORED-FIXTURE" for hit in hits)
    document = next(PLSIngester().iter_documents(PLS, "PLS-AUTHORED-FIXTURE", "authored-v1", max_rows=1))
    fact = LexicalExtractor().extract(ExtractionRequest(document_id=document.document_id, role="source_fact", query="aryl piperazines", component="title"), document)
    assert fact.model_called is False and fact.state.value == "supported" and fact.source_locator == document.source_locator
    index.close()


def test_missing_literal_is_unknown_and_model_adapter_is_disabled():
    document = next(PLSIngester().iter_documents(PLS, "PLS-AUTHORED-FIXTURE", "authored-v1", max_rows=1))
    fact = LexicalExtractor().extract(ExtractionRequest(document_id=document.document_id, role="source_fact", query="term-not-present", component="abstract"), document)
    assert fact.state.value == "unknown"
    with pytest.raises(RuntimeError):
        ModelExtractionAdapter(object()).extract(ExtractionRequest(document_id=document.document_id, role="source_fact", query="x"), document)


def test_unicode_casefold_returns_offsets_in_original_text():
    document = PatentDocument(document_id="D-UNICODE", source_id="S", source_version="v1", title="Straße glass", source_locator="fixture#title", source_sha256="0" * 64)
    fact = LexicalExtractor().extract(ExtractionRequest(document_id="D-UNICODE", role="source_fact", query="glass", component="title"), document)
    assert fact.state.value == "supported"
    assert (fact.char_start, fact.char_end) == (7, 12)
    assert fact.value == document.title[7:12] == "glass"


def test_missing_fields_and_duplicate_family_are_reported(tmp_path):
    source = tmp_path / "small.csv"
    source.write_text(
        "Family Number,Patent Number,Kind Code,Title,Abstract,Claims,Description,CPC,IPC,labels\n"
        "F1,P1,A1,Known title,,,,CPC,IPC,L1\n"
        "F1,P2,A1,Second title,abstract,claim,description,CPC,IPC,L2\n",
        encoding="utf-8",
    )
    out = tmp_path / "normalized.jsonl"
    report = PLSIngester().ingest_jsonl(source, out, "TEST", "fixture-v1")
    assert report.missing_counts["Abstract"] == 1
    assert report.duplicate_family_count == 1
    assert report.publication_dates_unknown == 2
    assert len(out.read_text(encoding="utf-8").splitlines()) == 2


def test_evaluator_fields_are_not_a_patent_document_contract():
    document = next(PLSIngester().iter_documents(PLS, "PLS-AUTHORED-FIXTURE", "authored-v1", max_rows=1))
    payload = json.loads(document.model_dump_json())
    payload["expected_doc_ids"] = ["hidden"]
    with pytest.raises(Exception):
        from patent_to_pilot.ingestion.pls import PatentDocument
        PatentDocument.model_validate(payload)


def test_malformed_row_rejects_and_preserves_previous_output(tmp_path):
    source = tmp_path / "malformed.csv"
    source.write_text(
        "Family Number,Patent Number,Kind Code,Title,Abstract,Claims,Description,CPC,IPC,labels\n"
        "F0,P0,A1,valid,a,b,c,CPC,IPC,L0\n"
        "F1,P1,A1,valid,a,b,c,CPC,IPC,L1,EXTRA\n", encoding="utf-8"
    )
    output = tmp_path / "normalized.jsonl"
    output.write_text("previous output\n", encoding="utf-8")
    with pytest.raises(ValueError, match="malformed CSV row.*expected 10 fields, got 11"):
        PLSIngester().ingest_jsonl(source, output, "TEST", "v1")
    assert output.read_text(encoding="utf-8") == "previous output\n"


def test_input_output_alias_is_rejected_without_touching_input(tmp_path):
    source = tmp_path / "same.csv"
    source.write_text("Family Number,Patent Number,Kind Code,Title,Abstract,Claims,Description,CPC,IPC,labels\nF1,P1,A1,t,a,c,d,CPC,IPC,L1\n", encoding="utf-8")
    with pytest.raises(ValueError, match="different files"):
        PLSIngester().ingest_jsonl(source, source, "TEST", "v1")
    assert source.read_text(encoding="utf-8").startswith("Family Number,Patent Number")


def test_fts_source_version_label_membership_and_tie_break(tmp_path):
    index = FTSIndex(tmp_path / "index.sqlite", source_id="S", source_version="v1")
    docs = [
        PatentDocument(document_id="D-B", source_id="S", source_version="v1", title="same", labels="['L1', 'L10']", source_locator="b", source_sha256="1" * 64),
        PatentDocument(document_id="D-A", source_id="S", source_version="v1", title="same", labels="['L10']", source_locator="a", source_sha256="2" * 64),
    ]
    for doc in docs: index.add(doc)
    index.connection.commit()
    assert [hit.document_id for hit in index.search("same", limit=10, label="L1")] == ["D-B"]
    assert [hit.document_id for hit in index.search("same", limit=10)] == ["D-A", "D-B"]
    with pytest.raises(ValueError, match="outside this index scope"):
        index.add(docs[0].model_copy(update={"document_id": "D-C", "source_version": "v2"}))
    index.close()
