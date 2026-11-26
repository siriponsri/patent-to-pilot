"""RA Pharma dossier: three document specialists over one product dossier.

A snapshot is built from a fixed input set: the incoming letter, the applicant documents
attached by the operator, the patent claim branch, operator edition choices and one
version of the evidence-role reading skill. Every step is deterministic code; no model
is called. The snapshot is stored whole, together with the bytes of every attached
document, so a historical snapshot reopens with its original values and citations after
later attachments, skill promotions or pack changes.

Statements follow the evidence handoff fields ``ra-pharma/1`` (docs/ra-pharma/EVIDENCE-CONTRACT.md).
Evaluator expectations for skill tests live in ``skill_eval`` and its fixture files, never here.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path
import re
from uuid import uuid4

from patent_to_pilot.workbench import letters
from patent_to_pilot.workbench.core import Conflict, CoreError, NotFound, sha256
from patent_to_pilot.workbench.store import Store, dumps, utc_now

PACK_DIR = Path(__file__).resolve().parent / "sample" / "ra_pharma"
SCOPE_BUNDLE = Path(__file__).resolve().parent / "sample" / "scope_reader.json"
SCHEMA = "ra-pharma/1"
ENGINE = "ra-pharma-dossier/1.0.0"
SKILL_ID = "evidence-role-reader"
BRANCHES = ("15", "18")
DRAFT_NOTICE = ("ร่างเพื่อการตรวจทาน ยังไม่ได้ลงนามหรือส่ง ผู้มีอำนาจของบริษัทเป็นผู้ตัดสินใจออกหนังสือ "
                "ผู้ยื่น ผลิตภัณฑ์ และผลทดสอบในแฟ้มนี้เป็นข้อมูลสมมติ")


def _find(text: str, quote: str, what: str, first: bool = False) -> int:
    """Locate a quote. It must be unique unless the caller binds the first occurrence explicitly."""
    start = text.find(quote)
    if start < 0 or (not first and text.find(quote, start + 1) >= 0):
        raise Conflict(f"quote for {what} is missing or ambiguous in its source", "invalid_pack")
    return start


def load_pack(pack_dir: Path = PACK_DIR) -> dict:
    """Read and verify the pack: canonical text digests, claim quotes and document bytes."""
    try:
        pack = json.loads((pack_dir / "pack.json").read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise Conflict("ไม่พบชุดแฟ้มตัวอย่าง RA Pharma โปรดคืนไฟล์จากรุ่นที่ติดตั้ง", "missing_pack") from None
    except (OSError, ValueError):
        raise Conflict("อ่านชุดแฟ้มตัวอย่าง RA Pharma ไม่ได้", "invalid_pack") from None
    if pack.get("schema_version") != SCHEMA:
        raise Conflict("ชุดแฟ้มตัวอย่างใช้รูปแบบอื่น", "invalid_pack")
    bundle = None
    for src in pack["sources"]:
        if "bundle_example" in src:
            bundle = bundle or {e["id"]: e for e in json.loads(SCOPE_BUNDLE.read_text(encoding="utf-8-sig"))["examples"]}
            src["text"] = bundle[src["bundle_example"]]["text"]
        digest = sha256(src["text"].encode("utf-8"))
        if src.setdefault("canonical_sha256", digest) != digest:
            raise Conflict(f"source text changed under {src['source_id']} {src['part']}", "invalid_pack")
    claims = source(pack, pack["claim_chart"]["source_id"], pack["claim_chart"]["part"])
    for el in pack["claim_chart"]["elements"]:
        _find(claims["text"], el["quote"], el["element_id"])
    for doc in pack["documents"]:
        data = (pack_dir / doc["file"]).read_bytes()
        digest = sha256(data)
        if doc.setdefault("sha256", digest) != digest:
            raise Conflict(f"document bytes changed for {doc['doc_id']}", "invalid_pack")
    pack["pack_sha256"] = sha256(dumps({k: v for k, v in pack.items() if k != "pack_sha256"}).encode("utf-8"))
    return pack


def source(pack: dict, source_id: str, part: str) -> dict:
    for src in pack["sources"]:
        if src["source_id"] == source_id and src["part"] == part:
            return src
    raise NotFound(f"unknown source {source_id} {part}", "unknown_source")


def source_ref(src: dict, quote: str | None = None, locator: str | None = None) -> dict:
    quote = quote if quote is not None else src["text"]
    start = _find(src["text"], quote, src["part"])
    return {"source_id": src["source_id"], "part": src["part"], "kind": src["kind"], "owner": src["owner"],
            "edition": src["edition"], "issued": src.get("issued"), "language": src["language"],
            "sha256": src["canonical_sha256"], "original_sha256": src.get("original_sha256"),
            "locator": locator or src.get("page_note"), "page": src.get("page"), "url": src.get("url"),
            "quote": quote, "start": start, "end": start + len(quote),
            "quote_sha256": sha256(quote.encode("utf-8")), "transcription": src.get("transcription", "digital_text"),
            "binding": src.get("binding")}


def doc_ref(doc: dict, layout: dict, page: int, quote: str, digest: str, first: bool = False) -> dict:
    text = letters.page_text(layout, page)
    start = _find(text, quote, doc["doc_id"], first)
    head = quote.split("\n")[0][:12]
    run = next((r for r in layout["pages"][page - 1]["runs"] if head and head in r["text"]), None)
    return {"source_id": doc["doc_id"], "part": f"page-{page}", "kind": doc["role"], "owner": doc.get("owner"),
            "edition": doc.get("edition"), "language": "th", "sha256": digest, "locator": f"PDF page {page}",
            "page": page, "y": run["y"] if run else None, "quote": quote, "start": start, "end": start + len(quote),
            "offset_basis": "page_text_layer", "quote_sha256": sha256(quote.encode("utf-8")),
            "transcription": "pdf_text_layer", "file_sha256": digest,
            "occurrence": "first" if first and text.count(quote) > 1 else "unique"}


# ------------------------------------------------------------------ evidence-role reading skill
def document_meta(layout: dict) -> dict:
    first = letters.page_text(layout, 1)
    meta = {}
    m = re.search(r"เลขที่รายงาน:\s*(\S+)\s+ฉบับที่\s*(\S+)\s+ลงวันที่\s*(.+)", first)
    if m:
        meta.update(report_id=m.group(1), edition=m.group(2), dated_th=m.group(3).strip())
    m = re.search(r"ผู้จัดทำ:\s*(.+)", first)
    meta["owner_name"] = m.group(1).strip() if m else None
    m = re.search(r"ผลิตภัณฑ์:\s*(.+)", first)
    meta["product_line"] = m.group(1).strip() if m else None
    m = re.search(r"รุ่นการผลิต:\s*(\S+)", first)
    meta["batch"] = m.group(1) if m else None
    return meta


def apply_skill(spec: dict, task: dict, passages: list[dict], dossier: dict) -> dict:
    """Decide which passages may serve as the applicant's result for ``task``.

    Each passage carries ``source_kind``, ``owner_name`` and ``text``. The skill
    specification is data, so a stored version replays exactly.
    """
    accept = spec["accept"]
    names = dossier["product"]["name_match_th"]
    candidates = []
    for p in passages:
        text = p["text"]
        if not any(t.lower() in text.lower() for t in task["terms"]):
            continue
        value = None
        for pattern in task["value_patterns"]:
            m = re.search(pattern, text)
            if m:
                value, match = m.group(1), m.group(0)
                break
        if value is None:
            continue
        kind_ok = "*" in accept["source_kinds"] or p["source_kind"] in accept["source_kinds"]
        owner_ok = not accept["require_applicant_owner"] or p.get("owner_name") == dossier["applicant"]["name_th"]
        subject_ok = not accept["require_product_subject"] or any(n in (p.get("subject_text") or "") for n in names)
        ok = kind_ok and owner_ok and subject_ok
        if ok:
            reason = "ผ่านเงื่อนไขของทักษะรุ่นนี้"
        elif not kind_ok:
            reason = "ค่าอยู่ในเอกสารสิทธิบัตร เป็นผลของตัวอย่างของผู้ประดิษฐ์ ไม่ใช่ผลของผลิตภัณฑ์ผู้ยื่น"
        elif not owner_ok:
            reason = "ผู้จัดทำเอกสารไม่ใช่ผู้ยื่นคำขอ"
        else:
            reason = "เอกสารไม่ได้ระบุว่าเป็นผลของผลิตภัณฑ์ในแฟ้มนี้"
        candidates.append({"passage_id": p["passage_id"], "source_kind": p["source_kind"], "value": value,
                           "match": match, "accepted": ok,
                           "role": spec["assign_role"] if ok else ("patent_disclosure" if p["source_kind"] == "patent"
                                                                   else "needs_review"),
                           "reason_th": reason, "edition": p.get("edition"), "report_id": p.get("report_id")})
    accepted = [c for c in candidates if c["accepted"]]
    return {"skill_id": spec["skill_id"], "version": spec["version"], "spec_sha256": spec_sha(spec),
            "candidates": candidates, "accepted": accepted}


def spec_sha(spec: dict) -> str:
    return sha256(dumps(spec).encode("utf-8"))


def propose_from_correction(parent: dict, correction: dict) -> dict:
    """Derive the next skill version from an operator rejection of a source role."""
    spec = copy.deepcopy(parent)
    major, minor, _patch = (int(x) for x in parent["version"].split("."))
    spec.update(version=f"{major}.{minor + 1}.0", parent=parent["version"],
                description_th=("ยอมรับเป็นผลของผู้ยื่นเฉพาะเอกสารที่ผู้ยื่นจัดทำและระบุผลิตภัณฑ์ในแฟ้มนี้ "
                                "ผลในสิทธิบัตรถือเป็นข้อเปิดเผยของสิทธิบัตร"),
                accept={"source_kinds": ["applicant_document"], "require_applicant_owner": True,
                        "require_product_subject": True},
                derived_from={"correction_id": correction["id"], "rejected_role": correction["from_role"],
                              "corrected_role": correction["to_role"], "source_kind": correction["source_kind"]})
    return spec


# ------------------------------------------------------------------ builder
class _Trace:
    def __init__(self, snapshot_id):
        self.snapshot_id, self.actions = snapshot_id, []

    def add(self, agent, action, kind, implementation, summary):
        idx = len(self.actions)
        self.actions.append({"index": idx, "agent": agent, "action": action, "kind": kind,
                             "implementation": implementation, "summary": summary})
        return f"{self.snapshot_id}:{idx}"


def _item(dossier, item_id, agent, task, statement, subject_id, role, jurisdiction, status, sources,
          trace_id, depends_on=(), missing=(), **extra):
    item = {"schema_version": SCHEMA, "dossier_id": dossier["dossier_id"], "item_id": item_id, "agent": agent,
            "task": task, "statement": statement, "subject_id": subject_id, "evidence_role": role,
            "jurisdiction": jurisdiction, "as_of": dossier["as_of"], "status": status, "sources": list(sources),
            "depends_on": list(depends_on), "missing": list(missing), "trace_id": trace_id, **extra}
    item["content_sha256"] = sha256(dumps({k: v for k, v in item.items() if k != "trace_id"}).encode("utf-8"))
    return item


def build_snapshot(pack: dict, inputs: dict, docs: dict[str, bytes], skill: dict, snapshot_id: str) -> dict:
    """Pure function of the pack, the inputs, the attached bytes and the skill version."""
    dossier = pack["dossier"]
    trace = _Trace(snapshot_id)
    items, layouts = [], {}
    by_id = {d["doc_id"]: d for d in pack["documents"]}
    for doc_id, data in docs.items():
        layouts[doc_id] = letters.read_layout(data)
    digests = {doc_id: sha256(data) for doc_id, data in docs.items()}
    trace.add("system", "verify_pack", "deterministic", ENGINE,
              {"pack_sha256": pack["pack_sha256"], "documents": digests})

    # ---------------- correspondence: read the incoming letter
    incoming_id = inputs["incoming_doc_id"]
    letter = letters.read_letter(docs[incoming_id])
    letter.pop("layout")
    tid = trace.add("correspondence", "read_incoming_letter", "deterministic", letters.READER_VERSION,
                    {"document_type": letter["document_type"], "sender_kind": letter["sender"]["kind"],
                     "requests": len(letter["requests"]), "uncertain": letter["uncertain"]})
    inc_doc = {**by_id[incoming_id], "owner": letter["sender"]["name"]}
    inc_text = letters.page_text(layouts[incoming_id], 1)
    sender_src = []
    if letter["fields"]["number"]["value"]:
        sender_src.append(doc_ref(inc_doc, layouts[incoming_id], 1, "ที่ " + letter["fields"]["number"]["value"],
                                  digests[incoming_id]))
    items.append(_item(dossier, "corr.incoming.sender", "correspondence", "identify_sender",
                       f"หนังสือที่ได้รับเป็น {letter['document_type']} จาก {letter['sender']['name']}",
                       f"party:{letter['sender']['kind']}", "incoming_request", dossier["market"],
                       "needs_review" if letter["uncertain"] else "supported", sender_src, tid,
                       missing=[f"ตรวจ: {u}" for u in letter["uncertain"]], layout_fields=letter["fields"],
                       emblem=letter["emblem"], sender=letter["sender"]))
    for req in letter["requests"]:
        head = req["text"][:20]
        quote_line = next(line for line in inc_text.split("\n") if head in line)
        items.append(_item(dossier, f"corr.incoming.request-{req['number']}", "correspondence", "read_request",
                           req["text"], dossier["applicant"]["id"], "incoming_request", dossier["market"], "supported",
                           [doc_ref(inc_doc, layouts[incoming_id], 1, quote_line, digests[incoming_id])], tid))

    # Outgoing sender is always the applicant company; the addressee is the incoming sender.
    selection = letters.select_template(pack["templates"], dossier["applicant"]["kind"], letter["sender"]["kind"])
    tid = trace.add("correspondence", "select_template", "deterministic", ENGINE,
                    {"template_id": selection["template"]["template_id"],
                     "rejected": [r["template_id"] for r in selection["rejected"]]})
    tpl_sources = [source_ref(source(pack, *selection["template"]["basis_source"]))] \
        if selection["template"].get("basis_source") else []
    opm = source(pack, "TH-OPM-SARABAN-2526", "clauses-11-71-75")
    items.append(_item(dossier, "corr.template", "correspondence", "select_outgoing_template",
                       f"ใช้แบบ {selection['template']['label_th']} เพราะผู้ส่งจริงคือ {dossier['applicant']['name_th']}",
                       dossier["applicant"]["id"], "regulatory_requirement", dossier["market"], "supported",
                       tpl_sources or [source_ref(opm, "ข้อ ๑๑ หนังสือภายนอก คือ หนังสือติดต่อราชการที่เป็นแบบพิธีโดยใช้กระดาษตราครุฑ",
                                                  "Clause 11, PDF page 3")], tid,
                       template=selection["template"], rejected_templates=selection["rejected"]))

    # ---------------- patent specialist
    chart = pack["claim_chart"]
    claims = source(pack, chart["source_id"], chart["part"])
    branch = inputs["claim_branch"]
    form_doc = by_id["applicant-formulation-record"]
    form_layout = layouts["applicant-formulation-record"]
    facts = {f["fact_id"]: f for f in pack["facts"]}
    tid = trace.add("patent", "compare_claim_elements", "deterministic", ENGINE,
                    {"branch": branch, "claims": chart["branches"][branch]})
    rows, statuses = [], []
    for el in chart["elements"]:
        if el["claim"] not in chart["branches"][branch]:
            continue
        fact = facts[el["fact_id"]]
        fref = doc_ref({**form_doc, "owner": dossier["applicant"]["name_th"], "edition": "2.0"}, form_layout,
                       fact["page"], fact["quote"], digests["applicant-formulation-record"], first=True)
        calc = None
        if "calculation" in fact:
            a, b = fact["calculation"]["acid"], fact["calculation"]["base"]
            ma, mb = a["mg"] / a["mw"], b["mg"] / b["mw"]
            calc = {"acid_mmol": round(ma, 4), "base_mmol": round(mb, 4),
                    "acid_proton_mmol": round(ma * a["protons"], 4), "base_proton_mmol": round(mb * b["protons"], 4),
                    "molecules_acid_excess": ma > mb, "protons_acid_excess": ma * a["protons"] > mb * b["protons"]}
        row = _item(dossier, f"patent.claim.{el['element_id']}", "patent", "claim_element_comparison",
                    f"{el['claim']}: {el['quote']} — {fact['statement_th']}", "patent:" + chart["source_id"],
                    "claim_limitation", chart["publication"]["jurisdiction"], "supported",
                    [source_ref(claims, el["quote"], el["claim"]), fref], tid,
                    comparison=el["status"], reason_th=el.get("reason_th"), calculation=calc, claim=el["claim"],
                    element_id=el["element_id"])
        rows.append(row)
        statuses.append(el["status"])
    items.extend(rows)
    branch_status = ("does_not_meet" if "does_not_meet" in statuses else
                     "needs_review" if {"needs_review", "unknown"} & set(statuses) else "all_elements_met_on_record")
    ex6 = source(pack, "US20120276199A1", "example-6")
    tid = trace.add("patent", "read_inventor_example", "deterministic", ENGINE, {"passage": "example-6"})
    items.append(_item(dossier, "patent.example-6", "patent", "read_disclosure",
                       "สิทธิบัตรรายงานผลการละลายของยาเม็ดตามตัวอย่างที่ 6 ของผู้ประดิษฐ์ ที่เวลา 30 ได้ร้อยละ 96 "
                       "(หัวคอลัมน์เวลาพิมพ์ว่า Hours)", ex6["subject_id"], "patent_disclosure", "US", "supported",
                       [source_ref(ex6, "30 96 1.6", "Table 2, PDF page 16"),
                        source_ref(ex6, ex6["text"].split("\n")[0], "[0245], PDF page 16")], tid,
                       reading_note_th=ex6["reading_note_th"]))
    items.append(_item(dossier, "patent.publication-status", "patent", "record_publication",
                       f"{chart['publication']['number']} เป็น {chart['publication']['kind']} เขตอำนาจ US "
                       "ยังไม่ได้ตรวจสถานะทางกฎหมายและตระกูลสิทธิบัตร", "patent:" + chart["source_id"],
                       "patent_disclosure", "US", "needs_review", [source_ref(claims, claims["text"][:60], "Claim 1")],
                       tid, missing=["สถานะทางกฎหมาย ณ วันที่ประเมิน", chart["publication"]["family_note_th"]]))
    items.append(_item(dossier, "patent.fto-th", "patent", "fto_assessment",
                       f"สาขาข้อถือสิทธิ {' → '.join(reversed(chart['branches'][branch]))}: ผลเทียบรายองค์ประกอบ = "
                       f"{branch_status} แต่ยังสรุปเสรีภาพในการดำเนินการในประเทศไทยไม่ได้ เพราะเอกสารเป็นคำขอของสหรัฐฯ",
                       dossier["product"]["id"], "claim_limitation", "TH", "needs_review",
                       [source_ref(claims, claims["text"][:60], "Claim 1")], tid,
                       depends_on=[r["item_id"] for r in rows], missing=chart["fto_missing_th"],
                       branch=branch, branch_status=branch_status))

    # ---------------- regulatory specialist
    passages = [{"passage_id": "US20120276199A1#example-6", "source_kind": "patent",
                 "owner_name": ex6["owner"], "subject_text": "Example 6 of US20120276199A1", "text": ex6["text"]}]
    attached_meta = {}
    for doc_id in inputs["attachments"]:
        doc = by_id[doc_id]
        meta = document_meta(layouts[doc_id])
        attached_meta[doc_id] = meta
        for page in layouts[doc_id]["pages"]:
            passages.append({"passage_id": f"{doc_id}#page-{page['page']}", "source_kind": doc["role"],
                             "owner_name": meta["owner_name"], "subject_text": meta["product_line"],
                             "text": letters.page_text(layouts[doc_id], page["page"]), "doc_id": doc_id,
                             "page": page["page"], "edition": meta.get("edition"), "report_id": meta.get("report_id")})
    task = pack["tasks"][0]
    result = apply_skill(skill, task, passages, dossier)
    tid = trace.add("regulatory", "assign_evidence_role", "deterministic", f"{SKILL_ID}/{skill['version']}",
                    {"candidates": [(c["passage_id"], c["value"], c["accepted"]) for c in result["candidates"]]})
    accepted = result["accepted"]
    choice = inputs.get("edition_choice") or {}
    reports = {}
    for c in accepted:
        reports.setdefault(c.get("report_id") or c["passage_id"], []).append(c)
    selected, status, conflict = None, "missing", None
    if skill["accept"]["source_kinds"] == ["*"] and accepted:
        selected, status = accepted[0], "supported"   # v1 behaviour: the first value found
    elif accepted:
        groups = list(reports.items())
        rid, cands = groups[0]
        editions = {c["edition"]: c for c in cands}
        if len(editions) > 1 and len({c["value"] for c in cands}) > 1:
            if rid in choice and choice[rid] in editions:
                selected, status = editions[choice[rid]], "supported"
                tid = trace.add("operator", "choose_edition", "operator", "operator_decision",
                                {"report_id": rid, "edition": choice[rid]})
            else:
                status, conflict = "conflict", [{"edition": e, "value": c["value"], "passage_id": c["passage_id"]}
                                                for e, c in sorted(editions.items())]
        else:
            selected, status = cands[-1], "supported"
    req_src = [source_ref(source(pack, *s)) for s in pack["checklist"][0]["sources"]]
    task_sources, value = [], None
    if selected:
        value = selected["value"]
        if selected["source_kind"] == "patent":
            task_sources = [source_ref(ex6, "30 96 1.6", "Table 2, PDF page 16")]
        else:
            doc_id, page = selected["passage_id"].split("#page-")
            meta = attached_meta[doc_id]
            task_sources = [doc_ref({**by_id[doc_id], "owner": meta["owner_name"], "edition": meta.get("edition")},
                                    layouts[doc_id], int(page), selected["match"], digests[doc_id])]
    statement = {
        "supported": f"ผลการละลายของผลิตภัณฑ์ที่ 30 นาที: ร้อยละ {value} (ค่าเฉลี่ย)",
        "missing": "ยังไม่มีรายงานผลการละลายของผลิตภัณฑ์ผู้ยื่น ค่าที่พบในสิทธิบัตรใช้แทนไม่ได้",
        "conflict": "มีรายงานฉบับต่างกันที่ให้ค่าไม่เท่ากัน ต้องเลือกฉบับที่ใช้ก่อนส่ง"}[status]
    items.append(_item(dossier, "reg.R-P54.applicant-result", "regulatory", task["task_id"], statement,
                       task["subject_id"], "applicant_result", dossier["market"], status, task_sources, tid,
                       depends_on=["reg.R-P54.requirement", "corr.incoming.request-1"],
                       missing=[] if status == "supported" else [pack["checklist"][0]["attachment_th"]],
                       value=value, skill={k: result[k] for k in ("skill_id", "version", "spec_sha256")},
                       candidates=result["candidates"], conflict=conflict,
                       selected_passage=selected["passage_id"] if selected else None))
    tid = trace.add("regulatory", "map_requirements", "deterministic", ENGINE, {"requirements": ["R-P54", "R-COA"]})
    items.append(_item(dossier, "reg.R-P54.requirement", "regulatory", "map_requirement",
                       "ACTD P 5.4 ขอผลการวิเคราะห์รุ่นการผลิตที่เกี่ยวข้อง และตารางสรุป (ข้อกำหนดทางเทคนิค ไม่ใช่บทบัญญัติกฎหมาย)",
                       "requirement:actd-quality-p5.4", "regulatory_requirement", "TH", "needs_review", req_src, tid,
                       missing=["ประกาศ อย. ที่ทำให้ข้อกำหนดนี้ใช้บังคับกับคำขอนี้", "การยืนยันฉบับที่ใช้บังคับ ณ วันที่ประเมิน"],
                       basis="technical_guidance", applicability_note_th=pack["checklist"][0]["applicability_note_th"],
                       edition_note_th="หน้าปกระบุ กันยายน ๒๕๕๐ ส่วนท้ายหน้าฉบับภาษาไทยระบุ quality part July 06 8/2/2006 "
                                       "ต้องยืนยันว่าฉบับใดใช้บังคับ"))
    coa = pack["checklist"][1]
    coa_req = next((i for i in items if i["item_id"] == "corr.incoming.request-2"), None)
    items.append(_item(dossier, "reg.R-COA.attachment", "regulatory", "check_attachment",
                       "ยังไม่มีหนังสือรับรองผลการวิเคราะห์ของรุ่นการผลิตที่ทดสอบ", dossier["product"]["id"],
                       "applicant_result", "TH", "missing", coa_req["sources"] if coa_req else [], tid,
                       depends_on=["corr.incoming.request-2"], missing=[coa["attachment_th"]]))

    # ---------------- correspondence: draft the reply
    blocks = draft_letter(pack, letter, selection["template"], {i["item_id"]: i for i in items}, inputs, attached_meta)
    tid = trace.add("correspondence", "draft_reply", "deterministic", ENGINE,
                    {"blocks": len(blocks), "template": selection["template"]["template_id"]})
    review = [{"block_id": b["block_id"], "text": b["text"], "item_ids": b["item_ids"], "needs_signer": b.get("needs_signer", False)}
              for b in blocks if b["item_ids"] or b.get("needs_signer")]
    content = {"items": [{k: v for k, v in i.items() if k != "trace_id"} for i in items], "letter": blocks}
    return {"schema_version": SCHEMA, "engine": ENGINE, "snapshot_id": snapshot_id, "dossier": dossier,
            "pack": {"pack_id": pack["pack_id"], "pack_version": pack["pack_version"], "pack_sha256": pack["pack_sha256"]},
            "inputs": inputs, "documents": {d: {"sha256": digests[d], "title_th": by_id[d]["title_th"],
                                                "role": by_id[d]["role"], **({"meta": attached_meta[d]} if d in attached_meta else {})}
                                            for d in docs},
            "identity": {"model": None, "model_calls": 0, "paid_calls": 0, "prompts": None,
                         "skill": {"skill_id": SKILL_ID, "version": skill["version"], "spec_sha256": spec_sha(skill)},
                         "harness": ENGINE, "reader": letters.READER_VERSION, "pdf_library": _pypdf_version()},
            "incoming": letter, "template": selection, "claim_branch": branch, "branch_status": branch_status,
            "items": items, "letter": blocks, "review": review, "actions": trace.actions,
            "jurisdictions": pack["jurisdictions"], "content_sha256": sha256(dumps(content).encode("utf-8"))}


def _pypdf_version():
    try:
        import pypdf
        return f"pypdf {pypdf.__version__}"
    except ImportError:  # pragma: no cover - read_layout already refused
        return None


def draft_letter(pack, letter, template, items, inputs, attached_meta) -> list[dict]:
    d = pack["dossier"]
    app = d["applicant"]
    f = letter["fields"]
    blocks = []

    def add(block_id, kind, text, item_ids=(), **extra):
        # Keep a number on the same line as its unit, as a typist would.
        text = re.sub(r"(\d) (มก\.|นาที|ชุด|รายการ)", lambda m: m.group(1) + "\u00a0" + m.group(2), text)
        blocks.append({"block_id": block_id, "kind": kind, "text": text, "item_ids": list(item_ids), **extra})

    add("letterhead", "letterhead", app["name_th"])
    add("letterhead-sub", "letterhead_sub", f"{app['name_en']} · {letters.arabic_digits(app['address_th'])}")
    add("number", "number", f"ที่ {app['letter_prefix']} ……/{int(d['as_of'][:4]) + 543}", needs_signer=True)
    add("date", "date", letters.thai_date(d["as_of"]))
    num = letters.arabic_digits   # the company draft writes Arabic numerals throughout
    add("subject", "subject", f"เรื่อง  {num(f['subject']['value'])}", ["corr.incoming.sender"])
    addressee = (f["signer_position"]["value"] or "").split(" / ")[0] or letter["sender"]["name"]
    add("salutation", "salutation", f"{template['salutation']}  {addressee}", ["corr.incoming.sender"])
    add("reference", "reference", f"อ้างถึง  หนังสือ{letter['sender']['name']} ที่ {num(f['number']['value'])} "
                                  f"ลงวันที่ {num(f['date']['value'])}", ["corr.incoming.sender"])
    result = items["reg.R-P54.applicant-result"]
    enclosures = []
    if result["status"] == "supported" and result["sources"] and result["sources"][0]["kind"] == "applicant_document":
        doc_id = result["sources"][0]["source_id"]
        meta = attached_meta[doc_id]
        enclosures.append((f"รายงานผลการทดสอบการละลาย เลขที่ {meta['report_id']} ฉบับที่ {meta['edition']} "
                           f"ลงวันที่ {meta['dated_th']} จำนวน 1 ชุด", ["reg.R-P54.applicant-result"]))
    add("enclosures", "enclosures", "สิ่งที่ส่งมาด้วย  " + ("ดังรายการต่อไปนี้" if enclosures else "-"),
        ["reg.R-P54.applicant-result"] if enclosures else [])
    for n, (text, ids) in enumerate(enclosures, start=1):
        add(f"enclosure-{n}", "enclosure_item", f"{n}. {text}", ids)
    requests = [i for k, i in items.items() if k.startswith("corr.incoming.request-")]
    if letter["document_type"] == "authority_external_letter" and requests:
        add("opening", "paragraph", f"ตามหนังสือที่อ้างถึง ขอให้บริษัทจัดส่งเอกสารเพิ่มเติมประกอบคำขอขึ้นทะเบียนตำรับยา "
                                    f"{d['product']['name_th']} จำนวน {len(requests)} รายการ ความละเอียดแจ้งแล้ว นั้น",
            [r["item_id"] for r in requests])
        add("intro", "paragraph", "บริษัทขอเรียนชี้แจงและจัดส่งเอกสาร ดังนี้", [])
        if result["status"] == "supported" and enclosures:
            meta = attached_meta[result["sources"][0]["source_id"]]
            text = (f"1. ผลการวิเคราะห์รุ่นการผลิต {meta['batch']} ตามหัวข้อ P 5.4 ของ ACTD มีผลการทดสอบการละลาย"
                    f"ของผลิตภัณฑ์ที่เวลา 30 นาที เท่ากับร้อยละ {result['value']} (ค่าเฉลี่ย) รายละเอียดตามสิ่งที่ส่งมาด้วย 1")
            add("req-1", "paragraph", text, ["reg.R-P54.applicant-result", "reg.R-P54.requirement", "corr.incoming.request-1"])
        elif result["status"] == "conflict":
            options = " / ".join(f"ฉบับที่ {c['edition']} ร้อยละ {c['value']}" for c in result["conflict"])
            add("req-1", "paragraph", f"1. [ต้องเลือกฉบับรายงานก่อนส่ง: {options}]",
                ["reg.R-P54.applicant-result", "corr.incoming.request-1"], blocking=True)
        elif result["status"] == "supported":
            # Only a v1 skill reaches here: it took a value that is not an applicant document.
            add("req-1", "paragraph", f"1. ผลการทดสอบการละลายของผลิตภัณฑ์ที่เวลา 30 นาที เท่ากับร้อยละ {result['value']}",
                ["reg.R-P54.applicant-result", "corr.incoming.request-1"])
        else:
            add("req-1", "paragraph", "1. สำหรับผลการวิเคราะห์รุ่นการผลิตตามหัวข้อ P 5.4 ของ ACTD รวมผลการทดสอบการละลาย"
                                      "ของผลิตภัณฑ์ที่เวลา 30 นาที บริษัทอยู่ระหว่างจัดทำรายงาน และจะจัดส่งภายในวันที่ "
                                      "[ผู้ลงนามกำหนด]", ["reg.R-P54.applicant-result", "corr.incoming.request-1"],
                needs_signer=True)
        add("req-2", "paragraph", "2. สำหรับหนังสือรับรองผลการวิเคราะห์ (Certificate of Analysis) ของรุ่นการผลิตดังกล่าว "
                                  "บริษัทจะจัดส่งเพิ่มเติมภายในวันที่ [ผู้ลงนามกำหนด]",
            ["reg.R-COA.attachment", "corr.incoming.request-2"], needs_signer=True)
    else:
        add("opening", "paragraph", f"ตามหนังสือที่อ้างถึง เรื่อง{num(f['subject']['value'])} นั้น บริษัทได้รับหนังสือแล้ว "
                                    "และจะพิจารณาตามเงื่อนไขของสัญญาที่เกี่ยวข้อง แล้วแจ้งผลให้ทราบต่อไป",
            ["corr.incoming.sender"])
    add("ending", "ending", template["ending"])
    add("closing", "closing", template["closing"])
    add("signature-space", "signature_space", "")
    add("signer", "signer", "( ........................................ )", needs_signer=True)
    add("signer-position", "signer_position", "ผู้มีอำนาจลงนามของบริษัท [ผู้ลงนามกรอก]", needs_signer=True)
    add("contact", "contact", f"{app['unit_th']} {letters.arabic_digits(app['phone_th'])}")
    return blocks


# ------------------------------------------------------------------ store-backed service
class DossierService:
    def __init__(self, store: Store, pack_dir: Path = PACK_DIR):
        self.store, self.pack_dir = store, pack_dir
        with store.tx() as con:
            con.execute("CREATE TABLE IF NOT EXISTS dossier_blobs (sha256 TEXT PRIMARY KEY, name TEXT NOT NULL, data BLOB NOT NULL)")
            con.execute("CREATE TABLE IF NOT EXISTS dossier_snapshots (id TEXT PRIMARY KEY, dossier_id TEXT NOT NULL, "
                        "seq INTEGER NOT NULL, label TEXT, created_at TEXT NOT NULL, content_sha256 TEXT NOT NULL, trace TEXT NOT NULL)")
            con.execute("CREATE TABLE IF NOT EXISTS dossier_letters (id TEXT PRIMARY KEY, snapshot_id TEXT NOT NULL, "
                        "parent_id TEXT, created_at TEXT NOT NULL, note TEXT, blocks TEXT NOT NULL)")
            con.execute("CREATE TABLE IF NOT EXISTS dossier_skills (version TEXT PRIMARY KEY, spec TEXT NOT NULL, "
                        "sha256 TEXT NOT NULL, parent TEXT, created_at TEXT NOT NULL)")
            con.execute("CREATE TABLE IF NOT EXISTS dossier_skill_events (id TEXT PRIMARY KEY, kind TEXT NOT NULL, "
                        "version TEXT, created_at TEXT NOT NULL, payload TEXT NOT NULL)")

    # ---- pack and skills
    def pack(self):
        return load_pack(self.pack_dir)

    def skills(self, pack=None) -> dict:
        pack = pack or self.pack()
        out = {v: s for v, s in pack["skills"][SKILL_ID].items()}
        with self.store.read() as con:
            for row in con.execute("SELECT version, spec FROM dossier_skills"):
                out[row["version"]] = json.loads(row["spec"])
        return out

    def events(self, kind=None):
        with self.store.read() as con:
            rows = con.execute("SELECT id, kind, version, created_at, payload FROM dossier_skill_events "
                               + ("WHERE kind=? " if kind else "") + "ORDER BY rowid", (kind,) if kind else ()).fetchall()
        return [{"id": r["id"], "kind": r["kind"], "version": r["version"], "created_at": r["created_at"],
                 **json.loads(r["payload"])} for r in rows]

    def active_skill(self) -> str:
        promotions = self.events("promotion")
        return promotions[-1]["version"] if promotions else "1.0.0"

    def _event(self, kind, version, payload):
        eid = uuid4().hex
        with self.store.tx() as con:
            con.execute("INSERT INTO dossier_skill_events VALUES (?,?,?,?,?)", (eid, kind, version, utc_now(), dumps(payload)))
        return {"id": eid, "kind": kind, "version": version, **payload}

    # ---- catalog
    def catalog(self):
        try:
            pack = self.pack()
        except Conflict as exc:
            return {"pack_error": {"code": exc.code, "message": str(exc)}, "snapshots": self.snapshots()}
        skills = self.skills(pack)
        return {"dossier": pack["dossier"], "pack": {"pack_id": pack["pack_id"], "pack_version": pack["pack_version"],
                                                     "pack_sha256": pack["pack_sha256"]},
                "documents": [{k: d[k] for k in ("doc_id", "title_th", "role", "sha256", "data_origin")} |
                              {"always_attached": d.get("always_attached", False)} for d in pack["documents"]],
                "branches": list(BRANCHES), "jurisdictions": pack["jurisdictions"],
                "sources": [{k: s.get(k) for k in ("source_id", "part", "kind", "owner", "edition", "language", "url",
                                                   "binding", "transcription", "page_note", "rights_note")}
                            for s in pack["sources"]],
                "skills": [{"version": v, "description_th": s["description_th"], "parent": s.get("parent"),
                            "spec_sha256": spec_sha(s), "derived_from": s.get("derived_from")} for v, s in sorted(skills.items())],
                "active_skill": self.active_skill(), "events": self.events(), "snapshots": self.snapshots()}

    def snapshots(self):
        with self.store.read() as con:
            rows = con.execute("SELECT id, seq, label, created_at, content_sha256 FROM dossier_snapshots ORDER BY seq").fetchall()
        return [dict(r) for r in rows]

    # ---- build and replay
    def _docs_for(self, pack, inputs) -> dict[str, bytes]:
        by_id = {d["doc_id"]: d for d in pack["documents"]}
        docs = {}
        for doc_id in [inputs["incoming_doc_id"], *inputs["attachments"]]:
            doc = by_id[doc_id]
            docs[doc_id] = (self.pack_dir / doc["file"]).read_bytes()
        return docs

    def _validate(self, pack, body):
        if not isinstance(body, dict) or set(body) - {"incoming_doc_id", "attachments", "claim_branch",
                                                      "edition_choice", "skill_version", "label"}:
            raise CoreError("คำขอสร้างแฟ้มมีอาร์กิวเมนต์ที่ไม่รองรับ", "invalid_request")
        by_id = {d["doc_id"]: d for d in pack["documents"]}
        incoming = body.get("incoming_doc_id", "incoming-authority-rfi")
        if by_id.get(incoming, {}).get("role") != "incoming_letter":
            raise CoreError("ต้องเลือกหนังสือที่ได้รับจากรายการ", "invalid_incoming")
        attachments = body.get("attachments", [])
        if not isinstance(attachments, list) or any(by_id.get(a, {}).get("role") != "applicant_document" for a in attachments):
            raise CoreError("เอกสารแนบต้องเป็นเอกสารของผู้ยื่นในแฟ้มนี้", "invalid_attachment")
        always = [d["doc_id"] for d in pack["documents"] if d.get("always_attached")]
        attachments = always + sorted(set(attachments) - set(always))
        branch = str(body.get("claim_branch", "15"))
        if branch not in BRANCHES:
            raise CoreError("สาขาข้อถือสิทธิต้องเป็น 15 หรือ 18", "invalid_branch")
        choice = body.get("edition_choice") or {}
        if not isinstance(choice, dict) or not all(isinstance(k, str) and isinstance(v, str) for k, v in choice.items()):
            raise CoreError("การเลือกฉบับรายงานไม่ถูกต้อง", "invalid_edition_choice")
        version = body.get("skill_version") or self.active_skill()
        skills = self.skills(pack)
        if version not in skills:
            raise NotFound("ไม่พบรุ่นทักษะนี้", "unknown_skill")
        return {"incoming_doc_id": incoming, "attachments": attachments, "claim_branch": branch,
                "edition_choice": dict(sorted(choice.items())), "skill_version": version}, skills[version]

    def build(self, body):
        pack = self.pack()
        inputs, skill = self._validate(pack, body or {})
        docs = self._docs_for(pack, inputs)
        sid = uuid4().hex
        snap = build_snapshot(pack, inputs, docs, skill, sid)
        snap["skill_spec"] = skill
        snap["created_at"] = utc_now()
        label = (body or {}).get("label")
        snap["label"] = label if isinstance(label, str) and len(label) <= 120 else None
        with self.store.tx() as con:
            for doc_id, data in docs.items():
                con.execute("INSERT OR IGNORE INTO dossier_blobs VALUES (?,?,?)", (sha256(data), doc_id, data))
            seq = con.execute("SELECT COALESCE(MAX(seq), 0) + 1 FROM dossier_snapshots").fetchone()[0]
            snap["seq"] = seq
            con.execute("INSERT INTO dossier_snapshots VALUES (?,?,?,?,?,?,?)",
                        (sid, pack["dossier"]["dossier_id"], seq, snap["label"], snap["created_at"],
                         snap["content_sha256"], dumps(snap)))
        return snap

    def snapshot(self, sid):
        with self.store.read() as con:
            row = con.execute("SELECT trace FROM dossier_snapshots WHERE id=?", (sid,)).fetchone()
        if row is None:
            raise NotFound("ไม่พบแฟ้มฉบับนี้", "missing_snapshot")
        return json.loads(row["trace"])

    def blob(self, digest):
        with self.store.read() as con:
            row = con.execute("SELECT name, data FROM dossier_blobs WHERE sha256=?", (digest,)).fetchone()
        if row is None:
            raise NotFound("ไม่พบไฟล์ที่อ้างถึงในเครื่องนี้", "missing_file")
        return row["name"], bytes(row["data"])

    def verify(self, sid):
        """Reopen a stored snapshot: every citation resolves to its retained bytes, and the
        same inputs with the same stored skill version rebuild the same content."""
        snap = self.snapshot(sid)
        pack = self.pack()
        checks = []
        texts = {}
        for item in snap["items"]:
            for ref in item["sources"]:
                if ref.get("file_sha256"):
                    key = (ref["file_sha256"], ref["page"])
                    if key not in texts:
                        _name, data = self.blob(ref["file_sha256"])
                        ok_bytes = sha256(data) == ref["file_sha256"]
                        texts[key] = (letters.page_text(letters.read_layout(data), ref["page"]), ok_bytes)
                    text, ok_bytes = texts[key]
                else:
                    src = source(pack, ref["source_id"], ref["part"])
                    text, ok_bytes = src["text"], src["canonical_sha256"] == ref["sha256"]
                ok = ok_bytes and text[ref["start"]:ref["end"]] == ref["quote"]
                checks.append({"item_id": item["item_id"], "source_id": ref["source_id"], "part": ref["part"], "ok": ok})
        docs = {}
        for doc_id, meta in snap["documents"].items():
            docs[doc_id] = self.blob(meta["sha256"])[1]
        rebuilt = build_snapshot(pack, snap["inputs"], docs, snap["skill_spec"], snap["snapshot_id"])
        return {"snapshot_id": sid, "citations": checks, "citations_ok": all(c["ok"] for c in checks),
                "content_sha256": snap["content_sha256"], "rebuilt_sha256": rebuilt["content_sha256"],
                "rebuild_matches": rebuilt["content_sha256"] == snap["content_sha256"],
                "skill_version": snap["identity"]["skill"]["version"], "pack_sha256_now": pack["pack_sha256"],
                "pack_sha256_then": snap["pack"]["pack_sha256"]}

    def diff(self, a, b):
        sa, sb = self.snapshot(a), self.snapshot(b)
        ia, ib = {i["item_id"]: i for i in sa["items"]}, {i["item_id"]: i for i in sb["items"]}
        changed, unchanged = [], []
        for key in sorted(set(ia) | set(ib)):
            x, y = ia.get(key), ib.get(key)
            if x and y and x["content_sha256"] == y["content_sha256"]:
                unchanged.append(key)
            else:
                changed.append({"item_id": key, "before": x and {k: x[k] for k in ("status", "statement")},
                                "after": y and {k: y[k] for k in ("status", "statement")}})
        la, lb = {x["block_id"]: x["text"] for x in sa["letter"]}, {x["block_id"]: x["text"] for x in sb["letter"]}
        letter = [{"block_id": k, "before": la.get(k), "after": lb.get(k)} for k in dict.fromkeys([*la, *lb])
                  if la.get(k) != lb.get(k)]
        return {"from": a, "to": b, "changed_items": changed, "unchanged_items": unchanged, "letter_changes": letter}

    # ---- letter revisions and export
    def letter(self, sid, rev=None):
        snap = self.snapshot(sid)
        with self.store.read() as con:
            if rev:
                row = con.execute("SELECT * FROM dossier_letters WHERE id=? AND snapshot_id=?", (rev, sid)).fetchone()
                if row is None:
                    raise NotFound("ไม่พบฉบับแก้ไขนี้", "missing_revision")
            else:
                row = con.execute("SELECT * FROM dossier_letters WHERE snapshot_id=? ORDER BY rowid DESC LIMIT 1", (sid,)).fetchone()
            revisions = [dict(r) | {"blocks": None} for r in con.execute(
                "SELECT id, parent_id, created_at, note FROM dossier_letters WHERE snapshot_id=? ORDER BY rowid", (sid,))]
        blocks = json.loads(row["blocks"]) if row else snap["letter"]
        return {"snapshot_id": sid, "revision": row["id"] if row else None, "blocks": blocks, "revisions": revisions,
                "notice": DRAFT_NOTICE}

    def save_letter(self, sid, body):
        current = self.letter(sid)
        edits = (body or {}).get("blocks")
        if not isinstance(edits, list) or not edits:
            raise CoreError("ต้องส่งข้อความที่แก้ไข", "invalid_letter")
        by_id = {b["block_id"]: dict(b) for b in current["blocks"]}
        for e in edits:
            if not isinstance(e, dict) or e.get("block_id") not in by_id or not isinstance(e.get("text"), str) \
                    or len(e["text"]) > 4000:
                raise CoreError("ข้อความที่แก้ไขไม่ถูกต้อง", "invalid_letter")
            block = by_id[e["block_id"]]
            if e["text"] != block["text"]:
                block.setdefault("original_text", block["text"])
                block["text"], block["operator_edited"] = e["text"], True
        blocks = [by_id[b["block_id"]] for b in current["blocks"]]
        rid = uuid4().hex
        note = (body or {}).get("note")
        with self.store.tx() as con:
            con.execute("INSERT INTO dossier_letters VALUES (?,?,?,?,?,?)",
                        (rid, sid, current["revision"], utc_now(), note if isinstance(note, str) else None, dumps(blocks)))
        return self.letter(sid, rid)

    def export(self, sid, fmt, rev=None):
        letter = self.letter(sid, rev)
        snap = self.snapshot(sid)
        title = f"{snap['dossier']['dossier_id']} reply draft {sid[:8]}"
        if fmt == "docx":
            return letters.render_docx(letter["blocks"], title, DRAFT_NOTICE), \
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document", f"reply-{sid[:8]}.docx"
        if fmt == "html":
            return letters.render_html(letter["blocks"], title, DRAFT_NOTICE).encode("utf-8"), "text/html", f"reply-{sid[:8]}.html"
        raise CoreError("รองรับเฉพาะ docx และ html", "invalid_format")

    def page(self, sid, item_id, index):
        """The page behind a citation: page text with the quote span, plus file and page links."""
        snap = self.snapshot(sid)
        item = next((i for i in snap["items"] if i["item_id"] == item_id), None)
        if item is None or not 0 <= index < len(item["sources"]):
            raise NotFound("ไม่พบหลักฐานนี้ในแฟ้มฉบับนี้", "missing_citation")
        ref = item["sources"][index]
        if ref.get("file_sha256"):
            _name, data = self.blob(ref["file_sha256"])
            text = letters.page_text(letters.read_layout(data), ref["page"])
            link = f"/api/dossier/files/{ref['file_sha256']}#page={ref['page']}"
        else:
            text = source(self.pack(), ref["source_id"], ref["part"])["text"]
            link = ref.get("url")
        return {"item_id": item_id, "ref": ref, "page_text": text, "open_url": link,
                "verified": text[ref["start"]:ref["end"]] == ref["quote"]}

    # ---- learning loop
    def correct(self, body):
        body = body or {}
        snap = self.snapshot(body.get("snapshot_id", ""))
        item = next((i for i in snap["items"] if i["item_id"] == body.get("item_id")), None)
        cand = item and next((c for c in item.get("candidates", []) if c["passage_id"] == body.get("passage_id")), None)
        if not cand or not cand["accepted"] or body.get("to_role") not in ("patent_disclosure",):
            raise CoreError("แก้ได้เฉพาะหลักฐานที่ทักษะรับเป็นผลของผู้ยื่น ให้เป็นข้อเปิดเผยของสิทธิบัตร", "invalid_correction")
        note = body.get("note") if isinstance(body.get("note"), str) else None
        return self._event("correction", snap["identity"]["skill"]["version"], {
            "snapshot_id": snap["snapshot_id"], "item_id": item["item_id"], "passage_id": cand["passage_id"],
            "source_kind": cand["source_kind"], "from_role": cand["role"], "to_role": body["to_role"], "note": note})

    def propose(self, body):
        cid = (body or {}).get("correction_id")
        correction = next((e for e in self.events("correction") if e["id"] == cid), None)
        if correction is None:
            raise NotFound("ไม่พบบันทึกการแก้ไข", "missing_correction")
        parent = self.skills()[correction["version"]]
        spec = propose_from_correction(parent, correction)
        if spec["version"] in self.skills():
            existing = self.skills()[spec["version"]]
            if spec_sha(existing) != spec_sha(spec):
                raise Conflict("มีรุ่นทักษะหมายเลขนี้แล้วแต่เนื้อหาต่างกัน", "skill_version_taken")
            return {"spec": existing, "created": False}
        with self.store.tx() as con:
            con.execute("INSERT INTO dossier_skills VALUES (?,?,?,?,?)",
                        (spec["version"], dumps(spec), spec_sha(spec), spec["parent"], utc_now()))
        self._event("proposal", spec["version"], {"correction_id": cid, "parent": spec["parent"], "spec_sha256": spec_sha(spec)})
        return {"spec": spec, "created": True}

    def evaluate(self, body):
        from patent_to_pilot.workbench import skill_eval
        version = (body or {}).get("version")
        skills = self.skills()
        if version not in skills:
            raise NotFound("ไม่พบรุ่นทักษะนี้", "unknown_skill")
        spec = skills[version]
        parent = skills.get(spec.get("parent")) if spec.get("parent") else None
        report = skill_eval.evaluate(spec, parent, self.pack(), self.pack_dir)
        return self._event("evaluation", version, report)

    def promote(self, body):
        version = (body or {}).get("version")
        evaluations = [e for e in self.events("evaluation") if e["version"] == version]
        if not evaluations or not evaluations[-1]["passed"]:
            raise Conflict("ต้องผ่านการทดสอบกับชุดพัฒนาแยกและไม่ถดถอยก่อนนำไปใช้", "evaluation_required")
        previous = self.active_skill()
        return self._event("promotion", version, {"previous": previous, "evaluation_id": evaluations[-1]["id"],
                                                  "retained_for_replay": sorted(self.skills())})
