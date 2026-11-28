"""Small contract and policy checks, plus validation of any generated demo files."""

from datetime import date
from pathlib import Path
from types import SimpleNamespace

from jsonschema import Draft202012Validator
import pytest

from product.mwd.audit import audit_dossier
from product.mwd.build import ranked_queue, select_demo
from product.mwd.contract import CURRENT, DEMO, SECTIONS, TRACK_A_DISCLAIMER, TRACK_A_LABEL, read_json
from product.mwd.render import CHROME, chrome_page, render


def test_rank_uses_native_scores_key_ties_and_exact_capacity():
    keys = "baced"
    rows = [{"key": key, "M3": 0.8 if key in "ab" else 0.1, "B1": 0.2} for key in keys]
    entities = {key: SimpleNamespace(nda_first=date(2012, 1, 1),
                                    anda_first=date(2016, 1, 1) if key == "a" else None,
                                    flag_at=lambda *_: True) for key in keys}
    evidence = SimpleNamespace(entities=entities, names={key: key.upper() for key in keys})
    manifest = {"metrics": [{"arm": "M3", "cutoff": "2014-01-01", "horizon": 24, "event_rows": 1}],
                "exports": {"24": {"sha256": "0" * 64}}}
    queue = ranked_queue("2014-01-01", 24, rows, evidence, manifest)
    assert [row["key"] for row in queue["ranked_rows"]] == list("abcde")
    assert queue["capture"] == {"eligible": 5, "events": 1, "captured": 1,
                                "queued_without_event": 0, "missed": 0, "recall": 1, "precision": 1}


def test_demo_selection_requires_dated_support_and_keeps_errors():
    rows = [dict(key=str(i), display_name=str(i), m3_rank=i, in_queue=i <= 7, event=i != 2)
            for i in range(1, 10)]
    evidence = SimpleNamespace(listing=lambda *_: (None, [], [True], []),
                               challenges=lambda _, key: key not in {"1", "4"})
    chosen = select_demo(dict(as_of="2014-01-01", ranked_rows=rows), evidence)
    assert [row["key"] for row in chosen] == ["3", "5", "6", "7", "2", "8"]
    assert [row["role"] for row in chosen][-2:] == ["false_alarm", "miss"]


@pytest.fixture
def dossier():
    return {
        "schema_version": "mwd.dossier.v1",
        "molecule": {"key": "U:TEST", "display_name": "<Drug>", "dosage_forms": []},
        "as_of": "2014-01-01", "jurisdiction": "US",
        "forecast": {"horizon_months": 24, "m3_p_entry": 0.8, "b1_p_entry": 0.4,
                     "m3_rank": 1, "queue_size": 3, "in_queue": True, "status": "DEVELOPMENT_ONLY"},
        "outcome_reveal": {"first_final_anda_date": None, "window_end": "2016-01-01"},
        "sections": [dict(id=id, title_th=th, title_en=en) for id, th, en in SECTIONS],
        "claims": [{"id": "patent", "section": "patents", "text_th": "พบหลักฐาน",
                    "text_en": "Evidence <material>", "state": "known", "kind": "observed", "source_ids": ["src"]}],
        "sources": [{"id": "src", "issuer": "FDA", "title": "Example", "version": "2013-01",
                     "public_date": "2013-01-02", "locator": "Row 5", "url": "https://www.fda.gov/",
                     "sha256": None, "retrieved": None}],
        "checklist": [{"id": "check", "text_th": "ตรวจ", "text_en": "Verify", "owner": "FTO evaluator",
                       "source_ids": ["src"]}],
    }


@pytest.fixture
def validator():
    schema = read_json(Path(__file__).resolve().parents[1] / "schema" / "dossier.v1.schema.json")
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema, format_checker=Draft202012Validator.FORMAT_CHECKER)


def test_schema_checks_hierarchy_and_development_reveal(validator, dossier):
    assert validator.is_valid(dossier)
    dossier["forecast"]["status"] = "TRACK_A_FROZEN"
    assert not validator.is_valid(dossier)
    dossier.pop("outcome_reveal")
    assert validator.is_valid(dossier)
    dossier["sections"].reverse()
    assert not validator.is_valid(dossier)


def test_audit_flags_future_claim_and_empty_locator(dossier):
    assert audit_dossier(dossier)["covered"] == 1
    dossier["sources"][0]["public_date"] = "2015-01-01"
    assert any("future-dated" in error for error in audit_dossier(dossier)["errors"])
    dossier["sources"][0]["locator"] = ""
    assert audit_dossier(dossier)["covered"] == 0


def test_current_lookup_label_cannot_authorize_a_us_claim(dossier):
    dossier["sources"][0]["public_date"] = "2026-11-28"
    claim = dossier["claims"][0]
    claim.update(time_basis="current_lookup", text_en="Current lookup results", text_th="ผลตรวจปัจจุบัน")
    assert audit_dossier(dossier)["errors"]
    claim["section"] = "thai_asean"
    assert not audit_dossier(dossier)["errors"]
    claim["text_en"] = "Status"
    assert audit_dossier(dossier)["errors"]


def test_future_scenario_cannot_launder_a_patent_source(dossier):
    claim = dossier["claims"][0]
    claim.update(id="price-scenario", section="market", kind="assumption", time_basis="retrospective_scenario")
    dossier["sources"][0]["public_date"] = "2019-12-01"
    assert audit_dossier(dossier)["errors"]
    dossier["sources"][0]["id"] = "fda-amp-2019"
    claim["source_ids"] = dossier["checklist"][0]["source_ids"] = ["fda-amp-2019"]
    assert not audit_dossier(dossier)["errors"]


def test_track_a_requires_all_references_hashed_and_dated(dossier):
    dossier["forecast"]["status"] = "TRACK_A_PENDING"
    dossier["as_of"] = "2026-11-27"
    dossier["label"] = TRACK_A_LABEL
    dossier["version"] = {"freeze": "pending", "core_manifest_sha256": "0" * 64}
    dossier["disclaimer"] = TRACK_A_DISCLAIMER
    assert audit_dossier(dossier)["errors"]
    dossier.pop("outcome_reveal")
    source = dossier["sources"][0]
    source.update(sha256="0" * 64, public_date=None, evidence_cutoff="2026-11-27")
    assert not audit_dossier(dossier)["errors"]
    source["evidence_cutoff"] = "2026-11-28"
    assert audit_dossier(dossier)["errors"]


@pytest.fixture(scope="module")
def page():
    pytest.importorskip("playwright.sync_api")
    if not CHROME.is_file():
        pytest.skip("Chrome is not installed at the expected path")
    with chrome_page(CHROME) as chrome:
        yield chrome


def current_dossier():
    return read_json(sorted(CURRENT.glob("dossier-*.json"))[0])


def test_report_escapes_values_and_numbers_the_sources(dossier, page):
    html = render(dossier, "en", "case.th.html", page=page)
    assert "<Drug>" not in html and "&lt;Drug&gt;" in html and "Evidence &lt;material&gt;" in html
    assert 'href="case.th.html"' in html and 'href="#pd-ref-1">[1]</a>' in html and 'id="pd-ref-1"' in html


def test_historical_report_hides_the_outcome_until_asked_and_marks_a_reveal(dossier, page):
    dossier["outcome_reveal"] = {"first_final_anda_date": "2014-02-18", "window_end": "2016-01-01", "source_ids": ["outcome"]}
    dossier["sources"].append({"id": "outcome", "issuer": "FDA", "title": "Approval", "version": "2026", "public_date": "2014-02-18",
                               "locator": "ORIG/AP 2014-02-18", "url": "https://www.fda.gov/", "sha256": None, "retrieved": None})
    hidden = render(dossier, "th", None, page=page)
    assert "2014-02-18" not in hidden and "18 Feb 2014" not in hidden
    assert "Outcome" not in hidden.replace("Development data: outcome hidden", "") and "REVEALED" not in hidden
    assert "Revealed export" not in hidden
    shown = render(dossier, "th", None, page=page, reveal=True)
    assert "Revealed export" in shown and "REVEALED: development outcome shown" in shown and 'id="pd-outcome"' in shown
    assert "2014-02-18" in shown


def test_current_report_page_one_and_no_outcome(page):
    dossier = current_dossier()
    for lang in ("th", "en"):
        html = render(dossier, lang, None, page=page, horizon=24, total=651)
        assert TRACK_A_LABEL in html and TRACK_A_DISCLAIMER[lang] in html
        assert "66.85%" in html and "26.62%" in html and "outcome_reveal" not in html and "pd-outcome" not in html
        assert dossier["version"]["tag"] in html
    with pytest.raises(ValueError, match="never contains outcome"):
        render(dossier, "en", None, page=page, horizon=24, reveal=True)
    with pytest.raises(ValueError, match="never contains outcome"):
        render({**dossier, "outcome_reveal": {"first_final_anda_date": None, "window_end": "2028-11-27"}}, "en", None, page=page, horizon=24)


def test_report_horizon_and_long_lists(dossier, page):
    with pytest.raises(ValueError, match="12-month horizon"):
        render(dossier, "en", None, page=page, horizon=12)
    dossier["claims"] = [{**dossier["claims"][0], "id": f"c{i}"} for i in range(30)]
    html = render(dossier, "en", None, page=page)
    assert html.count("Evidence &lt;material&gt;") == 30 and "22 more in Appendix A" in html and "Statements continued" in html


def test_generated_dossiers_validate(validator):
    paths = sorted((DEMO / "data").glob("dossier-*.json"))
    assert paths, "Build the development demo before validating the generated files"
    for path in [*paths, *sorted(CURRENT.glob("dossier-*.json"))]:
        dossier = read_json(path)
        validator.validate(dossier)
        assert not audit_dossier(dossier)["errors"], path.name
