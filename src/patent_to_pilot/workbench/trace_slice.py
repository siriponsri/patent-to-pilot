"""P0-T06: a source-bound SYNTHETIC search-and-trace slice on the existing Workbench engine.

Everything this module loads is an authored synthetic packet (``fixtures/p0_t06_synthetic``): a fictional letter whose
Clause 5 is governed by a separately filed Annex B, a decoy Annex A, a footnote that qualifies Clause 4, and one controlled
revision of Annex B. It demonstrates engineering plumbing only; it is not a real document, not an evaluation and not
evidence of retrieval quality.

What is real (executed, not authored):
* the sources are imported through ``EvidenceCore._import_source`` into the existing store, keeping three distinct
  artifacts per version: the original PDF bytes (``original_artifacts``), the canonical UTF-8 text
  (``source_versions``) and the page/region mapping of every node (``source_pages`` + ``doc_nodes``);
* both search actions run SQLite FTS5 BM25 over the current-scope index through ``EvidenceCore._lexical``; candidate pools
  before/after are the actual returned rows;
* the annex binding is resolved from the acquired pool (a reference label must meet exactly one annex heading);
* the revision goes through the same import transaction, the dependency rules predict what must be re-checked, and the
  re-check (search replay + re-assessment) is executed and compared with the prediction.

What is authored: the packet text, its line layout (regions are authored line bands, not glyph boxes), the synonym table
that produces the one search hypothesis, and the deterministic reference-coverage assessor (a structural signal, never a
semantic judgement). Generated hypotheses are a separate type and can never be cited as evidence (enforced in code, in
the SQLite schema and in the trace checks).

CLI::

    python -m patent_to_pilot.workbench.trace_slice --out trace.json [--data-dir DIR]
    python -m patent_to_pilot.workbench.trace_slice --regenerate-fixtures   # rebuild PDFs/text/layout from packet.json
"""
from __future__ import annotations

import argparse
import base64
from dataclasses import dataclass, field
from datetime import datetime
import hashlib
import json
from pathlib import Path
import platform
import re
import sqlite3
import sys
import tempfile

from patent_to_pilot.workbench.core import (PROGRAM_ID, Conflict, CoreError, EvidenceCore, NotFound,
                                            ValidationFailed)
from patent_to_pilot.workbench.store import dumps, utc_now

HERE = Path(__file__).resolve().parent
FIXTURE_DIR = HERE / "fixtures" / "p0_t06_synthetic"
SCHEMA_PATH = HERE / "schemas" / "evidence_trace.schema.json"
SCHEMA_SHA256 = "4ec5e368a141f796611fd1e1dccef08e0e48cf11ed1d591529985a57569d40a3"  # owner spec, copied verbatim
BUNDLE_SCHEMA = "ptp-p0-t06-trace-bundle/1"
SYNTHETIC_LABEL = "SYNTHETIC WORKFLOW EXAMPLE: authored fixture, not a real document and not an evaluation"
CLAIM_BOUNDARY = ("Engineering plumbing only. The packet, its layout and the synonym table are authored; the searches, "
                  "pools, bindings and revision re-check are executed. No retrieval-effectiveness claim follows.")
PROJECT_ID = "synthetic-p0-t06-trace-slice"
CANDIDATE_ID = "syn-packet"
GOAL_ID = "P0-T06"
PARSER_ID = "authored-fixture-layout-v1"
NORMALIZATION_ID = "authored-lines-lf-formfeed-page-break-v1"
CHUNKER_ID = "authored-line-nodes-v1"
ROUTE_ID = "sqlite-fts5-bm25-current-scope"
ELIGIBILITY_ID = "synthetic-packet-current-versions-only"
ASSESSOR_ID = "deterministic-reference-coverage-v1 (synthetic slice; structural signal, not a semantic judgement)"
RESULT_LIMIT = 5
ALIGN_METHOD = "fixture_anchor_match"
OFFSET_UNIT = "unicode_code_points_half_open"
STOPWORDS = frozenset("a an and are at by for from in is it of on or the to what which with applies apply".split())

_ANNEX_REF = re.compile(r"\bAnnex ([A-Z])\b")
_ANNEX_HEAD = re.compile(r"^Annex ([A-Z])\.")
_FOOT_MARK = re.compile(r"\[(\d+)\]")
_FOOT_HEAD = re.compile(r"^\[(\d+)\] ")
_TERM = re.compile(r"\w+", re.UNICODE)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# =========================================================================== typed records
class HypothesisNotEvidence(ValidationFailed):
    """A generated search hypothesis was offered where only source evidence is allowed."""
    code = "hypothesis_not_evidence"


@dataclass(frozen=True)
class SourceEvidence:
    """An exact canonical-text span of one node of one immutable source version."""
    evidence_id: str
    node_id: str
    start: int
    end: int
    quote: str
    kind: str = field(default="source_evidence", init=False)

    def as_trace(self) -> dict:
        return {"evidence_id": self.evidence_id, "kind": self.kind, "node_id": self.node_id,
                "span": {"start": self.start, "end": self.end, "unit": OFFSET_UNIT}, "quote": self.quote}


@dataclass(frozen=True)
class SearchHypothesis:
    """Generated query material. It may shape a search; it is never a citation."""
    hypothesis_id: str
    text: str
    generator_id: str
    generation_config_sha256: str | None
    source_evidence_ids: tuple[str, ...]
    kind: str = field(default="generated_search_hypothesis", init=False)

    def as_trace(self) -> dict:
        return {"hypothesis_id": self.hypothesis_id, "kind": self.kind, "text": self.text,
                "generator_id": self.generator_id, "generation_config_sha256": self.generation_config_sha256,
                "source_evidence_ids": list(self.source_evidence_ids)}


def require_source_evidence(item) -> SourceEvidence:
    """Type gate used before anything is cited: a hypothesis (or anything else) is refused."""
    if isinstance(item, SearchHypothesis):
        raise HypothesisNotEvidence(f"{item.hypothesis_id} is a generated search hypothesis and cannot be cited")
    if not isinstance(item, SourceEvidence):
        raise ValidationFailed(f"{type(item).__name__} is not source evidence", "not_source_evidence")
    return item


# =========================================================================== authoring (deterministic fixture build)
PAGE_W, PAGE_H = 612.0, 792.0
MARGIN_X, MARGIN_TOP, LINE_H, FONT_PT, BASELINE_DROP = 72.0, 72.0, 18.0, 11.0, 13.0


def layout_document(doc: dict) -> dict:
    """Canonical text and node layout of an authored document spec. Each line is one node; lines are joined with LF,
    each page ends with LF and pages are separated by a form feed line ("\\f\\n"). A node region is the authored line
    band (full text-column width, one line height), normalized to the displayed page with a top-left origin."""
    parts, nodes, pos = [], [], 0
    for pno, lines in enumerate(doc["pages"], start=1):
        if pno > 1:
            parts.append("\f\n")
            pos += 2
        slot = -1
        for ln in lines:
            text = ln["text"]
            if not text or "\n" in text or "\f" in text or not text.isascii():
                raise ValueError(f"{doc['source_id']}: lines must be non-empty single-line ASCII ({ln['anchor']})")
            slot = ln.get("slot", slot + 1)
            top = MARGIN_TOP + slot * LINE_H
            if top + LINE_H > PAGE_H - 36:
                raise ValueError(f"{doc['source_id']}: line {ln['anchor']} falls off the page")
            bbox = [round(MARGIN_X / PAGE_W, 6), round(top / PAGE_H, 6), round((PAGE_W - MARGIN_X) / PAGE_W, 6),
                    round((top + LINE_H) / PAGE_H, 6)]
            nodes.append({"anchor": ln["anchor"], "kind": ln["kind"], "start": pos, "end": pos + len(text),
                          "page": pno, "slot": slot, "bbox": bbox})
            parts.append(text + "\n")
            pos += len(text) + 1
    canonical = "".join(parts)
    anchors = [n["anchor"] for n in nodes]
    if len(set(anchors)) != len(anchors):
        raise ValueError(f"{doc['source_id']}: duplicate anchors")
    return {"canonical": canonical, "nodes": nodes, "n_pages": len(doc["pages"])}


def _pdf_str(text: str) -> bytes:
    return ("(" + text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)") + ")").encode("ascii")


def build_pdf(doc: dict, layout: dict) -> bytes:
    """A minimal, deterministic PDF 1.4 (Helvetica, WinAnsi) that draws every authored line at its layout slot."""
    n = layout["n_pages"]
    page_objs = [5 + 2 * i for i in range(n)]
    objs: list[bytes] = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        ("<< /Type /Pages /Kids [" + " ".join(f"{p} 0 R" for p in page_objs) + f"] /Count {n} >>").encode("ascii"),
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>",
        b"<< /Title " + _pdf_str("SYNTHETIC FIXTURE " + doc["title"]) + b" /Producer "
        + _pdf_str("patent_to_pilot.workbench.trace_slice authoring v1") + b" >>",
    ]
    for pno in range(1, n + 1):
        ops = []
        for node in (x for x in layout["nodes"] if x["page"] == pno):
            text = layout["canonical"][node["start"]:node["end"]]
            y = PAGE_H - (MARGIN_TOP + node["slot"] * LINE_H) - BASELINE_DROP
            ops.append(b"BT /F1 %d Tf %d %.2f Td " % (int(FONT_PT), int(MARGIN_X), y) + _pdf_str(text) + b" Tj ET")
        stream = b"\n".join(ops) + b"\n"
        content_no = page_objs[pno - 1] + 1
        objs.append((f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {int(PAGE_W)} {int(PAGE_H)}] /Resources << /Font "
                     f"<< /F1 3 0 R >> >> /Contents {content_no} 0 R >>").encode("ascii"))
        objs.append(b"<< /Length %d >>\nstream\n" % len(stream) + stream + b"endstream")
    out = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = []
    for i, body in enumerate(objs, start=1):
        offsets.append(len(out))
        out += b"%d 0 obj\n" % i + body + b"\nendobj\n"
    xref = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objs) + 1)
    for off in offsets:
        out += b"%010d 00000 n \n" % off
    out += b"trailer\n<< /Size %d /Root 1 0 R /Info 4 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objs) + 1, xref)
    return bytes(out)


def _doc_specs(packet: dict) -> list[dict]:
    return list(packet["documents"]) + [packet["revision"]]


def author_artifacts(doc: dict) -> dict:
    """Generated files of one document version: original PDF bytes, canonical text bytes and the layout record."""
    lay = layout_document(doc)
    pdf = build_pdf(doc, lay)
    canonical = lay["canonical"].encode("utf-8")
    layout = {"layout_schema": "ptp-p0-t06-layout/1", "synthetic": True, "label": SYNTHETIC_LABEL,
              "source_id": doc["source_id"], "version_id": doc["version_id"], "title": doc["title"],
              "parser_id": PARSER_ID, "normalization_id": NORMALIZATION_ID,
              "original": {"file": doc["file_stem"] + ".pdf", "media_type": "application/pdf", "sha256": sha256(pdf)},
              "canonical": {"file": doc["file_stem"] + ".canonical.txt", "sha256": sha256(canonical)},
              "pages": [{"number": p, "display_width_pt": PAGE_W, "display_height_pt": PAGE_H, "rotation_degrees": 0}
                        for p in range(1, lay["n_pages"] + 1)],
              "region_basis": "authored line band: full text-column width x one line height (not glyph-tight)",
              "nodes": [{k: x[k] for k in ("anchor", "kind", "start", "end", "page", "bbox")} for x in lay["nodes"]]}
    return {"pdf": pdf, "canonical": canonical,
            "layout": (json.dumps(layout, ensure_ascii=False, indent=1) + "\n").encode("utf-8")}


def regenerate_fixtures(fixture_dir: Path = FIXTURE_DIR) -> dict:
    packet = json.loads((fixture_dir / "packet.json").read_text(encoding="utf-8"))
    files = {"packet.json": sha256((fixture_dir / "packet.json").read_bytes())}
    for doc in _doc_specs(packet):
        art = author_artifacts(doc)
        for suffix, key in ((".pdf", "pdf"), (".canonical.txt", "canonical"), (".layout.json", "layout")):
            name = doc["file_stem"] + suffix
            (fixture_dir / name).write_bytes(art[key])
            files[name] = sha256(art[key])
    manifest = {"manifest_schema": "ptp-p0-t06-fixture-manifest/1", "synthetic": True, "label": SYNTHETIC_LABEL,
                "note": "Generated by trace_slice.regenerate_fixtures() from packet.json; do not edit generated files.",
                "files": dict(sorted(files.items()))}
    (fixture_dir / "MANIFEST.json").write_text(json.dumps(manifest, indent=1) + "\n", encoding="utf-8")
    return manifest


# =========================================================================== loading (verified)
def load_packet(fixture_dir: Path = FIXTURE_DIR) -> dict:
    """Read the packet and its generated artifacts, verifying every hash and every node span."""
    fixture_dir = Path(fixture_dir)
    manifest = json.loads((fixture_dir / "MANIFEST.json").read_text(encoding="utf-8"))
    if not manifest.get("synthetic"):
        raise ValidationFailed("fixture manifest is not labelled synthetic", "fixture_not_synthetic")
    for name, digest in manifest["files"].items():
        if sha256((fixture_dir / name).read_bytes()) != digest:
            raise ValidationFailed(f"fixture file {name} does not match MANIFEST.json", "fixture_hash")
    packet = json.loads((fixture_dir / "packet.json").read_text(encoding="utf-8"))
    if not packet.get("synthetic") or packet.get("data_origin") != "synthetic_demo":
        raise ValidationFailed("packet is not labelled synthetic", "fixture_not_synthetic")
    arts = {}
    for doc in _doc_specs(packet):
        arts[(doc["source_id"], doc["version_id"])] = _load_artifact(fixture_dir, doc)
    q, r = packet["question"]["text"], packet["requirement"]["text"]
    if q.find(r) < 0:
        raise ValidationFailed("the requirement is not a span of the question", "requirement_not_bound")
    return {"packet": packet, "artifacts": arts, "manifest": manifest,
            "manifest_sha256": sha256((fixture_dir / "MANIFEST.json").read_bytes()), "dir": fixture_dir}


def _load_artifact(fixture_dir: Path, doc: dict) -> dict:
    layout = json.loads((fixture_dir / (doc["file_stem"] + ".layout.json")).read_text(encoding="utf-8"))
    pdf = (fixture_dir / layout["original"]["file"]).read_bytes()
    canonical_bytes = (fixture_dir / layout["canonical"]["file"]).read_bytes()
    if sha256(pdf) != layout["original"]["sha256"] or sha256(canonical_bytes) != layout["canonical"]["sha256"]:
        raise ValidationFailed(f"{doc['file_stem']}: artifact hash does not match its layout", "fixture_hash")
    text = canonical_bytes.decode("utf-8", errors="strict")
    for nd in layout["nodes"]:
        if not (0 <= nd["start"] < nd["end"] <= len(text)) or "\n" in text[nd["start"]:nd["end"]]:
            raise ValidationFailed(f"{doc['file_stem']}#{nd['anchor']}: span does not resolve", "fixture_span")
        if not 1 <= nd["page"] <= len(layout["pages"]):
            raise ValidationFailed(f"{doc['file_stem']}#{nd['anchor']}: page out of range", "fixture_page")
    if (layout["source_id"], layout["version_id"]) != (doc["source_id"], doc["version_id"]):
        raise ValidationFailed(f"{doc['file_stem']}: layout identity mismatch", "fixture_identity")
    return {"doc": doc, "pdf": pdf, "canonical_bytes": canonical_bytes, "text": text, "layout": layout}


# =========================================================================== schema + semantic checks
def load_schema() -> dict:
    raw = SCHEMA_PATH.read_bytes()
    if sha256(raw) != SCHEMA_SHA256:
        raise RuntimeError("bundled evidence_trace.schema.json differs from the owner specification copy")
    return json.loads(raw.decode("utf-8"))


def schema_errors(event: dict) -> list[str]:
    from jsonschema import Draft202012Validator
    v = Draft202012Validator(load_schema())
    return sorted(f"{'/'.join(str(p) for p in e.absolute_path) or '<root>'}: {e.message}" for e in v.iter_errors(event))


def index_manifest_bytes(index: dict) -> bytes:
    body = {k: v for k, v in index.items() if k not in ("index_id", "manifest_sha256")}
    return json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def semantic_errors(event: dict) -> list[str]:
    """The five semantic checks of DOCUMENT_IR.md section 7, as far as one event can show them."""
    err: list[str] = []
    # 1. resolve the source
    texts, pages = {}, {}
    for s in event.get("sources", []):
        vid = s["version_id"]
        oa, ct = s["original_artifact"], s["canonical_text"]
        if "content_base64" in oa:
            try:
                raw = base64.b64decode(oa["content_base64"], validate=True)
            except ValueError:
                err.append(f"{vid}: original content is not base64")
                raw = None
            if raw is not None and sha256(raw) != oa["sha256"]:
                err.append(f"{vid}: original bytes do not match original sha256")
        if "text" in ct:
            if sha256(ct["text"].encode("utf-8")) != ct["sha256"]:
                err.append(f"{vid}: canonical text does not match canonical sha256")
            texts[vid] = ct["text"]
        if oa["sha256"] == ct["sha256"] and oa["media_type"] == "application/pdf":
            err.append(f"{vid}: a PDF original and its canonical text cannot share one hash")
        pages[vid] = {p["number"] for p in s["pages"]}
    nodes = {n["node_id"]: n for n in event.get("nodes", [])}
    for n in nodes.values():
        vid = n["source_version_id"]
        if vid not in pages:
            err.append(f"{n['node_id']}: source version {vid} is not in the event")
            continue
        sp = n["span"]
        if sp is not None:
            if not sp["start"] < sp["end"]:
                err.append(f"{n['node_id']}: empty or inverted span")
            if vid in texts and sp["end"] > len(texts[vid]):
                err.append(f"{n['node_id']}: span outside canonical text")
        for r in n["regions"]:
            x0, y0, x1, y1 = r["bbox"]
            if not (x0 < x1 and y0 < y1):
                err.append(f"{n['node_id']}: region without positive area")
            if r["page"] not in pages[vid]:
                err.append(f"{n['node_id']}: region page {r['page']} is not a page of {vid}")
        al = n.get("alignment")
        if al and al["prior_node_id"] == n["node_id"]:
            err.append(f"{n['node_id']}: alignment points to itself")
    ev = {e["evidence_id"]: e for e in event.get("evidence", [])}
    for e in ev.values():
        n = nodes.get(e["node_id"])
        if n is None:
            err.append(f"{e['evidence_id']}: node {e['node_id']} is not in the event")
            continue
        if e["span"] is None:
            continue
        s, t = e["span"]["start"], e["span"]["end"]
        if n["span"] is None or not (n["span"]["start"] <= s < t <= n["span"]["end"]):
            err.append(f"{e['evidence_id']}: evidence span is outside its node")
        text = texts.get(n["source_version_id"])
        if text is not None and text[s:t] != e["quote"]:
            err.append(f"{e['evidence_id']}: quote is not the canonical slice")
    # 2. keep types and authority separate
    hyp = {h["hypothesis_id"]: h for h in event.get("hypotheses", [])}
    for both in sorted(set(ev) & set(hyp)):
        err.append(f"{both}: id names both source evidence and a hypothesis")

    def must_be_evidence(where: str, ids) -> None:
        for i in ids:
            if i in hyp:
                err.append(f"{where}: generated hypothesis {i} used as source evidence")
            elif i not in ev:
                err.append(f"{where}: evidence {i} is not in the event")
    for a in event.get("runtime_assessments", []):
        must_be_evidence(a["assessment_id"], a["evidence_ids"])
        if a["requirement_span"]["end"] > len(event["original_query"]["text"]) or \
                a["requirement_span"]["start"] >= a["requirement_span"]["end"]:
            err.append(f"{a['assessment_id']}: requirement span does not resolve in the original query")
    for r in event.get("relations", []):
        must_be_evidence(r["relation_id"], r["provenance"]["evidence_ids"])
        for nid in [r["from_node_id"], r["to_node_id"], *r["scope_node_ids"]]:
            if nid not in nodes:
                err.append(f"{r['relation_id']}: node {nid} is not in the event")
    for h in hyp.values():
        must_be_evidence(h["hypothesis_id"], h["source_evidence_ids"])
    act = event["action"]
    for qid in act["query_artifact_ids"]:
        if qid not in hyp and qid not in ev:
            err.append(f"action: query artifact {qid} is neither a hypothesis nor source evidence")
    if act["selected_assessment_id"] is not None and act["selected_assessment_id"] not in {
            a["assessment_id"] for a in event.get("runtime_assessments", [])}:
        err.append("action: selected assessment is not in the event")
    # 3. reconcile the candidate transition
    cd = event["candidate_delta"]
    before, returned, after, new = cd["before_ids"], cd["returned_ids"], cd["after_ids"], cd["new_ids"]
    if after != before + [x for x in returned if x not in before]:
        err.append("candidate_delta: after is not dedup(before + returned)")
    if new != [x for x in returned if x not in before]:
        err.append("candidate_delta: new is not returned - before")
    if cd["identity_unit"] == "node":
        for x in set(before) | set(returned):
            if x not in nodes:
                err.append(f"candidate_delta: {x} is not a node of the event")
    # 4. index identity binds its manifest
    if sha256(index_manifest_bytes(event["index"])) != event["index"]["manifest_sha256"]:
        err.append("index: manifest_sha256 does not match the identity fields")
    # 5. time and money
    try:
        datetime.fromisoformat(event["event_time"].replace("Z", "+00:00"))
    except ValueError:
        err.append("event_time is not an ISO-8601 date-time")
    if event["mode"] == "synthetic_demo" and event["cost"]["state"] != "not_applicable":
        err.append("a synthetic event cannot carry a billable cost state")
    return err


def check_event(event: dict) -> dict:
    return {"trace_id": event.get("trace_id"), "schema_errors": schema_errors(event),
            "semantic_errors": semantic_errors(event)}


# =========================================================================== the slice engine
def _terms(text: str) -> list[str]:
    out = []
    for t in _TERM.findall(text.lower()):
        if t not in STOPWORDS and t not in out:
            out.append(t)
    return out


def _or_match(phrases: list[str]) -> str:
    """FTS5 MATCH: OR of quoted phrases (each phrase's tokens must be adjacent). Quoting keeps FTS operators inert."""
    return " OR ".join('"' + " ".join(_TERM.findall(p.lower())) + '"' for p in phrases)


class TraceSlice:
    """One synthetic project in an existing store: import -> seed search -> assess -> one structural expansion ->
    bind -> assess, then a controlled revision with predicted vs executed re-check."""

    def __init__(self, core: EvidenceCore, fixture_dir: Path = FIXTURE_DIR, project_id: str = PROJECT_ID) -> None:
        self.core, self.store, self.pid = core, core.store, project_id
        self.fx = load_packet(fixture_dir)
        self.packet = self.fx["packet"]
        self.run_id: str | None = None
        self.seq = 0
        self.hypotheses: dict[str, SearchHypothesis] = {}
        self.search_events: list[dict] = []   # every search event of this slice, in order
        self.state: dict = {}                 # pool / relations / assessment of the latest pipeline

    # ------------------------------------------------------------------ setup
    def setup(self, versions: list[tuple[str, str]] | None = None) -> dict:
        """Create the synthetic project and import the given (source_id, version_id) artifacts (default: the initial
        packet documents)."""
        _manifest, template = self.core._load_sample_inputs()
        mission = json.loads(dumps(template))
        mission.update(goal_id=GOAL_ID, scenario_id=self.packet["packet_id"], data_origin="synthetic_demo",
                       mission=f"{SYNTHETIC_LABEL}. {self.packet['question']['text']}",
                       candidates=[{"candidate_id": CANDIDATE_ID, "label": "Synthetic packet (P0-T06)"}],
                       requirements=[])
        manifest = {"scenario_id": self.packet["packet_id"], "data_origin": "synthetic_demo", "synthetic": True,
                    "label": SYNTHETIC_LABEL, "initial_sources": [], "incoming_changes": [],
                    "fixture_manifest_sha256": self.fx["manifest_sha256"]}
        with self.store.tx() as con:
            if con.execute("SELECT 1 FROM projects WHERE project_id=?", (self.pid,)).fetchone():
                raise Conflict(f"project {self.pid} already exists; use a fresh store", "project_exists")
            con.execute("INSERT INTO projects VALUES (?,?,?,?,?,?,?,?,?)",
                        (self.pid, PROGRAM_ID, GOAL_ID, self.packet["packet_id"], f"{SYNTHETIC_LABEL} (P0-T06)",
                         "synthetic_demo", dumps(mission), dumps(manifest), utc_now()))
            req, q = self.packet["requirement"], self.packet["question"]
            start = q["text"].find(req["text"])
            con.execute("INSERT INTO bound_requirements VALUES (?,?,?,?,?,?,?,?)",
                        (self.pid, req["requirement_id"], q["query_id"], q["text"], start, start + len(req["text"]),
                         req["text"], utc_now()))
        if versions is None:
            versions = [(d["source_id"], d["version_id"]) for d in self.packet["documents"]]
        for key in versions:
            self.import_version(self.fx["artifacts"][key], supersedes=None, event_id=f"SYN-IMPORT-{key[0]}-{key[1]}")
        return {"project_id": self.pid, "imported": [f"{s}@{v}" for s, v in versions]}

    def import_version(self, art: dict, supersedes: str | None, event_id: str) -> None:
        doc, layout, text = art["doc"], art["layout"], art["text"]
        sid, vid = doc["source_id"], doc["version_id"]
        passages = [{"passage_id": nd["anchor"], "start_char": nd["start"], "end_char": nd["end"],
                     "quote": text[nd["start"]:nd["end"]]} for nd in layout["nodes"]]
        entry = {"event_id": event_id, "event_type": "source_revision" if supersedes else "source_addition",
                 "source_id": sid, "version_id": vid, "supersedes_version_id": supersedes, "candidate_id": CANDIDATE_ID,
                 "source_kind": "synthetic_pdf_fixture", "license": "synthetic_fixture_authored_for_p0_t06",
                 "path": f"fixture:p0_t06_synthetic/{layout['canonical']['file']}#original={layout['original']['file']}"}
        prior = {}
        if supersedes:
            with self.store.read() as con:
                prior = {r["anchor"]: r["node_id"] for r in con.execute(
                    "SELECT anchor, node_id FROM doc_nodes WHERE project_id=? AND source_id=? AND version_id=?",
                    (self.pid, sid, supersedes))}

        def extra(con) -> None:
            con.execute("INSERT INTO original_artifacts VALUES (?,?,?,?,?,?,?,?,?)",
                        (self.pid, sid, vid, layout["original"]["media_type"], sha256(art["pdf"]), len(art["pdf"]),
                         art["pdf"], f"sqlite:original_artifacts/{self.pid}/{sid}@{vid}", utc_now()))
            for p in layout["pages"]:
                con.execute("INSERT INTO source_pages VALUES (?,?,?,?,?,?,?)",
                            (self.pid, sid, vid, p["number"], p["display_width_pt"], p["display_height_pt"],
                             p["rotation_degrees"]))
            for nd in layout["nodes"]:
                al = None
                if nd["anchor"] in prior:  # correspondence assertion only; the new node keeps its own identity
                    al = {"prior_node_id": prior[nd["anchor"]], "method": ALIGN_METHOD, "confidence": 1.0}
                con.execute("INSERT INTO doc_nodes VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                            (self.pid, node_id(sid, vid, nd["anchor"]), sid, vid, nd["anchor"], nd["kind"],
                             nd["start"], nd["end"], dumps([{"page": nd["page"], "bbox": nd["bbox"]}]),
                             dumps(al) if al else None, layout["parser_id"]))
        self.core._import_source(self.pid, entry, art["canonical_bytes"], text, passages, doc["title"], extra)

    # ------------------------------------------------------------------ store reads
    def _versions(self, con) -> dict:
        return self.core._current_versions(con, self.pid)

    def nodes(self) -> dict[str, dict]:
        """Every node of every version in the project, with its exact canonical slice."""
        with self.store.read() as con:
            texts = {(r["source_id"], r["version_id"]): r["text"] for r in con.execute(
                "SELECT source_id, version_id, text FROM source_versions WHERE project_id=?", (self.pid,))}
            out = {}
            for r in con.execute("SELECT * FROM doc_nodes WHERE project_id=? ORDER BY source_id, version_id, start_char",
                                 (self.pid,)):
                d = dict(r)
                d["regions"] = json.loads(d.pop("regions_json"))
                al = d.pop("alignment_json")
                d["alignment"] = json.loads(al) if al else None
                d["quote"] = texts[(d["source_id"], d["version_id"])][d["start_char"]:d["end_char"]]
                out[d["node_id"]] = d
        return out

    def requirement(self) -> dict:
        with self.store.read() as con:
            r = con.execute("SELECT * FROM bound_requirements WHERE project_id=?", (self.pid,)).fetchone()
        if not r:
            raise NotFound("no source-bound requirement", "requirement_not_found")
        return dict(r)

    # ------------------------------------------------------------------ typed records (persisted)
    def evidence(self, nid: str, start: int | None = None, end: int | None = None) -> SourceEvidence:
        n = self.nodes()[nid]
        s = n["start_char"] if start is None else start
        e = n["end_char"] if end is None else end
        if not n["start_char"] <= s < e <= n["end_char"]:
            raise ValidationFailed("evidence span is outside its node", "evidence_bounds")
        eid = f"ev:{nid}" if (s, e) == (n["start_char"], n["end_char"]) else f"ev:{nid}[{s}:{e}]"
        with self.store.tx() as con:
            text = con.execute("SELECT text FROM source_versions WHERE project_id=? AND source_id=? AND version_id=?",
                               (self.pid, n["source_id"], n["version_id"])).fetchone()[0]
            item = SourceEvidence(eid, nid, s, e, text[s:e])
            row = con.execute("SELECT node_id, start_char, end_char, quote FROM source_evidence WHERE project_id=? AND "
                              "evidence_id=?", (self.pid, eid)).fetchone()
            if row is None:
                con.execute("INSERT INTO source_evidence VALUES (?,?,?,?,?,?,?)",
                            (self.pid, eid, nid, s, e, item.quote, utc_now()))
            elif tuple(row) != (nid, s, e, item.quote):
                raise Conflict(f"{eid} already exists with different content", "evidence_conflict")
        return item

    def add_hypothesis(self, hyp: SearchHypothesis) -> SearchHypothesis:
        self.resolve_evidence(hyp.source_evidence_ids)
        with self.store.tx() as con:
            con.execute("INSERT OR IGNORE INTO search_hypotheses VALUES (?,?,?,?,?,?,?)",
                        (self.pid, hyp.hypothesis_id, hyp.text, hyp.generator_id, hyp.generation_config_sha256,
                         dumps(list(hyp.source_evidence_ids)), utc_now()))
        self.hypotheses[hyp.hypothesis_id] = hyp
        return hyp

    def resolve_evidence(self, ids) -> list[SourceEvidence]:
        """Resolve ids to stored source evidence. A hypothesis id is refused, whatever the caller intended."""
        out = []
        with self.store.read() as con:
            for i in ids:
                if con.execute("SELECT 1 FROM search_hypotheses WHERE project_id=? AND hypothesis_id=?",
                               (self.pid, i)).fetchone():
                    raise HypothesisNotEvidence(f"{i} is a generated search hypothesis and cannot be cited")
                r = con.execute("SELECT * FROM source_evidence WHERE project_id=? AND evidence_id=?",
                                (self.pid, i)).fetchone()
                if r is None:
                    raise ValidationFailed(f"{i} is not recorded source evidence", "unknown_evidence")
                out.append(require_source_evidence(SourceEvidence(r["evidence_id"], r["node_id"], r["start_char"],
                                                                  r["end_char"], r["quote"])))
        return out

    def record_assessment(self, status: str, evidence_ids: list[str], detail: dict) -> dict:
        req = self.requirement()
        self.resolve_evidence(evidence_ids)
        with self.store.tx() as con:
            n = con.execute("SELECT COUNT(*) FROM runtime_assessments WHERE project_id=?", (self.pid,)).fetchone()[0]
            aid = f"asm-{n + 1:03d}"
            con.execute("INSERT INTO runtime_assessments VALUES (?,?,?,?,?,?,?,?,?,?)",
                        (self.pid, aid, req["requirement_id"], status, detail.get("after_action", ""),
                         dumps(evidence_ids), ASSESSOR_ID, self.run_id or "", dumps(detail), utc_now()))
        return {"assessment_id": aid, "status": status, "evidence_ids": list(evidence_ids), "detail": detail,
                "requirement_span": {"start": req["start_char"], "end": req["end_char"], "unit": OFFSET_UNIT}}

    def record_relation(self, kind: str, frm: str, to: str, scope: list[str], method: str,
                        evidence_ids: list[str], confidence: float | None = None) -> dict:
        self.resolve_evidence(evidence_ids)
        rid = f"rel:{kind}:{frm}->{to}"
        prov = {"method": method, "evidence_ids": list(evidence_ids)}
        if confidence is not None:
            prov["confidence"] = confidence
        rel = {"relation_id": rid, "kind": kind, "from_node_id": frm, "to_node_id": to, "scope_node_ids": list(scope),
               "provenance": prov}
        with self.store.tx() as con:
            con.execute("INSERT OR REPLACE INTO doc_relations VALUES (?,?,?,?,?,?,?,?,?,?)",
                        (self.pid, rid, kind, frm, to, dumps(scope), dumps(prov), "current", utc_now(), None))
        return rel

    # ------------------------------------------------------------------ search + structure
    def _index_identity(self) -> dict:
        with self.store.read() as con:
            rows = con.execute("SELECT c.source_id, c.version_id, v.sha256 FROM current_sources c JOIN source_versions v "
                               "USING (project_id, source_id, version_id) WHERE c.project_id=? ORDER BY c.source_id",
                               (self.pid,)).fetchall()
        corpus = "synthetic-corpus-" + sha256(dumps([f"{r[0]}@{r[1]}:{r[2]}" for r in rows]).encode("utf-8"))[:16]
        idx = {"corpus_revision": corpus, "encoder": None,
               "lexical_config": {"algorithm": "BM25 via SQLite FTS5 bm25() (built-in k1=1.2, b=0.75)",
                                  "tokenizer_id": "fts5-unicode61", "version": f"sqlite-{sqlite3.sqlite_version}",
                                  "k1": 1.2, "b": 0.75},
               "normalization_id": "fts5-unicode61-default-casefold", "chunker_id": CHUNKER_ID}
        idx["manifest_sha256"] = sha256(index_manifest_bytes(idx))
        idx["index_id"] = f"fts5:{self.pid}:{corpus}"
        return {k: idx[k] for k in ("index_id", "manifest_sha256", "corpus_revision", "encoder", "lexical_config",
                                    "normalization_id", "chunker_id")}

    def search(self, match: str, limit: int = RESULT_LIMIT) -> list[dict]:
        """The real FTS5 path of the core (current-scope index, BM25, deterministic tie-break)."""
        with self.store.read() as con:
            hits = self.core._lexical(con, self.pid, CANDIDATE_ID, match, limit, match=match)
        return [{"node_id": node_id(h["source_id"], h["version_id"], h["passage_id"]), "bm25": h["score"]}
                for h in hits]

    def _annex_heading(self, label: str, among: list[str], nodes: dict) -> list[str]:
        return [n for n in among if nodes[n]["kind"] == "annex"
                and (m := _ANNEX_HEAD.match(nodes[n]["quote"])) and m.group(1) == label]

    def _children(self, heading: str, nodes: dict) -> list[str]:
        h = nodes[heading]
        sib = sorted((n for n in nodes.values() if (n["source_id"], n["version_id"]) == (h["source_id"], h["version_id"])),
                     key=lambda n: n["start_char"])
        out, inside = [], False
        for n in sib:
            if n["node_id"] == heading:
                inside = True
            elif inside:
                if n["kind"] in ("annex", "heading"):
                    break
                out.append(n["node_id"])
        return out

    def assess(self, seed_nodes: list[str], pool: list[str], after_action: str) -> tuple[dict, list[dict], list[dict]]:
        """Deterministic reference coverage. Footnote markers bind by closure inside the same immutable version;
        an annex reference binds only to an annex heading that has actually been acquired into the candidate pool
        (cross-document context must be found by search). Unbound references keep the requirement unresolved."""
        nodes = self.nodes()
        evidence_ids, relations, unresolved = [], [], []

        def add(eid: str) -> None:
            if eid not in evidence_ids:
                evidence_ids.append(eid)
        for nid in seed_nodes:
            n = nodes[nid]
            add(self.evidence(nid).evidence_id)
            if n["kind"] == "footnote":
                continue
            local = n["quote"]
            for m in _FOOT_MARK.finditer(local):
                mark = self.evidence(nid, n["start_char"] + m.start(), n["start_char"] + m.end())
                foot = [x for x in nodes.values() if (x["source_id"], x["version_id"]) == (n["source_id"], n["version_id"])
                        and x["kind"] == "footnote" and (h := _FOOT_HEAD.match(x["quote"])) and h.group(1) == m.group(1)]
                if len(foot) != 1:
                    unresolved.append({"from_node_id": nid, "reference": m.group(0), "kind": "footnote",
                                       "evidence_id": mark.evidence_id, "reason": f"{len(foot)} matching footnotes"})
                    continue
                fev = self.evidence(foot[0]["node_id"])
                add(fev.evidence_id)
                relations.append(self.record_relation("qualifies", foot[0]["node_id"], nid, [nid], "explicit_source",
                                                      [fev.evidence_id, mark.evidence_id]))
            for m in _ANNEX_REF.finditer(local):
                ref = self.evidence(nid, n["start_char"] + m.start(), n["start_char"] + m.end())
                heads = self._annex_heading(m.group(1), pool, nodes)
                if len(heads) != 1:
                    unresolved.append({"from_node_id": nid, "reference": m.group(0), "label": m.group(1),
                                       "kind": "annex", "evidence_id": ref.evidence_id,
                                       "reason": "no annex heading with this label in the candidate pool" if not heads
                                       else f"{len(heads)} annex headings with this label (ambiguous)"})
                    continue
                head = heads[0]
                kids = self._children(head, nodes)
                hev = self.evidence(head)
                add(ref.evidence_id)
                add(hev.evidence_id)
                kid_evs = [self.evidence(k).evidence_id for k in kids]
                for k, kev in zip(kids, kid_evs):
                    add(kev)
                    relations.append(self.record_relation("parent_of", head, k, [k], "parser_inferred",
                                                          [hev.evidence_id, kev], confidence=1.0))
                relations.append(self.record_relation("incorporates", nid, head, kids or [head], "explicit_source",
                                                      [ref.evidence_id, hev.evidence_id]))
        status = "unresolved" if (unresolved or not seed_nodes) else "supported"
        a = self.record_assessment(status, evidence_ids, {"after_action": after_action, "unresolved": unresolved,
                                                          "seed_nodes": seed_nodes})
        return a, relations, unresolved

    # ------------------------------------------------------------------ actions
    def _event(self, *, action_id: str, kind: str, match: str, artifact_ids: list[str], selected: str | None,
               before: list[str], returned: list[str], assessments: list[tuple[dict, str]], relations: list[dict],
               hypotheses: list[SearchHypothesis], index: dict, event_time: str, seq: int) -> dict:
        nodes = self.nodes()
        after = before + [x for x in returned if x not in before]
        ev_ids: list[str] = []
        for a, _t in assessments:
            ev_ids += [e for e in a["evidence_ids"] if e not in ev_ids]
        for r in relations:
            ev_ids += [e for e in r["provenance"]["evidence_ids"] if e not in ev_ids]
        for h in hypotheses:
            ev_ids += [e for e in h.source_evidence_ids if e not in ev_ids]
        ev_ids += [e for e in artifact_ids if e.startswith("ev:") and e not in ev_ids]
        evidence = self.resolve_evidence(ev_ids)
        used = set(after) | {e.node_id for e in evidence} | {x for r in relations for x in
                                                              [r["from_node_id"], r["to_node_id"], *r["scope_node_ids"]]}
        versions = sorted({(nodes[n]["source_id"], nodes[n]["version_id"]) for n in used})
        sources, node_out = [], []
        with self.store.read() as con:
            for sid, vid in versions:
                v = con.execute("SELECT text, sha256 FROM source_versions WHERE project_id=? AND source_id=? AND "
                                "version_id=?", (self.pid, sid, vid)).fetchone()
                o = con.execute("SELECT * FROM original_artifacts WHERE project_id=? AND source_id=? AND version_id=?",
                                (self.pid, sid, vid)).fetchone()
                pg = con.execute("SELECT * FROM source_pages WHERE project_id=? AND source_id=? AND version_id=? ORDER BY "
                                 "page", (self.pid, sid, vid)).fetchall()
                sources.append({
                    "source_id": sid, "version_id": version_key(sid, vid),
                    "original_artifact": {"media_type": o["media_type"], "storage_ref": o["storage_ref"],
                                          "sha256": o["sha256"],
                                          "content_base64": base64.b64encode(o["raw"]).decode("ascii")},
                    "canonical_text": {"storage_ref": f"sqlite:source_versions/{self.pid}/{sid}@{vid}",
                                       "sha256": v["sha256"], "normalization_id": NORMALIZATION_ID, "text": v["text"]},
                    "pages": [{"number": p["page"], "display_width_pt": p["display_width_pt"],
                               "display_height_pt": p["display_height_pt"], "rotation_degrees": p["rotation_degrees"]}
                              for p in pg],
                    "parser_id": PARSER_ID, "group_id": self.packet["packet_id"]})
        for n in sorted(nodes.values(), key=lambda x: (x["source_id"], x["version_id"], x["start_char"])):
            if (n["source_id"], n["version_id"]) not in versions:
                continue
            d = {"node_id": n["node_id"], "source_version_id": version_key(n["source_id"], n["version_id"]),
                 "kind": n["kind"], "span": {"start": n["start_char"], "end": n["end_char"], "unit": OFFSET_UNIT},
                 "regions": n["regions"]}
            if n["alignment"]:
                d["alignment"] = n["alignment"]
            node_out.append(d)
        q = self.requirement()
        event = {
            "schema_version": "ptp-evidence-trace/1", "trace_id": f"trace:{self.run_id}:{seq}",
            "run_id": self.run_id, "mode": "synthetic_demo", "event_time": event_time,
            "original_query": {"query_id": q["query_id"], "text": q["query_text"]},
            "action": {"action_id": action_id, "kind": kind, "query_text": match, "query_artifact_ids": artifact_ids,
                       "selected_assessment_id": selected, "route_id": ROUTE_ID, "result_limit": RESULT_LIMIT,
                       "eligibility_profile_id": ELIGIBILITY_ID},
            "index": index, "sources": sources, "nodes": node_out, "relations": relations,
            "evidence": [e.as_trace() for e in evidence], "hypotheses": [h.as_trace() for h in hypotheses],
            "candidate_delta": {"identity_unit": "node", "before_ids": before, "returned_ids": returned,
                                "after_ids": after, "new_ids": [x for x in returned if x not in before]},
            "runtime_assessments": [{"assessment_id": a["assessment_id"], "requirement_span": a["requirement_span"],
                                     "status": a["status"], "evidence_ids": a["evidence_ids"],
                                     "assessor_id": ASSESSOR_ID, "basis": "runtime_not_gold", "timing": t}
                                    for a, t in assessments],
            "cost": {"currency": "USD", "estimate_usd": 0, "provider_reported_usd": None, "invoiced_usd": None,
                     "invoice_id": None, "state": "not_applicable"}}
        chk = check_event(event)
        if chk["schema_errors"] or chk["semantic_errors"]:
            raise ValidationFailed(f"emitted trace failed its checks: {chk}", "trace_invalid")
        raw = json.dumps(event, ensure_ascii=False, sort_keys=True).encode("utf-8")
        with self.store.tx() as con:
            con.execute("INSERT INTO trace_events VALUES (?,?,?,?,?,?,?,?)",
                        (self.pid, event["trace_id"], self.run_id, seq, kind, raw.decode("utf-8"), sha256(raw),
                         utc_now()))
        self.search_events.append(event)
        return event

    def _begin_run(self, kind: str, strategy: str, change_event_id: str | None = None) -> None:
        with self.store.read() as con:
            mission = self.core._project(con, self.pid)["mission"]
        self.run_id = self.core._new_run(self.pid, kind, "trace_slice", strategy, mission, change_event_id)
        self.seq = 0

    def _search_action(self, *, action_id: str, kind: str, match: str, before: list[str], artifact_ids: list[str],
                       selected: str | None, purpose: str) -> tuple[list[dict], dict, str, int]:
        self.seq += 1
        seq, t0 = self.seq, utc_now()
        index = self._index_identity()
        hits = self.search(match)
        returned = [h["node_id"] for h in hits]
        self.core._action(self.run_id, seq, "trace_search", CANDIDATE_ID, self.packet["requirement"]["requirement_id"],
                          {"trace_id": f"trace:{self.run_id}:{seq}", "action_id": action_id, "kind": kind,
                           "purpose": purpose, "fts_match": match, "result_limit": RESULT_LIMIT, "hits": hits,
                           "before_ids": before, "new_ids": [x for x in returned if x not in before],
                           "corpus_revision": index["corpus_revision"], "data_origin": "synthetic_demo"}, started=t0)
        return hits, index, t0, seq

    def pipeline(self, replay: bool = False) -> dict:
        """Seed search -> assessment -> (one unresolved relation) -> one structural expansion -> assessment."""
        req = self.requirement()
        kind1, kind2 = ("replay_search", "replay_search") if replay else ("seed_search", "structural_expansion")
        # 1. seed: the requirement's own terms, OR-ed, BM25 over the current packet
        seed_match = _or_match(_terms(req["text"]))
        hits, index, t0, seq = self._search_action(action_id="replay-seed" if replay else "seed-1", kind=kind1,
                                                   match=seed_match, before=[], artifact_ids=[], selected=None,
                                                   purpose="seed retrieval for the source-bound requirement")
        seed_nodes = [h["node_id"] for h in hits]
        pool = list(seed_nodes)
        a1, rel1, unresolved = self.assess(seed_nodes, pool, "seed")
        seed_event = self._event(action_id="replay-seed" if replay else "seed-1", kind=kind1, match=seed_match,
                                 artifact_ids=[], selected=None, before=[], returned=seed_nodes,
                                 assessments=[(a1, "after_action")], relations=rel1, hypotheses=[], index=index,
                                 event_time=t0, seq=seq)
        out = {"seed_event": seed_event, "seed_nodes": seed_nodes, "assessment_before": a1, "unresolved_before":
               unresolved, "expansion_event": None, "pool": pool, "assessment": a1, "relations": rel1,
               "selected_reference": None}
        annex_refs = sorted((u for u in unresolved if u["kind"] == "annex"), key=lambda u: (u["from_node_id"], u["label"]))
        if not annex_refs:
            return out
        # 2. one structural expansion for the first unresolved annex reference (bounded: exactly one action)
        ref = annex_refs[0]
        nodes = self.nodes()
        frm = ref["from_node_id"]
        other_terms = {t for n in seed_nodes if n != frm for t in _terms(nodes[n]["quote"])}
        anchors = [t for t in _terms(req["text"]) if t in _terms(nodes[frm]["quote"]) and t not in other_terms]
        gen = self.packet["hypothesis_generator"]
        gen_sha = sha256(dumps(gen).encode("utf-8"))
        from_ev = self.evidence(frm).evidence_id
        hyps = []
        for t in anchors:
            for syn in gen["synonyms"].get(t, []):
                hyps.append(self.add_hypothesis(SearchHypothesis(
                    f"hyp:{self.run_id}:{t}->{syn}", syn, gen["generator_id"], gen_sha, (from_ev,))))
        phrases = [ref["reference"]] + anchors + [h.text for h in hyps]
        match = _or_match(phrases)
        artifact_ids = [ref["evidence_id"]] + [h.hypothesis_id for h in hyps]
        hits2, index2, t2, seq2 = self._search_action(
            action_id="replay-expansion" if replay else "expansion-1", kind=kind2, match=match, before=list(pool),
            artifact_ids=artifact_ids, selected=a1["assessment_id"],
            purpose=f"resolve '{ref['reference']}' referenced by {frm}")
        returned = [h["node_id"] for h in hits2]
        pool = pool + [x for x in returned if x not in pool]
        a2, rel2, unresolved2 = self.assess(seed_nodes, pool, "expansion")
        exp_event = self._event(action_id="replay-expansion" if replay else "expansion-1", kind=kind2, match=match,
                                artifact_ids=artifact_ids, selected=a1["assessment_id"], before=list(out["pool"]),
                                returned=returned, assessments=[(a1, "before_action"), (a2, "after_action")],
                                relations=rel2, hypotheses=hyps, index=index2, event_time=t2, seq=seq2)
        out.update(expansion_event=exp_event, pool=pool, assessment=a2, relations=rel2, unresolved_after=unresolved2,
                   selected_reference=ref, query_terms={
                       "copied_from_source": [{"phrase": ref["reference"], "evidence_id": ref["evidence_id"]}],
                       "original_anchors": anchors, "hypotheses": [h.hypothesis_id for h in hyps]})
        return out

    def run(self) -> dict:
        self._begin_run("trace_slice", "seed_then_one_structural_expansion")
        try:
            res = self.pipeline()
        except Exception as exc:
            self.core._finish_run(self.run_id, "failed", f"error:{type(exc).__name__}", {})
            raise
        self.core._finish_run(self.run_id, "completed", "bounded_trace_complete",
                              {"search_actions": 2 if res["expansion_event"] else 1, "paid_model_calls": 0,
                               "remote_calls": 0, "data_origin": "synthetic_demo"})
        self._mark_current(res["relations"])
        self.state = res
        return res

    def _mark_current(self, relations: list[dict]) -> None:
        ids = [r["relation_id"] for r in relations]
        with self.store.tx() as con:
            for r in con.execute("SELECT relation_id FROM doc_relations WHERE project_id=? AND state='current'",
                                 (self.pid,)).fetchall():
                if r[0] not in ids:
                    con.execute("UPDATE doc_relations SET state='superseded', superseded_reason=? WHERE project_id=? "
                                "AND relation_id=?", ("not re-derived by the latest pipeline", self.pid, r[0]))

    # ------------------------------------------------------------------ controlled revision
    def predict_recheck(self, source_id: str, old_version: str, new_version: str) -> dict:
        """Dependency rules -> what must be re-checked after a source revision (computed before re-running)."""
        nodes = self.nodes()
        old = {n["anchor"]: n for n in nodes.values() if (n["source_id"], n["version_id"]) == (source_id, old_version)}
        new = {n["anchor"]: n for n in nodes.values() if (n["source_id"], n["version_id"]) == (source_id, new_version)}
        changed, same = [], []
        for anchor, n in sorted(old.items()):
            succ = new.get(anchor)
            if succ is None or succ["quote"] != n["quote"] or succ["kind"] != n["kind"]:
                changed.append(n["node_id"])
            else:
                same.append(n["node_id"])
        added = [n["node_id"] for a, n in sorted(new.items()) if a not in old]
        old_ids = set(old[a]["node_id"] for a in old)
        a = self.state["assessment"]
        rels = self.state["relations"]
        ev_all = list(a["evidence_ids"])
        for r in rels:
            ev_all += [e for e in r["provenance"]["evidence_ids"] if e not in ev_all]
        ev_node = {e.evidence_id: e.node_id for e in self.resolve_evidence(ev_all)}
        evidence: dict[str, str] = {}
        for eid, nid in ev_node.items():
            if nid in changed:
                evidence[eid] = "recheck:cited_node_changed"
            elif nid in old_ids:
                evidence[eid] = "reanchor:version_superseded_text_identical"
        relations: dict[str, str] = {}
        for r in rels:
            ends = [r["from_node_id"], r["to_node_id"], *r["scope_node_ids"]]
            if any(x in changed for x in ends):
                relations[r["relation_id"]] = "rebind:endpoint_or_scope_changed"
            elif any(x in old_ids for x in ends):
                relations[r["relation_id"]] = "rebind:endpoint_version_superseded"
            # a changed qualifier or a changed governed scope re-opens the evidence it governs, even if unchanged
            if r["kind"] == "qualifies" and r["from_node_id"] in changed:
                for eid, nid in ev_node.items():
                    if nid in r["scope_node_ids"]:
                        evidence[eid] = "recheck:qualifier_changed"
            if r["kind"] == "incorporates" and any(x in changed for x in r["scope_node_ids"]):
                for eid, nid in ev_node.items():
                    if nid == r["from_node_id"]:
                        evidence[eid] = "recheck:governed_scope_changed"
        assessments = {}
        if evidence or relations:
            assessments[a["assessment_id"]] = "recheck:depends_on_changed_evidence_or_relation"
        searches = {e["trace_id"]: "replay:search_scope_contained_superseded_version"
                    for e in self.search_events if any(s["version_id"] == version_key(source_id, old_version)
                                                       for s in e["sources"])
                    or e["index"]["corpus_revision"] != self._index_identity()["corpus_revision"]}
        return {"node_changes": {"changed": changed, "unchanged_aligned": same, "added": added},
                "recheck": {"evidence": dict(sorted(evidence.items())), "relations": dict(sorted(relations.items())),
                            "assessments": assessments, "searches": searches},
                "retained_without_recheck": {
                    "evidence": sorted(e for e in ev_node if e not in evidence),
                    "relations": sorted(r["relation_id"] for r in rels if r["relation_id"] not in relations)}}

    def apply_revision(self, revision: dict | None = None) -> dict:
        rev = revision or self.packet["revision"]
        art = self.fx["artifacts"].get((rev["source_id"], rev["version_id"])) if revision is None else revision["_art"]
        before_state = self.state
        self.import_version(art, supersedes=rev["supersedes_version_id"], event_id=rev["event_id"])
        prediction = self.predict_recheck(rev["source_id"], rev["supersedes_version_id"], rev["version_id"])
        self._begin_run("trace_slice_revision", "dependency_predicted_recheck", rev["event_id"])
        try:
            res = self.pipeline(replay=True)
        except Exception as exc:
            self.core._finish_run(self.run_id, "failed", f"error:{type(exc).__name__}", {})
            raise
        self.core._finish_run(self.run_id, "completed", "revision_recheck_complete",
                              {"search_actions": 2 if res["expansion_event"] else 1, "paid_model_calls": 0,
                               "remote_calls": 0, "data_origin": "synthetic_demo"})
        self._mark_current(res["relations"])
        self.state = res
        nodes = self.nodes()

        def ev_set(state):
            s = list(state["assessment"]["evidence_ids"])
            for r in state["relations"]:
                s += [e for e in r["provenance"]["evidence_ids"] if e not in s]
            return set(s)
        old_ev, new_ev = ev_set(before_state), ev_set(res)
        old_rel = {r["relation_id"] for r in before_state["relations"]}
        new_rel = {r["relation_id"] for r in res["relations"]}
        old_quotes = {e.evidence_id: e.quote for e in self.resolve_evidence(sorted(old_ev))}
        new_quotes = {e.evidence_id: e.quote for e in self.resolve_evidence(sorted(new_ev))}

        def aligned(nid: str) -> str:  # map an old node id to its successor in the current version, if any
            for n in nodes.values():
                if n["alignment"] and n["alignment"]["prior_node_id"] == nid:
                    return n["node_id"]
            return nid
        observed = {
            "evidence_replaced": sorted(old_ev - new_ev), "evidence_added": sorted(new_ev - old_ev),
            "evidence_retained": sorted(old_ev & new_ev),
            "relations_replaced": sorted(old_rel - new_rel), "relations_added": sorted(new_rel - old_rel),
            "relations_retained": sorted(old_rel & new_rel),
            "pool_before_revision": before_state["pool"], "pool_after_replay": res["pool"],
            "pool_equivalent_under_alignment": [aligned(x) for x in before_state["pool"]] == res["pool"],
            "assessment_before": {k: before_state["assessment"][k] for k in ("assessment_id", "status")},
            "assessment_after": {k: res["assessment"][k] for k in ("assessment_id", "status")},
            "quotes_changed": {e: {"before": old_quotes[e], "after": new_quotes.get(f"ev:{aligned(e[3:])}")}
                               for e in sorted(old_ev - new_ev)
                               if new_quotes.get(f"ev:{aligned(e[3:])}") not in (None, old_quotes[e])}}
        flagged = set(prediction["recheck"]["evidence"])
        sound = (set(observed["evidence_replaced"]) <= flagged
                 and set(observed["relations_replaced"]) <= set(prediction["recheck"]["relations"])
                 and set(prediction["retained_without_recheck"]["evidence"]) <= set(observed["evidence_retained"])
                 and set(prediction["retained_without_recheck"]["relations"]) <= set(observed["relations_retained"]))
        impact = {"event_id": rev["event_id"], "source_id": rev["source_id"],
                  "from_version": rev["supersedes_version_id"], "to_version": rev["version_id"],
                  "description": rev.get("description", ""), "prediction": prediction, "observed": observed,
                  "prediction_covers_every_observed_change": sound,
                  "replay_trace_ids": [e["trace_id"] for e in (res["seed_event"], res["expansion_event"]) if e],
                  "run_id": self.run_id}
        with self.store.tx() as con:
            con.execute("UPDATE change_events SET status='applied', run_id=?, result_json=?, applied_at=? WHERE "
                        "project_id=? AND event_id=?", (self.run_id, dumps(impact), utc_now(), self.pid, rev["event_id"]))
        return impact


def node_id(source_id: str, version_id: str, anchor: str) -> str:
    return f"{source_id}@{version_id}#{anchor}"


def version_key(source_id: str, version_id: str) -> str:
    return f"{source_id}@{version_id}"


def author_revision(base: dict, source_id: str, version_id: str, supersedes: str, event_id: str,
                    replace: dict[str, str], description: str) -> dict:
    """An in-memory synthetic revision of an authored document (used for additional controlled revisions)."""
    doc = json.loads(json.dumps(base))
    doc.update(version_id=version_id, file_stem=f"{source_id}_{version_id}", title=doc["title"] + f", {version_id}")
    for page in doc["pages"]:
        for ln in page:
            if ln["anchor"] in replace:
                ln["text"] = replace[ln["anchor"]]
    return {"event_id": event_id, "description": description, "source_id": source_id, "version_id": version_id,
            "supersedes_version_id": supersedes, "_art": artifact_from_spec(doc)}


def artifact_from_spec(doc: dict) -> dict:
    """Author an in-memory artifact (PDF bytes, canonical text, layout) from a synthetic document spec."""
    files = author_artifacts(doc)
    return {"doc": doc, "pdf": files["pdf"], "canonical_bytes": files["canonical"],
            "text": files["canonical"].decode("utf-8"), "layout": json.loads(files["layout"].decode("utf-8"))}


# =========================================================================== one-call demo + bundle
def run_synthetic_slice(data_dir: str | Path | None = None, fixture_dir: Path = FIXTURE_DIR) -> dict:
    """Run the complete synthetic slice in ``data_dir`` (a fresh temporary store by default) and return the bundle."""
    if data_dir is None:
        with tempfile.TemporaryDirectory(prefix="ptp-p0t06-", ignore_cleanup_errors=True) as tmp:
            return run_synthetic_slice(Path(tmp) / "store", fixture_dir)
    core = EvidenceCore(data_dir)
    sl = TraceSlice(core, fixture_dir)
    sl.setup()
    first = sl.run()
    binding = None
    if first["expansion_event"]:
        inc = [r for r in first["relations"] if r["kind"] == "incorporates"]
        nodes = sl.nodes()
        binding = {"reference": first["selected_reference"]["reference"],
                   "reference_evidence_id": first["selected_reference"]["evidence_id"],
                   "from_node_id": first["selected_reference"]["from_node_id"],
                   "bound": [{"relation_id": r["relation_id"], "to_node_id": r["to_node_id"],
                              "to_quote": nodes[r["to_node_id"]]["quote"], "scope_node_ids": r["scope_node_ids"],
                              "scope_quotes": [nodes[s]["quote"] for s in r["scope_node_ids"]]} for r in inc],
                   "unbound_new_candidates": [x for x in first["expansion_event"]["candidate_delta"]["new_ids"]
                                              if x not in {e.node_id for e in sl.resolve_evidence(
                                                  first["assessment"]["evidence_ids"])}],
                   "query_terms": first["query_terms"]}
    impact = sl.apply_revision()
    events = list(sl.search_events)
    return {
        "bundle_schema": BUNDLE_SCHEMA, "synthetic": True, "label": SYNTHETIC_LABEL, "task": GOAL_ID,
        "claim_boundary": CLAIM_BOUNDARY,
        "note": "Each element of 'events' is one evidence-trace event that validates against the event schema; this "
                "wrapper itself is not an evidence-trace event.",
        "event_schema": {"path": "src/patent_to_pilot/workbench/schemas/evidence_trace.schema.json",
                         "sha256": SCHEMA_SHA256, "copied_from": "owner note 22112026 spec/evidence_trace.schema.json"},
        "fixture": {"path": "src/patent_to_pilot/workbench/fixtures/p0_t06_synthetic",
                    "manifest_sha256": sl.fx["manifest_sha256"], "packet_id": sl.packet["packet_id"]},
        "requirement": {**{k: v for k, v in sl.requirement().items() if k != "created_at"},
                        "unit": OFFSET_UNIT},
        "events": events, "event_checks": [check_event(e) for e in events],
        "annex_binding": binding, "revision": impact,
        "environment": {"python": platform.python_version(), "sqlite": sqlite3.sqlite_version,
                        "jsonschema": _version("jsonschema"), "network": "not used", "paid_calls": 0,
                        "model_calls": 0},
        "store_note": "temporary store" if data_dir is None else "caller-supplied store",
    }


def _version(mod: str) -> str | None:
    try:
        from importlib.metadata import version
        return version(mod)
    except Exception:  # noqa: BLE001 - informational only
        return None


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="P0-T06 synthetic source-bound search-and-trace slice (synthetic only)")
    ap.add_argument("--out", help="write the trace bundle JSON here (default: print a summary)")
    ap.add_argument("--data-dir", help="store directory (default: a fresh temporary store)")
    ap.add_argument("--regenerate-fixtures", action="store_true", help="rebuild the generated fixture files")
    a = ap.parse_args(argv)
    if a.regenerate_fixtures:
        m = regenerate_fixtures()
        print(json.dumps(m, indent=1))
        return 0
    try:
        bundle = run_synthetic_slice(a.data_dir)
    except CoreError as exc:
        print(f"error ({exc.code}): {exc}", file=sys.stderr)
        return 2
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(json.dumps(bundle, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    bad = [c for c in bundle["event_checks"] if c["schema_errors"] or c["semantic_errors"]]
    print(f"{SYNTHETIC_LABEL}\n  events: {len(bundle['events'])} (schema/semantic failures: {len(bad)})")
    for e in bundle["events"]:
        cd = e["candidate_delta"]
        print(f"  {e['action']['kind']:<21} before={len(cd['before_ids'])} returned={len(cd['returned_ids'])} "
              f"new={cd['new_ids']}")
    print(f"  revision {bundle['revision']['event_id']}: prediction covers every observed change = "
          f"{bundle['revision']['prediction_covers_every_observed_change']}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
