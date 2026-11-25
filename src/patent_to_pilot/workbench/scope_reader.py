"""Offline reader for curated, display-only questions on pinned source editions.

Lexical ranking nominates passages. A preset asks to inspect a named provision or
claim and shows its editor-supplied gloss only after binding the exact scope. This
reader does not judge arbitrary propositions or generate legal advice.
"""
from __future__ import annotations

import json
from pathlib import Path
import re
import sqlite3
from uuid import uuid4

from patent_to_pilot.workbench.acquisition import unit_id
from patent_to_pilot.workbench.core import (Conflict, CoreError, NotFound, OFFSET_CONVENTION,
                                           normalize_requirement, requirement_match, sha256)
from patent_to_pilot.workbench.product_lexical import ProductLexical
from patent_to_pilot.workbench.relation_search import ActionBudget
from patent_to_pilot.workbench.store import Store, dumps, utc_now
from patent_to_pilot.workbench.thai_analyzer import fold

BUNDLE = Path(__file__).parent / "sample" / "scope_reader.json"
CONTRACT = "evidence-scope/1.0"
POLICY = "curated-scope-reader/1.0"
SEED_DEPTH = 2
MAX_BUDGET = 4
CATALOG_FIELDS = ("family_id", "title_th", "question_th", "source_id", "version", "domain", "source_url")
SCOPE_FIELDS = ("parent", "date", "example")


def _key(value):
    return " ".join(fold(value or "").split())


def _mentions(text, target):
    target = _key(target)
    provision = re.fullmatch(r"(มาตรา|ข้อ|วรรค)\s*([0-9]+(?:/[0-9]+)*)", target)
    if provision:
        # Thai prose does not require spaces beside a reference. Match the whole
        # number, including slash subdivisions and named section suffixes.
        kind, number = provision.groups()
        pattern = rf"{kind}\s*{number}(?![0-9]|\s*/\s*[0-9]|\s*(?:ทวิ|ตรี|จัตวา|เบญจ))"
        return re.search(pattern, _key(text)) is not None
    return re.search(r"(?<!\w)" + re.escape(target) + r"(?!\w)", _key(text)) is not None


def _header(entry):
    return {"id": entry["id"], **{field: entry[field] for field in CATALOG_FIELDS},
            "data_origin": entry.get("data_origin", "authored_demo"),
            **{key: entry[key] for key in ("family_title_th", "publication_claim_count", "selected_claim_numbers")
               if key in entry},
            "issue_date": entry.get("issue_date"), "effective_date": entry.get("effective_date")}


def _prepare_units(entry):
    text = entry["text"]
    digest = sha256(text.encode("utf-8"))
    if entry.get("canonical_sha256", digest) != digest:
        raise Conflict("canonical text does not match the recorded digest", "invalid_edition_hash")
    units = {}
    for raw in entry["units"]:
        quote = raw["quote"]
        start = raw.get("start")
        if start is None:
            start = text.find(quote)
            if text.find(quote, start + 1) >= 0:
                raise Conflict("ambiguous excerpt in the bundled edition", "ambiguous_span")
        if not quote or type(start) is not int or start < 0 or text[start:start + len(quote)] != quote:
            raise Conflict("excerpt does not match the bundled edition", "invalid_span")
        uid = unit_id(entry["source_id"], entry["version"], raw["id"])
        if uid in units:
            raise Conflict("duplicate passage identifier", "invalid_bundle")
        units[uid] = {**raw, "id": uid, "passage_id": raw["id"], "start": start, "end": start + len(quote), "sha256": digest,
                      "quote_sha256": sha256(quote.encode("utf-8"))}
    return units


def _compatible(unit, requirement):
    if _key(unit["locator"]) != _key(requirement["locator"]) or not unit.get("meaning_th"):
        return False
    return all(not requirement.get(field) or _key(unit.get(field)) == _key(requirement[field])
               for field in SCOPE_FIELDS)


def _receipt(action, rid, reason, before, after, cost):
    return {"action": action, "requirement_id": rid, "reason_th": reason,
            "before": before, "after": after, "accepted": [i for i in after if i not in before],
            "displaced": [i for i in before if i not in after], "cost": cost}


def _resolve(index, entry, units, requirement, budget):
    """Keep or rerank two BM25 hits, then spend at most one action on scoped lookup."""
    rid = requirement["id"]
    normalized = normalize_requirement({"query": fold(requirement["query"]), "label": requirement["label_th"]}, rid)
    hits = ProductLexical._fts(index, "scope_fts", entry["family_id"], requirement_match(normalized), SEED_DEPTH,
                               None, {entry["source_id"]: entry["version"]})
    initial = [unit_id(hit["source_id"], hit["version_id"], hit["passage_id"]) for hit in hits]
    eligible = [uid for uid in initial if _compatible(units[uid], requirement)]
    actions = []
    winner = None
    reason = "ยังไม่มีหลักฐานที่ตรงกับขอบเขตที่ระบุ"
    # A locator may match multiple paragraphs or examples. Never choose one from a tie
    # using its rank alone. The source's structural index is metadata, not search gold.
    scoped = [uid for uid, unit in units.items() if _key(unit["locator"]) == _key(requirement["locator"])
              and all(not requirement.get(k) or _key(unit.get(k)) == _key(requirement[k]) for k in SCOPE_FIELDS)]
    if len(scoped) > 1:
        reason = "ตำแหน่งนี้ตรงกับหลายข้อความ ต้องระบุขอบเขตให้ชัดขึ้น"
    elif eligible and eligible[0] == initial[0]:
        winner, reason = eligible[0], "ข้อความอันดับแรกตรงกับตำแหน่งและขอบเขตที่เลือก"
        actions.append(_receipt("keep", rid, reason, initial, initial, 0))
    elif not budget.remaining:
        reason = "ใช้งบการค้นเพิ่มครบแล้ว หลักฐานที่ยืนยันได้ยังไม่ครบ"
    elif eligible:
        budget.consume("rerank")
        winner, reason = eligible[0], "เลือกข้อความในผลค้นเดิมที่ตรงกับขอบเขต"
        actions.append(_receipt("rerank", rid, reason, initial, [winner] + [i for i in initial if i != winner], 1))
    else:
        budget.consume("acquire")
        found = [uid for uid in scoped if _compatible(units[uid], requirement)]
        after = (found + [i for i in initial if i not in found])[:SEED_DEPTH]
        actions.append(_receipt("acquire", rid, "ค้นตำแหน่งที่ระบุภายในเอกสารฉบับเดียวกัน", initial, after, 1))
        if found:
            winner, reason = found[0], "พบข้อความที่ตรงกับตำแหน่งและขอบเขตหลังค้นเพิ่ม"
    if winner is None:
        after = actions[-1]["after"] if actions else initial
        actions.append(_receipt("qualify", rid, reason, after, after, 0))
    return winner, reason, actions


def _evidence(entry, unit):
    rights = entry["rights"]
    quote_allowed = rights.get("quote") is True and rights.get("export_quote") is True
    return {"id": unit["id"], "source_id": entry["source_id"], "version": entry["version"],
            "source_url": entry["source_url"], "sha256": unit["sha256"], "quote_sha256": unit["quote_sha256"],
            "start": unit["start"], "end": unit["end"], "offset_convention": OFFSET_CONVENTION,
            "locator": unit["locator"], "kind": unit["kind"], "quote": unit["quote"] if quote_allowed else None,
            "meaning_th": unit["meaning_th"] if quote_allowed else None,
            "gloss_basis": "curated_display_translation", "scope_basis": "selected_edition_and_curated_locator",
            **{k: unit.get(k) for k in SCOPE_FIELDS}}


def _graph(units, evidence, requirements):
    nodes = [{"id": "req:" + r["id"], "kind": "requirement", "label_th": r["label_th"]} for r in requirements]
    nodes.extend({"id": uid, "kind": u["kind"], "label_th": u["locator"]} for uid, u in evidence.items())
    edges = [{"from": "req:" + r["id"], "to": r["evidence_id"], "type": "inferred",
              "label_th": "ระบบจับคู่ตามขอบเขต", "evidence_id": r["evidence_id"]}
             for r in requirements if r["evidence_id"]]
    unresolved = []
    for uid in evidence:
        unit = units[uid]
        references = list(unit.get("references", []))
        if unit.get("parent"):
            references.append(unit["parent"])
        for locator in dict.fromkeys(references):
            targets = [key for key, target in units.items() if _key(target["locator"]) == _key(locator)]
            if len(targets) != 1 or targets[0] not in evidence or not _mentions(unit["quote"], locator):
                unresolved.append({"from": uid, "locator": locator, "status": "unresolved"})
                continue
            edges.append({"from": uid, "to": targets[0], "type": "stated", "label_th": "ต้นฉบับอ้างถึง",
                          "evidence_id": uid})
    return nodes, edges, unresolved


def _evaluate(entry, limit):
    units = _prepare_units(entry)
    actions, requirements, evidence = [], [], {}
    budget = ActionBudget(limit)
    index = sqlite3.connect(":memory:")
    try:
        index.row_factory = sqlite3.Row
        index.execute("CREATE VIRTUAL TABLE scope_fts USING fts5(project_id UNINDEXED, source_id UNINDEXED, "
                      "version_id UNINDEXED, passage_id UNINDEXED, candidate_id UNINDEXED, body, tokenize='unicode61')")
        index.executemany("INSERT INTO scope_fts VALUES (?, ?, ?, ?, ?, ?)",
                          ((entry["family_id"], entry["source_id"], entry["version"], unit["passage_id"],
                            entry["id"], fold(unit["quote"])) for unit in units.values()))
        for req in entry["requirements"]:
            winner, reason, steps = _resolve(index, entry, units, req, budget)
            actions.extend(steps)
            if winner:
                evidence[winner] = _evidence(entry, units[winner])
            requirements.append({"id": req["id"], "label_th": req["label_th"], "locator": req["locator"],
                                 **{k: req.get(k) for k in SCOPE_FIELDS}, "reason_th": reason,
                                 "status": "bound" if winner else "unresolved", "evidence_id": winner})
    finally:
        index.close()
    nodes, edges, unresolved = _graph(units, evidence, requirements)
    complete = requirements and all(r["evidence_id"] for r in requirements) and not unresolved
    return {**_header(entry), "id": uuid4().hex, "example_id": entry["id"], "contract": CONTRACT,
            "policy": POLICY, "created_at": utc_now(), "input_sha256": sha256(dumps(entry).encode("utf-8")),
            "source_sha256": sha256(entry["text"].encode("utf-8")), "status": "complete" if complete else "qualified",
            "originals": [{key: source[key] for key in ("url", "sha256", "retrieved_utc")}
                          for source in entry.get("originals", [])],
            "rights": {k: entry["rights"].get(k) is True for k in ("quote", "export_quote")},
            "baseline": {"method": "sqlite_fts5_bm25_unicode61", "depth": SEED_DEPTH, "queries": len(requirements)},
            "budget": {**budget.describe(), "unit": "supplemental_actions"},
            "requirements": requirements, "evidence": list(evidence.values()), "nodes": nodes,
            "edges": edges, "unresolved_relations": unresolved, "actions": actions}


class ScopeReader:
    def __init__(self, store: Store):
        self.store = store
        with store.tx() as con:
            con.execute("CREATE TABLE IF NOT EXISTS reader_runs "
                        "(id TEXT PRIMARY KEY, example_id TEXT NOT NULL, version TEXT NOT NULL, trace TEXT NOT NULL)")
            con.execute("CREATE TABLE IF NOT EXISTS reader_editions "
                        "(source_id TEXT, version TEXT, digest TEXT NOT NULL, PRIMARY KEY(source_id, version))")

    def _examples(self):
        entries = json.loads(BUNDLE.read_text(encoding="utf-8-sig"))["examples"]
        seen, editions = set(), {}
        for entry in entries:
            key = (entry["source_id"], entry["version"])
            digest = sha256(entry["text"].encode("utf-8"))
            req_ids = [r["id"] for r in entry["requirements"]]
            if (entry["id"] in seen or editions.setdefault(key, digest) != digest
                    or not req_ids or len(set(req_ids)) != len(req_ids)):
                raise Conflict("inconsistent example or edition identity", "invalid_bundle")
            seen.add(entry["id"])
        return entries

    def catalog(self):
        with self.store.read() as con:
            runs = [dict(row) for row in con.execute("SELECT id, example_id, version FROM reader_runs ORDER BY rowid DESC")]
        return {"examples": [_header(entry) for entry in self._examples()], "runs": runs}

    def run(self, body):
        if not isinstance(body, dict) or set(body) - {"example_id", "budget", "question_th"}:
            raise CoreError("คำขอต้องระบุตัวอย่างและใช้อาร์กิวเมนต์ที่รองรับ", "invalid_request")
        limit = body.get("budget", MAX_BUDGET)
        if type(limit) is not int or not 0 <= limit <= MAX_BUDGET:
            raise CoreError("งบการค้นเพิ่มต้องเป็นจำนวนเต็มตั้งแต่ 0 ถึง 4", "invalid_budget")
        entry = next((e for e in self._examples() if e["id"] == body.get("example_id")), None)
        if entry is None:
            raise NotFound("ไม่พบตัวอย่างที่เลือก", "unknown_example")
        question = body.get("question_th", entry["question_th"])
        if not isinstance(question, str) or question.strip() != entry["question_th"].strip():
            raise CoreError("ตัวอย่างนี้รองรับเฉพาะคำถามที่แสดงไว้", "unsupported_question")
        trace = _evaluate(entry, limit)
        key = (entry["source_id"], entry["version"])
        with self.store.tx() as con:
            con.execute("INSERT OR IGNORE INTO reader_editions VALUES (?,?,?)", (*key, trace["source_sha256"]))
            digest = con.execute("SELECT digest FROM reader_editions WHERE source_id=? AND version=?", key).fetchone()[0]
            if digest != trace["source_sha256"]:
                raise Conflict("source bytes changed under the same version identifier", "immutable_edition")
            con.execute("INSERT INTO reader_runs VALUES (?,?,?,?)", (trace["id"], entry["id"], entry["version"], dumps(trace)))
        return trace

    def replay(self, run_id):
        with self.store.read() as con:
            row = con.execute("SELECT trace FROM reader_runs WHERE id=?", (run_id,)).fetchone()
        if row is None:
            raise NotFound("ไม่พบบันทึกการอ่านนี้", "missing_run")
        return json.loads(row["trace"])
