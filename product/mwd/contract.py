"""Shared names and paths for dossier producers and consumers."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BENCH = ROOT / "loe-bench" / "data"
PRODUCT = ROOT / "docs" / "product"
DEMO = ROOT / "product" / "demo"
SCHEDULE = {
    12: ("2012-01-01", "2013-01-01", "2014-01-01", "2015-01-01"),
    24: ("2013-01-01", "2014-01-01"),
}
SECTIONS = (
    ("decision", "สรุปสำหรับฝ่ายพัฒนาธุรกิจและวิจัย", "BD and R&D decision"),
    ("market", "ช่วงเวลาของตลาด", "Market window"),
    ("competition", "ภาพการแข่งขัน", "Competitive landscape"),
    ("patents", "สิทธิบัตรและสิทธิผูกขาด", "Patents and exclusivities"),
    ("thai_asean", "ประเทศไทยและอาเซียน", "Thailand and ASEAN"),
    ("handoff", "รายการตรวจสอบสำหรับผู้ประเมิน FTO", "FTO evaluator checklist"),
    ("references", "เอกสารอ้างอิงและข้อมูลสำหรับตรวจซ้ำ", "References and reproducibility"),
)
DISCLAIMER = {
    "en": "This report summarizes dated market and patent evidence for planning. Commercial "
          "outcomes depend on the stated assumptions. Freedom to operate remains undetermined. "
          "Have qualified counsel assess the proposed product, intended activities and relevant "
          "claims in each jurisdiction.",
    "th": "รายงานนี้สรุปหลักฐานด้านตลาดและสิทธิบัตรตามวันที่ระบุเพื่อใช้วางแผน "
          "ผลทางธุรกิจขึ้นอยู่กับสมมติฐานที่ระบุไว้ ยังสรุปไม่ได้ว่าสามารถดำเนินการได้โดยไม่ละเมิดสิทธิ "
          "ให้ผู้เชี่ยวชาญกฎหมายประเมินผลิตภัณฑ์ที่เสนอ กิจกรรมที่วางแผน และข้อถือสิทธิที่เกี่ยวข้องในแต่ละเขตอำนาจ",
}


def read_json(path):
    return path and json.loads(Path(path).read_text(encoding="utf-8-sig"))


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
                    encoding="utf-8", newline="\n")
