"""Assemble C6/C7 fragments from dated development evidence and reviewed lookups."""
from collections import defaultdict
from datetime import date, datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import re
from urllib.parse import quote

from bs4 import BeautifulSoup

from acquire import OUT
from select_cases import CUTOFF

DEST = Path(__file__).resolve().parents[2] / "docs/product/evidence"
ROLES = [("drug_substance", "drug substance", "ตัวยาสำคัญ"),
         ("drug_product", "drug product", "ผลิตภัณฑ์ยา"),
         ("use_code", "method of use", "วิธีใช้ยา")]


def load(name):
    return json.loads((OUT / name).read_text(encoding="utf-8-sig"))


def source(identifier, issuer, title, version, public_date, locator, url, digest, retrieved):
    return dict(id=identifier, issuer=issuer, title=title, version=version, public_date=public_date,
                locator=locator, url=url, sha256=digest, retrieved=retrieved)


def grant(number):
    return number.removesuffix("*PED").strip()


def products(row):
    return f"NDA {row['appl_no']}/{row['product_no']}"


def family_targets(groups, challenged):
    """Trace the first-ranked grant, all substance grants, and patent-linked challenges."""
    return {number for i, (number, rows) in enumerate(groups) if i == 0 or number in challenged
            or any(row["drug_substance"] for row in rows)}


def ranked_patents(case):
    groups = defaultdict(list)
    for row in case["patents"]:
        groups[grant(row["patent_no"])].append(row)
    challenged = {
        hit["patent"] for witness in case["witnesses"]
        if witness["source"] == "RAI_OB_PATENT" for hit in witness["corroboration"]["matches"]
    }

    def rank(item):
        number, rows = item
        scope = min((i for row in rows for i, (field, _, _) in enumerate(ROLES) if row[field]), default=3)
        distances = [(date.fromisoformat(row["expiry"]) - CUTOFF).days for row in rows
                     if row["expiry"] and not row["patent_no"].endswith("*PED")]
        expiry = min(((days < 0, abs(days)) for days in distances), default=(True, date.max.toordinal()))
        return scope, expiry, number not in challenged, number

    return sorted(groups.items(), key=rank), challenged


def read_family(number, log):
    attempt = log[f"family:{number}"]
    lookup = log.get(f"family-alt:{number}", attempt)
    if not lookup.get("file"):
        return {"id": lookup["id"], "state": "unknown", "ids": [], "thai": [],
                "en": f"US {number}: family identifiers remain unverified.",
                "th": f"ยังยืนยันเลขอ้างอิงตระกูลสิทธิบัตรสหรัฐฯ เลขที่ {number} ไม่ได้"}
    page = BeautifulSoup((OUT / lookup["file"]).read_bytes(), "html.parser")
    published = page.select_one('[itemprop="publicationDate"]')
    priority_rows = page.select('[itemprop="appsClaimingPriority"]')
    priority_ids = [row.select_one("td").get_text(" ", strip=True) for row in priority_rows if row.select_one("td")]
    family_text = " ".join(node.get_text(" ", strip=True) for node in page.select('[itemprop="countryStatus"]'))
    wo = sorted(set(re.findall(r"\bWO[0-9]{8,13}[A-Z][0-9]?\b", family_text)))
    thai = sorted(set(re.findall(r"\bTH[0-9]{5,14}[A-Z]?[0-9]?\b", family_text)))
    asean = sorted(set(re.findall(r"\b(?:BN|KH|ID|LA|MY|MM|PH|SG|VN)[A-Z0-9-]*[0-9][A-Z0-9-]*\b",
                                  family_text)))
    identifiers = list(dict.fromkeys(value for value in [*priority_ids, *wo] if value))
    return dict(id=lookup["id"], date=published.get("content") or published.get_text(strip=True) if published else None,
                locator="Applications Claiming Priority; Country Status (WO and ASEAN rows)",
                ids=identifiers, thai=thai, asean=asean, state="known" if identifiers else "unknown",
                en=f"US {number}. Priority applications: {', '.join(priority_ids) or 'none returned'}. "
                   f"WO publications: {', '.join(wo) or 'none returned'}. "
                   f"TH publications in this index: {', '.join(thai) or 'none returned'}. "
                   f"Other ASEAN references in this index: {', '.join(asean) or 'none returned'}.",
                th=f"สิทธิบัตรสหรัฐฯ เลขที่ {number} คำขอที่ใช้อ้างสิทธิวันยื่นครั้งแรก: {', '.join(priority_ids) or 'ไม่พบในดัชนี'} "
                   f"เลขประกาศ WO: {', '.join(wo) or 'ไม่พบในดัชนี'} "
                   f"เลขประกาศ TH ในดัชนีนี้: {', '.join(thai) or 'ไม่พบ'} "
                   f"เลขอ้างอิงจากประเทศอาเซียนอื่นในดัชนีนี้: {', '.join(asean) or 'ไม่พบ'}")


def build(case, edition, reviews, log, piv_records, rai, fda_manifest):
    sources, claims, items = [], [], []

    def claim(identifier, section, en, th, refs, state="known"):
        claims.append(dict(id=identifier, section=section, text_th=th, text_en=en,
                           state=state, kind="observed", source_ids=refs))

    def checklist(identifier, en, th, owner, refs):
        items.append(dict(id=identifier, text_th=th, text_en=en, owner=owner, source_ids=refs))

    def add_lookup(identifier, locator=None, public_date=None):
        lookup = log[identifier]
        src_id = identifier.replace(":", "-")
        if not any(item["id"] == src_id for item in sources):
            sources.append(source(src_id, lookup["issuer"], lookup["query"],
                                  lookup["retrieved"][:10], public_date,
                                  locator or f"{lookup['access']}: {lookup['result']}", lookup["url"],
                                  lookup.get("sha256"), lookup["retrieved"]))
        return src_id

    def add_ob(identifier, locators):
        sources.append(source(identifier, "US FDA", "Orange Book data files", edition["edition_date"],
                              "2013-09-06", ", ".join(locators), edition["wayback_url"],
                              edition["sha256"], edition["retrieved_utc"]))
        return identifier

    presentations = defaultdict(set)
    for row in case["products"]:
        presentations[row["trade_name"]].add(row["ingredient"])
    ref = add_ob("ob-products", [row["locator"].replace("products data", "products.txt data")
                                 for row in case["products"]])
    scope = " / ".join(f"{name} ({', '.join(sorted(ingredients))})"
                       for name, ingredients in sorted(presentations.items()))
    claim("ob-product-scope", "patents", f"Archived presentation scope for the benchmark key: {scope}.",
          f"รายการผลิตภัณฑ์ที่จับคู่กับคีย์ของชุดข้อมูลใน Orange Book ฉบับเก็บถาวร: {scope}", [ref])

    groups, challenged = ranked_patents(case)
    patent_sources = {}
    for rank, (number, rows) in enumerate(groups, 1):
        ref = add_ob(f"ob-{number}", [row["locator"].replace("patent data", "patent.txt data") for row in rows])
        patent_sources[number] = ref
        flags_th, flags_en = [], []
        for row in rows:
            suffix = "*PED" if row["patent_no"].endswith("*PED") else ""
            flags = f"DS={'Y' if row['drug_substance'] else '–'}, DP={'Y' if row['drug_product'] else '–'}, "
            flags += f"use code={row['use_code'] or '–'}"
            flags += ", delist requested" if row["delist"] else ""
            flags_en.append(f"{products(row)}: {number}{suffix}, {row['expiry'] or 'date unavailable'} ({flags})")
            flags_th.append(f"{products(row)}: {number}{suffix} วันที่ตามรายการ {row['expiry'] or 'ไม่ปรากฏ'} "
                            f"({flags.replace('use code', 'รหัสการใช้').replace('delist requested', 'มีคำขอถอนรายการ')})")
        claim(f"patent-{number}", "patents", "Orange Book: " + " / ".join(flags_en),
              "รายการใน Orange Book: " + " / ".join(flags_th), [ref])
        checklist(f"check-{rank:02d}", f"Check first #{rank}: US {number}. Review the listed scope and dates for the intended presentation.",
                  f"ลำดับ {rank}: ตรวจขอบเขตและวันที่ในรายการสิทธิบัตรสหรัฐฯ เลขที่ {number} ให้ตรงกับรูปแบบและความแรงของยาที่จะพัฒนา",
                  "Patent reviewer", [ref])
    if not groups:
        ref = add_ob("ob-patent-coverage", ["patent.txt; join by NDA/product against products.txt"])
        claim("patent-coverage", "patents", "The archived edition returned no linked patent rows.",
              "ฉบับที่เก็บถาวรไม่พบรายการสิทธิบัตรที่จับคู่กับทะเบียนยาที่ศึกษา", [ref], "unknown")
    for row in case["exclusivities"]:
        identifier = "ob-excl-" + row["locator"].split()[-1]
        add_ob(identifier, [row["locator"].replace("exclusivity data", "exclusivity.txt data")])
        claim(identifier, "patents", f"{products(row)} lists exclusivity {row['code']} through {row['expiry']}.",
              f"{products(row)} ระบุสิทธิผูกขาดตามข้อกำหนดของ FDA รหัส {row['code']} ถึงวันที่ {row['expiry']}", [identifier])
    if not case["exclusivities"]:
        identifier = add_ob("ob-excl-coverage", ["exclusivity.txt; join by NDA/product against products.txt"])
        claim(identifier, "patents", "The archived edition returned no linked exclusivity rows.",
              "ฉบับที่เก็บถาวรไม่พบรายการสิทธิผูกขาดที่จับคู่กับทะเบียนยาที่ศึกษา", [identifier], "unknown")

    if not any(witness["source"] == "FDA_PIV" for witness in case["witnesses"]):
        edition_piv = max((record for record in piv_records if record["parse_status"] == "PASS"
                           and record.get("wayback_timestamp") and record["wayback_timestamp"][:8] <= "20140101"
                           and record["version_date"] <= "2014-01-01"),
                          key=lambda record: (record["version_date"], record["wayback_timestamp"]))
        capture = edition_piv["wayback_timestamp"]
        sources.append(source("piv-coverage", "US FDA", "Paragraph IV certifications list", edition_piv["version_date"],
                              f"{capture[:4]}-{capture[4:6]}-{capture[6:8]}",
                              "Archived FDA table, version metadata and product matching",
                              edition_piv["wayback_url"], edition_piv["sha256"], edition_piv["retrieved_at_utc"]))
        claim("piv-coverage", "patents", "The historical FDA list provided no admitted dated PIV row at the cutoff. The last usable archived list was stale at the cutoff.",
              "ณ วันตัดข้อมูล ยังไม่มีแถวข้อมูลจากบัญชี Paragraph IV ของ FDA ที่ผ่านเกณฑ์การรับหลักฐาน บัญชีฉบับเก็บถาวรล่าสุดที่อ่านได้เก่าเกินเกณฑ์ ณ วันดังกล่าว",
              ["piv-coverage"], "unknown")
    for index, witness in enumerate(case["witnesses"], 1):
        identifier = f"challenge-{index:02d}"
        day = witness["date"]
        ref_ids = [identifier]
        if witness["source"] == "FDA_PIV":
            captured = next(record for record in piv_records if record["wayback_url"] == witness["url"])
            public_date = captured["wayback_timestamp"]
            public_date = f"{public_date[:4]}-{public_date[4:6]}-{public_date[6:8]}"
            sources.append(source(identifier, "US FDA", "Paragraph IV certifications list", witness["version"],
                                  public_date, witness["locator"], witness["url"], witness["sha256"],
                                  captured["retrieved_at_utc"]))
            en = f"The FDA lists a first Paragraph IV submission on {day} for a matching drug presentation. The row gives no patent number."
            th = f"FDA ระบุการยื่นคำรับรองตาม Paragraph IV ครั้งแรกเมื่อ {day} สำหรับรูปแบบยาที่จับคู่ได้ โดยแถวข้อมูลนี้ไม่ได้ระบุเลขที่สิทธิบัตร"
        else:
            matches = witness["corroboration"].get("matches", [])
            numbers = ", ".join(sorted({hit["patent"] for hit in matches}))
            ref_ids += [patent_sources[n] for n in sorted({hit["patent"] for hit in matches}) if n in patent_sources]
            sources.append(source(identifier, "Rai et al.", "District court patent litigation dataset", witness["version"],
                                  "2021-06-10", witness["locator"], witness["url"], witness["sha256"],
                                  rai.get("retrieved_utc")))
            en = f"Rai records docket {witness['document_id']}, filed {day}."
            th = f"ชุดข้อมูล Rai ระบุคดี {witness['document_id']} ยื่นเมื่อ {day}"
            if numbers:
                en += f" The patent-number join at filing identifies US {numbers}."
                th += f" จับคู่เลขที่สิทธิบัตร ณ วันยื่นคดีได้เป็น {numbers}"
            proof = witness["corroboration"].get("case_type_proof") or witness["corroboration"]
            if proof.get("sha256"):
                proof_id = identifier + "-proof"
                sources.append(source(proof_id, proof.get("issuer", "Court record"), proof.get("document", "Corroborating document"),
                                      proof.get("version"), proof.get("public_date"), proof.get("locator"),
                                      proof.get("url"), proof["sha256"], proof.get("retrieved_utc")))
                ref_ids.append(proof_id)
        claim(identifier, "patents", en, th, ref_ids)

    review = reviews[case["key"]]
    for note in review.get("notes", []):
        refs = [add_lookup(x["id"], x.get("locator"), x.get("date")) for x in note["sources"]]
        refs += [patent_sources[number] for number in note.get("patents", []) if number in patent_sources]
        claim(note["id"], "patents", note["en"], note["th"], refs)
    label = review["restriction"]
    selection_path = OUT / "selection.json"
    sources.append(source("dev-selection", "LOE-Bench", "Pinned 24-month development selection replay",
                          "FREEZE development export; 2014-01-01", None, f"selection.json cases[key={case['key']}].event",
                          None, sha256(selection_path.read_bytes()).hexdigest(),
                          datetime.fromtimestamp(selection_path.stat().st_mtime, timezone.utc).isoformat()))
    refs = [add_lookup(x["id"], x.get("locator"), x.get("date")) for x in label["sources"]]
    refs += [patent_sources[number] for number in label.get("patents", []) if number in patent_sources]
    refs.append("dev-selection")
    if review.get("approval_locator"):
        raw = next(entry for entry in fda_manifest["files"] if entry["raw_file"] == "df_anda.jsonl")
        sources.append(source("dev-fda-anda", "openFDA / Drugs@FDA", "Pinned ANDA snapshot, development projection",
                              fda_manifest["t0"], None, review["approval_locator"],
                              "https://open.fda.gov/apis/drug/drugsfda/", raw["sha256"],
                              fda_manifest["fetched_at_utc"]))
        refs.append("dev-fda-anda")
    claim("restriction", "patents", label["en"], label["th"], refs, label["state"])
    checklist("restriction-review", "Confirm the earliest applicant and any patent-specific condition on effective approval from the approval letter or operative court order.",
              "ยืนยันผู้ยื่นคำขอรายแรกและเงื่อนไขที่ทำให้การอนุมัติมีผล โดยตรวจหนังสืออนุมัติหรือคำสั่งศาลที่ระบุเลขที่สิทธิบัตร",
              "US regulatory reviewer", refs)

    lookup_ids = []
    for number in sorted(family_targets(groups, challenged)):
        family = read_family(number, log)
        ref = add_lookup(family["id"], family.get("locator"), family.get("date"))
        lookup_ids.append(ref)
        claim(f"family-{number}", "thai_asean", family["en"], family["th"],
              [patent_sources[number], ref], family["state"])
    registry_ids = [add_lookup(f"{registry}:{case['key']}") for registry in ("wipo", "asean", "dip", "ndi")]
    wipo_terms = add_lookup("wipo-terms", "October 2025 Terms of Use, section 2.1, automated queries")
    claim("th-patent-status", "thai_asean", "Current check on 28 November 2026: Thai patent and national-phase status remain unknown. Family data do not establish enforceability.",
          "การตรวจสอบ ณ วันที่ 28 พฤศจิกายน 2569 ยังยืนยันสถานะสิทธิบัตรหรือการเข้าสู่ขั้นตอนระดับประเทศในไทยไม่ได้ การอยู่ในตระกูลสิทธิบัตรเดียวกันยังไม่เพียงพอที่จะยืนยันผลบังคับตามกฎหมาย",
          lookup_ids + registry_ids[:3] + [wipo_terms], "unknown")
    claim("th-fda-status", "thai_asean", "Current check on 28 November 2026: NDI registration remains unverified.",
          "การตรวจสอบ ณ วันที่ 28 พฤศจิกายน 2569 ยังยืนยันทะเบียนตำรับยาจากระบบ NDI ไม่ได้", registry_ids[3:], "unknown")
    checklist("th-register", "Check the Thai register using the priority/WO identifiers, then confirm grant, scope and legal-event history with DIP.",
              "ใช้เลขคำขอที่ใช้อ้างสิทธิวันยื่นครั้งแรกหรือเลขประกาศ WO ค้นในทะเบียนไทย แล้วตรวจการออกสิทธิบัตร ขอบเขตข้อถือสิทธิ และประวัติสถานะกับกรมทรัพย์สินทางปัญญา",
              "Thai patent reviewer", lookup_ids + registry_ids[:3])
    checklist("th-ndi", "Confirm registration, holder, strength and presentation in Thai FDA NDI.",
              "ตรวจเลขทะเบียนตำรับยา ผู้รับอนุญาต ความแรง และรูปแบบยาในระบบ NDI ของสำนักงานคณะกรรมการอาหารและยา",
              "Thai regulatory reviewer", registry_ids[3:])
    return dict(schema="mwd.dossier.v1", key=case["key"], claims=claims, sources=sources, checklist=items)


def registry_handoff(case, log):
    groups, challenged = ranked_patents(case)
    families = [read_family(n, log) for n in sorted(family_targets(groups, challenged))]
    identifiers = sorted({identifier for family in families for identifier in family["ids"]})
    drugs = sorted({row["ingredient"] for row in case["products"]})
    result = {
        "wipo": "PATENTSCOPE terms section 2.1 prohibits automated queries. Case search not submitted.",
        "asean": "HTTP 403 on robots.txt. Case search not submitted.",
        "dip": "HTTP 403 on robots.txt and public endpoint. Case search not submitted.",
        "ndi": "Connection failed on robots.txt and public endpoint timed out. Case search not submitted.",
    }
    lookups = []
    for registry in result:
        endpoint = log[registry]
        query = ", ".join(drugs if registry == "ndi" else identifiers)
        lookups.append(dict(id=f"{registry}:{case['key']}", issuer=endpoint["issuer"], url=endpoint["url"],
                            retrieved=endpoint["retrieved"], query=query, access="blocked", result=result[registry],
                            sha256=endpoint.get("sha256")))
    return lookups


if __name__ == "__main__":
    selection = load("selection.json")
    reviews = load("reviews.json")
    log = {item["id"]: item for line in (OUT / "lookups.jsonl").read_text(encoding="utf-8").splitlines()
           if (item := json.loads(line))}
    root = Path(__file__).resolve().parents[2] / "loe-bench/data"
    piv = json.loads((root / "PIV_EDITIONS.json").read_bytes())
    rai = json.loads((root / "E7_sources.json").read_bytes())["rai"]
    fda_manifest = json.loads((root / "S0_INPUT_MANIFEST.json").read_bytes())
    DEST.mkdir(parents=True, exist_ok=True)
    edition = next(entry for entry in json.loads((root / "OB_EDITIONS.json").read_bytes())["editions"]
                   if entry["file"] == selection["orange_book"]["source"]["file"])
    registry_lookups = [item for case in selection["cases"] for item in registry_handoff(case, log)]
    log.update((item["id"], item) for item in registry_lookups)
    (OUT / "registry-handoff.json").write_text(json.dumps(registry_lookups, indent=2) + "\n", encoding="utf-8")
    for case in selection["cases"]:
        fragment = build(case, edition, reviews, log,
                         piv["editions"], rai, fda_manifest)
        keys = {item["id"] for item in fragment["sources"]}
        assert len(keys) == len(fragment["sources"])
        assert all(set(item["source_ids"]) <= keys for group in ("claims", "checklist") for item in fragment[group])
        (DEST / f"{quote(case['key'], safe='')}.json").write_text(json.dumps(fragment, ensure_ascii=False, indent=2) + "\n",
                                                  encoding="utf-8", newline="\n")
    files = {item["file"]: item["sha256"] for item in log.values() if item.get("file")}
    for name, digest in files.items():
        if sha256((OUT / name).read_bytes()).hexdigest() != digest:
            raise ValueError(f"Saved source digest mismatch: {name}")
    for name in ("selection.json", "reviews.json", "lookups.jsonl", "registry-handoff.json"):
        files[name] = sha256((OUT / name).read_bytes()).hexdigest()
    (OUT / "SHA256SUMS").write_text("".join(f"{digest}  {name}\n" for name, digest in sorted(files.items())),
                                   encoding="utf-8", newline="\n")
