"""P3-T02 packet builder on small fictional inputs (no dataset content)."""
import importlib.util
import json
import pathlib

import pytest

pytest.importorskip("scipy")

_P = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "research" / "p3t02_build_packets.py"
_spec = importlib.util.spec_from_file_location("p3t02_build_packets", _P)
bp = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(bp)

PROV = {k: {"repo": f"fixture/{k}", "revision": "0" * 40, "license": "MIT", "file": f"{k}.parquet"}
        for k in ("wangchanx", "niti_ccl", "niti_tax", "niti_ccl_copy", "statute", "gazette_queries")}


def _ctx(law, sec, text="ข้อความสมมุติ"):
    return {"context": text, "metadata": {"law_code": law, "law_title": "x", "section": sec}, "unique_key": f"{law}-{sec}"}


def _rows():
    statute = [
        {"law_code": "L1", "law_name": "กฎหมายหนึ่ง", "section_num": "1", "section_content": "บทบัญญัติหนึ่ง", "reference": []},
        {"law_code": "L1", "law_name": "กฎหมายหนึ่ง", "section_num": "2", "section_content": "ให้นำมาใช้โดยอนุโลม",
         "reference": []},
        {"law_code": "L2", "law_name": "กฎหมายสอง", "section_num": "5", "section_content": "ผู้ขอต้องยื่นคำขอ",
         "reference": [{"include": True, "law_name": "กฎหมายสอง", "section_num": "6"}]},
        {"law_code": "L2", "law_name": "กฎหมายสอง", "section_num": "6", "section_content": "ค่าธรรมเนียม", "reference": []},
        {"law_code": "L3", "law_name": "กฎหมายสาม", "section_num": "9", "section_content": "การจดแจ้ง", "reference": []},
        {"law_code": "L4", "law_name": "กฎหมายสี่", "section_num": "1", "section_content": "ข้อความ", "reference": []},
    ]
    heldout_q = "บริษัทสมมุติต้องยื่นรายงานประจำปีต่อนายทะเบียนสมมุติภายในกี่วันนับแต่วันปิดบัญชี"
    wangchanx = [
        {"question": "คำถามเกี่ยวกับกฎหมายหนึ่ง", "positive_contexts": [_ctx("L1", "1")], "hard_negative_contexts": []},
        {"question": "ผู้ขอสมมุติต้องยื่นคำขอที่ใด", "positive_contexts": [_ctx("L2", "5"), _ctx("L3", "9")],
         "hard_negative_contexts": [_ctx("L1", "2"), _ctx("L2", "6")]},
        {"question": "คำถามไม่มีคำตอบ", "positive_contexts": [], "hard_negative_contexts": []},
        {"question": heldout_q + " ", "positive_contexts": [_ctx("L3", "9")], "hard_negative_contexts": []},
        {"question": "การจดแจ้งสมมุติต้องทำภายในกี่วัน", "positive_contexts": [_ctx("L3", "มาตรา ๙")],
         "hard_negative_contexts": []},
    ]
    ccl = [{"question": heldout_q, "relevant_laws": [{"law_name": "กฎหมายหนึ่ง", "section_num": "1", "section_content": "บทบัญญัติหนึ่ง"}],
            "reference_laws": []}]
    tax = [{"question": "ภาษีสมมุติ", "relevant_laws": [{"law_name": "กฎหมายหนึ่ง", "section_num": "2", "section_content": "x"}],
            "reference_laws": [{"law_name": "กฎหมายสี่", "section_num": "1", "section_content": "x"}]}]
    return {"wangchanx": wangchanx, "niti_ccl": ccl, "niti_tax": tax, "statute": statute,
            "gazette_queries": ["ประกาศสมมุติฉบับหนึ่ง"], "niti_ccl_copy": [{"question": heldout_q}]}


def test_normalise_thai_digits_zero_width_and_spacing():
    assert bp.normalise("มาตรา ๑๒​ ?") == bp.normalise("มาตรา12")
    assert bp.light_norm("ภายใน  ๓๐​ วัน") == "ภายใน 30 วัน"
    assert bp.norm_section("มาตรา ๓๘/๑") == "38/1"
    assert bp.source_id("L3", "มาตรา ๙") == bp.source_id("L3", "9") == "L3/9"


def test_jaccard_scan_values_and_pairs():
    a = [bp.shingles("abcdefg", 5), bp.shingles("zzzzzzzz", 5)]
    b = [bp.shingles("abcdefg", 5), bp.shingles("abcdexx", 5)]
    a_max, b_max, b_arg, _ = bp.jaccard_scan(a, b)
    assert a_max[0] == 1.0 and a_max[1] == 0.0
    assert b_arg[0] == 0 and 0 < b_max[1] < 1
    _, _, _, pairs = bp.jaccard_scan([a[0], a[0], a[1]], pair_threshold=0.8)
    assert pairs == [(0, 1)]  # diagonal ignored, each pair once


def test_task_type_rules_and_basis():
    tags = bp.tag_task_types("ต้องยื่นภายใน ๓๐ วัน", [{"id_section": "5", "text": "x", "has_reference": True}])
    assert tags == {"binding": ["source_reference"], "date": ["question"]}
    tags = bp.tag_task_types("อากรเท่าใด", [{"id_section": "ลักษณะแห่งตราสาร 3", "text": "x", "has_reference": False}])
    assert tags["annex"] == ["source_id"] and tags["table"] == ["source_id"]
    assert bp.tag_task_types("คำถามทั่วไป", [{"id_section": "1", "text": "x"}]) == {"plain": ["no_cue"]}
    assert bp.tag_task_types("ตามบัญชีท้ายพระราชบัญญัติ", [])["annex"] == ["question"]


def test_build_separates_families_and_records_provenance():
    res = bp.build(_rows(), PROV)
    c = res["counts"]
    assert all(res["checks"].values())
    # L1 is held out (relevant_laws); L4 is held out through reference_laws only
    assert c["heldout_laws"] == {"total": 2, "from_reference_laws_only": 1, "unmapped_law_name_mentions": 0}
    assert c["dev_exclusions"] == {"empty_question": 0, "heldout_family_quarantine": 1, "heldout_variant": 1,
                                   "no_positive_judgment": 1}
    dev, ho = res["splits"]["dev"], res["splits"]["heldout"]
    assert len(dev["requests"]) == 2 and len(ho["requests"]) == 2
    assert {s["law_code"] for s in dev["sources"]} == {"L2", "L3"}
    assert {s["law_code"] for s in ho["sources"]} == {"L1", "L4"}
    # one packet per law; the two-law record joins its rank-1 law and counts the other
    by_q = {r["question"]: r for r in dev["requests"]}
    two = by_q["ผู้ขอสมมุติต้องยื่นคำขอที่ใด"]
    j = next(x for x in dev["judgments"] if x["item_id"] == two["item_id"])
    assert two["packet_id"] == bp.law_family("dev", "L2") and j["gold_laws_in_other_packets"] == 1
    assert [g["source_id"] for g in j["relevant"]] == ["L2/5", "L3/9"]
    assert j["judged_nonrelevant"] == ["L2/6"] and c["dev_hard_negatives_dropped_heldout_law"] == 1
    assert j["task_types"]["binding"] == ["source_reference"]
    # Thai-digit section id resolves to the statute source
    k = next(x for x in dev["judgments"] if x["item_id"] == by_q["การจดแจ้งสมมุติต้องทำภายในกี่วัน"]["item_id"])
    assert k["relevant"][0]["in_statute_corpus"] and k["task_types"] == {"date": ["question"]}
    # labels and provenance
    assert {r["synthetic_label"] for r in dev["requests"]} == {"synthetic_question_real_source"}
    assert {r["synthetic_label"] for r in ho["requests"]} == {"real"}
    assert two["provenance"]["dataset"] == "fixture/wangchanx" and two["provenance"]["locator"] == "train[1]"
    assert all(x["independent_of_tested_policy"] for x in dev["judgments"] + ho["judgments"])
    assert all("dataset_gold" in x["judgment_origin"] for x in dev["judgments"] + ho["judgments"])
    # runtime requests carry no gold
    assert not any("relevant" in r or "task_types" in r for r in dev["requests"] + ho["requests"])


def test_overlap_audit_aggregates():
    a = bp.build(_rows(), PROV)["audit"]
    ccl = a["wangchanx_train_vs_nitibench_ccl"]
    assert ccl["exact"] == {"a_in_b": 0, "b_in_a": 0}          # trailing space differs
    assert ccl["normalised"] == {"a_in_b": 1, "b_in_a": 1}
    assert ccl["near_dup"]["0.8"]["b_with_match"] == 1
    assert ccl["sources"]["sections_shared"] == 1 and ccl["sources"]["laws_shared"] == 1
    assert a["wangchanx_train_vs_gazette_queries"]["normalised"]["b_in_a"] == 0
    assert a["nitibench_ccl_config_vs_noncfg_copy"]["normalised_multiset_equal"] is True


def test_dev_variants_share_one_packet():
    rows = _rows()
    rows["wangchanx"].append({"question": "การจดแจ้งสมมุติต้องทำภายในกี่วัน?", "positive_contexts": [_ctx("L2", "6")],
                              "hard_negative_contexts": []})
    dev = bp.build(rows, PROV)["splits"]["dev"]
    fams = {r["packet_id"] for r in dev["requests"] if r["question"].startswith("การจดแจ้งสมมุติ")}
    assert len(fams) == 1


def test_assert_aggregate_only():
    bp.assert_aggregate_only({"counts": {"dev": 3}})
    with pytest.raises(ValueError):
        bp.assert_aggregate_only({"law": "ป0001"})


def test_main_end_to_end(tmp_path):
    pa = pytest.importorskip("pyarrow")
    pq = pytest.importorskip("pyarrow.parquet")
    rows = _rows()
    data = tmp_path / "thai-data"
    datasets = {}
    for key, (repo, rel) in bp.INPUTS.items():
        folder = data / f"{repo.split('/')[1]}@00000000" / rel
        folder.parent.mkdir(parents=True, exist_ok=True)
        if key == "gazette_queries":
            pq.write_table(pa.table({"text": rows[key]}), folder)
        else:
            pq.write_table(pa.Table.from_pylist(rows[key]), folder)
        ds = datasets.setdefault(repo, {"repo": repo, "revision": "0" * 40, "license": "MIT", "files": []})
        ds["files"].append({"path": rel, "role": "X", "sha256": bp._sha256_file(folder)})
    (data / "MANIFEST.json").write_text(json.dumps({"datasets": list(datasets.values())}), encoding="utf-8")
    out, summ = tmp_path / "packets", tmp_path / "summary.json"
    assert bp.main(["--data", str(data), "--out", str(out), "--allow-no-pythainlp", "--summary-out", str(summ)]) == 0
    sums = dict(line.split("  ")[::-1] for line in (out / "SHA256SUMS").read_text().splitlines())
    assert "heldout/judgments.SEALED.jsonl" in sums and "dev/requests.jsonl" in sums
    for rel, h in sums.items():
        assert bp._sha256_file(out / rel) == h
    summary = json.loads(summ.read_text(encoding="utf-8"))
    assert summary["counts"]["dev"]["items"] == 2 and all(summary["checks"].values())
    with pytest.raises(SystemExit):  # one settle: refuses a non-empty output directory
        bp.main(["--data", str(data), "--out", str(out), "--allow-no-pythainlp"])
    # deterministic data files
    out2 = tmp_path / "packets2"
    bp.main(["--data", str(data), "--out", str(out2), "--allow-no-pythainlp"])
    for rel in sums:
        if rel != "MANIFEST.json":
            assert (out / rel).read_bytes() == (out2 / rel).read_bytes()
    # a tampered input is refused
    victim = next(data.glob("nitibench@*/data/tax-*.parquet"))
    victim.write_bytes(victim.read_bytes() + b"x")
    with pytest.raises(SystemExit):
        bp.main(["--data", str(data), "--out", str(tmp_path / "p3"), "--allow-no-pythainlp"])
