"""P4-T03: real-import structure adapter for owner documents (owner fix plan of 23 Nov 2026, section 5.2).

A small Thai/English document profile builds source-bound structure for one immutable source version from what the
input actually exposes, and nothing more:

* numbered units from line-start identifiers: ``มาตรา``, ``ข้อ``, ``หมวด``, ``ส่วน``/``ส่วนที่``, ``ภาคผนวก``,
  ``บัญชีท้าย`` and English ``Section``, ``Clause``, ``Article``, ``Chapter``, ``Part``, ``Annex``, ``Appendix``,
  ``Schedule``, ``Attachment``, ``Exhibit`` (a Markdown ``#`` prefix is allowed), with Thai or ASCII digits;
* nested numbering under a numbered unit: parenthesised items ``(๒)``, ``(2)``, ``(ก)``, ``(a)`` and decimal items
  ``4.2`` whose first component equals the unit's number;
* paragraph ordinals (``วรรค``) of a numbered unit, from the passage boundaries of the import;
* plain Markdown ATX headings (Markdown only; fixture ``## <passage-id>`` delimiters are not headings);
* Markdown footnotes ``[^id]`` / ``[^id]:`` and Markdown pipe tables (header row + separator) -- only Markdown exposes
  them; a PDF text layer or plain text gets no footnote, table or geometry binding.

Every node and edge records the extraction rule and a declared confidence. Node keys are qualified by
``(source_id, version_id, section_path)``; identifier keys fold Thai digits to ASCII (``ข้อ ๕(๒)`` -> ``ข้อ:5(2)``)
while the original spelling and exact code-point spans are kept. References in body text are parsed with the same
profile; their resolution is a deterministic lookup over persisted nodes (``resolve_in_version`` and
``StructureStore.resolve``). Nothing here is a semantic judgement.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import re

from patent_to_pilot.workbench.store import dumps, utc_now
from patent_to_pilot.workbench.thai_analyzer import fold

RULESET = "ptp-owner-structure/1.0.0"
PROFILE = "thai-english-legal-structure-v1"
RULES = {   # rule -> declared confidence (a fixed property of the rule, not a learned score)
    "line_start_identifier_v1": 0.9,
    "markdown_heading_identifier_v1": 1.0,
    "nested_parenthesized_item_v1": 0.9,
    "nested_decimal_item_v1": 0.8,
    "unit_paragraph_ordinal_v1": 0.7,
    "markdown_atx_heading_v1": 1.0,
    "markdown_footnote_v1": 1.0,
    "markdown_pipe_table_v1": 1.0,
    "numbering_hierarchy_v1": 0.9,
    "explicit_reference_exact_v1": 0.9,
    "explicit_reference_enclosing_unit_v1": 0.6,
    "annex_unit_in_other_source_v1": 0.8,
    "external_instrument_title_v1": 0.7,
}
SCHEMA = """
CREATE TABLE IF NOT EXISTS structure_builds (
  project_id TEXT NOT NULL, source_id TEXT NOT NULL, version_id TEXT NOT NULL, ruleset TEXT NOT NULL,
  source_kind TEXT NOT NULL, status TEXT NOT NULL, n_nodes INTEGER NOT NULL, n_edges INTEGER NOT NULL,
  detail_json TEXT NOT NULL, built_at TEXT NOT NULL, PRIMARY KEY (project_id, source_id, version_id, ruleset));
CREATE TABLE IF NOT EXISTS structure_nodes (
  project_id TEXT NOT NULL, source_id TEXT NOT NULL, version_id TEXT NOT NULL, node_key TEXT NOT NULL,
  kind TEXT NOT NULL, ident_kind TEXT NOT NULL, ident_label TEXT NOT NULL, ident_key TEXT NOT NULL,
  section_path TEXT NOT NULL, container TEXT NOT NULL, level INTEGER NOT NULL, start_char INTEGER NOT NULL,
  end_char INTEGER NOT NULL, head_start INTEGER NOT NULL, head_end INTEGER NOT NULL, head_text TEXT NOT NULL,
  parent_key TEXT, passage_id TEXT, rule TEXT NOT NULL, confidence REAL NOT NULL,
  PRIMARY KEY (project_id, source_id, version_id, node_key));
CREATE TABLE IF NOT EXISTS structure_edges (
  project_id TEXT NOT NULL, source_id TEXT NOT NULL, version_id TEXT NOT NULL, edge_key TEXT NOT NULL,
  kind TEXT NOT NULL, from_node TEXT, to_node TEXT, from_passage TEXT, span_start INTEGER, span_end INTEGER,
  span_text TEXT, state TEXT NOT NULL, rule TEXT NOT NULL, confidence REAL NOT NULL,
  PRIMARY KEY (project_id, source_id, version_id, edge_key));
"""

ANNEX_KINDS = frozenset({"ภาคผนวก", "บัญชีท้าย", "annex", "appendix", "schedule", "attachment", "exhibit"})
RANK = {**{k: 1 for k in ANNEX_KINDS}, "หมวด": 2, "chapter": 2, "part": 2, "ส่วน": 3,
        "มาตรา": 4, "ข้อ": 4, "section": 4, "clause": 4, "article": 4}
UNLABELED_TH = frozenset({"ภาคผนวก", "บัญชีท้าย"})
THAI_ORDINALS = {"หนึ่ง": 1, "สอง": 2, "สาม": 3, "สี่": 4, "ห้า": 5, "หก": 6, "เจ็ด": 7, "แปด": 8, "เก้า": 9,
                 "สิบ": 10}
_D = "[0-9๐-๙]"
_SUB = rf"\((?:{_D}{{1,3}}|[ก-ฮ]|[a-z])\)"
_KIND = (r"(?P<kind>มาตรา|ข้อ|หมวด|ส่วนที่|ส่วน|ภาคผนวก|บัญชีท้าย|(?<![A-Za-z])"
         r"(?i:section|clause|article|chapter|part|annex|appendix|schedule|attachment|exhibit)(?![A-Za-z]))")
_LABEL = rf"(?P<label>{_D}+(?:\.{_D}+)*(?:[ \t]*{_SUB})*|[ก-ฮ](?![ก-๛])|[A-Z](?![A-Za-z0-9]))"
_SP = r"[ \t ]*"
_PARA = r"(?:" + _SP + r"วรรค(?P<para>หนึ่ง|สอง|สาม|สี่|ห้า|หก|เจ็ด|แปด|เก้า|สิบ|" + _D + r"+))?"
REF = re.compile(_KIND + _SP + rf"(?:{_LABEL})?" + _PARA)
REF_PARA = re.compile(r"วรรค(?P<para>หนึ่ง|สอง|สาม|สี่|ห้า|หก|เจ็ด|แปด|เก้า|สิบ|" + _D + r"+)")
LINE_UNIT = re.compile(r"^(?P<lead>[ \t]*(?:#{1,6}[ \t]+)?(?:[*>-][ \t]+)?)" + _KIND + _SP + rf"(?:{_LABEL})?"
                       r"(?P<after>.*)$")
SUB_LINE = re.compile(rf"^[ \t]*\((?P<lab>{_D}{{1,3}}|[ก-ฮ]|[a-z])\)")
DEC_LINE = re.compile(rf"^[ \t]*(?P<item>{_D}+(?:\.{_D}+)+)(?=[ \t.)])")
MD_HEAD = re.compile(r"^(?P<hashes>#{1,6})[ \t]+(?P<title>.+?)[ \t#]*$")
PAGE_MARK = re.compile(r"^\[page \d+\]$")
FN_DEF = re.compile(r"^\[\^(?P<id>[^\]\s]+)\]:")
FN_REF = re.compile(r"\[\^(?P<id>[^\]\s]+)\](?!:)")
TABLE_ROW = re.compile(r"^[ \t]*\|.*\|[ \t]*$")
TABLE_SEP = re.compile(r"^[ \t]*\|?[ \t]*:?-{3,}:?[ \t]*(?:\|[ \t]*:?-{3,}:?[ \t]*)*\|?[ \t]*$")
_EXT_TH = re.compile(_SP + r"(?:แห่ง|ของ|ใน|ตาม|ท้าย)?" + _SP +
                     r"(?P<inst>(?:พระราชบัญญัติ|พระราชกำหนด|ประมวลกฎหมาย|กฎกระทรวง|ประกาศ|ระเบียบ|ข้อบังคับ|คำสั่ง)\S*)")
_EXT_YEAR = re.compile(r"^[ \t ]*(?:พ\.ศ\.|ค\.ศ\.)[ \t ]*[0-9๐-๙]{4}")
_EXT_EN_THIS = re.compile(r"[ \t]+of[ \t]+this\b", re.I)
_EXT_EN = re.compile(r"[ \t]+of[ \t]+(?P<inst>(?:the[ \t]+)?(?:[A-Z][\w-]*[ \t]+){0,8}?"
                     r"(?:Act|Regulations?|Code|Directive|Decree|Rules|Ordinance|Law)(?:[ \t]+(?:of[ \t]+)?\d{4})?)")
_TRAIL = ".,;:)]}\"'"


def norm_kind(kind: str) -> str:
    k = fold(kind)
    return "ส่วน" if k == "ส่วนที่" else k


def norm_label(label: str | None) -> str:
    return re.sub(r"[ \t ]+", "", fold(label or ""))


def paragraph_number(p: str | None) -> int | None:
    if not p:
        return None
    return THAI_ORDINALS.get(p) or int(fold(p))


def norm_title(text: str) -> str:
    return re.sub(r"\s+", " ", fold(text or "")).strip().strip(_TRAIL).strip()


# =========================================================================== references
@dataclass(frozen=True)
class Ref:
    kind: str                 # normalised kind ("ข้อ", "annex", ...) or "วรรค" for a standalone paragraph reference
    label: str                # normalised label ("5(2)", "b", "") -- digits folded, spaces removed
    key: str                  # identifier key ("ข้อ:5(2)"); "" for a standalone paragraph reference
    paragraph: int | None
    start: int                # half-open code points in the canonical text
    end: int
    text: str                 # original spelling of the reference span
    instrument: str | None    # instrument named right after the reference ("พระราชบัญญัติ... พ.ศ. ๒๕๒๒")
    internal_marker: bool     # the instrument is "this" one (นี้ / of this)
    annex_type: bool

    @property
    def external(self) -> bool:
        return bool(self.instrument) and not self.internal_marker

    def as_record(self) -> dict:
        return asdict(self)


def _instrument(text: str, pos: int) -> tuple[str | None, bool]:
    tail = text[pos:pos + 200].split("\n", 1)[0]
    m = _EXT_TH.match(tail)
    if m:
        name = m.group("inst")
        rest = tail[m.end("inst"):]
        y = _EXT_YEAR.match(rest)
        if y:
            name += rest[:y.end()]
        name = name.rstrip(_TRAIL)
        return name, name.endswith("นี้")
    if _EXT_EN_THIS.match(tail):
        return "this", True
    m = _EXT_EN.match(tail)
    if m:
        return m.group("inst").rstrip(_TRAIL), False
    return None, False


def parse_references(text: str, base: int = 0, exclude_starts=frozenset()) -> list[Ref]:
    """Explicit references in ``text`` (offsets shifted by ``base``). A reference starting at an excluded offset (the
    identifier of a unit's own heading) is a definition, not a reference, and is skipped."""
    out: list[Ref] = []
    spans = []
    for m in REF.finditer(text):
        kind = norm_kind(m.group("kind"))
        label = m.group("label")
        if label is None and kind not in UNLABELED_TH:
            continue
        s, e = base + m.start(), base + m.end()
        spans.append((m.start(), m.end()))
        if s in exclude_starts:
            continue
        lab = norm_label(label)
        inst, internal = _instrument(text, m.end())
        out.append(Ref(kind, lab, f"{kind}:{lab}", paragraph_number(m.group("para")), s, e, m.group(0), inst,
                       internal, kind in ANNEX_KINDS))
    for m in REF_PARA.finditer(text):
        if any(a <= m.start() < b for a, b in spans):
            continue
        out.append(Ref("วรรค", "", "", paragraph_number(m.group("para")), base + m.start(), base + m.end(),
                       m.group(0), None, False, False))
    return sorted(out, key=lambda r: (r.start, r.end))


# =========================================================================== build (pure)
def _lines(text: str) -> list[tuple[int, int, str]]:
    out = []
    for m in re.finditer(r"[^\n]*\n|[^\n]+$", text):
        content = m.group(0).rstrip("\r\n")
        out.append((m.start(), m.start() + len(content), content))
    return out


def _passage_at(passages: list[dict], pos: int, end: int | None = None) -> str | None:
    for p in passages:
        if p["start_char"] <= pos < p["end_char"]:
            return p["passage_id"]
    for p in passages:     # a heading line outside every passage: the first passage that starts inside the node
        if pos <= p["start_char"] < (end if end is not None else pos + 1):
            return p["passage_id"]
    return None


def _trim(text: str, start: int, end: int) -> int:
    while end > start and text[end - 1].isspace():
        end -= 1
    return end


def build(text: str, passages: list[dict], source_kind: str) -> dict:
    """Nodes and edges of one source version, only to the level the input exposes."""
    markdown = source_kind == "owner_markdown"
    pdf = source_kind == "owner_pdf"
    pids = {p["passage_id"] for p in passages}
    lines = _lines(text)
    numbered: list[dict] = []
    headings: list[dict] = []
    footnotes: list[dict] = []
    stack: list[dict] = []

    def node(**kw) -> dict:
        kw.setdefault("ident_kind", "")
        kw.setdefault("ident_label", "")
        kw.setdefault("ident_key", "")
        kw.setdefault("section_path", "")
        kw.setdefault("container", "")
        kw.setdefault("parent_key", None)
        kw["confidence"] = RULES[kw["rule"]]
        return kw

    for ls, le, content in lines:
        if pdf and PAGE_MARK.match(content):
            continue
        m = LINE_UNIT.match(content)
        if m:
            kind = norm_kind(m.group("kind"))
            label = m.group("label")
            after = m.group("after").strip()
            ok = label is not None or (kind in UNLABELED_TH) or (
                kind in ANNEX_KINDS and (not after or after[0] in ".:-–"))
            if ok:
                rank = RANK[kind]
                while stack and stack[-1]["level"] >= rank:
                    stack.pop()
                parent = stack[-1] if stack else None
                lab = norm_label(label)
                key = f"{kind}:{lab}"
                n = node(kind="unit", ident_kind=kind, ident_label=lab, ident_key=key,
                         section_path=(parent["section_path"] + "/" if parent else "") + key,
                         container=key if rank == 1 else (parent["container"] if parent else ""), level=rank,
                         start=ls, head_start=ls + m.start("kind"), head_end=le, head_text=content.strip(),
                         parent=parent,
                         rule="markdown_heading_identifier_v1" if "#" in m.group("lead") else "line_start_identifier_v1")
                numbered.append(n)
                stack.append(n)
                continue
        m = SUB_LINE.match(content)
        if m and stack:
            lab = norm_label(m.group("lab"))
            numeric = lab.isdigit()
            top = stack[-1]
            rank = 6 if (not numeric and top["kind"] == "subitem" and top["level"] == 5
                         and top.get("ident_label_last", "").isdigit()) else 5
            while stack and stack[-1]["level"] >= rank:
                stack.pop()
            parent = stack[-1] if stack else None
            if parent is not None and parent["level"] >= 4:
                n = node(kind="subitem", ident_kind=parent["ident_kind"], ident_label=f"{parent['ident_label']}({lab})",
                         ident_key=f"{parent['ident_key']}({lab})", section_path=f"{parent['section_path']}({lab})",
                         container=parent["container"], level=rank, start=ls, head_start=ls + m.start(),
                         head_end=le, head_text=content.strip(), parent=parent, ident_label_last=lab,
                         rule="nested_parenthesized_item_v1")
                numbered.append(n)
                stack.append(n)
                continue
        m = DEC_LINE.match(content)
        if m and stack:
            item = norm_label(m.group("item"))
            while stack and stack[-1]["level"] >= 5:
                stack.pop()
            parent = stack[-1] if stack else None
            if parent is not None and parent["level"] == 4 and parent["ident_label"] == item.split(".")[0]:
                key = f"{parent['ident_kind']}:{item}"
                n = node(kind="subitem", ident_kind=parent["ident_kind"], ident_label=item, ident_key=key,
                         section_path=parent["section_path"][:len(parent["section_path"]) - len(parent["ident_key"])]
                         + key, container=parent["container"], level=5, start=ls, head_start=ls + m.start("item"),
                         head_end=le, head_text=content.strip(), parent=parent, ident_label_last=item,
                         rule="nested_decimal_item_v1")
                numbered.append(n)
                stack.append(n)
                continue
        if markdown:
            m = MD_HEAD.match(content)
            if m and m.group("title").strip() not in pids:
                headings.append(node(kind="heading", level=len(m.group("hashes")), start=ls, head_start=ls,
                                     head_end=le, head_text=m.group("title").strip(), rule="markdown_atx_heading_v1"))
                continue
            m = FN_DEF.match(content)
            if m:
                footnotes.append(node(kind="footnote", ident_kind="footnote", ident_label=m.group("id"),
                                      ident_key=f"footnote:{m.group('id')}", level=9, start=ls, end=le,
                                      head_start=ls, head_end=le, head_text=content.strip(),
                                      rule="markdown_footnote_v1"))
    # ---- extents
    for i, n in enumerate(numbered):
        nxt = next((x["start"] for x in numbered[i + 1:] if x["level"] <= n["level"]), len(text))
        if n["kind"] == "subitem":   # a nested item never runs past the passage (paragraph block) it starts in
            nxt = min([nxt] + [p["end_char"] for p in passages if p["start_char"] <= n["start"] < p["end_char"]])
        n["end"] = _trim(text, n["start"], nxt)
    for i, n in enumerate(headings):
        nxt = next((x["start"] for x in headings[i + 1:] if x["level"] <= n["level"]), len(text))
        n["end"] = _trim(text, n["start"], nxt)
    nodes = numbered + headings + footnotes
    # ---- paragraph ordinals (วรรค) of numbered units of rank 4
    paragraphs = []
    for u in [n for n in numbered if n["kind"] == "unit" and n["level"] == 4]:
        k = 0
        for p in sorted(passages, key=lambda p: p["start_char"]):
            if not (u["start"] <= p["start_char"] < u["end"]):
                continue
            if p["start_char"] <= u["head_start"] and p["end_char"] <= u["head_end"]:
                continue   # a passage that is only the unit's own heading line
            k += 1
            paragraphs.append(node(kind="paragraph", ident_kind=u["ident_kind"], ident_label=f"{u['ident_label']}/{k}",
                                   ident_key=f"{u['ident_key']}/วรรค:{k}",
                                   section_path=f"{u['section_path']}/วรรค:{k}", container=u["container"], level=7,
                                   start=p["start_char"], end=p["end_char"], head_start=p["start_char"],
                                   head_end=p["start_char"], head_text="", parent=u,
                                   rule="unit_paragraph_ordinal_v1", passage_id=p["passage_id"]))
    nodes += paragraphs
    # ---- tables (Markdown pipe tables only)
    tables = []
    if markdown:
        i = 0
        while i < len(lines) - 1:
            if TABLE_ROW.match(lines[i][2]) and TABLE_SEP.match(lines[i + 1][2]) and "|" in lines[i + 1][2]:
                j = i + 2
                while j < len(lines) and TABLE_ROW.match(lines[j][2]):
                    j += 1
                t = node(kind="table", level=8, start=lines[i][0], end=lines[j - 1][1], head_start=lines[i][0],
                         head_end=lines[i][1], head_text=lines[i][2].strip(), rule="markdown_pipe_table_v1")
                h = node(kind="table_header", level=8, start=lines[i][0], end=lines[i][1], head_start=lines[i][0],
                         head_end=lines[i][1], head_text=lines[i][2].strip(), rule="markdown_pipe_table_v1", parent=t)
                tables += [t, h]
                i = j
            else:
                i += 1
    nodes += tables
    nodes.sort(key=lambda n: (n["start"], -n["end"], n["level"]))
    for i, n in enumerate(nodes, start=1):
        n["node_key"] = f"n{i:04d}"
        n.setdefault("passage_id", None)
        if n["passage_id"] is None:
            n["passage_id"] = _passage_at(passages, n["start"], n["end"])
    for n in nodes:
        parent = n.pop("parent", None)
        n.pop("ident_label_last", None)
        n["parent_key"] = parent["node_key"] if parent else None
    # ---- edges
    edges = []
    for n in nodes:
        if n["parent_key"]:
            edges.append({"kind": "table_header_of" if n["kind"] == "table_header" else "contains",
                          "from_node": n["parent_key"], "to_node": n["node_key"], "from_passage": None,
                          "span_start": None, "span_end": None, "span_text": None, "state": "bound",
                          "rule": "markdown_pipe_table_v1" if n["kind"] == "table_header" else "numbering_hierarchy_v1"})
    if markdown:
        defs = {n["ident_label"]: n for n in nodes if n["kind"] == "footnote"}
        for p in passages:
            for m in FN_REF.finditer(p["quote"]):
                d = defs.get(m.group("id"))
                edges.append({"kind": "footnote_ref", "from_node": None, "to_node": d["node_key"] if d else None,
                              "from_passage": p["passage_id"], "span_start": p["start_char"] + m.start(),
                              "span_end": p["start_char"] + m.end(), "span_text": m.group(0),
                              "state": "bound" if d else "unresolved_no_target", "rule": "markdown_footnote_v1"})
    heads = {n["head_start"] for n in nodes if n["kind"] in ("unit", "subitem")}
    for p in passages:
        for r in parse_references(p["quote"], p["start_char"], heads):
            res = resolve_in_version(nodes, r)
            t = res["targets"][0]["node_key"] if len(res["targets"]) == 1 else None
            edges.append({"kind": "reference", "from_node": None, "to_node": t, "from_passage": p["passage_id"],
                          "span_start": r.start, "span_end": r.end, "span_text": r.text,
                          "state": "external" if r.external else res["state"],
                          "rule": res["rule"] or "explicit_reference_exact_v1"})
    for i, e in enumerate(edges, start=1):
        e["edge_key"] = f"e{i:04d}"
        e["confidence"] = RULES[e["rule"]]
    return {"nodes": nodes, "edges": edges}


# =========================================================================== resolution (pure, over node dicts)
def container_at(nodes: list[dict], pos: int) -> str:
    for n in nodes:
        if n["kind"] == "unit" and n["level"] == 1 and n["start"] <= pos < max(n["end"], n["start"] + 1):
            return n["ident_key"]
    return ""


def _parent_keys(key: str) -> list[str]:
    out = []
    k = key
    while True:
        if "/วรรค:" in k:
            k = k.rsplit("/วรรค:", 1)[0]
        elif k.endswith(")") and "(" in k:
            k = k[:k.rindex("(")]
        elif ":" in k and "." in k.split(":", 1)[1]:
            k = k.rsplit(".", 1)[0]
        else:
            return out
        out.append(k)


def resolve_in_version(nodes: list[dict], ref: Ref) -> dict:
    """Deterministic lookup of ``ref`` inside one source version. States: resolved, resolved_parent, ambiguous,
    unresolved_no_target, self_reference."""
    def done(state, targets, rule):
        return {"state": state, "targets": targets, "rule": rule,
                "confidence": RULES[rule] if rule else None}
    keyed = [n for n in nodes if n["ident_key"] and n["kind"] in ("unit", "subitem", "paragraph")]
    if ref.kind == "วรรค":
        enc = [n for n in keyed if n["kind"] == "unit" and n["level"] == 4 and n["start"] <= ref.start < n["end"]]
        if not enc:
            return done("unresolved_no_target", [], None)
        u = max(enc, key=lambda n: n["start"])
        t = [n for n in keyed if n["section_path"] == f"{u['section_path']}/วรรค:{ref.paragraph}"]
        return done("resolved", t, "explicit_reference_exact_v1") if len(t) == 1 else \
            done("unresolved_no_target", [], None)
    cont = container_at(nodes, ref.start)

    def match(key: str, unlabeled: bool) -> list[dict]:
        if unlabeled:
            c = [n for n in keyed if n["kind"] == "unit" and n["level"] == 1 and n["ident_kind"] == ref.kind]
        else:
            c = [n for n in keyed if n["ident_key"] == key]
        if len(c) > 1:
            same = [n for n in c if n["container"] == cont]
            c = same or c
        return c
    key = ref.key + (f"/วรรค:{ref.paragraph}" if ref.paragraph else "")
    c = match(key, not ref.label)
    rule = "explicit_reference_exact_v1"
    if not c:
        for pk in _parent_keys(key):
            c = match(pk, False)
            if c:
                rule = "explicit_reference_enclosing_unit_v1"
                break
    if len(c) > 1:
        return done("ambiguous", c, rule)
    if not c:
        return done("unresolved_no_target", [], None)
    t = c[0]
    if t["kind"] == "unit" and t["start"] <= ref.start < t["end"] and not ref.paragraph:
        return done("self_reference", c, rule)
    return done("resolved" if rule == "explicit_reference_exact_v1" else "resolved_parent", c, rule)


# =========================================================================== persistence and runtime resolution
class StructureStore:
    def __init__(self, store) -> None:
        self.store = store
        con = store.connect()
        try:   # additive migration: new tables only
            con.executescript(SCHEMA)
        finally:
            con.close()

    def persist(self, con, project_id: str, source_id: str, version_id: str, text: str, passages: list[dict],
                source_kind: str) -> dict:
        """Build and write the structure of one version inside the caller's transaction. A build error is recorded
        (status ``failed``) instead of blocking the import; acquisition then treats the version as unstructured."""
        if con.execute("SELECT 1 FROM structure_builds WHERE project_id=? AND source_id=? AND version_id=? AND "
                       "ruleset=?", (project_id, source_id, version_id, RULESET)).fetchone():
            return {"status": "exists"}
        try:
            built = build(text, passages, source_kind)
        except Exception as exc:  # noqa: BLE001 - recorded, never silent
            con.execute("INSERT INTO structure_builds VALUES (?,?,?,?,?,?,?,?,?,?)",
                        (project_id, source_id, version_id, RULESET, source_kind, "failed", 0, 0,
                         dumps({"error": type(exc).__name__, "message": str(exc)[:300]}), utc_now()))
            return {"status": "failed", "error": type(exc).__name__}
        for n in built["nodes"]:
            con.execute("INSERT INTO structure_nodes VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                        (project_id, source_id, version_id, n["node_key"], n["kind"], n["ident_kind"],
                         n["ident_label"], n["ident_key"], n["section_path"], n["container"], n["level"], n["start"],
                         n["end"], n["head_start"], n["head_end"], n["head_text"], n["parent_key"], n["passage_id"],
                         n["rule"], n["confidence"]))
        for e in built["edges"]:
            con.execute("INSERT INTO structure_edges VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                        (project_id, source_id, version_id, e["edge_key"], e["kind"], e["from_node"], e["to_node"],
                         e["from_passage"], e["span_start"], e["span_end"], e["span_text"], e["state"], e["rule"],
                         e["confidence"]))
        kinds: dict = {}
        for n in built["nodes"]:
            kinds[n["kind"]] = kinds.get(n["kind"], 0) + 1
        detail = {"profile": PROFILE, "node_kinds": kinds,
                  "exposed": {"numbering": True, "markdown_headings": source_kind == "owner_markdown",
                              "footnotes": source_kind == "owner_markdown", "tables": source_kind == "owner_markdown",
                              "geometry": False}}
        con.execute("INSERT INTO structure_builds VALUES (?,?,?,?,?,?,?,?,?,?)",
                    (project_id, source_id, version_id, RULESET, source_kind, "built", len(built["nodes"]),
                     len(built["edges"]), dumps(detail), utc_now()))
        return {"status": "built", "nodes": len(built["nodes"]), "edges": len(built["edges"])}

    def ensure(self, project_id: str, versions) -> None:
        """Build missing structure for existing versions (stores created before P4-T03), one transaction."""
        versions = list(versions)
        with self.store.read() as con:
            missing = [(s, v) for s, v in versions if not con.execute(
                "SELECT 1 FROM structure_builds WHERE project_id=? AND source_id=? AND version_id=? AND ruleset=?",
                (project_id, s, v, RULESET)).fetchone()]
        if not missing:
            return
        with self.store.tx() as con:
            for s, v in missing:
                row = con.execute("SELECT text, source_kind FROM source_versions WHERE project_id=? AND source_id=? "
                                  "AND version_id=?", (project_id, s, v)).fetchone()
                passages = [dict(p) for p in con.execute(
                    "SELECT passage_id, start_char, end_char, quote FROM passages WHERE project_id=? AND "
                    "source_id=? AND version_id=? ORDER BY start_char", (project_id, s, v))]
                self.persist(con, project_id, s, v, row["text"], passages, row["source_kind"])

    @staticmethod
    def build_state(con, project_id: str, source_id: str, version_id: str) -> str | None:
        r = con.execute("SELECT status FROM structure_builds WHERE project_id=? AND source_id=? AND version_id=? AND "
                        "ruleset=?", (project_id, source_id, version_id, RULESET)).fetchone()
        return r[0] if r else None

    @staticmethod
    def nodes(con, project_id: str, source_id: str, version_id: str) -> list[dict]:
        out = []
        for r in con.execute("SELECT * FROM structure_nodes WHERE project_id=? AND source_id=? AND version_id=? "
                             "ORDER BY start_char, node_key", (project_id, source_id, version_id)):
            d = dict(r)
            d["start"], d["end"] = d.pop("start_char"), d.pop("end_char")
            out.append(d)
        return out

    @staticmethod
    def edges(con, project_id: str, source_id: str, version_id: str) -> list[dict]:
        return [dict(r) for r in con.execute("SELECT * FROM structure_edges WHERE project_id=? AND source_id=? AND "
                                             "version_id=? ORDER BY edge_key", (project_id, source_id, version_id))]

    @staticmethod
    def _target(sid: str, vid: str, n: dict) -> dict:
        return {"source_id": sid, "version_id": vid, "node_key": n["node_key"], "kind": n["kind"],
                "ident_key": n["ident_key"], "section_path": n["section_path"], "passage_id": n["passage_id"],
                "start_char": n["start"], "end_char": n["end"], "head_text": n["head_text"][:200],
                "qualified_key": f"{sid}@{vid}#{n['section_path'] or n['node_key']}"}

    def resolve(self, con, project_id: str, ref: Ref, source_id: str, version_id: str, scope, titles: dict) -> dict:
        """Resolve ``ref`` found in (source_id, version_id) against the eligible ``scope`` [(sid, vid), ...] of the same
        candidate. ``titles`` maps (sid, vid) -> title. Returns {state, rule, confidence, targets, note}."""
        def out(state, targets=(), rule=None, note=""):
            return {"state": state, "targets": list(targets), "rule": rule,
                    "confidence": RULES[rule] if rule else None, "note": note}
        if self.build_state(con, project_id, source_id, version_id) != "built":
            return out("structure_unavailable", note="no structure was built for the referring version")
        if ref.external:
            inst = norm_title(ref.instrument)
            hits = []
            for s, v in scope:
                t = norm_title(titles.get((s, v), ""))
                if t and len(t) >= 6 and (t == inst or t.startswith(inst) or inst.startswith(t)):
                    hits.append((s, v))
            if not hits:
                return out("external_unidentified", note=f"no eligible source of this candidate is identified as "
                                                         f"'{ref.instrument}'")
            if len(hits) > 1:
                return out("external_ambiguous", note=f"{len(hits)} eligible sources match '{ref.instrument}'")
            s, v = hits[0]
            if self.build_state(con, project_id, s, v) != "built":
                return out("structure_unavailable", note=f"no structure for {s}@{v}")
            nodes = self.nodes(con, project_id, s, v)
            res = resolve_in_version(nodes, Ref(ref.kind, ref.label, ref.key, ref.paragraph, -1, -1, ref.text, None,
                                                False, ref.annex_type))
            state = res["state"] if res["state"] != "self_reference" else "resolved"
            return out(state, [self._target(s, v, n) for n in res["targets"]],
                       "external_instrument_title_v1" if res["targets"] else None,
                       note=f"instrument identified by title: {s}@{v}")
        nodes = self.nodes(con, project_id, source_id, version_id)
        res = resolve_in_version(nodes, ref)
        if res["state"] != "unresolved_no_target" or not ref.annex_type:
            return out(res["state"], [self._target(source_id, version_id, n) for n in res["targets"]], res["rule"])
        found = []
        for s, v in scope:
            if (s, v) == (source_id, version_id) or self.build_state(con, project_id, s, v) != "built":
                continue
            for n in self.nodes(con, project_id, s, v):
                if n["kind"] == "unit" and n["level"] == 1 and (
                        n["ident_key"] == ref.key if ref.label else n["ident_kind"] == ref.kind):
                    found.append((s, v, n))
        if len({(s, v) for s, v, _ in found}) > 1 or len(found) > 1:
            return out("ambiguous", [self._target(s, v, n) for s, v, n in found], "annex_unit_in_other_source_v1",
                       note="more than one eligible source holds this annex")
        if found:
            s, v, n = found[0]
            return out("resolved", [self._target(s, v, n)], "annex_unit_in_other_source_v1",
                       note=f"annex held by another source of the same candidate: {s}@{v}")
        return out("unresolved_no_target", note="no unit with this key in the version or the candidate's scope")

    def bindings(self, con, project_id: str, source_id: str, version_id: str, passage: dict) -> list[dict]:
        """Parser-exposed bindings of one passage whose bound unit lies in ANOTHER passage of the same version: the
        parent numbered unit's heading (when the passage does not hold it), footnote definitions of its markers, and
        the header row of a table it sits in."""
        if self.build_state(con, project_id, source_id, version_id) != "built":
            return []
        nodes = self.nodes(con, project_id, source_id, version_id)
        ps, pe, pid = passage["start_char"], passage["end_char"], passage["passage_id"]
        out = []
        enc = [n for n in nodes if n["kind"] in ("unit", "subitem") and n["start"] <= ps < n["end"]
               and n["head_start"] < ps and n["passage_id"] not in (None, pid)]
        if enc:
            n = max(enc, key=lambda n: (n["start"], n["level"]))
            out.append({"binding": "parent_unit_heading", "node": n, "rule": "numbering_hierarchy_v1",
                        "span_start": ps, "span_end": min(pe, ps + 40), "text": passage["quote"][:40]})
        defs = {n["ident_label"]: n for n in nodes if n["kind"] == "footnote"}
        for e in self.edges(con, project_id, source_id, version_id):
            if e["kind"] == "footnote_ref" and e["from_passage"] == pid and e["to_node"]:
                d = next((n for n in defs.values() if n["node_key"] == e["to_node"]), None)
                if d and d["passage_id"] not in (None, pid):
                    out.append({"binding": "footnote_definition", "node": d, "rule": "markdown_footnote_v1",
                                "span_start": e["span_start"], "span_end": e["span_end"], "text": e["span_text"]})
        for t in [n for n in nodes if n["kind"] == "table" and n["start"] <= ps < n["end"]]:
            h = next((n for n in nodes if n["kind"] == "table_header" and n["parent_key"] == t["node_key"]), None)
            if h and h["passage_id"] not in (None, pid):
                out.append({"binding": "table_header", "node": h, "rule": "markdown_pipe_table_v1",
                            "span_start": ps, "span_end": min(pe, ps + 40), "text": passage["quote"][:40]})
        return out

    def summary(self, con, project_id: str, source_id: str, version_id: str) -> dict | None:
        r = con.execute("SELECT * FROM structure_builds WHERE project_id=? AND source_id=? AND version_id=? AND "
                        "ruleset=?", (project_id, source_id, version_id, RULESET)).fetchone()
        if not r:
            return None
        d = dict(r)
        d["detail"] = json.loads(d.pop("detail_json"))
        return d
