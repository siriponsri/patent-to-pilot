"""P0-T06: source-bound SYNTHETIC search-and-trace slice. Every packet used here is authored and fictional; these tests
check engineering behaviour (exact spans, binding, type separation, real pool membership, revision re-check scope and
schema validity), never retrieval quality."""
from __future__ import annotations

import base64
import copy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sqlite3
import threading
import urllib.request

import pytest

from patent_to_pilot.workbench import trace_slice as T
from patent_to_pilot.workbench.core import Conflict, EvidenceCore, ValidationFailed
from patent_to_pilot.workbench.server import create_server
from patent_to_pilot.workbench.store import SCHEMA, SCHEMA_G02, SCHEMA_VERSION

REPO = Path(__file__).resolve().parents[1]
OWNER_SPEC = REPO / "docs/owner/owner-note-22112026/spec"
HAS_PYPDF = importlib.util.find_spec("pypdf") is not None
LETTER = "syn-letter@v1"


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


@pytest.fixture
def ran(tmp_path):
    """A slice after the first bounded run (seed + one expansion), before any revision."""
    sl = T.TraceSlice(EvidenceCore(tmp_path / "store"))
    sl.setup()
    res = sl.run()
    return sl, res


@pytest.fixture
def revised(ran):
    sl, res = ran
    impact = sl.apply_revision()
    return sl, res, impact


@pytest.fixture(scope="module")
def bundle(tmp_path_factory):
    return T.run_synthetic_slice(tmp_path_factory.mktemp("bundle") / "store")


# --------------------------------------------------------------------------- fixture, labels, artifacts
def test_fixture_is_labelled_synthetic_and_regenerates_byte_identically():
    fx = T.load_packet()
    assert fx["packet"]["synthetic"] is True and fx["packet"]["data_origin"] == "synthetic_demo"
    assert fx["manifest"]["synthetic"] is True and "SYNTHETIC" in fx["manifest"]["label"]
    for doc in fx["packet"]["documents"] + [fx["packet"]["revision"]]:
        art = T.author_artifacts(doc)
        for suffix, key in ((".pdf", "pdf"), (".canonical.txt", "canonical"), (".layout.json", "layout")):
            assert (T.FIXTURE_DIR / (doc["file_stem"] + suffix)).read_bytes() == art[key], (doc["file_stem"], suffix)
        loaded = fx["artifacts"][(doc["source_id"], doc["version_id"])]
        assert loaded["text"].startswith("SYNTHETIC FIXTURE - NOT A REAL DOCUMENT")
        assert b"SYNTHETIC FIXTURE" in loaded["pdf"] and loaded["layout"]["synthetic"] is True


def test_tampered_fixture_is_refused(tmp_path):
    import shutil
    dst = tmp_path / "fx"
    shutil.copytree(T.FIXTURE_DIR, dst)
    p = dst / "annex_b_v1.canonical.txt"
    p.write_bytes(p.read_bytes().replace(b"60 C", b"70 C"))
    with pytest.raises(ValidationFailed) as e:
        T.load_packet(dst)
    assert e.value.code == "fixture_hash"


def test_original_bytes_canonical_text_and_regions_are_distinct_and_survive_restart(ran, tmp_path):
    sl, _ = ran
    fx = T.load_packet()
    core2 = EvidenceCore(tmp_path / "store")   # reopen: everything must resolve from the store alone
    with core2.store.read() as con:
        for (sid, vid), art in fx["artifacts"].items():
            if vid == "v2":
                continue
            o = con.execute("SELECT * FROM original_artifacts WHERE project_id=? AND source_id=? AND version_id=?",
                            (T.PROJECT_ID, sid, vid)).fetchone()
            v = con.execute("SELECT raw, text, sha256 FROM source_versions WHERE project_id=? AND source_id=? AND "
                            "version_id=?", (T.PROJECT_ID, sid, vid)).fetchone()
            assert o["media_type"] == "application/pdf" and o["raw"] == art["pdf"] and o["sha256"] == sha(art["pdf"])
            assert v["raw"] == art["canonical_bytes"] and v["sha256"] == sha(v["raw"]) and v["text"] == art["text"]
            assert o["sha256"] != v["sha256"]                     # two artifacts, two identities
            pages = con.execute("SELECT * FROM source_pages WHERE project_id=? AND source_id=? AND version_id=?",
                                (T.PROJECT_ID, sid, vid)).fetchall()
            assert [(p["page"], p["display_width_pt"], p["rotation_degrees"]) for p in pages] == [(1, 612.0, 0)]
    nodes = T.TraceSlice(core2, project_id=T.PROJECT_ID).nodes()
    assert {n["node_id"] for n in nodes.values()} >= {f"{LETTER}#clause-4", f"{LETTER}#footnote-1"}
    for n in nodes.values():
        (r,) = n["regions"]
        x0, y0, x1, y1 = r["bbox"]
        assert r["page"] == 1 and 0 <= x0 < x1 <= 1 and 0 <= y0 < y1 <= 1
    assert core2.source_version(T.PROJECT_ID, "syn-letter", "v1")["original_artifact"]["sha256"] == \
        sha(fx["artifacts"][("syn-letter", "v1")]["pdf"])


@pytest.mark.skipif(not HAS_PYPDF, reason="pypdf (optional 'pdf' extra) not installed")
def test_canonical_text_is_the_text_layer_of_the_original_pdf():
    import pypdf
    for art in T.load_packet()["artifacts"].values():
        page = pypdf.PdfReader(io.BytesIO(art["pdf"])).pages[0].extract_text()
        assert page + "\n" == art["text"]
        for nd in art["layout"]["nodes"]:
            assert art["text"][nd["start"]:nd["end"]] in page


# --------------------------------------------------------------------------- spans and search membership
def test_every_cited_span_resolves_exactly_to_stored_text_and_original_bytes(bundle, ran):
    sl, _ = ran
    for event in bundle["events"]:
        texts = {s["version_id"]: s["canonical_text"]["text"] for s in event["sources"]}
        for s in event["sources"]:
            raw = base64.b64decode(s["original_artifact"]["content_base64"])
            assert sha(raw) == s["original_artifact"]["sha256"] and raw.startswith(b"%PDF-")
            assert sha(s["canonical_text"]["text"].encode("utf-8")) == s["canonical_text"]["sha256"]
        nodes = {n["node_id"]: n for n in event["nodes"]}
        for e in event["evidence"]:
            t = texts[nodes[e["node_id"]]["source_version_id"]]
            assert t[e["span"]["start"]:e["span"]["end"]] == e["quote"]
    # and against the store, independently of the trace JSON
    for e in sl.resolve_evidence([r for r in sl.state["assessment"]["evidence_ids"]]):
        sid, rest = e.node_id.split("@")
        vid = rest.split("#")[0]
        assert sl.core.source_version(T.PROJECT_ID, sid, vid)["text"][e.start:e.end] == e.quote
    q = bundle["requirement"]
    assert q["query_text"][q["start_char"]:q["end_char"]] == q["text"]


def _independent_fts(store_path: Path, match: str) -> list[str]:
    con = sqlite3.connect(store_path)
    try:
        rows = con.execute("SELECT source_id, version_id, passage_id FROM passage_fts WHERE passage_fts MATCH ? AND "
                           "project_id=? ORDER BY bm25(passage_fts), source_id, version_id, passage_id LIMIT ?",
                           (match, T.PROJECT_ID, T.RESULT_LIMIT)).fetchall()
    finally:
        con.close()
    return [T.node_id(*r) for r in rows]


def test_candidate_pools_are_real_fts5_membership_before_and_after_the_action(ran):
    sl, res = ran
    seed, exp = res["seed_event"], res["expansion_event"]
    for ev in (seed, exp):
        assert ev["candidate_delta"]["returned_ids"] == _independent_fts(sl.store.path, ev["action"]["query_text"])
    sd, xd = seed["candidate_delta"], exp["candidate_delta"]
    assert sd["before_ids"] == [] and set(sd["returned_ids"]) == {f"{LETTER}#clause-4", f"{LETTER}#clause-5"}
    rule = "syn-annex-b@v1#annex-b-1"
    assert rule not in sd["after_ids"]                     # the baseline really misses the governing annex rule
    assert xd["before_ids"] == sd["after_ids"]
    assert xd["after_ids"] == xd["before_ids"] + [x for x in xd["returned_ids"] if x not in xd["before_ids"]]
    assert xd["new_ids"] == [x for x in xd["returned_ids"] if x not in xd["before_ids"]]
    assert {rule, "syn-annex-b@v1#annex-heading", "syn-annex-a@v1#annex-a-1"} == set(xd["new_ids"])
    # a new pool member is not evidence: the Annex A decoy entered the pool but is bound to nothing
    cited = {e.node_id for e in sl.resolve_evidence(res["assessment"]["evidence_ids"])}
    assert "syn-annex-a@v1#annex-a-1" not in cited and rule in cited
    # the run and its two actions are in the existing runs/actions tables
    run = sl.core.run_view(seed["run_id"])
    assert run["kind"] == "trace_slice" and run["status"] == "completed"
    assert [a["detail"]["trace_id"] for a in run["actions"]] == [seed["trace_id"], exp["trace_id"]]


def test_seed_assessment_is_unresolved_and_names_the_missing_annex(ran):
    _, res = ran
    assert res["assessment_before"]["status"] == "unresolved"
    (ref,) = res["unresolved_before"]
    assert ref["kind"] == "annex" and ref["label"] == "B" and ref["from_node_id"] == f"{LETTER}#clause-5"
    assert res["expansion_event"]["action"]["selected_assessment_id"] == res["assessment_before"]["assessment_id"]
    assert res["assessment"]["status"] == "supported"


# --------------------------------------------------------------------------- annex binding
def test_annex_binding_resolves_to_the_referenced_annex_and_its_scope(ran):
    sl, res = ran
    nodes = sl.nodes()
    inc = [r for r in res["relations"] if r["kind"] == "incorporates"]
    assert len(inc) == 1
    r = inc[0]
    assert r["from_node_id"] == f"{LETTER}#clause-5" and r["to_node_id"] == "syn-annex-b@v1#annex-heading"
    assert nodes[r["to_node_id"]]["quote"].startswith("Annex B.")
    assert r["scope_node_ids"] == ["syn-annex-b@v1#annex-b-1"]
    assert "60 C" in nodes["syn-annex-b@v1#annex-b-1"]["quote"]
    ref_ev, head_ev = sl.resolve_evidence(r["provenance"]["evidence_ids"])
    assert ref_ev.quote == "Annex B" and ref_ev.node_id == f"{LETTER}#clause-5"
    q = [x for x in res["relations"] if x["kind"] == "qualifies"]
    assert [(x["from_node_id"], x["scope_node_ids"]) for x in q] == [(f"{LETTER}#footnote-1", [f"{LETTER}#clause-4"])]


def test_an_ambiguous_annex_label_is_not_bound(tmp_path):
    sl = T.TraceSlice(EvidenceCore(tmp_path / "store"))
    sl.setup()
    dup = copy.deepcopy(sl.packet["documents"][2])
    dup.update(source_id="syn-annex-b-copy", file_stem="annex_b_copy", title="SYNTHETIC duplicate Annex B")
    sl.import_version(T.artifact_from_spec(dup), supersedes=None, event_id="SYN-IMPORT-dup")
    res = sl.run()
    assert res["assessment"]["status"] == "unresolved"
    assert not [r for r in res["relations"] if r["kind"] == "incorporates"]
    assert "ambiguous" in res["unresolved_after"][0]["reason"]


# --------------------------------------------------------------------------- hypothesis is never evidence
def test_generated_hypothesis_can_never_be_cited(ran):
    sl, res = ran
    (hyp,) = res["expansion_event"]["hypotheses"]
    assert hyp["kind"] == "generated_search_hypothesis" and hyp["text"] == "coastal"
    assert hyp["hypothesis_id"] in res["expansion_event"]["action"]["query_artifact_ids"]
    h = sl.hypotheses[hyp["hypothesis_id"]]
    with pytest.raises(T.HypothesisNotEvidence):
        T.require_source_evidence(h)
    with pytest.raises(T.HypothesisNotEvidence):
        sl.record_assessment("supported", [hyp["hypothesis_id"]], {"after_action": "test"})
    with pytest.raises(T.HypothesisNotEvidence):
        sl.record_relation("qualifies", f"{LETTER}#clause-4", f"{LETTER}#clause-5", [f"{LETTER}#clause-5"],
                           "explicit_source", [hyp["hypothesis_id"]])
    with sl.store.connect() as con, pytest.raises(sqlite3.IntegrityError):
        con.execute("INSERT INTO source_evidence VALUES (?,?,?,?,?,?,?)",
                    (T.PROJECT_ID, hyp["hypothesis_id"], f"{LETTER}#clause-5", 0, 1, "x", "now"))
    # nothing a hypothesis touched became evidence
    ev_ids = {e["evidence_id"] for e in res["expansion_event"]["evidence"]}
    assert hyp["hypothesis_id"] not in ev_ids
    for a in res["expansion_event"]["runtime_assessments"]:
        assert hyp["hypothesis_id"] not in a["evidence_ids"]


def test_trace_checks_reject_a_hypothesis_used_as_evidence(ran):
    _, res = ran
    ev = copy.deepcopy(res["expansion_event"])
    hid = ev["hypotheses"][0]["hypothesis_id"]
    ev["runtime_assessments"][-1]["evidence_ids"].append(hid)
    assert any("generated hypothesis" in m for m in T.semantic_errors(ev))
    ev2 = copy.deepcopy(res["expansion_event"])
    ev2["evidence"].append({**ev2["hypotheses"][0]})   # a hypothesis object smuggled into the evidence list
    assert T.schema_errors(ev2)


# --------------------------------------------------------------------------- schema
def test_bundled_schema_is_the_owner_specification():
    raw = T.SCHEMA_PATH.read_bytes()
    assert sha(raw) == T.SCHEMA_SHA256
    if (OWNER_SPEC / "evidence_trace.schema.json").exists():
        assert (OWNER_SPEC / "evidence_trace.schema.json").read_bytes() == raw


def test_every_emitted_event_validates_against_the_schema_and_semantic_checks(bundle):
    assert bundle["synthetic"] is True and bundle["label"] == T.SYNTHETIC_LABEL
    assert [e["action"]["kind"] for e in bundle["events"]] == ["seed_search", "structural_expansion",
                                                              "replay_search", "replay_search"]
    for e, c in zip(bundle["events"], bundle["event_checks"]):
        assert e["mode"] == "synthetic_demo" and e["cost"]["state"] == "not_applicable"
        assert T.schema_errors(e) == [] and T.semantic_errors(e) == [] and c["schema_errors"] == []
        assert all(a["basis"] == "runtime_not_gold" for a in e["runtime_assessments"])


def test_checks_catch_tampering(bundle):
    base = bundle["events"][1]
    cases = []
    e = copy.deepcopy(base); e["evidence"][0]["quote"] += "!"; cases.append(e)                       # noqa: E702
    e = copy.deepcopy(base); e["candidate_delta"]["after_ids"].pop(); cases.append(e)                 # noqa: E702
    e = copy.deepcopy(base); e["candidate_delta"]["new_ids"] = e["candidate_delta"]["returned_ids"]; cases.append(e)  # noqa: E702,E501
    e = copy.deepcopy(base); s = e["sources"][0]["original_artifact"]                                   # noqa: E702
    s["content_base64"] = base64.b64encode(b"%PDF-1.4 other").decode(); cases.append(e)               # noqa: E702
    e = copy.deepcopy(base); e["index"]["corpus_revision"] = "other"; cases.append(e)                  # noqa: E702
    e = copy.deepcopy(base); e["relations"][0]["scope_node_ids"] = ["no-such-node"]; cases.append(e)  # noqa: E702
    for c in cases:
        assert T.semantic_errors(c), c["trace_id"]
    e = copy.deepcopy(base); del e["candidate_delta"]                                                  # noqa: E702
    assert T.schema_errors(e)
    e = copy.deepcopy(base); e["cost"]["state"] = "invoiced"                                           # noqa: E702
    assert T.schema_errors(e)


@pytest.mark.skipif(not (OWNER_SPEC / "evidence_trace.synthetic.json").exists(), reason="owner package not present")
def test_validator_accepts_the_owner_synthetic_example():
    ex = json.loads((OWNER_SPEC / "evidence_trace.synthetic.json").read_text(encoding="utf-8"))
    assert T.schema_errors(ex) == [] and T.semantic_errors(ex) == []


# --------------------------------------------------------------------------- controlled revision
def test_annex_revision_rechecks_exactly_the_dependent_evidence(revised):
    sl, before, impact = revised
    p, o = impact["prediction"], impact["observed"]
    assert p["node_changes"]["changed"] == ["syn-annex-b@v1#annex-b-1"]
    assert set(p["node_changes"]["unchanged_aligned"]) == {"syn-annex-b@v1#annex-heading", "syn-annex-b@v1#label"}
    assert p["recheck"]["evidence"] == {
        "ev:syn-annex-b@v1#annex-b-1": "recheck:cited_node_changed",
        "ev:syn-annex-b@v1#annex-heading": "reanchor:version_superseded_text_identical",
        f"ev:{LETTER}#clause-5": "recheck:governed_scope_changed",
        f"ev:{LETTER}#clause-5[274:281]": "recheck:governed_scope_changed"}
    assert p["retained_without_recheck"]["evidence"] == [f"ev:{LETTER}#clause-4", f"ev:{LETTER}#clause-4[201:204]",
                                                          f"ev:{LETTER}#footnote-1"]
    assert p["retained_without_recheck"]["relations"] == [f"rel:qualifies:{LETTER}#footnote-1->{LETTER}#clause-4"]
    assert set(p["recheck"]["searches"]) == {before["seed_event"]["trace_id"], before["expansion_event"]["trace_id"]}
    assert impact["prediction_covers_every_observed_change"] is True
    assert set(o["evidence_replaced"]) == {"ev:syn-annex-b@v1#annex-b-1", "ev:syn-annex-b@v1#annex-heading"}
    assert o["pool_equivalent_under_alignment"] is True and o["assessment_after"]["status"] == "supported"
    assert o["quotes_changed"]["ev:syn-annex-b@v1#annex-b-1"]["after"].endswith("up to 55 C.")
    # immutable history: v1 still resolves, but the current index no longer finds its superseded text
    assert "60 C" in sl.core.source_version(T.PROJECT_ID, "syn-annex-b", "v1")["text"]
    assert _independent_fts(sl.store.path, '"60"') == []
    assert _independent_fts(sl.store.path, '"55"') == ["syn-annex-b@v2#annex-b-1"]
    nodes = sl.nodes()
    v2 = nodes["syn-annex-b@v2#annex-b-1"]
    assert v2["alignment"] == {"prior_node_id": "syn-annex-b@v1#annex-b-1", "method": T.ALIGN_METHOD, "confidence": 1.0}
    changes = {c["event_id"]: c for c in sl.core.available_changes(T.PROJECT_ID)}
    assert changes["SYN-REV-ANNEX-B-V2"]["status"] == "applied"


def test_footnote_revision_reopens_the_qualified_clause_even_though_its_text_is_unchanged(ran):
    sl, _ = ran
    rev = T.author_revision(sl.packet["documents"][0], "syn-letter", "v2", "v1", "SYN-REV-FOOTNOTE",
                            {"footnote-1": "[1] The Clause 4 limit is measured at the exhaust of the unit."},
                            "synthetic footnote-only revision")
    impact = sl.apply_revision(rev)
    p = impact["prediction"]
    assert p["node_changes"]["changed"] == [f"{LETTER}#footnote-1"]
    ev = p["recheck"]["evidence"]
    assert ev[f"ev:{LETTER}#footnote-1"] == "recheck:cited_node_changed"
    assert ev[f"ev:{LETTER}#clause-4"] == "recheck:qualifier_changed"
    assert ev[f"ev:{LETTER}#clause-5"] == "reanchor:version_superseded_text_identical"
    assert p["recheck"]["relations"][f"rel:qualifies:{LETTER}#footnote-1->{LETTER}#clause-4"].startswith("rebind")
    assert "ev:syn-annex-b@v1#annex-b-1" in p["retained_without_recheck"]["evidence"]
    assert impact["prediction_covers_every_observed_change"] is True
    assert "ev:syn-annex-b@v1#annex-b-1" in impact["observed"]["evidence_retained"]


def test_selective_recheck_equals_a_full_rerun_on_the_revised_corpus(revised, tmp_path):
    sl, _, _ = revised
    full = T.TraceSlice(EvidenceCore(tmp_path / "full"))
    full.setup(versions=[("syn-letter", "v1"), ("syn-annex-a", "v1"), ("syn-annex-b", "v2")])
    ref = full.run()
    got = sl.state
    assert got["pool"] == ref["pool"]
    assert got["assessment"]["status"] == ref["assessment"]["status"]
    assert set(got["assessment"]["evidence_ids"]) == set(ref["assessment"]["evidence_ids"])
    assert {r["relation_id"] for r in got["relations"]} == {r["relation_id"] for r in ref["relations"]}


# --------------------------------------------------------------------------- product surface and store migration
def test_read_only_api_serves_the_synthetic_trace_without_touching_the_store(tmp_path):
    core = EvidenceCore(tmp_path / "owner-store")
    srv = create_server(core, port=0)
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    try:
        port = srv.server_address[1]
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/synthetic/trace-slice", timeout=60) as r:
            body = json.loads(r.read().decode("utf-8"))
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=10) as r:
            assert b"/api/synthetic/trace-slice" in r.read()
    finally:
        srv.shutdown()
        srv.server_close()
    assert body["synthetic"] is True and len(body["events"]) == 4
    assert all(not c["schema_errors"] and not c["semantic_errors"] for c in body["event_checks"])
    assert core.list_projects() == []


def test_owner_ingestion_now_keeps_the_original_bytes(tmp_path):
    core = EvidenceCore(tmp_path / "store")
    pid = core.create_project("original bytes")["project_id"]
    raw = b"Powered circulation: no.\n"
    out = core.ingest_document(pid, "notes.txt", raw, "CONCEPT-A")
    oa = core.source_version(pid, out["source_id"], out["version_id"])["original_artifact"]
    assert oa["sha256"] == sha(raw) and oa["media_type"] == "text/plain"
    if HAS_PYPDF:
        pdf = T.load_packet()["artifacts"][("syn-letter", "v1")]["pdf"]
        out = core.ingest_document(pid, "letter.pdf", pdf, "CONCEPT-A")
        sv = core.source_version(pid, out["source_id"], out["version_id"])
        assert sv["original_artifact"]["sha256"] == sha(pdf) and sv["original_artifact"]["media_type"] == "application/pdf"
        assert sv["sha256"] != sha(pdf)


def test_the_synthetic_project_refuses_owner_uploads(ran):
    sl, _ = ran
    with pytest.raises(Conflict) as e:
        sl.core.ingest_document(T.PROJECT_ID, "x.txt", b"text\n", T.CANDIDATE_ID)
    assert e.value.code == "sample_is_fixed"
    assert sl.core.project_view(T.PROJECT_ID)["data_origin"] == "synthetic_demo"


def test_existing_g02_store_gains_the_new_tables_additively(tmp_path):
    d = tmp_path / "old"
    d.mkdir()
    con = sqlite3.connect(d / "workbench.sqlite3")
    con.executescript(SCHEMA)
    con.executescript(SCHEMA_G02)
    con.execute("INSERT INTO meta VALUES ('schema_version', ?)", (SCHEMA_VERSION,))
    con.execute("INSERT INTO projects VALUES ('p-old','PTP','G02','S','Old','owner_files','{}','{}','2026-11-01')")
    con.commit()
    con.close()
    core = EvidenceCore(d)
    assert [p["project_id"] for p in core.list_projects()] == ["p-old"]
    with core.store.read() as c:
        names = {r[0] for r in c.execute("SELECT name FROM sqlite_master")}
    assert {"original_artifacts", "source_pages", "doc_nodes", "doc_relations", "source_evidence",
            "search_hypotheses", "bound_requirements", "runtime_assessments", "trace_events"} <= names
