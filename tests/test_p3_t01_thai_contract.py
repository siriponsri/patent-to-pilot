"""P3-T01 Thai dataset/profile rights and exposure contract.

Metadata and synthetic rows only: every row below is fictional Thai text written for this test. Nothing is
downloaded, no gate is accepted and no provider is called."""
from __future__ import annotations

import copy
import unicodedata

import pytest

from patent_to_pilot.workbench.datasets import adapters as A
from patent_to_pilot.workbench.datasets import registry as R
from patent_to_pilot.workbench.datasets import thai_contract as T
from patent_to_pilot.workbench.datasets.inspect import inspect_schema
from patent_to_pilot.workbench.datasets.loaders import iter_jsonl
from patent_to_pilot.workbench.datasets.policy import ProtectedPathError

REG = T.load_thai_contract()
GAZETTE = A.GAZETTE
NITI = A.NITIBENCH
STATUTE = A.NITIBENCH_STATUTE
NITI_PLUS = A.NITIBENCH_PLUS
OCR = "typhoon-ai/ThaiOCRBench"
PACKETS = "PTP_authorized_thai_packets"

# Revisions read from the public Hugging Face API on 2026-11-22.
PINS = {
    GAZETTE: "87e695ee4951ff34932804431433ac55991ec374",
    NITI_PLUS: "41286bcb1eeba6721c03d581d4ca3095a1b7f7b7",
    NITI: "9f75697075e0f5691e3b821037b908c05f1821a7",
    STATUTE: "069e774f015a50e801dbe2055a29be580c54a83c",
    OCR: "ca610d1ab33059e721251137ab1f19f936b87648",
}


def ds(did: str, reg: dict = REG) -> dict:
    return next(d for d in reg["datasets"] if d["dataset_id"] == did)


# ------------------------------------------------------------------------------------------ pins
def test_registry_and_thai_contract_validate():
    R.validate_registry(REG)
    T.validate_thai_contract(REG)
    assert set(T.thai_resource_ids(REG)) >= set(PINS) | {PACKETS, "PTP_supplied_document_tasks", "PTP_packet_ocr_diagnostics"}


@pytest.mark.parametrize("did,rev", sorted(PINS.items()))
def test_thai_releases_are_pinned(did, rev):
    d = ds(did)
    assert d["revision"] == rev == d["thai_contract"]["release"]["dataset_revision"]
    assert d["sources"]["revision"] and d["sources"]["thai_contract"]
    assert d["language"] == "th"


def test_licenses_and_gating_recorded():
    expected = {GAZETTE: ("CC-BY-4.0", False), NITI_PLUS: ("CC-BY-4.0", False), NITI: ("MIT", False),
                STATUTE: ("MIT", False), OCR: ("CC-BY-SA-4.0", True)}
    for did, (lic, share_alike) in expected.items():
        rights = ds(did)["thai_contract"]["rights"]
        assert rights["license"] == lic and rights["share_alike"] is share_alike
        assert rights["redistribution_in_product"] is False and ds(did)["product_bundle_allowed"] is False
    assert ds(NITI_PLUS)["access"]["kind"] == "auto_gated"
    assert ds(NITI_PLUS)["access"]["acceptance_performed"] is False
    for did in (GAZETTE, NITI, STATUTE, OCR):
        assert ds(did)["access"]["kind"] == "public"


def test_related_wangchanx_training_source_pinned_not_downloaded():
    rel = {r["resource_id"]: r for r in REG["thai_contract"]["related_training_resources"]}
    wx = rel["airesearch/WangchanX-Legal-ThaiCCL-RAG"]
    assert wx["revision"] == "654e1a10afc44ecaee36fd739bc90078dcc62388"
    assert wx["splits"] == {"train": 8211, "test": 3742} and wx["status"] == "NOT_DOWNLOADED"


# ----------------------------------------------------------------------------- exposure / overlap
def test_gazette_exposure_records_public_card_preview():
    exp = ds(GAZETTE)["exposure"]
    assert exp.startswith("public_card_auto_preview_and_public_transfer")
    assert "not fresh confirmation" in exp
    assert ds(GAZETTE)["thai_contract"]["splits"]["native_dev_split"] is None


def test_specialist_training_overlap_is_disclosed():
    subjects = " ".join(r["subject"] + " " + r["finding"] for r in ds(NITI)["thai_contract"]["training_overlap_risk"])
    for model in ("typhoon-s-4b-nitibench-ccl-legal-agent-research-preview", "WangchanX-Legal-ThaiCCL-Retriever",
                  "nitibench-ccl-human-finetuned-bge-m3"):
        assert model in subjects
    for did in PINS:
        assert ds(did)["thai_contract"]["training_overlap_risk"]


def test_nitibench_plus_judge_score_is_not_ground_truth():
    c = ds(NITI_PLUS)["thai_contract"]
    assert "rule 12" in c["study_metric"]
    assert "restricted_gold_section_pool" not in ds(NITI_PLUS)["allowed_named_settings"]
    assert {"gate_acceptance", "download", "owner_decision"} <= {b["kind"] for b in c["blocked_pending_owner"]}


# ---------------------------------------------------------------------------------- scoreboards
def test_six_separate_scoreboards():
    assert set(REG["thai_contract"]["scoreboards"]) == set(T.SCOREBOARDS)
    assert T.scoreboard_of(GAZETTE, REG) == "thai_gazette_retrieval"
    assert T.scoreboard_of(NITI, REG) == T.scoreboard_of(STATUTE, REG) == "nitibench_original"
    assert T.scoreboard_of(NITI_PLUS, REG) == "nitibench_plus"
    assert T.scoreboard_of(PACKETS, REG) == "fresh_structural_packets"
    assert T.scoreboard_of("PTP_supplied_document_tasks", REG) == "supplied_document_tasks"
    assert T.scoreboard_of(OCR, REG) == T.scoreboard_of("PTP_packet_ocr_diagnostics", REG) == "ocr_diagnostics"


def test_one_table_may_not_mix_scoreboards():
    assert T.assert_single_scoreboard([{"dataset_id": GAZETTE}, {"dataset_id": GAZETTE}], REG) == "thai_gazette_retrieval"
    assert T.assert_single_scoreboard([{"dataset_id": NITI}, {"dataset_id": STATUTE}], REG) == "nitibench_original"
    for other in (NITI, NITI_PLUS, PACKETS, OCR, "PTP_supplied_document_tasks"):
        with pytest.raises(T.ScoreboardMixError, match="mixes scoreboards"):
            T.assert_single_scoreboard([{"dataset_id": GAZETTE}, {"dataset_id": other}], REG)
    with pytest.raises(T.ScoreboardMixError, match="belongs to"):
        T.assert_single_scoreboard([{"dataset_id": NITI_PLUS, "scoreboard": "nitibench_original"}], REG)
    with pytest.raises(T.ScoreboardMixError, match="not a Thai resource"):
        T.assert_single_scoreboard([{"dataset_id": A.DAPFAM}], REG)


def test_nitibench_plus_rows_need_a_native_setting():
    ok = [{"dataset_id": NITI_PLUS, "setting": "gold_cited_in_force_public_validation"}]
    assert T.assert_single_scoreboard(ok, REG) == "nitibench_plus"
    with pytest.raises(T.ScoreboardMixError, match="not a native named setting"):
        T.assert_single_scoreboard([{"dataset_id": NITI_PLUS, "setting": "restricted_gold_section_pool"}], REG)


# --------------------------------------------------------------------------------- permitted use
@pytest.mark.parametrize("rid", sorted(PINS) + [PACKETS, "PTP_supplied_document_tasks", "PTP_packet_ocr_diagnostics"])
def test_nothing_is_downloadable_or_trainable_without_owner_record(rid):
    for purpose in ("download", "gate_acceptance", "development", "method_selection", "training",
                    "held_out_evaluation", "product_bundle"):
        d = T.permitted_use(rid, purpose, REG)
        assert d.allowed is False, (rid, purpose, d.reason)
    for purpose in ("metadata_read", "synthetic_fixture"):
        assert T.permitted_use(rid, purpose, REG).allowed is True


def test_recorded_download_approval_unblocks_download_and_held_out_only():
    reg = copy.deepcopy(REG)
    c = ds(GAZETTE, reg)["thai_contract"]
    c["download_approval"] = {"approved_by": "owner", "date": "2026-12-01", "scope": "pinned revision, all three configs",
                              "record": "hypothetical approval record for this test"}
    T.validate_thai_contract(reg)
    assert T.permitted_use(GAZETTE, "download", reg).allowed is True
    assert T.permitted_use(GAZETTE, "held_out_evaluation", reg).allowed is True
    assert T.permitted_use(GAZETTE, "development", reg).allowed is False
    assert T.permitted_use(GAZETTE, "product_bundle", reg).allowed is False


def test_gate_still_blocks_nitibench_plus_even_with_download_approval():
    reg = copy.deepcopy(REG)
    ds(NITI_PLUS, reg)["thai_contract"]["download_approval"] = {"approved_by": "owner", "date": "2026-12-01",
                                                                "scope": "validation", "record": "hypothetical"}
    T.validate_thai_contract(reg)
    d = T.permitted_use(NITI_PLUS, "download", reg)
    assert d.allowed is False and "gated" in d.reason


def test_unknown_purpose_rejected():
    with pytest.raises(ValueError):
        T.permitted_use(GAZETTE, "scrape", REG)


# ------------------------------------------------------------------------------ validator rejects
def test_validator_requires_download_block_without_approval():
    bad = copy.deepcopy(REG)
    c = ds(NITI, bad)["thai_contract"]
    c["blocked_pending_owner"] = [b for b in c["blocked_pending_owner"] if b["kind"] != "download"]
    with pytest.raises(T.ContractError, match="'download' block is required"):
        T.validate_thai_contract(bad)


def test_validator_rejects_incomplete_approval_and_gate_without_block():
    bad = copy.deepcopy(REG)
    ds(GAZETTE, bad)["thai_contract"]["download_approval"] = {"approved_by": "owner"}
    c = ds(NITI_PLUS, bad)["thai_contract"]
    c["blocked_pending_owner"] = [b for b in c["blocked_pending_owner"] if b["kind"] != "gate_acceptance"]
    with pytest.raises(T.ContractError) as exc:
        T.validate_thai_contract(bad)
    assert "download_approval needs" in str(exc.value) and "'gate_acceptance' block is required" in str(exc.value)


def test_validator_rejects_scoreboard_reassignment_and_bundling():
    bad = copy.deepcopy(REG)
    ds(GAZETTE, bad)["thai_contract"]["scoreboard"] = "nitibench_plus"
    ds(OCR, bad)["product_bundle_allowed"] = True
    with pytest.raises(T.ContractError) as exc:
        T.validate_thai_contract(bad)
    msg = str(exc.value)
    assert "listed under" in msg and "may not be bundled" in msg


def test_validator_rejects_license_or_revision_drift_and_missing_contract():
    bad = copy.deepcopy(REG)
    ds(STATUTE, bad)["thai_contract"]["rights"]["license"] = "CC-BY-4.0"
    ds(OCR, bad)["thai_contract"]["release"]["dataset_revision"] = "0" * 40
    del ds(NITI, bad)["thai_contract"]
    with pytest.raises(T.ContractError) as exc:
        T.validate_thai_contract(bad)
    msg = str(exc.value)
    assert "differs from registry license" in msg and "dataset_revision differs" in msg
    assert "Thai dataset has no thai_contract" in msg


def test_validator_rejects_extra_or_missing_scoreboard():
    bad = copy.deepcopy(REG)
    bad["thai_contract"]["scoreboards"]["thai_average"] = {"members": []}
    with pytest.raises(T.ContractError, match="scoreboards must be exactly"):
        T.validate_thai_contract(bad)


# ------------------------------------------------------------------------- availability / paths
def test_new_thai_datasets_not_downloaded_and_nitibench_plus_still_gated(tmp_path):
    for did in (NITI, STATUTE, OCR, GAZETTE):
        assert R.availability(did, [tmp_path], REG).status == R.NOT_DOWNLOADED
    assert R.availability(NITI_PLUS, [tmp_path], REG).status == R.GATED_ACCEPTANCE_REQUIRED


@pytest.mark.parametrize("rel", ["data/test-00000-of-00004.parquet", "default/test-00000-of-00001.jsonl",
                                 "data/test-00000-of-00004.jsonl"])
def test_test_split_paths_refused_before_opening(tmp_path, rel):
    p = tmp_path / rel  # never created: refusal must happen before any open
    with pytest.raises(ProtectedPathError):
        inspect_schema(p)
    with pytest.raises(ProtectedPathError):
        list(iter_jsonl(p))


# ------------------------------------------------------------------------------------- adapters
QUESTION = "ผู้ถือหุ้นสมมุติของบริษัทตัวอย่างต้องแจ้งอะไรภายในสามสิบวัน"  # fictional
SECTION = "มาตรา ๙๙๙ ข้อความสมมุติสำหรับการทดสอบเท่านั้นำ"  # fictional, ends with SARA AM


def test_nitibench_question_adapter_drops_labels_and_keeps_thai_exact():
    row = {"question": QUESTION, "answer": "คำตอบสมมุติ", "relevant_laws": [{"law": "x"}],
           "reference_answer": "อ้างอิงสมมุติ", "reference_laws": ["y"]}
    rec = A.NitiBenchAdapter(REG).request_from_question(row, split="ccl", index=7)
    assert rec.request_id == "ccl[7]" and rec.text == QUESTION
    assert rec.text.encode("utf-8") == QUESTION.encode("utf-8")
    assert ("request_id_kind", "positional_locator") in rec.attributes
    flat = repr(rec)
    for label in ("คำตอบสมมุติ", "อ้างอิงสมมุติ", "relevant_laws"):
        assert label not in flat
    for field in ("answer", "relevant_laws", "reference_answer", "reference_laws"):
        with pytest.raises(A.EvaluatorFieldRequested):
            A.NitiBenchAdapter(REG).request_from_question(row, split="tax", index=0, include=(field,))
    with pytest.raises(A.MissingIdentifier):
        A.NitiBenchAdapter(REG).request_from_question(row, split="ccl", index=-1)
    with pytest.raises(KeyError):
        A.NitiBenchAdapter(REG).request_from_question(row, split="train", index=0)


def test_nitibench_statute_adapter_keys_section_and_preserves_text():
    nfd = unicodedata.normalize("NFD", SECTION)
    row = {"law_code": "TESTCODE", "law_name": "พระราชบัญญัติสมมุติ", "section_num": "999",
           "section_content": nfd, "reference": "ref-fictional"}
    rec = A.NitiBenchStatuteAdapter(REG).source_from_section(row, include=("reference",))
    assert rec.source_id == "TESTCODE/999" and rec.version_id == PINS[STATUTE]
    assert rec.text == nfd and rec.text.encode("utf-8") == nfd.encode("utf-8")
    assert rec.locator.endswith(":statute_ccl/TESTCODE/999") and ("reference", "ref-fictional") in rec.attributes
    with pytest.raises(A.MissingIdentifier):
        A.NitiBenchStatuteAdapter(REG).source_from_section({**row, "section_num": ""})
