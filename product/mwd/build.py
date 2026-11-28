"""Build the development-only dossier and queue JSON files."""

import argparse
from datetime import date
from pathlib import Path
import re
from urllib.parse import quote

from .contract import BENCH, DEMO, PRODUCT, SECTIONS, read_json, write_json
from .inputs import Evidence, PRIVATE, SCORE_FILES, scores, verify

FDA = "U.S. FDA"
REPO_URL = "https://github.com/siriponsri/patent-to-pilot/blob/7f3593b8/"
DRUGS_FDA = "https://www.fda.gov/drugs/drug-approvals-and-databases/drugsfda-data-files"
AMP_SHA256 = "5b748fa2eb20a4af86d1c28705add5e99a9351f58dbfaf6833736871c6610a4b"


def window_end(cutoff, horizon):
    return date(int(cutoff[:4]) + horizon // 12, 1, 1)


def ranked_queue(cutoff, horizon, rows, evidence, manifest):
    capacity = len(rows) // 5
    end = window_end(cutoff, horizon)
    day = date.fromisoformat(cutoff)
    eligible = {key for key, entity in evidence.entities.items() if entity.nda_first
                and entity.nda_first <= day and entity.flag_at("nme", day)
                and (entity.anda_first is None or entity.anda_first > day)}
    if {row["key"] for row in rows} != eligible:
        raise ValueError(f"Frozen roster does not match reconstructed development eligibility: {cutoff}, {horizon}")
    ranked = []
    for rank, row in enumerate(sorted(rows, key=lambda r: (-r["M3"], r["key"])), 1):
        key = row["key"]
        first = evidence.entities[key].anda_first
        event = first is not None and first <= end
        ranked.append(dict(key=key, display_name=evidence.names[key], m3_p=row["M3"],
                           b1_p=row["B1"], m3_rank=rank, in_queue=rank <= capacity, event=event))
    events = sum(row["event"] for row in ranked)
    captured = sum(row["in_queue"] and row["event"] for row in ranked)
    frozen = next(item for item in manifest["metrics"] if item["arm"] == "M3"
                  and item["cutoff"] == cutoff and item["horizon"] == horizon)
    if events != frozen["event_rows"]:
        raise ValueError(f"Frozen event denominator differs: {cutoff}, {horizon}")
    return dict(schema_version="mwd.queue.v1", as_of=cutoff, horizon_months=horizon,
                status="DEVELOPMENT_ONLY", window_end=end.isoformat(), queue_size=capacity,
                ranked_rows=ranked, tie_rule="M3 descending, key ascending",
                score_export_sha256=manifest["exports"][str(horizon)]["sha256"],
                capture=dict(eligible=len(ranked), events=events, captured=captured,
                             queued_without_event=capacity - captured, missed=events - captured,
                             recall=captured / events if events else None,
                             precision=captured / capacity if capacity else None))


def select_demo(queue, evidence):
    day = queue["as_of"]
    ranked = queue["ranked_rows"]
    supported = [r for r in ranked if r["in_queue"] and r["event"]
                 and evidence.listing(day, r["key"])[2] and evidence.challenges(day, r["key"])]
    false_alarm = next((r for r in ranked if r["in_queue"] and not r["event"]), None)
    missed = next((r for r in ranked if not r["in_queue"] and r["event"]), None)
    if len(supported) < 4 or false_alarm is None or missed is None:
        raise ValueError("The shared demo selection rule cannot yield six cases")
    return [{**{field: row[field] for field in ("key", "display_name", "m3_rank")}, "role": role}
            for row, role in zip([*supported[:4], false_alarm, missed],
                                 ["supported_event"] * 4 + ["false_alarm", "miss"], strict=True)]


class Dossier:
    def __init__(self):
        self.claims = []
        self.sources = {}
        self.checklist = []

    def source(self, id, issuer, title, version, public_date, locator, url=None, sha256=None,
               retrieved=None):
        source = dict(id=id, issuer=issuer, title=title, version=version, public_date=public_date,
                      locator=locator, url=url, sha256=sha256, retrieved=retrieved)
        if self.sources.setdefault(id, source) != source:
            raise ValueError(f"Conflicting source ID: {id}")
        return id

    def claim(self, id, section, th, en, refs, state="known", kind="observed", time_basis=None):
        claim = dict(id=id, section=section, text_th=th, text_en=en, source_ids=refs,
                     state=state, kind=kind)
        if time_basis:
            claim["time_basis"] = time_basis
        self.claims.append(claim)

    def task(self, id, th, en, owner, refs):
        self.checklist.append(dict(id=id, text_th=th, text_en=en, owner=owner, source_ids=refs))


def orange_source(report, evidence, id, identity, proof, edition, locator):
    raw = evidence.ob_entries[identity["sha256"]]
    return report.source(id, FDA, "Orange Book historical FDA ZIP", edition, proof["date"],
                         locator, proof["url"], identity["sha256"],
                         raw.get("retrieved_at_utc") or raw.get("retrieved_utc"))


def add_challenges(report, evidence, cutoff, key, fallback):
    from loe_bench.challenge_patents import normalize_patent_number

    challenged = {}
    witnesses = evidence.challenges(cutoff, key)
    for i, w in enumerate(witnesses, 1):
        ref = f"challenge-{i}"
        if w["source"] == "FDA_PIV":
            pinned = evidence.piv_entries[w["sha256"]]
            verify(evidence.root / "piv" / pinned["file"], w["sha256"])
            report.source(ref, FDA, "Paragraph IV certification list", w["version"],
                          evidence.piv_date(w), w["locator"], w["url"], w["sha256"],
                          pinned["retrieved_at_utc"])
            report.claim(ref, "patents", f"รายการ FDA ระบุวันที่ยื่น Paragraph IV {w['date']}",
                         f"FDA lists a Paragraph IV submission dated {w['date']}.", [ref])
            continue
        rai = read_json(BENCH / "E7_sources.json")["rai"]
        verify(evidence.root / "challenge" / rai["file"], w["sha256"])
        report.source(ref, "U.S. district court filings, indexed by Rai et al.",
                      "Patent litigation docket", w["version"], w["date"],
                      w["locator"], w["url"], w["sha256"])
        refs = [ref]
        linked = set()
        for j, match in enumerate(w["corroboration"]["matches"], 1):
            ob = match["orange_book"]
            proof = ob["availability_proof"]
            if proof["date"] > w["date"]:
                continue
            verify(evidence.root / "ob_editions" / ob["file"], ob["sha256"])
            match_ref = orange_source(report, evidence, f"{ref}-ob-{j}", ob, proof,
                                      ob["edition_date"], ob["locator"])
            refs.append(match_ref)
            number = normalize_patent_number(match["patent"])
            linked.add(number)
            challenged.setdefault(number, []).extend([ref, match_ref])
        numbers = ", ".join(sorted(linked))
        report.claim(ref, "patents",
                     f"คดี {w['document_id']} ยื่นวันที่ {w['date']} เชื่อมโยงกับสิทธิบัตร {numbers} "
                     "โดยอาศัยสมมติฐานว่าเปิดเผยในวันยื่น ยังไม่ทราบประเภทและผลคดีจากหลักฐานนี้",
                     f"Docket {w['document_id']}, filed {w['date']}, links to patent(s) {numbers}. "
                     "The replay assumes public access on filing. Case type and disposition require verification.",
                     refs)
    if not witnesses:
        scope = report.source("challenge-scope", "LOE-Bench", "Development challenge search scope",
                              "E7/E7b development", None, "E7b receipt, admission rules and limitations",
                              REPO_URL + "docs/loe-bench/receipts/E7b.md")
        report.claim("challenge-unknown", "patents", "ยังไม่มีหลักฐานการท้าทายที่เข้าเกณฑ์ในชุดที่ตรวจ",
                     "Challenge status is unknown within the searched evidence.", [scope, fallback], "unknown")
    return challenged


def add_listings(report, evidence, cutoff, key, fallback, *, challenge_adder=add_challenges):
    from loe_bench.challenge_patents import normalize_patent_number
    from loe_bench.common import add_months

    edition, products, patents, exclusivities = evidence.listing(cutoff, key)
    challenged = challenge_adder(report, evidence, cutoff, key, fallback)
    if not edition:
        report.claim("listings-unknown", "patents", "ยังไม่มีฉบับ Orange Book ที่ยืนยันว่ามีเผยแพร่ทันวันตัดข้อมูล",
                     "Orange Book listings are unknown without an edition proven public by cutoff.",
                     [fallback], "unknown")
        return [], [fallback]

    identity, proof, stamp = edition
    names = sorted({p["form_route"] for p in products if p["form_route"]})
    base = orange_source(report, evidence, "ob-edition", identity, proof, stamp,
                         ", ".join(p["locator"] for p in products) or "products.txt, exact linked moiety lookup")
    if date.fromisoformat(stamp) < add_months(date.fromisoformat(cutoff), -6):
        report.claim("stale-edition", "patents",
                     f"ฉบับล่าสุดที่ยืนยันว่าเปิดเผยทันวันตัดข้อมูลคือ {stamp} ซึ่งเก่ากว่า 6 เดือน",
                     f"The latest proven edition ({stamp}) is over six months old at cutoff.", [base])
    if names:
        report.claim("forms", "competition", f"รูปแบบยาและวิธีให้ยาที่เชื่อมโยงได้ในฉบับ {stamp}: {', '.join(names)}",
                     f"Linked dosage forms and routes in the {stamp} edition: {', '.join(names)}.", [base])
    for i, product in enumerate(products, 1):
        if product["approval_date"] is None:
            continue
        ref = orange_source(report, evidence, f"ob-approval-{i}", identity, proof, stamp, product["locator"])
        day = product["approval_date"].isoformat()
        item = f"NDA {product['appl_no']} / {product['product_no']}"
        report.claim(ref, "competition", f"Orange Book ระบุวันที่อนุมัติ {item} เป็น {day}",
                     f"Orange Book lists approval of {item} on {day}.", [ref])
    if not patents or not exclusivities:
        report.claim("protection-gaps", "patents",
                     f"ฉบับ {stamp} พบรายการสิทธิบัตร {len(patents)} แถว และสิทธิผูกขาด {len(exclusivities)} แถว "
                     "การตรวจสอบกับทะเบียนและเอกสารต้นทางยังจำเป็น",
                     f"The linked edition contains {len(patents)} patent rows and {len(exclusivities)} "
                     "exclusivity rows. Verify coverage against primary records.", [base],
                     "known" if products else "unknown")

    def priority(p):
        return (0 if p["drug_substance"] else 1 if p["drug_product"] else 2 if p["use_code"] else 3,
                p["expiry"] or date.max, normalize_patent_number(p["patent_no"]) not in challenged,
                p["patent_no"], p["appl_no"], p["product_no"])

    for i, p in enumerate(sorted(patents, key=priority), 1):
        ref = orange_source(report, evidence, f"patent-{i}", identity, proof, stamp, p["locator"])
        expiry = p["expiry"].isoformat() if p["expiry"] else None
        number = p["patent_no"]
        item = f"US {number}, NDA {p['appl_no']} / {p['product_no']}"
        listed = (f"DS={int(p['drug_substance'])}, DP={int(p['drug_product'])}, "
                  f"use={p['use_code'] or '∅'}, delist={int(p['delist'])}")
        report.claim(ref, "patents", f"{item} · {listed} · วันหมดอายุที่ระบุ {expiry or 'ไม่ทราบ'}",
                     f"{item} · {listed} · listed expiry {expiry or 'unknown'}.", [ref])
        if not any(task["id"] == f"check-us-{number}" for task in report.checklist):
            refs = list(dict.fromkeys([ref, *challenged.get(normalize_patent_number(number), ())]))
            report.task(f"check-us-{number}", f"ตรวจข้อถือสิทธิและสถานะของ US {number} เทียบกับผลิตภัณฑ์ที่จะพัฒนา",
                        f"Compare claims and verified status of US {number} with the proposed product.",
                        "FTO evaluator", refs)
        else:
            task = next(t for t in report.checklist if t["id"] == f"check-us-{number}")
            task["source_ids"].append(ref)
    for i, x in enumerate(exclusivities, 1):
        ref = orange_source(report, evidence, f"exclusivity-{i}", identity, proof, stamp, x["locator"])
        expiry = x["expiry"].isoformat() if x["expiry"] else None
        item = f"{x['code']}, NDA {x['appl_no']} / {x['product_no']}"
        report.claim(ref, "patents", f"สิทธิผูกขาด {item} · วันสิ้นสุดที่ระบุ {expiry or 'ไม่ทราบ'}",
                     f"Exclusivity {item} · listed end {expiry or 'unknown'}.", [ref])
    return names, [base]


EVP_OWNERS = {"Patent reviewer": "FTO evaluator", "Thai patent reviewer": "FTO evaluator",
              "Thai regulatory reviewer": "R&D"}


def evidence_path(key):
    # EVP writes the URL-encoded key because Windows reserves ":"; a filename-safe slug also works.
    slug = re.sub(r"[^A-Za-z0-9_-]+", "-", key).strip("-")
    for name in (key, quote(key, safe=""), slug):
        path = PRODUCT / "evidence" / f"{name}.json"
        if path.is_file():
            return path
    return None


def add_thai(report, key, day):
    path = evidence_path(key)
    if path:
        data = read_json(path)
        if "key" in data and data["key"] != key:
            raise ValueError(f"Thai evidence identity differs: {path.name}")
        sources = {source["id"]: source for source in data["sources"]}
        cutoff = date.fromisoformat(day)

        def as_of(refs):
            # Merge only items whose every source was public on or before the dossier date.
            dates = [sources[ref]["public_date"] for ref in refs]
            return all(d is None or date.fromisoformat(d) <= cutoff for d in dates)

        # EVP patent-section claims restate Orange Book rows the builder already lists for each
        # cutoff, and its restriction review uses documents from the outcome window, so only the
        # Thai/ASEAN claims and the ranked patent and Thai checklist items are merged.
        claims = [c for c in data["claims"] if c["section"] == "thai_asean" and as_of(c["source_ids"])]
        tasks = [t for t in data.get("checklist", []) if t["id"].startswith(("check-", "th-"))
                 and as_of(t["source_ids"])]
        used = {ref for item in claims + tasks for ref in item["source_ids"]}
        if claims:
            for id in sorted(used, key=list(sources).index):
                report.source(**sources[id])
            for claim in claims:
                report.claim(claim["id"], claim["section"], claim["text_th"], claim["text_en"],
                             claim["source_ids"], claim["state"], claim["kind"], claim.get("time_basis"))
            for task in tasks:
                # mwd.dossier.v1 allows three owners; EVP's patent reviewers hand to the FTO evaluator.
                owner = EVP_OWNERS.get(task["owner"], task["owner"])
                report.task(task["id"], task["text_th"], task["text_en"], owner, task["source_ids"])
            return sorted({ref for claim in claims for ref in claim["source_ids"]}, key=list(sources).index)
    dip = report.source("dip-lookup", "Thailand Department of Intellectual Property",
                        "Patent search portal", "Lookup route", None, "Patent search form",
                        "https://patentsearch.ipthailand.go.th")
    report.claim("thai-status", "thai_asean", "ยังไม่ทราบสถานะในไทย โปรดตรวจที่กรมทรัพย์สินทางปัญญา",
                 "Thai status unknown: verify at DIP.", [dip], "unknown")
    return [dip]


def build_dossier(queue, row, evidence, manifest, demand):
    day, horizon, key = queue["as_of"], queue["horizon_months"], row["key"]
    report = Dossier()
    score = report.source("freeze-score", "LOE-Bench", "Frozen native development scores",
                          manifest["implementation_sha"], None,
                          f"{SCORE_FILES[horizon]} $.rows[cutoff={day}, key={key}].{{M3,B1}}",
                          REPO_URL + "loe-bench/data/FREEZE_DEV_SCORES_MANIFEST.json",
                          manifest["exports"][str(horizon)]["sha256"])
    scope = "อยู่ในคิว" if row["in_queue"] else "อยู่นอกคิว"
    review = "in the queue" if row["in_queue"] else "outside the queue"
    report.claim("queue", "decision",
                 f"{scope}ตรวจทบทวน · ลำดับ {row['m3_rank']} จาก {len(queue['ranked_rows'])} รายการ "
                 f"และรับตรวจได้ {queue['queue_size']} รายการ ใช้ทบทวนข้อมูลก่อนตัดสินใจพัฒนา",
                 f"Rank {row['m3_rank']} of {len(queue['ranked_rows'])}, {review} of {queue['queue_size']} slots. "
                 "Use the evidence to plan the next development review.", [score], kind="estimate")
    report.claim("entry", "market",
                 f"โอกาสได้รับอนุมัติ ANDA ขั้นสุดท้ายครั้งแรกภายใน {horizon} เดือน "
                 f"M3 {row['m3_p']:.1%} และเกณฑ์เทียบตามอายุยา B1 {row['b1_p']:.1%} "
                 "วันอนุมัติและวันเริ่มจำหน่ายเป็นคนละเหตุการณ์",
                 f"Estimated first final ANDA approval within {horizon} months: M3 {row['m3_p']:.1%}; "
                 f"drug-age baseline B1 {row['b1_p']:.1%}. Approval and marketing are separate events.",
                 [score], kind="estimate")
    fda = report.source("anda-at-risk", FDA, "Drugs@FDA original final ANDA approvals",
                        evidence.s0["fetched_at_utc"], None,
                        f"df_anda.jsonl, exact development active-moiety {key}; ORIG/AP through {day}",
                        DRUGS_FDA, evidence.development_anda_pin, evidence.s0["fetched_at_utc"])
    report.claim("approved-applicants", "competition",
                 "พบผู้ยื่น ANDA ที่ได้รับอนุมัติขั้นสุดท้ายก่อนหรือ ณ วันตัดข้อมูล 0 ราย "
                 "ในกลุ่มตัวยาสำคัญที่เชื่อมโยงได้ จำนวนผู้ผลิตที่วางจำหน่ายยังไม่ทราบ",
                 "Zero distinct final ANDA applicants in linked records through the cutoff, as required "
                 "for eligibility. Marketed producer count is unknown.", [fda, score])

    amp = report.source("fda-amp-2019", FDA, "Generic Competition and Drug Prices",
                        "December 2019 (month precision)", "2019-12-31",
                        "PDF p. 9, median AMP ratio, producer counts 2–4",
                        "https://www.fda.gov/media/133509/download#page=9", AMP_SHA256)
    report.claim("price-scenario", "market",
                 "สมมติฐานย้อนหลังจาก FDA ปี 2019 หากมีผู้ผลิตยาสามัญวางจำหน่าย 2, 3 หรือ 4 ราย "
                 "ราคาเฉลี่ยผู้ผลิต (AMP) ของยาสามัญเท่ากับ 46.5%, 32.2% หรือ 21.2% "
                 "ของ AMP ยาต้นแบบก่อนมียาสามัญตามลำดับ ยังไม่มีราคาอ้างอิงเพื่อคำนวณราคาของยานี้",
                 "Retrospective scenario from the FDA's 2019 study. With 2, 3 or 4 marketed generic producers, "
                 "assume generic average manufacturer price (AMP) of 46.5%, 32.2% or 21.2% of the pre-entry "
                 "brand AMP, respectively. The implied price is unknown without a documented brand AMP.",
                 [amp], kind="assumption", time_basis="retrospective_scenario")
    demand.add_claim(report, day, key)
    if row["in_queue"]:
        report.task("review-spec", "ระบุรูปแบบยา ความแรง ข้อบ่งใช้ และวันเปิดตัวเป้าหมาย",
                    "Specify dosage form, strength, indication and target launch date.", "R&D", [score])
    else:
        report.task("review-spec", "ระบุรูปแบบยา ความแรง และข้อบ่งใช้ก่อนประเมินโอกาสอีกครั้ง",
                    "Specify dosage form, strength and indication before revisiting the opportunity.", "R&D", [score])
    dosage_forms, listing_refs = add_listings(report, evidence, day, key, fda)
    thai_refs = add_thai(report, key, day)
    report.claim("fto-scope", "handoff",
                 "ใช้ประกอบการตัดสินใจ ยังไม่มีข้อสรุป FTO หรือความเห็นทางกฎหมาย",
                 "Decision support. FTO remains undetermined and requires a qualified legal opinion.",
                 listing_refs + thai_refs, "unknown")
    report.task("verify-national", "ตรวจตระกูลสิทธิบัตร ข้อถือสิทธิ และสถานะในแต่ละประเทศที่วางแผนจำหน่าย",
                "Verify patent family, claims and legal status in each intended jurisdiction.", "FTO evaluator",
                listing_refs + thai_refs)
    report.task("verify-price", "หา AMP ยาต้นแบบและตรวจผู้ผลิตที่ขายจริง รวมทั้งความต้องการ ณ วันเปิดตัว",
                "Document brand AMP, marketed producers and demand at the intended launch date.", "BD", [amp])
    report.claim("reproduce", "references",
                 "คะแนนและลำดับใช้ไฟล์ development ที่ตรึงไว้ หากคะแนน M3 เท่ากัน ให้เรียงตามรหัสตัวยา",
                 "Reproduce the ranking from frozen development scores, breaking M3 ties by ascending key.",
                 [score], kind="estimate")

    first = evidence.approvals[key][0] if row["event"] else None
    reveal_refs = []
    if first:
        ref = report.source("outcome", FDA, "Drugs@FDA final original ANDA approval",
                            first.evidence.version, first.approved.isoformat(), first.evidence.locator,
                            DRUGS_FDA, first.evidence.sha256, evidence.s0["fetched_at_utc"])
        reveal_refs.append(ref)
    return dict(schema_version="mwd.dossier.v1", molecule=dict(key=key, display_name=row["display_name"],
                dosage_forms=dosage_forms), as_of=day, jurisdiction="US",
                forecast=dict(horizon_months=horizon, m3_p_entry=row["m3_p"], b1_p_entry=row["b1_p"],
                              m3_rank=row["m3_rank"], queue_size=queue["queue_size"],
                              in_queue=row["in_queue"], status="DEVELOPMENT_ONLY"),
                outcome_reveal=dict(first_final_anda_date=first.approved.isoformat() if first else None,
                                    window_end=queue["window_end"], source_ids=reveal_refs),
                sections=[dict(id=id, title_th=th, title_en=en) for id, th, en in SECTIONS],
                claims=report.claims, sources=list(report.sources.values()), checklist=report.checklist)


def main():
    from .audit import audit_dossier
    from .demand import Demand

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--private-root", type=Path, default=PRIVATE)
    parser.add_argument("--data-dir", type=Path, default=DEMO / "data")
    parser.add_argument("--molecules", type=Path, default=PRODUCT / "DEMO_MOLECULES.json")
    args = parser.parse_args()
    rows, manifest = scores(args.private_root)
    evidence = Evidence(args.private_root, {r["key"] for group in rows.values() for r in group})
    queues = {cell: ranked_queue(*cell, data, evidence, manifest) for cell, data in rows.items()}
    selection = select_demo(queues["2014-01-01", 24], evidence)
    included = {row["key"] for row in selection}
    print("Demo molecules:", ", ".join(row["display_name"] for row in selection), flush=True)
    demand = Demand(args.private_root, evidence.linker, included)
    amp_file = args.private_root / "medicaid_sdud" / "FDA-Generic-Competition-2019.pdf"
    verify(amp_file, AMP_SHA256)
    dossiers = {}
    for (day, horizon), queue in queues.items():
        for row in queue["ranked_rows"]:
            if row["key"] in included:
                dossier = build_dossier(queue, row, evidence, manifest, demand)
                result = audit_dossier(dossier)
                if result["errors"]:
                    raise ValueError(f"Traceability failed for {row['key']} {day} {horizon}: {result['errors']}")
                slug = row["key"].replace(":", "-").replace("|", "--").replace(" ", "-")
                dossiers[f"{slug}-{day}-{horizon}m"] = dossier
    write_json(args.molecules, selection)
    for (day, horizon), queue in queues.items():
        write_json(args.data_dir / f"queue-{day}-{horizon}m.json", queue)
    for stem, dossier in dossiers.items():
        write_json(args.data_dir / f"dossier-{stem}.json", dossier)
    print(f"Built {len(dossiers)} dossiers and {len(queues)} queues.")


if __name__ == "__main__":
    main()
