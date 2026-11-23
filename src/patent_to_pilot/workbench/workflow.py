"""P4-T01: Search, Compare and Inspect on the existing Workbench store (owner note 22 Nov 2026).

Everything here reads or writes the same SQLite store through the same ``EvidenceCore``; no model, network or paid
call is used.

* **Search** -- a free-text query over the project's current-scope passage index. ``terms`` and ``phrase`` modes are
  SQLite FTS5 BM25 queries (``unicode61``); ``literal`` is an explicitly labelled case-sensitive substring scan of the
  same current passages, for Thai text inside longer unsegmented runs. Each result carries the exact passage quote,
  its code-point offsets in the stored canonical text and the offsets of the highlighted matches.
* **Requirements** -- explicit requirements typed by the user are validated (``core.normalize_requirement``) and stored
  in the project's mission. Bounded-field requirements keep the G01 parser; free-text requirements are searched and
  their best passage is reported as evidence without any judgement. The sample and synthetic projects stay fixed.
* **Compare** -- runs the requirement set through the assessment path (``EvidenceCore.run_comparison``). P4-T03: for an
  owner project that path itself takes at most one structural acquisition action per obligation (``POLICY_V2``) BEFORE
  the assessment is committed; Compare shows the persisted action receipt linked to each committed assessment
  (``acquisition``), and ``{"acquisition": "baseline"}`` runs the comparable no-action mode. The earlier read-only
  side-by-side of one ``POLICY_V1`` relation search (``relation_action``) is only computed on explicit request
  (``legacy_side_by_side``) and is labelled an ENGINEERING DEMO, never a committed improvement; the synthetic P2-T03
  packet keeps ``RelationSearchSlice``.
* **Inspect** -- opens any span of a stored source version, verifies the stored bytes, reports the original artifact
  and the page/region mapping where one exists (P0-T06 nodes, or ``[page N]`` markers of the PDF text layer), and says
  so plainly when no page or region mapping exists.
"""
from __future__ import annotations

import json
import re

from patent_to_pilot.workbench import product_lexical as PL
from patent_to_pilot.workbench import relation_search as R
from patent_to_pilot.workbench import trace_slice as T
from patent_to_pilot.workbench.core import (OFFSET_CONVENTION, Conflict, EvidenceCore, NotFound, ValidationFailed,
                                            fts_phrase, fts_terms, normalize_requirement, requirement_kind,
                                            requirement_match, sha256, MAX_REQUIREMENTS)
from patent_to_pilot.workbench.store import dumps, utc_now

TASK_ID = "P4-T01"
# P4-T01a: "auto" (default) is the product Thai-aware route (product_lexical.auto_search); "terms", "phrase" and
# "literal" stay as advanced options on the legacy unicode61 index, unchanged.
SEARCH_MODES = ("auto", "terms", "phrase", "literal")
SEARCH_LIMIT_DEFAULT, SEARCH_LIMIT_MAX = 10, 50
MAX_QUERY_CHARS = 500
SNIPPET_CHARS = 240
FIXED_ORIGINS = ("synthetic_fixture", "synthetic_demo")
FTS_ROUTE = "sqlite_fts5_bm25_current_scope (unicode61)"
LITERAL_ROUTE = "literal_substring_scan_current_scope (case-sensitive; not FTS5, no ranking)"
ENGINEERING_DEMO_LABEL = ("ENGINEERING DEMO - one bounded relation-search action under the pinned default policy. "
                          "It shows what the mechanism did on these sources; it is not a research result and says "
                          "nothing about retrieval quality.")
ADAPTER_FORM = "project adapter of relation_search.relation_search_step (Workbench FTS5 backend, no hypotheses)"
SLICE_FORM = "relation_search.RelationSearchSlice (Workbench form, synthetic P2-T03 packet)"
REFERENCE_DETECTOR = ("explicit-cross-reference-v1: 'Annex|Appendix|Schedule|Exhibit|Attachment <label>' or "
                      "'ภาคผนวก <label>' in a seed passage; bound only when a pool passage has a line starting with the "
                      "same reference (a heading). A structural signal, not a semantic judgement.")
_THAI = re.compile(r"[฀-๿]")
_WORD = re.compile(r"\w+", re.UNICODE)
_REF = re.compile(r"\b(Annex|Appendix|Schedule|Exhibit|Attachment)\s+([A-Z0-9]{1,4})\b|ภาคผนวก\s*([ก-ฮA-Z0-9]{1,4})")
_PAGE_MARK = re.compile(r"^\[page (\d+)\]$", re.M)
MAX_RELATIONS = 40


def _heading_re(kind: str, label: str) -> re.Pattern:
    return re.compile(rf"^[ \t#>*-]*{re.escape(kind)}\s*{re.escape(label)}(?![A-Za-z0-9ก-ฮ])", re.M)


def node_id(source_id: str, version_id: str, passage_id: str) -> str:
    return f"{source_id}@{version_id}#{passage_id}"


def split_node(nid: str) -> tuple[str, str, str]:
    sv, pid = nid.split("#", 1)
    sid, vid = sv.split("@", 1)
    return sid, vid, pid


class Workflow:
    def __init__(self, core: EvidenceCore) -> None:
        self.core, self.store = core, core.store

    # ================================================================== shared reads
    def _project(self, project_id: str) -> dict:
        with self.store.read() as con:
            return self.core._project(con, project_id)

    def _index(self, con, project_id: str) -> dict:
        n = con.execute("SELECT COUNT(*) FROM passage_fts WHERE project_id=?", (project_id,)).fetchone()[0]
        versions = sorted(f"{s}@{v}" for s, v in self.core._current_versions(con, project_id).items())
        return {"passages": n, "source_versions": versions,
                "corpus_revision": sha256(dumps(versions).encode("utf-8"))[:16]}

    def _project_lexical(self, con, project_id: str, match: str, limit: int,
                         candidate_id: str | None = None) -> list[dict]:
        """FTS5 BM25 over every current passage of the project (all candidates unless one is given). Same SQL and
        tie-break as ``EvidenceCore._lexical``; the current-version invariant is re-checked."""
        current = self.core._current_versions(con, project_id)
        sql = ("SELECT source_id, version_id, passage_id, candidate_id, bm25(passage_fts) AS score FROM passage_fts "
               "WHERE passage_fts MATCH ? AND project_id=?")
        args: list = [match, project_id]
        if candidate_id is not None:
            sql += " AND candidate_id=?"
            args.append(candidate_id)
        rows = con.execute(sql + " ORDER BY score, source_id, version_id, passage_id LIMIT ?", (*args, limit)).fetchall()
        out = []
        for r in rows:
            if current.get(r["source_id"]) != r["version_id"]:
                raise RuntimeError("current lexical index contains a non-current version")
            out.append({"source_id": r["source_id"], "version_id": r["version_id"], "passage_id": r["passage_id"],
                        "candidate_id": r["candidate_id"], "bm25": round(r["score"], 6)})
        return out

    def _passage(self, con, project_id: str, sid: str, vid: str, pid: str, texts: dict) -> dict:
        """One stored passage with its offsets verified against the stored canonical text."""
        if (sid, vid) not in texts:
            v = con.execute("SELECT text, sha256, title, candidate_id FROM source_versions WHERE project_id=? AND "
                            "source_id=? AND version_id=?", (project_id, sid, vid)).fetchone()
            texts[(sid, vid)] = dict(v)
        v = texts[(sid, vid)]
        p = con.execute("SELECT start_char, end_char, quote FROM passages WHERE project_id=? AND source_id=? AND "
                        "version_id=? AND passage_id=?", (project_id, sid, vid, pid)).fetchone()
        s, e = p["start_char"], p["end_char"]
        if v["text"][s:e] != p["quote"]:
            raise ValidationFailed(f"{sid}@{vid}#{pid}: stored passage does not match its source", "citation_integrity")
        return {"node_id": node_id(sid, vid, pid), "source_id": sid, "version_id": vid, "passage_id": pid,
                "candidate_id": v["candidate_id"], "title": v["title"], "sha256": v["sha256"], "start_char": s,
                "end_char": e, "quote": p["quote"]}

    # ================================================================== requirements
    def requirements(self, project_id: str) -> dict:
        proj = self._project(project_id)
        editable = proj["data_origin"] not in FIXED_ORIGINS
        reqs = []
        for r in proj["mission"]["requirements"]:
            reqs.append({**r, "kind": requirement_kind(r), "match": r.get("match", "phrase"),
                         "fts_match": requirement_match(r)})
        out = {"project_id": project_id, "editable": editable, "requirements": reqs,
               "candidates": proj["mission"]["candidates"]}
        lifecycle = self.core.requirement_lifecycle(project_id)   # P4-T01b: revisions and removed requirements
        for r in reqs:
            r["lifecycle_revision"] = lifecycle["active"].get(r["requirement_id"], 0)
        out.update(mission_revision=lifecycle["mission_revision"], removed=lifecycle["removed"])
        if not editable:
            out["note"] = ("The sample and synthetic projects are fixed so their recorded results stay reproducible. "
                           "Create a project to type your own requirements.")
        if proj["data_origin"] == "synthetic_demo":
            with self.store.read() as con:
                out["bound_requirements"] = [dict(r) for r in con.execute(
                    "SELECT requirement_id, query_id, query_text, start_char, end_char, text FROM bound_requirements "
                    "WHERE project_id=?", (project_id,))]
        return out

    def save_requirement(self, project_id: str, body: dict) -> dict:
        """Create or update one explicit requirement of an owner project. A new requirement opens one obligation per
        candidate; an edited one reopens its obligations (its next run re-acquires and commits a new assessment
        version; earlier versions stay in history)."""
        proj = self._project(project_id)
        if proj["data_origin"] in FIXED_ORIGINS:
            raise Conflict("the sample and synthetic projects are fixed; create a project for your own requirements",
                           "project_is_fixed")
        if not isinstance(body, dict):
            raise ValidationFailed("body must be an object", "bad_requirement")
        mission = proj["mission"]
        reqs = list(mission["requirements"])
        rid = body.get("requirement_id")
        with self.store.read() as con:   # P4-T01b: a removed requirement keeps its ID; it is never reused
            removed = {r[0] for r in con.execute("SELECT requirement_id FROM requirement_lifecycle WHERE project_id=? "
                                                 "AND state='removed'", (project_id,))}
        if rid in (None, ""):
            taken = {r["requirement_id"] for r in reqs} | removed
            rid = next(f"U{n}" for n in range(1, 10_000) if f"U{n}" not in taken)
        elif rid in removed:
            raise Conflict(f"requirement {rid} was removed; use Undo (restore) to bring it back. A removed ID is never "
                           "reused for another requirement.", "requirement_removed")
        new = normalize_requirement(body, rid)
        old = next((r for r in reqs if r["requirement_id"] == rid), None)
        if old is None and len(reqs) >= MAX_REQUIREMENTS:
            raise ValidationFailed(f"at most {MAX_REQUIREMENTS} requirements per project", "too_many_requirements")
        if old == new:
            return {"status": "unchanged", "requirement": new, "fts_match": requirement_match(new)}
        reqs = [new if r["requirement_id"] == rid else r for r in reqs] if old else reqs + [new]
        mission = {**mission, "requirements": reqs}
        now = utc_now()
        new_sha = sha256(dumps(new).encode("utf-8"))
        event_id = self.core._new_event_id("REQ")
        reopened = []
        with self.store.tx() as con:
            con.execute("UPDATE projects SET mission_json=? WHERE project_id=?", (dumps(mission), project_id))
            # P4-T01b: every add/edit advances the requirement and mission lifecycle revisions
            self.core._advance_lifecycle(con, project_id, new, "active",
                                         next(i for i, r in enumerate(reqs) if r["requirement_id"] == rid), event_id, now)
            self.core._advance_mission(con, project_id, now)
            for c in mission["candidates"]:
                reason = f"requirement {rid} {'edited' if old else 'added'} ({event_id})"
                if old:
                    con.execute("UPDATE obligations SET state='open', reason=?, updated_at=? WHERE project_id=? AND "
                                "candidate_id=? AND requirement_id=?", (reason, now, project_id, c["candidate_id"], rid))
                else:
                    con.execute("INSERT OR REPLACE INTO obligations VALUES (?,?,?,?,?,?)",
                                (project_id, c["candidate_id"], rid, "open", reason, now))
                reopened.append(f"{c['candidate_id']}/{rid}")
            result = {"event_id": event_id, "requirement_id": rid, "action": "edited" if old else "added",
                      "reopened_obligations": reopened,
                      "note": f"Requirement {rid} {'edited' if old else 'added'}; {len(reopened)} obligation(s) "
                              "reopened. Run the comparison to assess it."}
            con.execute("INSERT INTO change_events VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                        (project_id, event_id, "requirement_change", rid, new_sha[:12],
                         sha256(dumps(old).encode("utf-8"))[:12] if old else None, new_sha, "applied", None,
                         dumps(result), now, now))
        return {"status": "edited" if old else "added", "requirement": new, "fts_match": requirement_match(new),
                "kind": requirement_kind(new), **result}

    # ================================================================== requirement lifecycle (P4-T01b)
    def archive_requirement(self, project_id: str, requirement_id: str, body: dict | None = None) -> dict:
        return self.core.archive_requirement(project_id, requirement_id, body if isinstance(body, dict) else {})

    def restore_requirement(self, project_id: str, requirement_id: str, body: dict | None = None) -> dict:
        return self.core.restore_requirement(project_id, requirement_id, body if isinstance(body, dict) else {})

    # ================================================================== search
    def search(self, project_id: str, body: dict) -> dict:
        body = body if isinstance(body, dict) else {}
        query = body.get("query")
        if not isinstance(query, str) or not query.strip() or len(query) > MAX_QUERY_CHARS:
            raise ValidationFailed(f"query must be 1-{MAX_QUERY_CHARS} characters", "bad_query")
        mode = body.get("mode") or "auto"
        if mode not in SEARCH_MODES:
            raise ValidationFailed(f"mode must be one of {list(SEARCH_MODES)}", "bad_mode")
        limit = body.get("limit", SEARCH_LIMIT_DEFAULT)
        if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= SEARCH_LIMIT_MAX:
            raise ValidationFailed(f"limit must be an integer 1-{SEARCH_LIMIT_MAX}", "bad_limit")
        proj = self._project(project_id)
        cand = body.get("candidate_id") or None
        if cand is not None and cand not in {c["candidate_id"] for c in proj["mission"]["candidates"]}:
            raise ValidationFailed(f"unknown candidate {cand}", "unknown_candidate")
        if mode == "auto":
            return PL.auto_search(self, project_id, proj, query, cand, limit)
        notes = []
        texts: dict = {}
        with self.store.read() as con:
            index = self._index(con, project_id)
            if mode == "literal":
                needle = query.strip()
                sql = ("SELECT source_id, version_id, passage_id, candidate_id FROM passage_fts WHERE project_id=? AND "
                       "instr(body, ?) > 0")
                args: list = [project_id, needle]
                if cand:
                    sql += " AND candidate_id=?"
                    args.append(cand)
                current = self.core._current_versions(con, project_id)
                rows = con.execute(sql + " ORDER BY source_id, version_id, passage_id LIMIT ?", (*args, limit)).fetchall()
                hits = []
                for r in rows:
                    if current.get(r["source_id"]) != r["version_id"]:
                        raise RuntimeError("current lexical index contains a non-current version")
                    hits.append({**dict(r), "bm25": None})
                match, route = None, LITERAL_ROUTE
            else:
                match = fts_terms(query) if mode == "terms" else fts_phrase(query)
                hits = self._project_lexical(con, project_id, match, limit, cand)
                route = FTS_ROUTE
                if _THAI.search(query):
                    notes.append("The unicode61 tokenizer does not split Thai words: a Thai term matches only a whole "
                                 "space-delimited run. Use Literal mode to find Thai text inside a longer run.")
            results = []
            for rank, h in enumerate(hits, start=1):
                p = self._passage(con, project_id, h["source_id"], h["version_id"], h["passage_id"], texts)
                marks = self._marks(p["quote"], query.strip(), mode)
                results.append({"rank": rank, **p, "score_bm25": h["bm25"], "data_origin": proj["data_origin"],
                                "offset_convention": OFFSET_CONVENTION,
                                "matches": [{"start_char": p["start_char"] + a, "end_char": p["start_char"] + b}
                                            for a, b in marks],
                                **self._snippet(p, marks)})
        if not index["passages"]:
            notes.append("This project has no searchable passages yet. Add documents on the Evidence page.")
        elif not results:
            notes.append("No current passage matched. Try fewer words, Terms mode, or Literal mode for Thai text.")
        return {"task": TASK_ID, "project_id": project_id, "query": query, "mode": mode, "route": route,
                "fts_match": match, "candidate_id": cand, "limit": limit, "index": index, "results": results,
                "result_count": len(results), "notes": notes, "paid_model_calls": 0, "remote_calls": 0}

    @staticmethod
    def _marks(quote: str, query: str, mode: str) -> list[tuple[int, int]]:
        """Offsets (inside the passage) of the literal text that matched: the substring for literal mode, otherwise
        the word tokens equal (case-insensitively) to a query token. Tokens that FTS5 matched only after its own
        diacritic folding are not highlighted."""
        if mode == "literal":
            out, i = [], quote.find(query)
            while i >= 0:
                out.append((i, i + len(query)))
                i = quote.find(query, i + len(query))
            return out
        want = {t.lower() for t in _WORD.findall(query)}
        return [(m.start(), m.end()) for m in _WORD.finditer(quote) if m.group(0).lower() in want]

    @staticmethod
    def _snippet(p: dict, marks: list[tuple[int, int]]) -> dict:
        q = p["quote"]
        if len(q) <= SNIPPET_CHARS:
            a, b = 0, len(q)
        else:
            first = marks[0][0] if marks else 0
            a = max(0, min(first - SNIPPET_CHARS // 3, len(q) - SNIPPET_CHARS))
            b = a + SNIPPET_CHARS
        return {"snippet": q[a:b], "snippet_start_char": p["start_char"] + a, "snippet_end_char": p["start_char"] + b,
                "snippet_truncated": (a, b) != (0, len(q))}

    # ================================================================== inspect
    def inspect(self, project_id: str, source_id: str, version_id: str, start: str | int, end: str | int) -> dict:
        try:
            s, e = int(start), int(end)
        except (TypeError, ValueError):
            raise ValidationFailed("span offsets must be integers", "bad_span") from None
        sv = self.core.source_version(project_id, source_id, version_id)
        text = sv["text"]
        if not 0 <= s < e <= len(text):
            raise ValidationFailed(f"span [{s},{e}) is outside {source_id}@{version_id} (0..{len(text)})", "bad_span")
        with self.store.read() as con:
            raw = con.execute("SELECT raw FROM source_versions WHERE project_id=? AND source_id=? AND version_id=?",
                              (project_id, source_id, version_id)).fetchone()["raw"]
            stored_ok = sha256(raw) == sv["sha256"] and raw.decode("utf-8") == text
            passages = [dict(r) for r in con.execute(
                "SELECT passage_id, start_char, end_char FROM passages WHERE project_id=? AND source_id=? AND "
                "version_id=? AND start_char < ? AND end_char > ? ORDER BY start_char",
                (project_id, source_id, version_id, e, s))]
            nodes = []
            for r in con.execute("SELECT node_id, anchor, kind, start_char, end_char, regions_json, parser_id FROM "
                                 "doc_nodes WHERE project_id=? AND source_id=? AND version_id=? AND start_char < ? AND "
                                 "end_char > ? ORDER BY start_char", (project_id, source_id, version_id, e, s)):
                d = dict(r)
                d["regions"] = json.loads(d.pop("regions_json"))
                nodes.append(d)
            pages = [dict(r) for r in con.execute(
                "SELECT page, display_width_pt, display_height_pt, rotation_degrees FROM source_pages WHERE "
                "project_id=? AND source_id=? AND version_id=? ORDER BY page", (project_id, source_id, version_id))]
            orig = con.execute("SELECT media_type, sha256, size_bytes, storage_ref, raw FROM original_artifacts WHERE "
                               "project_id=? AND source_id=? AND version_id=?",
                               (project_id, source_id, version_id)).fetchone()
            # P4-T03: the persisted document structure overlapping the span (rule and confidence per node)
            structure = {"build": self.core.structure.summary(con, project_id, source_id, version_id),
                         "nodes": [{k: n[k] for k in ("node_key", "kind", "ident_key", "section_path", "start",
                                                      "end", "head_text", "passage_id", "rule", "confidence")}
                                   for n in self.core.structure.nodes(con, project_id, source_id, version_id)
                                   if n["start"] < e and n["end"] > s]}
        if not stored_ok:
            raise ValidationFailed("stored canonical text does not match its recorded hash", "citation_integrity")
        base = f"/api/projects/{project_id}/sources/{source_id}/versions/{version_id}"
        if orig is not None:
            original = {"state": "kept", "media_type": orig["media_type"], "sha256": orig["sha256"],
                        "size_bytes": orig["size_bytes"], "storage_ref": orig["storage_ref"],
                        "integrity": "verified" if sha256(orig["raw"]) == orig["sha256"] else "MISMATCH",
                        "same_bytes_as_canonical_text": orig["sha256"] == sv["sha256"], "url": base + "/original"}
        else:
            original = {"state": "not_kept",
                        "note": "No separate original file is stored for this version (it was imported before original "
                                "files were kept, or from a text fixture). The stored canonical text bytes are shown and "
                                "verified against their hash."}
        regions = [{"node_id": n["node_id"], "kind": n["kind"], **r} for n in nodes for r in n["regions"]]
        if regions:
            mapping = {"state": "regions", "pages": sorted({r["page"] for r in regions}), "regions": regions,
                       "page_sizes": pages, "basis": "doc_nodes regions recorded at import (parser "
                       f"{nodes[0]['parser_id']}); bbox is normalized [x0, y0, x1, y1], top-left origin"}
        elif sv["source_kind"] == "owner_pdf":
            marks = [(m.start(), int(m.group(1))) for m in _PAGE_MARK.finditer(text)]
            first = [p for off, p in marks if off <= s]
            last = [p for off, p in marks if off < e]
            if first and last:
                mapping = {"state": "page_only", "pages": list(range(first[-1], last[-1] + 1)), "regions": [],
                           "basis": "the '[page N]' marker lines of the PDF text layer (pdf_text_layer_v1); no region "
                                    "geometry was extracted, so the location inside the page is not shown"}
            else:
                mapping = {"state": "none", "pages": [], "regions": [],
                           "reason": "the span lies before the first page marker of this PDF text layer"}
        else:
            mapping = {"state": "none", "pages": [], "regions": [],
                       "reason": "This source version has no page or region mapping (plain text or Markdown, or no "
                                 "layout was recorded). Only the exact canonical text span is available."}
        return {"task": TASK_ID, "project_id": project_id, "source_id": source_id, "version_id": version_id,
                "title": sv["title"], "status": sv["status"], "current_version": sv["current_version"],
                "all_versions": sv["all_versions"], "data_origin": sv["data_origin"], "source_kind": sv["source_kind"],
                "license": sv["license"], "sha256": sv["sha256"], "stored_text_integrity": "verified",
                "start_char": s, "end_char": e, "offset_convention": OFFSET_CONVENTION, "quote": text[s:e],
                "text_before": text[:s], "text_after": text[e:], "passages": passages, "nodes": nodes,
                "page_mapping": mapping, "original_artifact": original, "origin_path": sv["origin_path"],
                "structure": structure}

    def original(self, project_id: str, source_id: str, version_id: str) -> tuple[bytes, str, str]:
        self.core.source_version(project_id, source_id, version_id)   # project / source / version must exist
        with self.store.read() as con:
            o = con.execute("SELECT media_type, sha256, raw FROM original_artifacts WHERE project_id=? AND source_id=? "
                            "AND version_id=?", (project_id, source_id, version_id)).fetchone()
        if o is None:
            raise NotFound(f"no original file is stored for {source_id}@{version_id}", "original_not_kept")
        if sha256(o["raw"]) != o["sha256"]:
            raise ValidationFailed("stored original bytes do not match their hash", "original_integrity")
        ext = {"application/pdf": ".pdf", "text/markdown": ".md"}.get(o["media_type"], ".txt")
        return o["raw"], o["media_type"], f"{source_id}@{version_id}{ext}"

    # ================================================================== compare
    def compare(self, project_id: str, body: dict | None = None, invoked_via: str = "http") -> dict:
        body = body if isinstance(body, dict) else {}
        proj = self._project(project_id)
        mission = proj["mission"]
        if proj["data_origin"] == "synthetic_demo":
            return self._compare_synthetic(project_id)
        wanted = body.get("requirement_ids")
        reqs = [r for r in mission["requirements"] if not wanted or r["requirement_id"] in wanted]
        if wanted and len(reqs) != len(set(wanted)):
            raise ValidationFailed("unknown requirement id in requirement_ids", "unknown_requirement")
        run = None
        if body.get("run", True) and mission["requirements"]:
            # P4-T03: the structural acquisition step runs INSIDE this assessment run (before commit)
            r = self.core.run_comparison(project_id, invoked_via=invoked_via, acquisition=body.get("acquisition"))
            run = {"run_id": r["run_id"], "status": r["status"], "stop_reason": r["stop_reason"],
                   "counters": r["counters"], "provider_dispatch": self.core.acquisition.run_usage(r["run_id"])}
        cmp_ = self.core.comparison(project_id)
        texts: dict = {}
        out = []
        with self.store.read() as con:
            for req in reqs:
                cells = []
                for c in mission["candidates"]:
                    cell = next((x for x in cmp_["cells"] if x["candidate_id"] == c["candidate_id"]
                                 and x["requirement_id"] == req["requirement_id"]), None)
                    if cell and cell["citation"]:
                        ci = cell["citation"]
                        cell = {**cell, "citation": {**ci, **{k: v for k, v in self._passage(
                            con, project_id, ci["source_id"], ci["version_id"], ci["passage_id"], texts).items()
                            if k in ("quote", "title", "sha256")}}}
                    cells.append({"candidate_id": c["candidate_id"], "candidate_label": c["label"], "cell": cell})
                entry = {"requirement": {**req, "kind": requirement_kind(req), "match": req.get("match", "phrase"),
                                         "fts_match": requirement_match(req)},
                         "assessments": cells,
                         # P4-T03: read from the persisted run trace (the receipt linked to the committed assessment)
                         "acquisition": self.core.acquisition.trace_for(project_id, req["requirement_id"], cells)}
                if body.get("legacy_side_by_side"):
                    # P4-T01 read-only V1 demonstration, only on explicit request; never a committed improvement
                    entry["side_by_side"] = self.relation_action(project_id, req)
                out.append(entry)
        counters = (run or {}).get("counters") or {}
        return {"task": TASK_ID, "subtask": "P4-T03", "project_id": project_id, "data_origin": proj["data_origin"],
                "run": run, "requirements": out, "engineering_demo_label": ENGINEERING_DEMO_LABEL,
                "assessment_path": ("EvidenceCore.run_comparison (PLAN -> seed search -> at most one structural action "
                                    f"under {R.POLICY_V2.name} -> assess against the original requirement -> COMMIT)"),
                "acquisition_policy": {"name": R.POLICY_V2.name, "sha256": R.POLICY_V2_SHA256},
                # P4-T03: the run's own counters (not constants); provider dispatch is measured in run.provider_dispatch
                "paid_model_calls": counters.get("paid_model_calls", 0), "remote_calls": counters.get("remote_calls", 0),
                "counters_source": "run counters of this request's run" if run else "no run in this request"}

    # ---------------------------------------------------------------- one bounded relation-search action
    def relation_action(self, project_id: str, req: dict) -> dict:
        """Baseline (seed search) vs ONE bounded relation search under ``POLICY_V1`` for one requirement, over the
        project's current FTS5 passages. Read-only: nothing is written to the store."""
        rid, text = req["requirement_id"], req["query"]
        qr = R.QueryRequirements(f"{project_id}:{rid}", text, (R.Requirement(rid, 0, len(text), text),))
        mask = R.workbench_mask(profile_id="project-current-versions-only")
        budget = R.ActionBudget(R.WORKBENCH_BUDGET)
        terms = T._terms(text) or [t for t in _WORD.findall(text.lower())]
        seed_match = T._or_match(terms)
        registry = R.EvidenceRegistry()
        texts: dict = {}
        with self.store.read() as con:
            index = self._index(con, project_id)
            budget.consume("seed_search")
            seed_hits = self._project_lexical(con, project_id, seed_match, R.WORKBENCH_FETCH_LIMIT)
            seed = [node_id(h["source_id"], h["version_id"], h["passage_id"]) for h in seed_hits
                    if not mask.reason(node_id(h["source_id"], h["version_id"], h["passage_id"]))][:T.RESULT_LIMIT]

            def passage(nid: str) -> dict:
                return self._passage(con, project_id, *split_node(nid), texts)

            def states(pool: list[str]) -> list[R.RelationState]:
                return self._reference_states(qr, seed, pool, registry, passage)
            states_before = states(seed)
            box: dict = {}

            def search(query: R.ExpansionQuery, limit: int, _mask) -> list[tuple]:
                box["hits"] = self._project_lexical(con, project_id, query.text, limit)
                return [(node_id(h["source_id"], h["version_id"], h["passage_id"]), -h["bm25"]) for h in box["hits"]]

            def assess(after: tuple) -> list[R.RelationState]:
                return states(list(after))

            def rerank(request: R.RerankRequest, ids: tuple) -> dict:
                rterms = T._terms(" ".join(request.requirement_texts)) or terms
                rows = self._project_lexical(con, project_id, T._or_match(rterms), 10_000)
                sc = {node_id(h["source_id"], h["version_id"], h["passage_id"]): -h["bm25"] for h in rows}
                return {i: sc[i] for i in ids if i in sc}

            record = R.relation_search_step(
                requirements=qr, relations=states_before, pool_before=seed, search=search, assess=assess,
                rerank=rerank, budget=budget, eligibility=mask, evidence=registry, policy=R.POLICY_V1,
                result_limit=T.RESULT_LIMIT, fetch_limit=R.WORKBENCH_FETCH_LIMIT)
            delta = record["candidate_delta"]
            after = delta["after_ids"] if delta else seed
            final = record["rerank"]["final_ids"] if record.get("rerank") else seed
            cards = {nid: passage(nid) for nid in dict.fromkeys(seed + after)}
        return self._side_by_side(rid, ADAPTER_FORM, False, None, seed_match, seed, record, after, final, cards, index)

    def _reference_states(self, qr: R.QueryRequirements, seed: list[str], pool: list[str], registry, passage):
        """Deterministic explicit cross-reference coverage: every reference in a seed passage is a relation; it is
        supported when exactly one pool passage has a heading line for the same reference, else unresolved."""
        req = qr.requirements[0]
        rterms = T._terms(req.text)
        quotes = {nid: passage(nid) for nid in dict.fromkeys(seed + pool)}

        def ev_full(nid: str) -> str:
            p = quotes[nid]
            return registry.add_evidence(T.SourceEvidence(f"ev:{nid}", nid, p["start_char"], p["end_char"],
                                                          p["quote"])).evidence_id
        out: dict[str, R.RelationState] = {}
        for nid in seed:
            p = quotes[nid]
            own = T._terms(p["quote"])
            other = {t for n in seed if n != nid for t in T._terms(quotes[n]["quote"])}
            anchors = tuple(t for t in rterms if t in own and t not in other)
            for m in _REF.finditer(p["quote"]):
                if len(out) >= MAX_RELATIONS:
                    break
                kind, label = (m.group(1), m.group(2)) if m.group(1) else ("ภาคผนวก", m.group(3))
                s, e = p["start_char"] + m.start(), p["start_char"] + m.end()
                ref = registry.add_evidence(T.SourceEvidence(f"ev:{nid}[{s}:{e}]", nid, s, e, m.group(0)))
                head = _heading_re(kind, label)
                heads = [n for n in pool if head.search(quotes[n]["quote"])]
                key = f"reference:{ref.evidence_id}"
                if len(heads) == 1:
                    out[key] = R.RelationState(key, req.requirement_id, "cross_document_reference", "supported", nid,
                                               ref.quote, ref.evidence_id, anchors, (ev_full(nid), ev_full(heads[0])),
                                               note=f"bound to heading in {heads[0]}")
                else:
                    out[key] = R.RelationState(key, req.requirement_id, "cross_document_reference", "unresolved", nid,
                                               ref.quote, ref.evidence_id, anchors, (ev_full(nid),),
                                               note="no heading for this reference in the candidate pool" if not heads
                                               else f"{len(heads)} headings for this reference (ambiguous)")
        return [out[k] for k in sorted(out)]

    @staticmethod
    def _side_by_side(rid, form, recorded, run_id, seed_match, seed, record, after, final, cards, index) -> dict:
        delta = record.get("candidate_delta") or {}
        new = delta.get("new_ids", [])
        outcome = record["outcome"]
        summary = {
            "searched": (f"One relation search was issued; {len(new)} new candidate(s) entered the pool."
                         if new else "One relation search was issued; it returned no new candidate."),
            "no_unresolved_relation": "No unresolved, search-actionable relation in the seed results, so no extra "
                                      "search was issued (the action budget was not spent).",
            "budget_exhausted": "The action budget was already spent; no extra search was issued."}[outcome]
        cov = record.get("coverage") or {}
        return {
            "label": ENGINEERING_DEMO_LABEL, "requirement_id": rid, "form": form, "recorded_in_store": recorded,
            "run_id": run_id, "policy": {"name": record["policy"]["name"], "sha256": record["policy"]["sha256"]},
            "reference_detector": REFERENCE_DETECTOR if form == ADAPTER_FORM else T.ASSESSOR_ID,
            "eligibility": record["eligibility"]["trace_id"], "outcome": outcome, "summary": summary,
            "seed_query": seed_match, "issued_query": (record.get("query") or {}).get("submitted_text"),
            "query_terms": (record.get("query") or {}).get("terms", []),
            "selected_relation": record["selection"]["selected_relation_key"],
            "selection": record["selection"], "coverage_before": cov.get("before", []),
            "coverage_after": cov.get("after"), "requirement_status_before": cov.get("requirement_before"),
            "requirement_status_after": cov.get("requirement_after"),
            "baseline": {"ids": list(seed), "candidates": [cards[i] for i in seed]},
            "action": {"before_ids": delta.get("before_ids", list(seed)), "returned_ids": delta.get("returned_ids", []),
                       "after_ids": list(after), "new_ids": list(new), "final_ids": list(final),
                       "candidates": [{**cards[i], "is_new": i in new} for i in final]},
            "budget": record["budget_after"], "search_calls": 1 + record["search_calls"], "index": index,
            "paid_model_calls": 0, "remote_calls": 0}

    # ---------------------------------------------------------------- synthetic P2-T03 packet (the Workbench form)
    def load_synthetic_example(self) -> dict:
        """Opt-in: create the labelled synthetic P2-T03 project in this store (once) and run the Workbench form of the
        relation search on it. Its sources keep original PDF bytes and page regions, so Inspect can show them."""
        sl = R.RelationSearchSlice(self.core)
        with self.store.read() as con:
            exists = con.execute("SELECT 1 FROM projects WHERE project_id=?", (R.PROJECT_ID,)).fetchone()
        if not exists:
            sl.setup()
        return {"project_id": R.PROJECT_ID, "created": not exists, "label": T.SYNTHETIC_LABEL,
                "side_by_side": self._run_slice(sl)}

    def _run_slice(self, sl: R.RelationSearchSlice) -> dict:
        res = sl.run_relation_search()
        rec = res["record"]
        texts: dict = {}
        delta = rec.get("candidate_delta") or {}
        after = delta.get("after_ids", res["seed_nodes"])
        final = rec["rerank"]["final_ids"] if rec.get("rerank") else res["seed_nodes"]
        with self.store.read() as con:
            cards = {nid: self._passage(con, sl.pid, *split_node(nid), texts)
                     for nid in dict.fromkeys(res["seed_nodes"] + after)}
            index = self._index(con, sl.pid)
        seed_match = T._or_match(T._terms(sl.requirement()["text"]))
        out = self._side_by_side(rec["requirements"]["requirements"][0]["requirement_id"], SLICE_FORM, True, sl.run_id,
                                 seed_match, res["seed_nodes"], rec, after, final, cards, index)
        out["synthetic_label"] = T.SYNTHETIC_LABEL
        return out

    def _compare_synthetic(self, project_id: str) -> dict:
        if project_id != R.PROJECT_ID:
            raise Conflict("this synthetic project has no relation-search packet; open the P2-T03 example",
                           "synthetic_compare_unavailable")
        sl = R.RelationSearchSlice(self.core)
        sbs = self._run_slice(sl)
        req = sl.requirement()
        a = sl.state["assessment"]
        evid = sl.resolve_evidence(a["evidence_ids"])
        assessment = {"assessment_id": a["assessment_id"], "status": a["status"], "assessor_id": T.ASSESSOR_ID,
                      "basis": "runtime_not_gold",
                      "evidence": [{"evidence_id": x.evidence_id, "node_id": x.node_id, "start_char": x.start,
                                    "end_char": x.end, "quote": x.quote, **dict(zip(
                                        ("source_id", "version_id", "passage_id"), split_node(x.node_id)))}
                                   for x in evid]}
        return {"task": TASK_ID, "project_id": project_id, "data_origin": "synthetic_demo", "run": {
                    "run_id": sl.run_id, "status": "completed", "stop_reason": None, "counters": {}},
                "requirements": [{"requirement": {"requirement_id": req["requirement_id"], "label": req["text"],
                                                  "query": req["query_text"], "kind": "source_bound_span",
                                                  "span": [req["start_char"], req["end_char"]]},
                                  "assessments": [], "runtime_assessment": assessment, "side_by_side": sbs}],
                "engineering_demo_label": ENGINEERING_DEMO_LABEL, "synthetic_label": T.SYNTHETIC_LABEL,
                "assessment_path": "RelationSearchSlice deterministic reference-coverage assessor (synthetic slice)",
                "paid_model_calls": 0, "remote_calls": 0}
