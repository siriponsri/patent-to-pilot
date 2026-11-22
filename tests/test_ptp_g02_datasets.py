"""PTP-2026-11-21/G02 dataset contracts: registry, availability, schema inspection, adapters.

All rows come from tests/fixtures/ptp_g02/datasets (synthetic, fictional, schema-only)."""
from __future__ import annotations

import copy
import dataclasses
import json
from pathlib import Path
import unicodedata

import pytest

from patent_to_pilot.workbench.datasets import adapters as A
from patent_to_pilot.workbench.datasets import evaluator as E
from patent_to_pilot.workbench.datasets import registry as R
from patent_to_pilot.workbench.datasets.inspect import inspect_schema
from patent_to_pilot.workbench.datasets.loaders import iter_jsonl
from patent_to_pilot.workbench.datasets.policy import ProtectedPathError

REPO = Path(__file__).resolve().parents[1]
FIX = REPO / "tests/fixtures/ptp_g02/datasets"
REG = R.load_registry()


def rows(rel: str) -> list[dict]:
    # Test-side read of synthetic fixtures (including the evaluator-side ones) without the runtime guard.
    with (FIX / rel).open(encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def all_strings(obj) -> list[str]:
    if isinstance(obj, str):
        return [obj]
    if isinstance(obj, dict):
        return [s for v in obj.values() for s in all_strings(v)]
    if isinstance(obj, (list, tuple)):
        return [s for v in obj for s in all_strings(v)]
    if dataclasses.is_dataclass(obj):
        return all_strings(dataclasses.asdict(obj))
    return []


# ----------------------------------------------------------------------------------------- registry
def test_registry_validates_and_pins_revisions():
    ids = {d["dataset_id"]: d for d in REG["datasets"]}
    assert ids["datalyes/DAPFAM_patent"]["revision"] == "780f4011d60297fc6e97a4119b0c516d13afea2d"
    assert ids["VISAI-AI/thai-gazette-evidence-retrieval"]["revision"] == "87e695ee4951ff34932804431433ac55991ec374"
    assert ids["VISAI-AI/nitibench-plus"]["revision"] == "41286bcb1eeba6721c03d581d4ca3095a1b7f7b7"
    assert "ptp_g01_fixture" in ids
    assert ids["datalyes/DAPFAM_patent"]["exposure"].startswith("previously_exposed_benchmark")
    assert ids["datalyes/DAPFAM_patent"]["exposure_counts"] == {"all": 1247, "out": 905, "in": 1217}
    for d in REG["datasets"]:
        if d.get("hf_repo"):
            assert d["development_use"] is False
            assert d["sources"]["revision"] and d["sources"]["license"]


def test_registry_rejects_field_in_runtime_and_evaluator():
    bad = copy.deepcopy(REG)
    cfg = next(d for d in bad["datasets"] if d["dataset_id"] == A.GAZETTE)["native_configs"][1]
    cfg["runtime_fields"].append("question_type")
    with pytest.raises(R.RegistryError, match="question_type"):
        R.validate_registry(bad)


def test_registry_rejects_unsourced_fact_and_claimed_acceptance():
    bad = copy.deepcopy(REG)
    niti = next(d for d in bad["datasets"] if d["dataset_id"] == A.NITIBENCH_PLUS)
    niti["access"]["acceptance_performed"] = True
    del niti["sources"]["license"]
    with pytest.raises(R.RegistryError) as exc:
        R.validate_registry(bad)
    assert "acceptance_record" in str(exc.value) and "'license' has no source" in str(exc.value)


def test_evaluator_configs_have_no_runtime_fields():
    for d in REG["datasets"]:
        for c in d["native_configs"]:
            if c["config"] in ("relations", "default", "gold_sections"):
                assert c["evaluator_only"] is True and c["runtime_fields"] == []


# ------------------------------------------------------------------------------------- availability
def test_not_downloaded_when_no_markers(tmp_path):
    a = R.availability(A.DAPFAM, [tmp_path / "ds"])
    assert a.status == R.NOT_DOWNLOADED and not a.available


def test_local_copy_found_from_markers_and_sidecar(tmp_path):
    d = tmp_path / "ds" / "datalyes__DAPFAM_patent"
    d.mkdir(parents=True)
    (d / "corpus.parquet").write_bytes(b"")
    (d / "queries.parquet").write_bytes(b"")
    (d / R.SIDECAR_NAME).write_text(json.dumps({"revision": "780f4011d60297fc6e97a4119b0c516d13afea2d"}), encoding="utf-8")
    a = R.availability(A.DAPFAM, [tmp_path / "ds"])
    assert a.status == R.LOCAL_COPY_FOUND and a.path == str(d) and a.revision_matches is True


def test_hf_cache_snapshot_revision_is_recorded(tmp_path):
    snap = tmp_path / "hub" / "datasets--VISAI-AI--thai-gazette-evidence-retrieval" / "snapshots" / ("0" * 40)
    (snap / "corpus").mkdir(parents=True)
    (snap / "queries").mkdir()
    a = R.availability(A.GAZETTE, [tmp_path / "hub"])
    assert a.status == R.LOCAL_COPY_FOUND and a.recorded_revision == "0" * 40 and a.revision_matches is False


def test_gated_dataset_never_available_even_with_files(tmp_path):
    d = tmp_path / "ds" / "VISAI-AI" / "nitibench-plus"
    d.mkdir(parents=True)
    (d / "validation_split.jsonl").write_text("", encoding="utf-8")
    a = R.availability(A.NITIBENCH_PLUS, [tmp_path / "ds"])
    assert a.status == R.GATED_ACCEPTANCE_REQUIRED and not a.available and a.path is None
    assert R.availability(A.NITIBENCH_PLUS, []).status == R.GATED_ACCEPTANCE_REQUIRED
    assert "files exist locally" in a.detail


def test_g01_fixture_is_bundled():
    a = R.availability("ptp_g01_fixture")
    assert a.status == R.LOCAL_COPY_FOUND


# ----------------------------------------------------------------------------------------- inspect
@pytest.mark.parametrize("name", ["gazette/default_test.jsonl", "dapfam/qrels_all.jsonl"])
def test_inspection_refuses_test_and_qrels_fixture_paths(name):
    with pytest.raises(ProtectedPathError):
        inspect_schema(FIX / name)


@pytest.mark.parametrize("rel", ["split/test-00000.jsonl", "sealed/x.jsonl", "private/a.csv", "qrels/run.json", "TEST_cases.csv"])
def test_inspection_refuses_protected_paths_without_opening(tmp_path, rel):
    p = tmp_path / "ds" / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("not json at all", encoding="utf-8")  # would fail to parse if it were opened
    with pytest.raises(ProtectedPathError):
        inspect_schema(p, root=tmp_path / "ds")


def test_inspection_returns_schema_and_no_values():
    rep = inspect_schema(FIX / "gazette/corpus.jsonl")
    assert rep.columns == ("_id", "title", "text", "category") and rep.row_count == 2
    assert rep.types["text"] == "string"
    dumped = json.dumps(rep.to_dict(), ensure_ascii=False) + repr(rep)
    for value in all_strings(rows("gazette/corpus.jsonl")):
        if value and value not in rep.columns and value != "string":
            assert value not in dumped
    assert "FICT-NOTICE-001" not in dumped and "ประกาศ" not in dumped


def test_inspection_csv_types_and_evaluator_reduction(tmp_path):
    d = tmp_path / "ds"
    d.mkdir()
    (d / "rows.csv").write_text("id,score,name\nSECRETVAL1,3,alpha\nSECRETVAL2,4.5,\n", encoding="utf-8")
    rep = inspect_schema(d / "rows.csv")
    assert rep.columns == ("id", "score", "name") and rep.row_count == 2
    assert rep.types == {"id": "string", "score": "float|int", "name": "empty|string"}
    assert "SECRETVAL" not in repr(rep)
    gold = inspect_schema(FIX / "nitibench_plus/gold_sections.jsonl")
    assert gold.reduced and gold.types == {} and gold.row_count is None and "version_uri" in gold.columns
    ev = inspect_schema(FIX / "gazette/queries.jsonl", role="evaluator")
    assert ev.reduced and ev.columns[0] == "_id"


def test_runtime_loader_refuses_evaluator_and_test_paths():
    with pytest.raises(ProtectedPathError):
        list(iter_jsonl(FIX / "gazette/default_test.jsonl", allow_evaluator=True))
    with pytest.raises(ProtectedPathError):
        list(iter_jsonl(FIX / "nitibench_plus/gold_sections.jsonl"))
    assert len(list(iter_jsonl(FIX / "nitibench_plus/gold_sections.jsonl", allow_evaluator=True))) == 1


# ---------------------------------------------------------------------------------------- adapters
def test_dapfam_views_and_no_label_leak():
    ad = A.DapfamAdapter(REG)
    c1, c2 = rows("dapfam/corpus.jsonl")
    s = ad.source_from_corpus(c1)
    assert s.source_id == "FICT-FAM-0001" and s.version_id == ad.revision and s.locator.endswith("#view=TAC")
    assert s.text == "\n".join([c1["title_en"], c1["abstract_en"], c1["claims_text"]])
    assert ad.source_from_corpus(c1, view="TA").text == c1["title_en"] + "\n" + c1["abstract_en"]
    assert ad.source_from_corpus(c2).text == c2["title_en"]  # empty/None components skipped, not invented
    poisoned = dict(c1, relevance_score=1.0, domain_rel="IN")
    rec = ad.source_from_corpus(poisoned, include=("ipcr_codes_str",))
    assert "domain_rel" not in repr(rec) and dict(rec.attributes) == {"ipcr_codes_str": c1["ipcr_codes_str"]}
    with pytest.raises(A.EvaluatorFieldRequested):
        ad._project(rows("dapfam/qrels_all.jsonl")[0], "relations")
    q = ad.request_from_query(rows("dapfam/queries.jsonl")[0])
    assert q.request_id == "FICT-Q-0001" and q.as_of is None
    with pytest.raises(A.MissingIdentifier):
        ad.source_from_corpus(dict(c1, relevant_id=None))


def test_gazette_evaluator_fields_cannot_reach_runtime():
    ad = A.GazetteAdapter(REG)
    q = rows("gazette/queries.jsonl")[0]
    leaky = dict(q, evidence_text="LEAK-EVIDENCE", **{"corpus-id": "LEAK-DOC"})
    rec = ad.request_from_query(leaky)
    assert rec.text == q["text"] and rec.attributes == ()
    strings = all_strings(rec)
    assert not any(s in strings for s in ("single_source", "LEAK-EVIDENCE", "LEAK-DOC", q["author_model"]))
    for field in ("question_type", "author_model", "evidence_text"):
        with pytest.raises(A.EvaluatorFieldRequested):
            ad.request_from_query(q, include=(field,))
    with pytest.raises(A.EvaluatorFieldRequested):
        ad.request_from_query(q, release_withheld=("judge_model",))
    released = ad.request_from_query(q, include=("question_type",), release_withheld=("question_type",))
    assert dict(released.attributes) == {"question_type": "single_source"}


def test_gazette_thai_text_byte_exact_and_code_point_offsets():
    ad = A.GazetteAdapter(REG)
    raw_lines = (FIX / "gazette/corpus.jsonl").read_bytes().decode("utf-8").splitlines()
    corpus = {r["_id"]: r for r in rows("gazette/corpus.jsonl")}
    for line in raw_lines:
        native = json.loads(line)
        rec = ad.source_from_corpus(native)
        assert rec.text == native["text"] and rec.text.encode("utf-8") == native["text"].encode("utf-8")
        assert rec.title == "" and rec.language == "th"
    t1 = corpus["FICT-NOTICE-001"]["text"]
    assert "ุ่" in t1 and unicodedata.normalize("NFC", t1) != t1  # non-canonical mark order kept
    assert "ำ" in t1 and unicodedata.normalize("NFKC", t1) != t1
    assert t1.endswith("\n") and "  " in t1
    for ev in E.gazette_evidence(rows("gazette/default_test.jsonl")):
        text = corpus[ev.corpus_id]["text"]
        assert E.check_gazette_span(ev, text)
        span = A.Span(ev.corpus_id, ev.start, ev.end)
        assert span.slice(text) == ev.evidence_text
        b0, b1 = span.utf8_byte_range(text)
        assert text.encode("utf-8")[b0:b1].decode("utf-8") == ev.evidence_text
        assert (b0, b1) != (ev.start, ev.end)  # Thai: bytes and code points differ
    assert E.gazette_document_qrels(E.gazette_evidence(rows("gazette/default_test.jsonl"))) == {
        "FICT-GQ-001": {"FICT-NOTICE-001"}, "FICT-GQ-002": {"FICT-NOTICE-001", "FICT-NOTICE-002"}}


def test_nitibench_requests_exclude_labels_and_preserve_thai():
    ad = A.NitiBenchPlusAdapter(REG)
    case = rows("nitibench_plus/validation_split.jsonl")[0]
    reqs = ad.requests_from_case(case)
    assert [r.request_id for r in reqs] == ["FICT-CASE-001/sub_questions[0]", "FICT-CASE-001/sub_questions[1]"]
    assert all(dict(r.attributes)["request_id_kind"] == "positional_locator" for r in reqs)
    assert reqs[0].as_of == "2599-01-15" and reqs[0].context == case["fact_pattern"]
    assert reqs[0].text == case["sub_questions"][0]["question"]
    strings = set(all_strings(reqs))
    forbidden = {"SYNTHETIC-VERDICT-A", "SYNTHETIC-VERDICT-B", "fict://law/1/s1/v2", "fict://law/1/s1", "amended",
                 "FICT-DEC-999/2599", "PTP-SYNTHETIC-CANARY-NOT-NATIVE", "ruling", "เหตุผลสมมติ"}
    assert not strings & forbidden
    for field in ("verdict", "citations", "drift_band", "source_id", "canary", "question_type"):
        with pytest.raises(A.EvaluatorFieldRequested):
            ad.requests_from_case(case, include=(field,))
    with pytest.raises(A.MissingIdentifier):
        ad.requests_from_case(dict(case, id=None))


def test_nitibench_gold_sections_only_under_named_oracle_setting():
    ad = A.NitiBenchPlusAdapter(REG)
    g = rows("nitibench_plus/gold_sections.jsonl")[0]
    with pytest.raises(A.EvaluatorFieldRequested):
        ad.source_from_gold_section(g, setting="parametric_public_validation")
    s = ad.source_from_gold_section(g, setting="gold_cited_in_force_public_validation", observed_at="2026-11-22T00:00:00Z")
    assert s.version_id == "fict://law/1/s1/v2" and s.source_id == "fict://law/1/s1"
    assert s.valid_from == "2595-01-01" and s.valid_to is None and s.observed_at == "2026-11-22T00:00:00Z"
    assert s.text == g["text"] and "PTP-SYNTHETIC-CANARY-NOT-NATIVE" not in all_strings(s)
    no_current = {k: v for k, v in g.items() if k != "current_uri"}
    assert ad.source_from_gold_section(no_current, setting="gold_cited_in_force_public_validation").source_id is None


def test_nitibench_missing_citation_ids_stay_missing():
    case = rows("nitibench_plus/validation_split.jsonl")[0]
    labels = E.nitibench_labels(case, REG)
    cites = [c for lab in labels for c in lab.citations]
    assert len(cites) == 3  # nothing dropped
    resolved = [c for c in cites if c.resolved]
    unresolved = [c for c in cites if not c.resolved]
    assert len(resolved) == 1 and len(unresolved) == 2
    for c in unresolved:
        assert c.version_uri is None and c.current_uri is None and c.valid_from is None and c.law
    assert labels[0].verdict == "SYNTHETIC-VERDICT-A" and labels[0].question_type == "ruling"


def test_dapfam_evaluator_relations_positive_only():
    rel = E.dapfam_relations(rows("dapfam/qrels_all.jsonl"))
    assert [(r.relevant_id, r.domain_rel) for r in rel] == [("FICT-FAM-0001", "IN")]


def test_runtime_adapters_do_not_import_evaluator():
    src = (REPO / "src/patent_to_pilot/workbench/datasets/adapters.py").read_text(encoding="utf-8")
    assert "evaluator import" not in src and "import evaluator" not in src and "from .evaluator" not in src
