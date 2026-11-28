"""Generate FIXTURE data for the Market Window Dossier demo (contract mwd.dossier.v1).

Every molecule, company, number, date and digest written here is synthetic. The
molecule names are invented so that no fixture can be mistaken for a real
forecast or a real outcome. Real data from card PRD1 goes to product/demo/data/
and replaces these files without code changes.

Run from the repository root:  python product/demo/fixtures/make_fixtures.py
Standard library only.
"""

from __future__ import annotations

import hashlib
import json
import math
import random
from pathlib import Path

OUT = Path(__file__).resolve().parent
SEED = 20261128
CAPACITY_RATIO = 5  # review capacity: 1 in 5 candidates

CUTOFFS = [(2012, 12), (2013, 12), (2014, 12), (2015, 12), (2013, 24), (2014, 24)]

DOSSIER_MOLECULES = [
    ("lorvastatin", "Lorvastatin", ["tablet"], "Corvale Pharma"),
    ("brivosartan", "Brivosartan", ["tablet"], "Northgate Therapeutics"),
    ("zentrapine", "Zentrapine", ["tablet", "extended-release tablet"], "Aster Biopharma"),
    ("talcoxib", "Talcoxib", ["capsule"], "Kestrel Labs"),
    ("mirelukast", "Mirelukast", ["tablet", "chewable tablet", "oral granules"], "Halden Pharma"),
    ("dexoprazole", "Dexoprazole", ["delayed-release capsule"], "Meridian Rx"),
]

QUEUE_ONLY = [
    "aprenolol", "cortaglitin", "dulvaxetine", "fenoxitrel", "glimapride", "halvudine",
    "ibrastatin", "ketrolimus", "levoxinib", "mepratadine", "nolvastran", "oxacitabine",
    "pravuzole", "quinetiapine", "rilmotidine", "sertoxamine", "tebrinavir", "ursoparin",
    "vortaxetine",
]

SECTIONS = [
    ("decision", "หน้าตัดสินใจ", "Decision"),
    ("market", "ช่วงเวลาตลาด", "Market window"),
    ("competition", "การแข่งขัน", "Competition"),
    ("patents", "สิทธิบัตรและสิทธิผูกขาด", "Patents & exclusivity"),
    ("thai_asean", "ไทยและอาเซียน", "Thailand & ASEAN"),
    ("handoff", "ส่งต่อผู้ประเมิน FTO", "FTO hand-off"),
    ("references", "เอกสารอ้างอิง", "References"),
]


def fake_sha(*parts: object) -> str:
    return hashlib.sha256(("FIXTURE|" + "|".join(map(str, parts))).encode()).hexdigest()


def add_months(year: int, months: int) -> str:
    y = year + months // 12
    return f"{y}-01-01"


def pct(p: float) -> str:
    return f"{round(p * 100)}"


def make_queue(year: int, horizon: int, rng: random.Random) -> dict:
    names = [m[0] for m in DOSSIER_MOLECULES] + QUEUE_ONLY
    display = {m[0]: m[1] for m in DOSSIER_MOLECULES}
    rows = []
    for key in names:
        base = rng.betavariate(1.6, 3.2)
        if horizon == 24:
            base = min(0.97, base * 1.35 + 0.05)
        m3 = round(min(0.97, max(0.02, base)), 3)
        b1 = round(min(0.95, max(0.02, base * 0.7 + rng.uniform(-0.12, 0.18))), 3)
        event = rng.random() < (m3 * 0.85 + 0.04)
        rows.append({"key": key, "display_name": display.get(key, key.capitalize()),
                     "m3_p": m3, "b1_p": b1, "event": event})
    rows.sort(key=lambda r: (-r["m3_p"], r["key"]))
    slots = math.ceil(len(rows) / CAPACITY_RATIO)
    for i, r in enumerate(rows):
        r["in_queue"] = i < slots
    b1_top = {r["key"] for r in sorted(rows, key=lambda r: (-r["b1_p"], r["key"]))[:slots]}
    events = sum(r["event"] for r in rows)
    return {
        "schema": "mwd.queue.v1",
        "fixture": True,
        "cutoff": str(year),
        "as_of": f"{year}-01-01",
        "horizon_months": horizon,
        "jurisdiction": "US",
        "n_candidates": len(rows),
        "queue_size": slots,
        "capacity_ratio": f"1/{CAPACITY_RATIO}",
        "rows": [{k: r[k] for k in ("key", "display_name", "m3_p", "b1_p", "in_queue", "event")}
                 for r in rows],
        "capture": {
            "events_total": events,
            "m3_captured": sum(r["event"] for r in rows if r["in_queue"]),
            "b1_captured": sum(r["event"] for r in rows if r["key"] in b1_top),
        },
    }


def make_sources(key: str, year: int) -> list[dict]:
    prev = year - 1
    rows = [
        ("ob", "U.S. FDA", "Orange Book: Approved Drug Products with Therapeutic Equivalence Evaluations",
         f"{prev}-12 edition (FIXTURE)", f"{prev}-12-20", f"Patent and exclusivity data for {key}",
         "https://www.accessdata.fda.gov/scripts/cder/ob/"),
        ("df", "U.S. FDA", "Drugs@FDA data files", f"{prev}-12-18 snapshot (FIXTURE)", f"{prev}-12-18",
         "Applications and Submissions tables, ORIG/AP rows",
         "https://www.fda.gov/drugs/drug-approvals-and-databases/drugsfda-data-files"),
        ("p4", "U.S. FDA", "Paragraph IV Patent Certifications list", f"{prev}-11 update (FIXTURE)",
         f"{prev}-11-30", f"Row for {key}",
         "https://www.fda.gov/drugs/abbreviated-new-drug-application-anda/patent-certifications-and-suitability-petitions"),
        ("pv", "USPTO", "PatentsView granted patent data", f"{prev}-10 release (FIXTURE)", f"{prev}-10-01",
         "patent, application and cpc_current tables", "https://patentsview.org/download/data-download-tables"),
        ("sdud", "CMS", "State Drug Utilization Data", f"{prev - 1} annual file (FIXTURE)", f"{prev}-06-30",
         "National totals, units reimbursed",
         "https://www.medicaid.gov/medicaid/prescription-drugs/state-drug-utilization-data"),
        ("price", "U.S. FDA", "Generic competition and drug prices (median price by number of manufacturers)",
         "Scenario table (FIXTURE)", f"{prev}-05-01", "Table 1, ratio to brand price",
         "https://www.fda.gov/about-fda/center-drug-evaluation-and-research-cder/generic-competition-and-drug-prices"),
        ("thfda", "Thai FDA (อย.)", "ฐานข้อมูลทะเบียนตำรับยา / Drug registration search", "Lookup (FIXTURE)",
         None, f"Search term: {key}", "https://pertento.fda.moph.go.th/FDA_SEARCH_DRUG/SEARCH_DRUG/FRM_SEARCH_DRUG.aspx"),
        ("dip", "Department of Intellectual Property, Thailand", "DIP patent search", "Lookup (FIXTURE)", None,
         f"Search term: {key}", "https://patentsearch.ipthailand.go.th/"),
        ("aip", "ASEAN IP Register / WIPO PATENTSCOPE", "Patent family trace", "Lookup (FIXTURE)", None,
         f"Family search seeded from US patents for {key}", "https://patentscope.wipo.int/search/en/search.jsf"),
    ]
    out = []
    for sid, issuer, title, version, date, locator, url in rows:
        out.append({"id": f"{key}-{sid}", "issuer": issuer, "title": title, "version": version,
                    "public_date": date, "locator": locator, "url": url,
                    "sha256": fake_sha(key, sid, year), "retrieved": "2026-11-28"})
    return out


def make_dossier(mol: tuple, year: int, horizon: int, queue: dict, rng: random.Random) -> dict:
    key, name, forms, holder = mol
    rows = queue["rows"]
    idx = next(i for i, r in enumerate(rows) if r["key"] == key)
    row = rows[idx]
    p, b = row["m3_p"], row["b1_p"]
    s = lambda sid: f"{key}-{sid}"  # noqa: E731
    as_of = f"{year}-01-01"
    window_end = add_months(year, horizon)
    launch = f"{year + 3}-07-01"
    expiry = f"{year + rng.randint(0, 2)}-{rng.randint(1, 12):02d}-{rng.randint(1, 28):02d}"
    n_pat = rng.randint(2, 7)
    n_tent = rng.randint(0, 5)
    units = round(rng.uniform(4, 180), 1)
    p3 = round(min(0.95, p * rng.uniform(0.5, 0.9)) * 100)
    erosion = rng.choice([39, 44, 52])
    has_excl = rng.random() < 0.4
    thai_reg = rng.randint(0, 6)
    thai_lookup_ok = rng.random() < 0.6
    asean = rng.choice(["SG, MY", "SG, MY, VN", "SG", "PH, SG, TH"])
    pending_p4 = rng.random() < 0.5

    claims = [
        ("decision", "estimate", "known",
         f"M3 ประเมินโอกาสที่ยาสามัญรายแรกได้รับอนุมัติขั้นสุดท้ายภายใน {horizon} เดือน ที่ {pct(p)}% (B1: {pct(b)}%)",
         f"M3 estimates a {pct(p)}% chance that a first generic receives final approval within {horizon} months (B1: {pct(b)}%).",
         [s("ob"), s("df")]),
        ("decision", "assumption", "known",
         "สมมติว่าสิทธิบัตรสารออกฤทธิ์ฉบับหลักหมดอายุตามวันที่ใน Orange Book และไม่มีการขยายอายุเพิ่ม",
         "Assumes the main compound patent expires on its Orange Book date with no further term extension.",
         [s("ob")]),
        ("decision", "observed", "unknown" if pending_p4 else "known",
         "ยังไม่ได้ยืนยันว่ามีคดี Paragraph IV ค้างอยู่หรือไม่" if pending_p4 else "ไม่พบการรับรอง Paragraph IV ในรายการล่าสุดก่อนวันตัดข้อมูล",
         "Whether Paragraph IV litigation is pending is not yet verified." if pending_p4 else "No Paragraph IV certification appears in the last list before the cutoff.",
         [s("p4")]),
        ("market", "observed", "known",
         f"ปริมาณยาที่ Medicaid จ่ายในปี {year - 2}: {units} ล้านหน่วย",
         f"Medicaid reimbursed {units} million units in {year - 2}.",
         [s("sdud")]),
        ("market", "estimate", "known",
         "คาดว่าความต้องการยายังคงอยู่ถึงวันเปิดตัวที่วางแผน (ค่าพื้นฐาน naïve with drift)",
         "Demand is expected to persist to the planned launch date (naïve-with-drift baseline).",
         [s("sdud")]),
        ("market", "assumption", "known",
         f"สมมติวันเปิดตัวที่วางแผนไว้คือ {launch}",
         f"Assumes a planned launch date of {launch}.",
         []),
        ("competition", "observed", "known",
         f"ผู้ถือ NDA ต้นแบบ: {holder}",
         f"Reference NDA holder: {holder}.",
         [s("df")]),
        ("competition", "observed", "unknown" if n_tent == 0 else "known",
         "ยังไม่ทราบจำนวน ANDA ที่ได้รับอนุมัติเบื้องต้น" if n_tent == 0 else f"มี ANDA ที่ได้รับอนุมัติเบื้องต้น (tentative) {n_tent} รายการ",
         "The number of tentatively approved ANDAs is unknown." if n_tent == 0 else f"{n_tent} ANDAs hold tentative approval.",
         [s("df")]),
        ("competition", "estimate", "known",
         f"โอกาสมีผู้ยื่น ANDA ที่ได้รับอนุมัติอย่างน้อย 3 รายภายใน 36 เดือน: {p3}%",
         f"Chance of at least three approved ANDA applicants within 36 months: {p3}%.",
         [s("df"), s("ob")]),
        ("competition", "assumption", "known",
         f"สถานการณ์จำลอง: ราคาลดลงราว {erosion}% เมื่อมีผู้ผลิต 3 ราย (ค่ามัธยฐานของ FDA ไม่ได้ปรับให้เข้ากับยานี้)",
         f"Scenario: price falls about {erosion}% with three manufacturers (FDA median, not fitted to this product).",
         [s("price")]),
        ("patents", "observed", "known",
         f"มีสิทธิบัตร {n_pat} ฉบับใน Orange Book ฉบับหลักหมดอายุ {expiry}",
         f"{n_pat} patents are listed in the Orange Book; the main patent expires {expiry}.",
         [s("ob"), s("pv")]),
        ("patents", "observed", "known" if has_excl else "not_applicable",
         f"สิทธิผูกขาดทางการตลาด (exclusivity) สิ้นสุด {year}-{rng.randint(2, 11):02d}-15" if has_excl else "ไม่มีสิทธิผูกขาดทางการตลาดคงเหลือ",
         f"Regulatory exclusivity ends {year}-{rng.randint(2, 11):02d}-15." if has_excl else "No regulatory exclusivity remains.",
         [s("ob")]),
        ("patents", "estimate", "unknown",
         "ประเภทของสิทธิบัตรที่จำกัดการเข้าตลาด (สารออกฤทธิ์ สูตรตำรับ หรือวิธีใช้) ต้องตรวจจากเอกสารสิทธิบัตร",
         "The type of restricting patent (compound, formulation or method of use) must be checked against the patent documents.",
         [s("pv")]),
        ("thai_asean", "observed", "known" if thai_lookup_ok else "unknown",
         f"พบทะเบียนตำรับยาในไทย {thai_reg} ทะเบียน" if thai_lookup_ok else "ค้นทะเบียนตำรับยาของ อย. ไม่สำเร็จ จึงแสดงเป็นไม่ทราบ",
         f"{thai_reg} Thai drug registrations were found." if thai_lookup_ok else "The Thai FDA registration lookup failed, so the status is shown as unknown.",
         [s("thfda")]),
        ("thai_asean", "observed", "unknown",
         "ยังไม่พบครอบครัวสิทธิบัตรในฐานข้อมูลกรมทรัพย์สินทางปัญญา ต้องค้นซ้ำด้วยชื่อผู้ขอ",
         "No patent family was found in the DIP database; repeat the search by applicant name.",
         [s("dip")]),
        ("thai_asean", "observed", "known",
         f"ASEAN IP Register พบสมาชิกครอบครัวสิทธิบัตรใน {asean}",
         f"The ASEAN IP Register shows family members in {asean}.",
         [s("aip")]),
        ("thai_asean", "observed", "not_applicable",
         "การขยายอายุสิทธิบัตร (PTE) แบบสหรัฐฯ ไม่มีในระบบสิทธิบัตรไทย",
         "US-style patent term extension does not exist in the Thai patent system.",
         []),
        ("handoff", "assumption", "known",
         "รายการนี้เป็นข้อมูลประกอบการตัดสินใจ ผู้ประเมิน FTO ต้องยืนยันทุกข้อก่อนใช้",
         "This list is decision support; the FTO evaluator must confirm every item before use.",
         []),
    ]
    claim_rows = [{"id": f"c{i + 1:02d}", "section": sec, "text_th": th, "text_en": en,
                   "state": state, "kind": kind, "source_ids": src}
                  for i, (sec, kind, state, th, en, src) in enumerate(claims)]

    checklist = [
        ("FTO evaluator", "ตรวจสถานะและวันหมดอายุของสิทธิบัตรทุกฉบับใน Orange Book",
         "Check the status and expiry of every Orange Book patent.", [s("ob")]),
        ("FTO evaluator", "อ่านข้อถือสิทธิของสิทธิบัตรสูตรตำรับเทียบกับสูตรที่วางแผนไว้",
         "Read formulation patent claims against the planned formulation.", [s("pv")]),
        ("FTO evaluator", "ตรวจคดี Paragraph IV และคำพิพากษาที่เกี่ยวข้อง",
         "Check Paragraph IV litigation and related judgments.", [s("p4")]),
        ("R&D", "ยืนยันรูปแบบยาและความแรงที่จะใช้ศึกษาชีวสมมูล",
         "Confirm the dosage form and strength for the bioequivalence study.", [s("df")]),
        ("BD", "ทบทวนสมมติฐานวันเปิดตัวและราคาเทียบกับคู่แข่ง",
         "Review the launch-date and price assumptions against competitors.", [s("sdud"), s("price")]),
        ("FTO evaluator", "ค้นครอบครัวสิทธิบัตรในไทยกับกรมทรัพย์สินทางปัญญาซ้ำ",
         "Repeat the Thai patent family search with the DIP.", [s("dip")]),
    ]
    in_queue = row["in_queue"]
    next_th = ("ส่งเข้าคิวผู้ประเมิน FTO และเริ่มรายการตรวจข้อ 1–3" if in_queue
               else "ยังไม่อยู่ในคิว ติดตาม Orange Book ฉบับถัดไป")
    next_en = ("Send to the FTO evaluator queue and start checklist items 1–3." if in_queue
               else "Not in the queue; watch the next Orange Book edition.")
    sections = []
    for sid, th, en in SECTIONS:
        sec = {"id": sid, "title_th": th, "title_en": en}
        if sid == "decision":
            sec.update({"next_action_th": next_th, "next_action_en": next_en, "decisive_claim": "c02"})
        sections.append(sec)

    first_anda = None
    if row["event"]:
        month = rng.randint(1, horizon)
        y = year + (month - 1) // 12
        first_anda = f"{y}-{(month - 1) % 12 + 1:02d}-{rng.randint(1, 28):02d}"

    return {
        "schema": "mwd.dossier.v1",
        "fixture": True,
        "molecule": {"key": key, "display_name": name, "dosage_forms": forms},
        "as_of": as_of,
        "jurisdiction": "US",
        "forecast": {"horizon_months": horizon, "m3_p_entry": p, "b1_p_entry": b, "m3_rank": idx + 1,
                     "queue_size": queue["queue_size"], "in_queue": in_queue, "status": "DEVELOPMENT_ONLY"},
        "outcome_reveal": {"first_final_anda_date": first_anda, "window_end": window_end},
        "sections": sections,
        "claims": claim_rows,
        "sources": make_sources(key, year),
        "checklist": [{"id": f"k{i + 1}", "text_th": th, "text_en": en, "owner": owner, "source_ids": src}
                      for i, (owner, th, en, src) in enumerate(checklist)],
    }


def main() -> None:
    rng = random.Random(SEED)
    index = {"schema": "mwd.index.v1", "fixture": True,
             "note": "FIXTURE: synthetic molecules, numbers and dates for UI development only.",
             "jurisdiction": "US", "queues": [], "dossiers": [],
             "molecules": [{"key": m[0], "display_name": m[1]} for m in DOSSIER_MOLECULES]}
    for year, horizon in CUTOFFS:
        queue = make_queue(year, horizon, rng)
        qname = f"queues/queue-{year}-h{horizon}.json"
        (OUT / "queues").mkdir(exist_ok=True)
        (OUT / qname).write_text(json.dumps(queue, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        index["queues"].append({"cutoff": str(year), "as_of": queue["as_of"], "horizon_months": horizon,
                                "path": qname})
        for mol in DOSSIER_MOLECULES:
            d = make_dossier(mol, year, horizon, queue, rng)
            dname = f"dossiers/{mol[0]}-{year}-h{horizon}.json"
            (OUT / "dossiers").mkdir(exist_ok=True)
            (OUT / dname).write_text(json.dumps(d, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
            index["dossiers"].append({"key": mol[0], "cutoff": str(year), "horizon_months": horizon,
                                      "path": dname})
    (OUT / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"wrote {len(index['queues'])} queues and {len(index['dossiers'])} dossiers to {OUT}")


if __name__ == "__main__":
    main()
