"""Offline product scenarios for the P0 evidence foundation (owner plan section 10).

All data is fictional and authored (tests/fixtures/healthtech_scenarios/scenarios.json).
Every oracle is deterministic: identifiers, field values, offsets, sets and counts.
No LLM, network, provider, or evaluator gold is used.

Tests named ``*_current`` check behaviour the existing engine/contracts already had.
The others need the P0 foundation module; before it existed they failed with an
import error, which is the recorded "before" state in the gap audit.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import date, datetime, timezone
import importlib
import json
from pathlib import Path
import socket

import pytest
from pydantic import ValidationError

from patent_to_pilot.healthtech.contracts import (DossierVersion, EvidenceItem, PatentCandidate,
    canonical_patent_id, content_hash)
from patent_to_pilot.healthtech.engine import DossierInput, export_markdown, run_dossier, serialize_dossier
from patent_to_pilot.healthtech.history import load_versions, save_version
from patent_to_pilot.healthtech.provenance import check_evidence
from patent_to_pilot.healthtech.sources import field_evidence, source_payload

FIXTURE = json.loads((Path(__file__).parent / "fixtures/healthtech_scenarios/scenarios.json")
                     .read_text(encoding="utf-8"))
OBSERVED = datetime(2026, 11, 1, 9, 0, tzinfo=timezone.utc)


def foundation():
    """Import lazily so a missing module fails each scenario, not the whole file."""
    return importlib.import_module("patent_to_pilot.healthtech.foundation")


# ---------------------------------------------------------------- builders

def _source(spec: dict):
    return source_payload(
        spec["id"], spec["payload"], uri=spec.get("uri", f"urn:synthetic:{spec['id']}"),
        revision=spec.get("revision", "authored-fixture-v1"), source_date=date.fromisoformat(spec["date"]),
        jurisdiction=spec.get("jurisdiction", "US"), source_type=spec["type"],
        license_note="Project-authored synthetic fixture; not a real record", synthetic=True)


def _evidence(spec: dict, sources: dict) -> EvidenceItem:
    source = sources[spec["source"]]
    if spec["kind"] == "field":
        return field_evidence(source, spec["field"], spec["id"])
    start = source.payload.index(spec["quote"])
    return EvidenceItem(evidence_id=spec["id"], source_id=source.source.source_id,
        source_version=source.source.version_label, payload_hash=source.source.sha256,
        locator=f"chars:{start}:{start + len(spec['quote'])}", quoted_span=spec["quote"],
        evidence_kind=spec["evidence_kind"], statement=spec["statement"],
        support_basis="Exact authored text only; no semantic interpretation",
        jurisdiction=source.jurisdiction, source_date=source.source_date, extraction_method="literal_span")


def _patent(spec: dict) -> dict:
    canonical = canonical_patent_id(spec["patent_id"])
    payload = _source({"id": f"patent-{canonical}", "type": "patent_document", "date": "2026-10-01",
                       "payload": spec["text"]})
    return {"patent_id": spec["patent_id"], "title": spec["title"], "source": payload.model_dump(mode="json")}


def project_input(name: str, *, policy: str = "HT-B2", extra_sources=(), extra_patents=(),
                  **query_updates) -> dict:
    p = FIXTURE["projects"][name]
    sources = [_source(s) for s in p["sources"]]
    by_id = {s.source.source_id: s for s in sources}
    permitted = [s.source.source_id for s in sources]
    query = {
        "query_id": p["query_id"],
        "brief": {"project_id": p["project_id"], "version": 1, "objective": "Authored offline scenario",
                  "audience": "researcher", "data_class": "synthetic", "language": "en",
                  "theme": "formal-light"},
        "device_id_raw": p["device_id_raw"], "device_id_canonical": p["device_id_canonical"],
        "selected_comparator_source_id": p["comparator"],
        "technical_description": p["technical_description"],
        "features_of_interest": list(p["features_of_interest"]),
        "user_questions": [], "company_metadata": dict(p["company_metadata"]),
        "company_source_id": p["comparator"] if p["company_metadata"] else None,
        "jurisdiction": "US", "evidence_cutoff": p["cutoff"], "permitted_inputs": permitted,
        "acquisition_budget": {"max_search_calls": 5, "max_returned_candidates": 40,
                               "accounting": "offline_counts"},
    } | query_updates
    return {
        "query": query,
        "sources": [s.model_dump(mode="json") for s in sources]
                   + [_source(s).model_dump(mode="json") for s in extra_sources],
        "patents": [_patent(x) for x in p["patents"]] + [_patent(x) for x in extra_patents],
        "evidence": [_evidence(e, by_id).model_dump(mode="json") for e in p["evidence"]],
        "policy_id": policy,
    }


def run(name: str, run_id: str = "scn", **kwargs):
    return run_dossier(DossierInput.model_validate(project_input(name, **kwargs)),
                       run_id=run_id, code_commit="scenario-fixture")


def with_disclosed_alpha(dossier: DossierVersion) -> DossierVersion:
    """Promote US0000101B2 using the authored marking span (a source-backed disclosure)."""
    data = dossier.model_dump(mode="json")
    for c in data["candidates"]:
        if c["patent_id_canonical"] == "US0000101B2":
            c["association_status"] = "disclosed_link"
            c["disclosure_evidence_id"] = "alpha-ev-marking"
    return DossierVersion.model_validate(data)


def ids(items, attr):
    return [getattr(x, attr) for x in items]


# ---------------------------------------------- P0 acceptance: three sample projects

@pytest.mark.parametrize("name", ["alpha", "beta", "gamma"])
def test_three_authored_projects_export_json_and_md_current(name, monkeypatch):
    def denied(*a, **kw):
        pytest.fail("offline scenario tried network access")
    monkeypatch.setattr(socket, "create_connection", denied)
    monkeypatch.setattr(socket.socket, "connect", denied)
    dossier, events, manifest = run(name)
    assert all(c.association_status == "retrieved_candidate" for c in dossier.candidates)
    assert all(e.verification_status in {"field_value_checked", "exact_span_checked"} for e in dossier.evidence)
    sources = {s.source.source_id: s for s in dossier.sources}
    assert all(check_evidence(e, sources[e.source_id]) == e for e in dossier.evidence)
    md = export_markdown(dossier)
    assert "SYNTHETIC ENGINEERING EXAMPLE" in md and "| disclosed_link |" not in md
    assert DossierVersion.model_validate(serialize_dossier(dossier)) == dossier
    assert manifest.provider_calls == manifest.paid_cost_usd == 0


# ------------------------------------------------------------ S01 ambiguous names

@pytest.mark.parametrize("case", FIXTURE["intake_cases"], ids=lambda c: c["raw"].strip())
def test_s01_ambiguous_device_names_are_not_resolved_silently(case):
    F = foundation()
    records = [F.DeviceRecordRef(**d) for d in FIXTURE["devices"]]
    result = F.resolve_device_intake(case["raw"], records)
    assert result.status == case["status"]
    assert sorted(r.source_id for r in result.matches) == case["match_ids"]
    if result.status != "resolved":
        assert result.reason


def test_s01_resolution_never_invents_a_manufacturer():
    F = foundation()
    records = [F.DeviceRecordRef(**d) for d in FIXTURE["devices"]]
    result = F.resolve_device_intake("VasoLine", records)
    assert result.status == "resolved" and result.manufacturer is None


# ------------------------------------------------------- S02 manufacturer != assignee

def test_s02_company_search_never_promotes_links_current():
    dossier, events, _ = run("beta", policy="HT-B0a")
    assert events[0].action_type == "company_search"
    assert all(c.association_status == "retrieved_candidate" for c in dossier.candidates)


@pytest.mark.parametrize("case", FIXTURE["parties"], ids=lambda c: c["patent_assignee"])
def test_s02_manufacturer_assignee_mismatch_gives_no_company_link(case):
    F = foundation()
    link = F.company_link(device_id="K000101", manufacturer=case["device_manufacturer"],
                          manufacturer_source_id="alpha-device", patent_id="US0000101B2",
                          assignee=case["patent_assignee"], assignee_source_id="patent-US0000101B2")
    if not case["company_match"]:
        assert link is None
    else:
        assert link.link_type == "company_name_match" and not link.is_verified_association
        assert link.source_ids == ["alpha-device", "patent-US0000101B2"]


def test_s02_link_types_require_their_basis():
    F = foundation()
    base = dict(device_id="K000101", patent_id_canonical="US0000101B2", basis="authored", source_ids=["s"])
    with pytest.raises(ValidationError):
        F.CandidateLink(link_type="source_disclosed", **base)
    with pytest.raises(ValidationError):
        F.CandidateLink(link_type="reviewer_confirmed", **base)
    with pytest.raises(ValidationError):
        F.CandidateLink(link_type="company_name_match", reviewer_decision_id="r1", **base)
    dossier = with_disclosed_alpha(run("alpha")[0])
    links = {link.patent_id_canonical: link for link in F.candidate_links(dossier)}
    assert links["US0000101B2"].link_type == "source_disclosed"
    assert links["US0000101B2"].evidence_ids == ["alpha-ev-marking"]
    assert links["US0000102A1"].link_type == "retrieved_candidate"
    assert [k for k, v in links.items() if v.is_verified_association] == ["US0000101B2"]


# ------------------------------------------------------------ S03 family duplicates

@pytest.mark.parametrize("case", FIXTURE["patent_id_cases"], ids=lambda c: c["raw"])
def test_s03_patent_id_resolution_current(case):
    assert canonical_patent_id(case["raw"]) == case["canonical"]


@pytest.mark.parametrize("raw", FIXTURE["patent_id_rejects"])
def test_s03_unknown_patent_id_syntax_fails_closed_current(raw):
    with pytest.raises(ValueError):
        canonical_patent_id(raw)


def test_s03_formatting_duplicates_are_rejected_current():
    data = project_input("beta")
    data["patents"].append(deepcopy(data["patents"][0]) | {"patent_id": "US 0,000,201 A1"})
    data["patents"][-1]["source"] = _source({"id": "dup", "type": "patent_document", "date": "2026-10-01",
                                             "payload": "duplicate"}).model_dump(mode="json")
    with pytest.raises(ValidationError, match="duplicate canonical patent"):
        DossierInput.model_validate(data)


def test_s03_family_members_collapse_only_with_a_sourced_family_record():
    F = foundation()
    dossier, _, _ = run("beta")
    families = [F.PatentFamily(**f) for f in FIXTURE["families"]]
    groups = F.group_candidates_by_family(dossier.candidates, families)
    family_rows = [g for g in groups if g.family_id == "SYNFAM-0201"]
    assert len(family_rows) == 1
    assert sorted(family_rows[0].member_ids) == ["EP0000201B1", "US0000201A1", "US0000201B2"]
    assert family_rows[0].family_source_id == "beta-family-record"
    singles = [g for g in groups if g.family_id is None]
    assert [g.member_ids for g in singles] == [["US0000202B2"]]
    assert sum(len(g.member_ids) for g in groups) == len(dossier.candidates)
    # Without a family record nothing merges: kind codes stay distinct documents.
    assert all(len(g.member_ids) == 1 for g in F.group_candidates_by_family(dossier.candidates, []))
    with pytest.raises(ValueError):
        F.group_candidates_by_family(dossier.candidates, families + [F.PatentFamily(
            family_id="OTHER", member_ids=["US0000201A1"], representative_id="US0000201A1", source_id="x")])


# -------------------------------------------------- S04 only archived regulatory

def test_s04_archived_source_is_kept_current():
    dossier, _, _ = run("beta")
    assert "beta-device-archive" in {s.source.source_id for s in dossier.sources}


def test_s04_only_archived_regulatory_source_is_flagged():
    F = foundation()
    dossier, _, _ = run("beta")
    state = F.SourceState(source_id="beta-device-archive", source_version="authored-fixture-v1",
                          status="archived", observed_at=OBSERVED, reason="Only an archived copy was available")
    warnings = F.source_state_warnings(dossier, [state])
    assert any("beta-device-archive" in w and "archived" in w for w in warnings)
    assert any("no current regulatory record" in w.lower() for w in warnings)
    with pytest.raises(ValueError):
        F.source_state_warnings(dossier, [state.model_copy(update={"source_version": "other"})])
    current = state.model_copy(update={"status": "current"})
    assert F.source_state_warnings(dossier, [current]) == []


# ------------------------------------------------------- S05 missing filing date

def test_s05_missing_dates_are_flagged_never_imputed():
    F = foundation()
    dates = [F.PatentDates(**d) for d in FIXTURE["patent_dates"]]
    flags = {(f.patent_id_canonical, f.flag) for f in F.date_gaps(dates, cutoff=date(2026, 10, 30))}
    assert flags == {
        ("US0000202B2", "missing_filing_date"),
        ("US0000203A1", "missing_filing_date"),
        ("US0000203A1", "missing_publication_date"),
        ("US0000203A1", "cutoff_unknown"),
        ("EP0000201B1", "after_cutoff"),
    }
    assert dates[1].filing_date is None  # input is not mutated or back-filled


# ------------------------------------------------------- S06 conflicting sources

def test_s06_conflicting_values_are_both_kept_current():
    dossier, _, _ = run("gamma")
    applicants = {e.source_id: e.structured_value for e in dossier.evidence if e.structured_field == "applicant"}
    assert applicants == {"gamma-device-us": "Gamma Diagnostics Ltd",
                          "gamma-device-registry": "Gamma Diagnostics Holdings Ltd"}


def test_s06_conflicts_are_reported_without_choosing_a_winner():
    F = foundation()
    dossier, _, _ = run("gamma")
    conflicts = F.detect_field_conflicts(dossier.evidence)
    assert [c.field for c in conflicts] == ["applicant"]  # device_name agrees across sources
    assert sorted(v.evidence_id for v in conflicts[0].values) == ["gamma-ev-applicant-registry",
                                                                  "gamma-ev-applicant-us"]
    assert conflicts[0].status == "conflict"


# ------------------------------------------------------- S07 source withdrawal

def test_s07_withdrawal_downgrades_dependent_evidence_and_links():
    F = foundation()
    before = with_disclosed_alpha(run("alpha")[0])
    after, impact = F.withdraw_source(before, "alpha-maker-page", reason="Authored page removed",
                                      observed_at=OBSERVED)
    assert (after.version, after.parent_version, after.created_at) == (2, 1, OBSERVED)
    assert impact.affected_evidence_ids == ["alpha-ev-marking"]
    assert impact.affected_candidate_ids == ["US0000101B2"]
    marking = {e.evidence_id: e for e in after.evidence}["alpha-ev-marking"]
    assert marking.evidence_kind == "unresolved" and marking.verification_status == "not_independently_validated"
    assert {c.patent_id_canonical: c.association_status for c in after.candidates}["US0000101B2"] == "retrieved_candidate"
    assert any("alpha-maker-page" in u and "withdrawn" in u.lower() for u in after.unresolved_items)
    assert "alpha-maker-page" in {s.source.source_id for s in after.sources}  # original kept, not deleted
    with pytest.raises(ValueError):
        F.withdraw_source(after, "alpha-maker-page", reason="again", observed_at=OBSERVED)
    with pytest.raises(ValueError):
        F.withdraw_source(after, "no-such-source", reason="x", observed_at=OBSERVED)


def test_s07_withdrawn_version_saves_into_existing_history(tmp_path):
    F = foundation()
    before = with_disclosed_alpha(run("alpha")[0])
    after, _ = F.withdraw_source(before, "alpha-maker-page", reason="removed", observed_at=OBSERVED)
    save_version(tmp_path, before)
    save_version(tmp_path, after)
    assert [v.version for v in load_versions(tmp_path)] == [1, 2]


# --------------------------------------------------- S08 user constraint change

def test_s08_constraint_change_reports_scoped_diff_and_keeps_user_edits():
    F = foundation()
    before = run("alpha")[0].model_copy(update={"user_edits": {"review_note": "keep me"}})
    rerun = run("alpha", features_of_interest=["occlusion sensor", "wound dressing"])[0]
    revised = F.carry_forward(before, rerun)
    assert (revised.version, revised.parent_version, revised.dossier_id) == (2, 1, before.dossier_id)
    assert revised.user_edits == {"review_note": "keep me"}
    diff = F.dossier_diff(before, revised)
    assert diff.query_changes == ["features_of_interest"]
    assert diff.added_candidates == ["US0000103B1"]
    assert diff.removed_candidates == []
    assert sorted(diff.unchanged_candidates + diff.changed_candidates) == ["US0000101B2", "US0000102A1"]
    assert diff.added_evidence == diff.removed_evidence == diff.changed_evidence == []


@pytest.mark.xfail(strict=True, reason="GAP (not fixed): a tightened cutoff rejects the whole input instead "
                   "of blocking only the routes that depend on the newer source (plan J06).")
def test_s08_tightened_cutoff_blocks_only_dependent_routes():
    data = project_input("alpha", evidence_cutoff="2026-10-02")  # brochure (10-03) becomes too new
    dossier, _, _ = run_dossier(DossierInput.model_validate(data), run_id="cut", code_commit="x")
    assert "alpha-ev-flow" not in {e.evidence_id for e in dossier.evidence}


# --------------------------------------------------- S09 numerical unit ambiguity

def test_s09_structured_value_types_are_not_coerced_current():
    sources = {s["id"]: _source(s) for s in FIXTURE["projects"]["alpha"]["sources"]}
    item = field_evidence(sources["alpha-device"], "decision_date", "d")
    with pytest.raises(ValueError):
        check_evidence(item.model_copy(update={"structured_value": "2024-03-01T00:00:00"}), sources["alpha-device"])


def test_s09_quantities_keep_written_value_and_flag_missing_or_ambiguous_units():
    F = foundation()
    text = FIXTURE["quantity_text"]
    found = F.quantity_mentions(text)
    assert [(q.value, q.unit, q.status) for q in found] == [
        (q["value"], q["unit"], q["status"]) for q in FIXTURE["quantity_expected"]]
    for q in found:
        assert text[q.start:q.end].startswith(q.value)


# ------------------------------------------------------ S10 model/tool timeout

class TimeoutVectors:
    calls = 0

    def search(self, query, *, limit):
        TimeoutVectors.calls += 1
        raise TimeoutError("authored timeout")


def test_s10_tool_timeout_is_recorded_without_retry_and_keeps_lexical_results():
    TimeoutVectors.calls = 0
    data = DossierInput.model_validate(project_input("alpha"))
    dossier, events, manifest = run_dossier(data, run_id="timeout", code_commit="x",
                                            vector_search=TimeoutVectors())
    searches = [e for e in events if e.action_type != "stop"]
    assert TimeoutVectors.calls == len(searches) == manifest.actual_search_calls
    assert all("vector_search_timeout" in e.errors for e in searches)
    assert manifest.stop_reason == "run_failure" and manifest.failed_query_ids == ["HT-SCN-ALPHA"]
    assert {c.patent_id_canonical for c in dossier.candidates} == {"US0000101B2", "US0000102A1"}


# ------------------------------------------------------------ metamorphic + replay

def _accepted(dossier: DossierVersion):
    return ([e.model_dump(mode="json") for e in dossier.evidence],
            [(c.patent_id_canonical, c.association_status, c.disclosure_evidence_id) for c in dossier.candidates])


def test_m1_irrelevant_document_does_not_change_accepted_links_current():
    extra = FIXTURE["irrelevant_additions"]
    base = with_disclosed_alpha(run("alpha")[0])
    plus = with_disclosed_alpha(run("alpha", extra_sources=[extra["source"]], extra_patents=[extra["patent"]])[0])
    assert _accepted(base) == _accepted(plus)


def test_m2_withdrawal_invalidates_only_descendants():
    F = foundation()
    before = with_disclosed_alpha(run("alpha")[0])
    after, impact = F.withdraw_source(before, "alpha-device", reason="authored", observed_at=OBSERVED)
    changed = {e.evidence_id for e, o in zip(after.evidence, before.evidence) if e != o}
    assert changed == {"alpha-ev-name", "alpha-ev-applicant"} == set(impact.affected_evidence_ids)
    assert after.candidates == before.candidates  # no candidate depends on the device record
    assert impact.affected_candidate_ids == []
    # Withdrawing a source with no descendants changes no evidence or link at all.
    extra = FIXTURE["irrelevant_additions"]["source"]
    base = with_disclosed_alpha(run("alpha", extra_sources=[extra])[0])
    after2, impact2 = F.withdraw_source(base, extra["id"], reason="authored", observed_at=OBSERVED)
    assert after2.evidence == base.evidence and after2.candidates == base.candidates
    assert impact2.affected_evidence_ids == impact2.affected_candidate_ids == []
    assert len(after2.unresolved_items) == len(base.unresolved_items) + 1


def test_replay_same_input_gives_same_ids_and_input_hash():
    a = run("beta", run_id="same")
    b = run("beta", run_id="same")
    assert ids(a[0].candidates, "patent_id_canonical") == ids(b[0].candidates, "patent_id_canonical")
    assert ids(a[1], "step_id") == ids(b[1], "step_id")
    assert a[0].dossier_id == b[0].dossier_id and a[0].input_hash == b[0].input_hash


def test_replay_run_id_and_fingerprint_are_deterministic():
    F = foundation()
    data = DossierInput.model_validate(project_input("beta"))
    run_id = F.replay_run_id(data)
    assert run_id == F.replay_run_id(DossierInput.model_validate(project_input("beta")))
    assert run_id != F.replay_run_id(DossierInput.model_validate(project_input("gamma")))
    first = run_dossier(data, run_id=run_id, code_commit="x")
    second = run_dossier(data, run_id=run_id, code_commit="x")
    assert first[0].created_at is not None
    assert F.replay_fingerprint(*first) == F.replay_fingerprint(*second)
    changed = first[0].model_copy(update={"unresolved_items": [*first[0].unresolved_items, "x"]})
    assert F.replay_fingerprint(changed, first[1], first[2]) != F.replay_fingerprint(*first)
    assert set(F.VOLATILE_FIELDS) == {"created_at", "started_at", "ended_at", "elapsed_seconds"}
    assert content_hash(F.strip_volatile({"created_at": 1, "x": {"elapsed_seconds": 2, "y": 3}})) == \
        content_hash({"x": {"y": 3}})
