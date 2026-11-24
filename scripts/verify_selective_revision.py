"""P4-T04: verify selective revision against full recomputation (deterministic, synthetic fixtures only).

For each scenario the harness builds one authored base corpus in an owner project, runs the full comparison once (the
"before" state S0), and then applies one change three ways:

* ``selective``     -- the product path: ``EvidenceCore.ingest_document`` imports the change and settles it through
                       ``_process_revision`` (re-acquire / re-validate by dependency), on a copy of S0;
* ``full_in_place`` -- the same import on another copy of S0, but the settle step only closes the event; then a full
                       ``run_comparison`` re-assesses every obligation in that store;
* ``full_scratch``  -- a new empty store, the final corpus imported, one full ``run_comparison``.

The evidence of every (candidate, requirement) cell is reduced to a version-independent signature (version ids are
replaced by the SHA-256 of the version text, so ``spec@v2`` in one store equals ``spec@v1`` in another when the text
is identical) and compared exactly: outcome, reading, explanation, cited span (source, content hash, passage,
code-point offsets, quote), the stored search receipt (ordered unit ids), the linked structural-acquisition receipt
(gaps, reference states, action, anchors with offsets, new and final units) and the obligation state.

Work is measured by instrumenting the engine objects of each store (seed searches, structural action searches,
acquisition steps, passages written to ``passages`` and to the Thai derivative index, structure builds, passage reads
from the run counters, provider-client construction, ``provider_usage`` rows) and by wall time. Every provider client
is replaced by a function that raises, so any model call would fail the run instead of passing silently.

A mismatch is reported, never repaired. No network, no model, no paid call, no download; the fixtures are authored
and say so in their first line. Nothing here measures retrieval effectiveness.

Usage::

    python scripts/verify_selective_revision.py --out receipt.json [--work-dir DIR] [--scenario ID ...]
        [--policy ptp-structural-acquisition/2.0.0]

``--policy`` sets the structural-acquisition policy of every run in every path (default: the engine default,
``ptp-structural-acquisition/2.1.0`` since owner decision D25). ``2.0.0`` reproduces the original D2 results.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from patent_to_pilot.workbench import acquisition as A  # noqa: E402
from patent_to_pilot.workbench import core as C  # noqa: E402
from patent_to_pilot.workbench import relation_search as R  # noqa: E402
from patent_to_pilot.workbench import thai_analyzer as TA  # noqa: E402

TASK_ID = "P4-T04"
# 1.1.0 (D25): --policy, the run counter of sibling seed searches (policy 2.1.0 S1a) in the work meter
HARNESS_VERSION = "ptp-p4-t04-selective-revision/1.1.0"
LABEL = "SYNTHETIC FIXTURE - NOT A REAL DOCUMENT - P4-T04 revision check"

# --------------------------------------------------------------------------------------------------- fixtures
CANDIDATES = [{"candidate_id": "C1", "label": "Supplier one"}, {"candidate_id": "C2", "label": "Supplier two"}]
REQUIREMENTS = [
    {"requirement_id": "P1", "label": "No powered circulation", "query": "Powered circulation",
     "field": "powered_circulation", "predicate": {"operator": "equals", "value": False}},
    {"requirement_id": "S1", "label": "spare parts list"},
    {"requirement_id": "T1", "label": "Covers 10-50 C", "query": "operating temperature",
     "field": "supported_temperature_range",
     "predicate": {"operator": "contains_interval", "minimum": 10, "maximum": 50, "unit": "degC"}},
]
# A1 sorts before E1, and A1's no-hit action anchors on a sibling requirement: on its stored citation under policy
# 2.0.0 (history-dependent, D2), on its current seed hits under policy 2.1.0 (D25)
ORDER_REQUIREMENTS = [
    {"requirement_id": "A1", "label": "annual application fee", "match": "phrase"},
    {"requirement_id": "E1", "label": "registered company", "query": "registered company"},
]


def _doc(title: str, *blocks: str) -> str:
    return "\n\n".join([LABEL, f"# {title}", *blocks]) + "\n"


SPEC = _doc("Supplier one product sheet",
            "Clause 1. The enclosure is rated for outdoor installation near the coast.",
            "Clause 2. The operating temperature of the unit is governed by Annex B.",
            "Clause 3. Cooling arrangement\nPowered circulation: no.",
            "Clause 4. The spare parts list is given in Annex D.")
ANNEX_A = _doc("Supplier one inland annex", "Annex A. Inland rule\nSupported temperature range: 0 to 40 °C.")
ANNEX_B = _doc("Supplier one coastal annex", "Annex B. Coastal exception\nSupported temperature range: 5 to 60 °C.")
MISC = _doc("Supplier one logistics note", "Crates are recyclable and ship on pallets.")
SHEET2 = _doc("Supplier two product sheet",
              "Clause 1. The enclosure is rated for outdoor installation.",
              "Clause 2. Operating range\nSupported temperature range: 0 to 70 °C.",
              "Clause 3. Cooling arrangement\nPowered circulation: yes.")
# no word of the S1 query ("spare parts list") occurs here, so S1's retrieved passages do not change
ANNEX_D = _doc("Supplier one stock annex", "Annex D. Components\nFilters, fans and gaskets are stocked for ten years.")

BASE = [  # (source_id, candidate_id, filename, text) -- imported in this order
    ("spec", "C1", "spec.md", SPEC),
    ("annex-a", "C1", "annex_a.md", ANNEX_A),
    ("annex-b", "C1", "annex_b.md", ANNEX_B),
    ("misc", "C1", "misc.md", MISC),
    ("sheet2", "C2", "sheet2.md", SHEET2),
]

ORDER_SPEC = _doc("Supplier one company profile",
                  "Section 1. Supplier one is a registered company.",
                  "Section 2. The application fee is 500 baht per filing.")
ORDER_PRICING = _doc("Supplier one price list", "Fee schedule: application filing 900 baht; annual renewal fee 300 baht.")
ORDER_MISC = _doc("Supplier one logistics note", "Crates are recyclable and ship on pallets.")
ORDER_BASE = [
    ("profile", "C1", "profile.md", ORDER_SPEC),
    ("pricing", "C1", "pricing.md", ORDER_PRICING),
    ("misc", "C1", "misc.md", ORDER_MISC),
]

# Each change: ("revise", source_id, new_text) | ("add", source_id, candidate_id, filename, text) | ("remove", sid)
SCENARIOS = [
    {"id": "a1-text-cited-annex", "kind": "source_text",
     "description": "Edit the cited Annex B passage (5 to 60 C -> 20 to 45 C); the clause that references it is "
                    "unchanged.",
     "changes": [("revise", "annex-b", ANNEX_B.replace("5 to 60", "20 to 45"))]},
    {"id": "a2-text-seed-clause", "kind": "source_text",
     "description": "Reword Clause 1 of the product sheet (a cited free-text passage); no field value changes.",
     "changes": [("revise", "spec", SPEC.replace("near the coast", "near the sea"))]},
    {"id": "a3-text-uncited-member", "kind": "source_text",
     "description": "Edit a member that no result cites or retrieves (logistics note).",
     "changes": [("revise", "misc", MISC.replace("on pallets", "on wooden pallets"))]},
    {"id": "b1-edge-target-relabelled", "kind": "scope_edge",
     "description": "Relabel the annex heading 'Annex B.' -> 'Annex C.' in the annex source; the referencing clause "
                    "is unchanged, so its 'Annex B' edge loses its target.",
     "changes": [("revise", "annex-b", ANNEX_B.replace("Annex B. Coastal", "Annex C. Coastal"))]},
    {"id": "b2-edge-retargeted", "kind": "scope_edge",
     "description": "Edit the referencing clause so its edge points to Annex A instead of Annex B.",
     "changes": [("revise", "spec", SPEC.replace("governed by Annex B", "governed by Annex A"))]},
    {"id": "b3-edge-made-ambiguous", "kind": "scope_edge",
     "description": "Edit an unrelated member so it also holds an 'Annex B.' unit: the clause's edge becomes "
                    "ambiguous.",
     "changes": [("revise", "misc", MISC + "\nAnnex B. Pallet rule\nPallets are heat treated.\n")]},
    {"id": "b4-edge-resolved-by-unrelated-member", "kind": "scope_edge",
     "description": "Edit an unrelated member so it holds the 'Annex D.' unit that Clause 4 refers to: an "
                    "unresolved edge becomes resolvable without any change to the retrieved passages.",
     "changes": [("revise", "misc", MISC + "\nAnnex D. Components\nFilters, fans and gaskets are stocked for ten "
                                    "years.\n")]},
    {"id": "c1-member-added-resolves-edge", "kind": "corpus_membership",
     "description": "Add a new member that holds 'Annex D.' (the unresolved reference of Clause 4).",
     "changes": [("add", "annex-d", "C1", "annex_d.md", ANNEX_D)]},
    {"id": "c2-member-added-retrieved", "kind": "corpus_membership",
     "description": "Add a new member that the temperature search retrieves directly (operating temperature stated "
                    "in place).",
     "changes": [("add", "addendum", "C1", "addendum.md",
                  _doc("Supplier one addendum", "Operating temperature addendum\n"
                                                "Supported temperature range: 15 to 45 °C."))]},
    {"id": "c3-member-added-other-candidate", "kind": "corpus_membership",
     "description": "Add a member to the other candidate (C2); C1 results must not move.",
     "changes": [("add", "sheet2-parts", "C2", "sheet2_parts.md",
                  _doc("Supplier two parts", "The spare parts list covers fans only."))]},
    {"id": "c4-member-removed", "kind": "corpus_membership",
     "description": "Remove a member (Annex B) from the corpus.",
     "changes": [("remove", "annex-b")]},
    {"id": "d1-sibling-anchor-order", "kind": "source_text", "base": "order",
     "description": "Edit an uncited member in a project where a no-hit requirement (A1) anchors its action on a "
                    "sibling requirement (E1) that sorts after it (its citation under policy 2.0.0, its current seed "
                    "hits under 2.1.0).",
     "changes": [("revise", "misc", ORDER_MISC.replace("on pallets", "on wooden pallets"))]},
]

BASES = {"main": (BASE, REQUIREMENTS), "order": (ORDER_BASE, ORDER_REQUIREMENTS)}


# --------------------------------------------------------------------------------------------------- instrumentation
class Meter:
    """Counts engine work on one EvidenceCore by wrapping its instance methods (no engine code is changed)."""

    KEYS = ("seed_searches", "structural_action_searches", "acquisition_steps", "derivative_rows_written",
            "derivative_full_rebuilds", "structure_builds", "provider_client_requests")

    def __init__(self, core) -> None:
        self.core = core
        self.n = dict.fromkeys(self.KEYS, 0)
        self._wrap(core, "_search", "seed_searches")
        self._wrap(core.acquisition, "_execute", "structural_action_searches")
        self._wrap(core.acquisition, "acquire", "acquisition_steps")
        self._wrap(core.structure, "persist", "structure_builds")
        self._wrap(core.product_lexical, "_rebuild", "derivative_full_rebuilds")
        real_insert = core.product_lexical._insert

        def insert(con, project_id, rows, *a, **k):
            rows = list(rows)
            self.n["derivative_rows_written"] += len(rows)
            return real_insert(con, project_id, rows, *a, **k)
        core.product_lexical._insert = insert

        def no_provider(*_a, **_k):
            self.n["provider_client_requests"] += 1
            raise AssertionError("P4-T04 harness: the local lexical profile must not dispatch to any provider")
        core.registry.client = no_provider

    def _wrap(self, obj, name: str, key: str) -> None:
        real = getattr(obj, name)

        def wrapped(*a, **k):
            self.n[key] += 1
            return real(*a, **k)
        setattr(obj, name, wrapped)

    def snapshot(self) -> dict:
        return dict(self.n)


def _count(core, sql: str, args=()) -> int:
    with core.store.read() as con:
        return con.execute(sql, args).fetchone()[0]


@contextmanager
def measured(core, meter: Meter, project_id: str, out: dict):
    before = meter.snapshot()
    rows = {"passages": _count(core, "SELECT COUNT(*) FROM passages WHERE project_id=?", (project_id,)),
            "structure_nodes": _count(core, "SELECT COUNT(*) FROM structure_nodes WHERE project_id=?", (project_id,)),
            "provider_usage": _count(core, "SELECT COUNT(*) FROM provider_usage"),
            "runs": {r for r in _rows(core, "SELECT run_id FROM runs WHERE project_id=?", (project_id,))}}
    t0 = time.perf_counter()
    yield
    wall = time.perf_counter() - t0
    after = meter.snapshot()
    new_runs = [r for r in _rows(core, "SELECT run_id FROM runs WHERE project_id=? ORDER BY started_at", (project_id,))
                if r not in rows["runs"]]
    counters = [json.loads(_rows(core, "SELECT counters_json FROM runs WHERE run_id=?", (r,))[0] or "{}")
                for r in new_runs]
    planned = sum(_count(core, "SELECT COUNT(*) FROM actions WHERE run_id=? AND action_type='plan_obligation'", (r,))
                  for r in new_runs)
    out.update({k: after[k] - before[k] for k in Meter.KEYS})
    out.update(
        wall_seconds=round(wall, 4), runs=len(new_runs),
        obligations_reassessed=planned,
        obligations_reused_after_verification=sum(c.get("reused_after_verification", 0) for c in counters),
        passage_reads=sum(c.get("source_reads", 0) for c in counters),
        run_counter_acquisition_actions=sum(c.get("acquisition_actions", 0) for c in counters),
        run_counter_structural_actions=sum(c.get("structural_actions", 0) for c in counters),
        run_counter_sibling_seed_searches=sum(c.get("sibling_seed_searches", 0) for c in counters),
        paid_model_calls=sum(c.get("paid_model_calls", 0) for c in counters),
        remote_calls=sum(c.get("remote_calls", 0) for c in counters),
        passages_indexed=_count(core, "SELECT COUNT(*) FROM passages WHERE project_id=?", (project_id,)) - rows["passages"],
        structure_nodes_written=_count(core, "SELECT COUNT(*) FROM structure_nodes WHERE project_id=?", (project_id,))
        - rows["structure_nodes"],
        provider_usage_rows=_count(core, "SELECT COUNT(*) FROM provider_usage") - rows["provider_usage"])


def _rows(core, sql: str, args=()) -> list:
    with core.store.read() as con:
        return [r[0] for r in con.execute(sql, args)]


# --------------------------------------------------------------------------------------------------- engine driving
def _new_core(data_dir: Path):
    core = C.EvidenceCore(data_dir)
    return core, Meter(core)


def _ingest(core, pid: str, sid: str, cand: str, filename: str, text: str) -> dict:
    out = core.ingest_document(pid, filename, text.encode("utf-8"), cand, sid)
    if out["status"] != "ingested":
        raise RuntimeError(f"ingest of {sid} did not import a version: {out['status']}")
    return out


def _apply(core, pid: str, base_docs: list, change: tuple) -> dict:
    """Apply one change through the product API. Returns the ingest result, or an UNSUPPORTED record."""
    if change[0] == "revise":
        _op, sid, text = change
        cand, filename = next((c, f) for s, c, f, _t in base_docs if s == sid)
        return _ingest(core, pid, sid, cand, filename, text)
    if change[0] == "add":
        _op, sid, cand, filename, text = change
        return _ingest(core, pid, sid, cand, filename, text)
    if change[0] == "remove":
        api = [n for n in ("remove_source", "remove_document", "delete_source", "retire_source", "archive_source")
               if hasattr(core, n)]
        return {"status": "unsupported", "reason": "the engine has no corpus-removal operation "
                "(checked EvidenceCore for remove_source/remove_document/delete_source/retire_source/archive_source; "
                f"found {api or 'none'}); ingest_document only adds sources or new versions"}
    raise ValueError(change[0])


def _final_corpus(base_docs: list, changes: list) -> list:
    docs = [list(d) for d in base_docs]
    for ch in changes:
        if ch[0] == "revise":
            next(d for d in docs if d[0] == ch[1])[3] = ch[2]
        elif ch[0] == "add":
            docs.append([ch[1], ch[2], ch[3], ch[4]])
        elif ch[0] == "remove":
            docs = [d for d in docs if d[0] != ch[1]]
    return [tuple(d) for d in docs]


def _close_without_settling(core):
    """full_in_place: the import happens exactly as in the product path, but the reopened work is not processed
    selectively; the event is closed and a full comparison follows."""
    def settle(project_id, entry, mission, invoked_via):
        with core.store.tx() as con:
            con.execute("UPDATE change_events SET status='applied', result_json=?, applied_at=? WHERE project_id=? "
                        "AND event_id=?", (C.dumps({"note": "P4-T04 full_in_place: settled by a full rerun"}),
                                           C.utc_now(), project_id, entry["event_id"]))
        return {"already_applied": False, "event_id": entry["event_id"], "run_id": None, "result": None}
    core._settle_event = settle


def _build_base(work: Path, base_docs: list, reqs: list) -> tuple[Path, str]:
    d = work / "base"
    core, _m = _new_core(d)
    pid = core.create_project("P4-T04 revision check", CANDIDATES, reqs)["project_id"]
    for sid, cand, fn, text in base_docs:
        _ingest(core, pid, sid, cand, fn, text)
    run = core.run_comparison(pid)
    if run["status"] != "completed":
        raise RuntimeError(f"base comparison did not complete: {run['stop_reason']}")
    return d, pid


def _clone(src_dir: Path, dst_dir: Path):
    dst_dir.mkdir(parents=True, exist_ok=True)
    C.EvidenceCore(src_dir).store.backup(dst_dir / "workbench.sqlite3")
    return _new_core(dst_dir)


# --------------------------------------------------------------------------------------------------- signatures
_UNIT = re.compile(r"(?P<sid>[A-Za-z0-9][A-Za-z0-9._-]*)@(?P<vid>v\d+)(?=$|[^A-Za-z0-9_])")


def _version_hashes(core, pid: str) -> dict:
    with core.store.read() as con:
        return {(r[0], r[1]): r[2][:12] for r in con.execute(
            "SELECT source_id, version_id, sha256 FROM source_versions WHERE project_id=?", (pid,))}


def _norm(value, vh: dict):
    """Replace every 'source@vN' by 'source@<content-sha12>' inside strings, lists and dicts."""
    if isinstance(value, str):
        return _UNIT.sub(lambda m: f"{m['sid']}@{vh.get((m['sid'], m['vid']), m['vid'] + '?')}", value)
    if isinstance(value, list):
        return [_norm(v, vh) for v in value]
    if isinstance(value, dict):
        return {k: _norm(v, vh) for k, v in value.items()}
    return value


def _receipt_signature(rec: dict | None, vh: dict) -> dict | None:
    if rec is None:
        return None
    sel = rec.get("selection") or {}
    keep = {
        "gaps": rec.get("gaps"), "outcome": rec.get("outcome"), "action": rec.get("action"),
        "action_key": rec.get("action_key"), "query": rec.get("query"),
        "anchors": [{k: a.get(k) for k in ("source_id", "version_id", "start", "end", "text", "kind")}
                    for a in rec.get("anchors") or []],
        "reference_states": [{"action_key": c.get("action_key"), "action": c.get("action"), "state": c.get("state"),
                              "actionable": c.get("actionable")} for c in sel.get("candidates") or []],
        "pool_before": rec.get("pool_before"), "new_unit_ids": rec.get("new_unit_ids"),
        "same_document_unit_ids": rec.get("same_document_unit_ids"), "new_document_ids": rec.get("new_document_ids"),
        "final_ids": rec.get("final_ids"), "search_calls": rec.get("search_calls"),
    }
    out = _norm(keep, vh)
    for a in out["anchors"]:   # anchor version -> content hash
        if a.get("version_id"):
            a["version_id"] = vh.get((a["source_id"], a["version_id"]), a["version_id"])
    return out


def signatures(core, pid: str) -> dict:
    """Version-independent evidence signature of every current cell, plus every obligation's state."""
    vh = _version_hashes(core, pid)
    out = {}
    with core.store.read() as con:
        active = {r["requirement_id"] for r in core._project(con, pid)["mission"]["requirements"]}
        obl = {(r["candidate_id"], r["requirement_id"]): r["state"]
               for r in con.execute("SELECT * FROM obligations WHERE project_id=?", (pid,))}
        for a in con.execute("SELECT * FROM assessments WHERE project_id=? AND state='current' ORDER BY candidate_id, "
                             "requirement_id", (pid,)).fetchall():
            if a["requirement_id"] not in active:
                continue
            c = con.execute("SELECT * FROM citations WHERE assessment_id=?", (a["assessment_id"],)).fetchone()
            cit = None
            if c is not None:
                cit = {"source_id": c["source_id"], "content": c["sha256"][:12], "passage_id": c["passage_id"],
                       "start_char": c["start_char"], "end_char": c["end_char"], "quote": c["quote"]}
            hits = [f"{h['source_id']}@{vh.get((h['source_id'], h['version_id']), h['version_id'] + '?')}"
                    f"#{h['passage_id']}" + ("+acquired" if h.get("acquired") else "")
                    for h in json.loads(a["search_hits_json"])]
            r = con.execute("SELECT receipt_json FROM acquisition_receipts WHERE assessment_id=? ORDER BY created_at "
                            "DESC, run_id DESC, seq DESC LIMIT 1", (a["assessment_id"],)).fetchone()
            key = f"{a['candidate_id']}/{a['requirement_id']}"
            rec = json.loads(r[0]) if r else None
            out[key] = {"outcome": a["outcome"], "reading": json.loads(a["reading_json"]),
                        "explanation": _norm(a["explanation"], vh), "citation": cit, "search_hits": hits,
                        "acquisition": _receipt_signature(rec, vh),
                        "obligation_state": obl.get((a["candidate_id"], a["requirement_id"])),
                        # provenance, not evidence: the eligible scope recorded when the receipt was written
                        PROVENANCE: {"receipt_eligible_scope": _norm((rec or {}).get("eligible_scope"), vh)}}
        for (cand, rid), state in obl.items():
            key = f"{cand}/{rid}"
            if rid in active and key not in out:
                out[key] = {"outcome": None, "obligation_state": state}
    return dict(sorted(out.items()))


PROVENANCE = "provenance"


def diff(a: dict, b: dict, provenance: bool = False) -> dict:
    """Per cell, the evidence fields whose values differ (exact comparison). ``provenance=True`` compares only the
    receipt provenance (reported separately; a re-validated cell keeps the receipt written by its original run)."""
    pick = (lambda v: None if v is None else {PROVENANCE: v.get(PROVENANCE)}) if provenance else         (lambda v: None if v is None else {f: x for f, x in v.items() if f != PROVENANCE})
    a = {k: pick(v) for k, v in a.items()}
    b = {k: pick(v) for k, v in b.items()}
    out = {}
    for k in sorted(set(a) | set(b)):
        x, y = a.get(k), b.get(k)
        if x == y:
            continue
        if x is None or y is None:
            out[k] = {"cell": {"left": x, "right": y}}
            continue
        fields = {f: {"left": x.get(f), "right": y.get(f)} for f in sorted(set(x) | set(y)) if x.get(f) != y.get(f)}
        out[k] = fields
    return out


# --------------------------------------------------------------------------------------------------- one scenario
@contextmanager
def structural_policy(policy: str | None):
    """Every run of every path (base, selective settle, full reruns) uses ``policy`` (None: the engine default)."""
    if policy is None:
        yield A.DEFAULT_POLICY
        return
    if policy not in R.STRUCTURAL_POLICY_NAMES:
        raise ValueError(f"unknown structural policy {policy}; one of {sorted(R.STRUCTURAL_POLICY_NAMES)}")
    old = A.DEFAULT_POLICY
    A.DEFAULT_POLICY = policy
    try:
        yield policy
    finally:
        A.DEFAULT_POLICY = old


def run_scenario(sc: dict, work: Path, disable_scope_fix: bool = False, policy: str | None = None) -> dict:
    with structural_policy(policy) as used:
        rep = _run_scenario(sc, work, disable_scope_fix)
    rep["acquisition_policy"] = used
    return rep


def _run_scenario(sc: dict, work: Path, disable_scope_fix: bool = False) -> dict:
    base_docs, reqs = BASES[sc.get("base", "main")]
    work.mkdir(parents=True, exist_ok=True)
    base_dir, pid = _build_base(work, base_docs, reqs)
    base_core = C.EvidenceCore(base_dir)
    s0 = signatures(base_core, pid)
    rep = {"id": sc["id"], "kind": sc["kind"], "description": sc["description"],
           "changes": [{"op": c[0], "source_id": c[1]} for c in sc["changes"]]}

    # ---- selective (product path) on a copy of S0
    sel_core, sel_m = _clone(base_dir, work / "selective")
    if disable_scope_fix:   # reproduce the selective path as it was before the P4-T04 fix (defect demonstration)
        sel_core._decision_depends_on_scope = lambda *_a, **_k: False
    sel_work, results = {}, []
    with measured(sel_core, sel_m, pid, sel_work):
        for ch in sc["changes"]:
            results.append(_apply(sel_core, pid, base_docs, ch))
    unsupported = [r for r in results if r.get("status") == "unsupported"]
    if unsupported:
        rep.update(verdict="NOT_SUPPORTED", reason=unsupported[0]["reason"], selective_work=sel_work)
        return rep
    sel = signatures(sel_core, pid)
    plan = results[-1]["result"] or {}
    rep["selective_plan"] = {k: plan.get(k) for k in ("reacquired", "revalidated_by_search", "outside_changed_scope")}

    # ---- full in place: same import, then one full comparison
    inp_core, inp_m = _clone(base_dir, work / "full_in_place")
    _close_without_settling(inp_core)
    inp_work = {}
    with measured(inp_core, inp_m, pid, inp_work):
        for ch in sc["changes"]:
            _apply(inp_core, pid, base_docs, ch)
        inp_core.run_comparison(pid)
    inp = signatures(inp_core, pid)

    # ---- full from scratch: new store, final corpus, one full comparison
    scr_core, scr_m = _new_core(work / "full_scratch")
    scr_work = {}
    with measured(scr_core, scr_m, "", scr_work):   # project id unknown before creation: rows counted store-wide
        spid = scr_core.create_project("P4-T04 revision check", CANDIDATES, reqs)["project_id"]
        for sid, cand, fn, text in _final_corpus(base_docs, sc["changes"]):
            _ingest(scr_core, spid, sid, cand, fn, text)
        scr_core.run_comparison(spid)
    _recount_store_wide(scr_core, spid, scr_work)
    scr = signatures(scr_core, spid)

    truth_changed = sorted(diff(s0, scr))
    sel_changed = sorted(diff(s0, sel))
    reprocessed = sorted(set(plan.get("reacquired") or []))
    d_scr, d_inp, d_inp_scr = diff(sel, scr), diff(sel, inp), diff(inp, scr)
    rep.update(
        truth_changed_cells=truth_changed, selective_changed_cells=sel_changed,
        selective_reacquired=reprocessed,
        selective_revalidated=sorted(plan.get("revalidated_by_search") or []),
        selective_untouched=sorted(plan.get("outside_changed_scope") or []),
        over_invalidated=sorted(k for k in reprocessed if k not in truth_changed),
        missed=sorted(k for k in truth_changed if k not in reprocessed),
        mismatch_selective_vs_scratch=d_scr, mismatch_selective_vs_in_place=d_inp,
        mismatch_in_place_vs_scratch=d_inp_scr,
        provenance_only_selective_vs_scratch=sorted(diff(sel, scr, provenance=True)),
        selective_work=sel_work, full_in_place_work=inp_work, full_scratch_work=scr_work,
        cells_after={k: _brief(v) for k, v in scr.items()})
    # primary check: the selective path against a full recomputation from scratch on the final corpus
    if not d_scr:
        rep["verdict"] = "MATCH"
    elif not d_inp:
        rep["verdict"] = "MISMATCH_HISTORY"      # selective = full rerun in the same store; both differ from scratch
    else:
        rep["verdict"] = "MISMATCH_SELECTIVE"    # the selective path differs from both full recomputations
    # secondary check: does a full rerun in the existing store reproduce a full run from scratch?
    rep["full_in_place_vs_scratch"] = "MATCH" if not d_inp_scr else "MISMATCH_HISTORY"
    return rep


def _recount_store_wide(core, pid: str, out: dict) -> None:
    out["passages_indexed"] = _count(core, "SELECT COUNT(*) FROM passages WHERE project_id=?", (pid,))
    out["structure_nodes_written"] = _count(core, "SELECT COUNT(*) FROM structure_nodes WHERE project_id=?", (pid,))
    runs = _rows(core, "SELECT run_id FROM runs WHERE project_id=?", (pid,))
    counters = [json.loads(_rows(core, "SELECT counters_json FROM runs WHERE run_id=?", (r,))[0] or "{}") for r in runs]
    out["runs"] = len(runs)
    out["obligations_reassessed"] = sum(
        _count(core, "SELECT COUNT(*) FROM actions WHERE run_id=? AND action_type='plan_obligation'", (r,)) for r in runs)
    out["passage_reads"] = sum(c.get("source_reads", 0) for c in counters)
    out["run_counter_acquisition_actions"] = sum(c.get("acquisition_actions", 0) for c in counters)
    out["run_counter_structural_actions"] = sum(c.get("structural_actions", 0) for c in counters)
    out["run_counter_sibling_seed_searches"] = sum(c.get("sibling_seed_searches", 0) for c in counters)
    out["paid_model_calls"] = sum(c.get("paid_model_calls", 0) for c in counters)
    out["remote_calls"] = sum(c.get("remote_calls", 0) for c in counters)


def _brief(sig: dict) -> dict:
    c = sig.get("citation")
    acq = sig.get("acquisition") or {}
    return {"outcome": sig.get("outcome"),
            "citation": None if c is None else f"{c['source_id']}#{c['passage_id']}[{c['start_char']}:{c['end_char']}]",
            "action": acq.get("action"), "gaps": acq.get("gaps")}


# --------------------------------------------------------------------------------------------------- whole run
def environment() -> dict:
    import platform
    import sqlite3
    try:
        an = TA.analyzer()
        analyzer = an.identity_id
    except TA.AnalyzerUnavailable as exc:
        analyzer = f"unavailable ({exc}); owner projects use the legacy unicode61 index"
    return {"python": platform.python_version(), "sqlite": sqlite3.sqlite_version, "platform": platform.platform(),
            "thai_analyzer": analyzer, "core_code_sha256": C.core_code_sha256()}


def run_all(work_dir: Path, only: list[str] | None = None, disable_scope_fix: bool = False,
            policy: str | None = None) -> dict:
    scenarios = [s for s in SCENARIOS if not only or s["id"] in only]
    reports = [run_scenario(s, work_dir / s["id"], disable_scope_fix, policy) for s in scenarios]
    totals = {}
    for path in ("selective_work", "full_in_place_work", "full_scratch_work"):
        keys = ("obligations_reassessed", "seed_searches", "run_counter_acquisition_actions",
                "run_counter_sibling_seed_searches", "structural_action_searches", "passage_reads",
                "passages_indexed", "derivative_rows_written", "structure_nodes_written", "wall_seconds",
                "paid_model_calls", "remote_calls", "provider_client_requests", "provider_usage_rows")
        totals[path] = {k: round(sum(r.get(path, {}).get(k, 0) for r in reports), 4) for k in keys}
    return {"record_schema": HARNESS_VERSION, "task": TASK_ID, "data": "authored synthetic fixtures only",
            "claim_boundary": "engineering check of the revision path; not a retrieval-effectiveness result",
            "environment": environment(), "selective_path": "pre-P4-T04 (scope fix disabled)" if disable_scope_fix
            else "current engine", "acquisition_policy": policy or A.DEFAULT_POLICY,
            "acquisition_policy_sha256": R.PINNED_POLICY_SHA256[policy or A.DEFAULT_POLICY], "scenarios": reports,
            "verdicts": {r["id"]: r["verdict"] for r in reports}, "work_totals": totals}


def markdown(rep: dict) -> str:
    """The comparison and work tables of the receipt."""
    lines = ["| Scenario | Kind | Selective vs scratch | Full in place vs scratch | Changed cells (scratch truth) | "
             "Re-acquired | Re-validated by search | Untouched | Missed | Over-invalidated |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    j = lambda xs: ", ".join(xs) if xs else "none"   # noqa: E731
    for s in rep["scenarios"]:
        if s["verdict"] == "NOT_SUPPORTED":
            lines.append(f"| {s['id']} | {s['kind']} | NOT_SUPPORTED | - | - | - | - | - | - | - |")
            continue
        lines.append(f"| {s['id']} | {s['kind']} | {s['verdict']} | {s['full_in_place_vs_scratch']} | "
                     f"{j(s['truth_changed_cells'])} | {j(s['selective_reacquired'])} | "
                     f"{j(s['selective_revalidated'])} | {len(s['selective_untouched'])} | {j(s['missed'])} | "
                     f"{j(s['over_invalidated'])} |")
    keys = [("obligations_reassessed", "obligations re-assessed"), ("seed_searches", "seed searches (measured)"),
            ("run_counter_acquisition_actions", "searches in run counters"),
            ("run_counter_sibling_seed_searches", "sibling seed searches in run counters"),
            ("structural_action_searches", "structural action searches"), ("passage_reads", "passage reads"),
            ("passages_indexed", "passages indexed"), ("derivative_rows_written", "Thai index rows written"),
            ("structure_nodes_written", "structure nodes written"), ("wall_seconds", "wall s"),
            ("provider_usage_rows", "provider requests"), ("paid_model_calls", "paid model calls")]
    lines += ["", "| Scenario | Path | " + " | ".join(k[1] for k in keys) + " |",
              "|---|---|" + "---|" * len(keys)]
    for s in rep["scenarios"]:
        for path, name in (("selective_work", "selective"), ("full_in_place_work", "full in place"),
                           ("full_scratch_work", "full scratch")):
            w = s.get(path)
            if not w:
                continue
            lines.append(f"| {s['id']} | {name} | " + " | ".join(str(w.get(k, 0)) for k, _ in keys) + " |")
    lines += ["", "| Path | " + " | ".join(k[1] for k in keys) + " |", "|---|" + "---|" * len(keys)]
    for path, w in rep["work_totals"].items():
        lines.append(f"| {path.replace('_work', '')} | " + " | ".join(str(w.get(k, 0)) for k, _ in keys) + " |")
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--out", type=Path, help="write the JSON report here")
    ap.add_argument("--markdown", type=Path, help="write the receipt tables (Markdown) here")
    ap.add_argument("--work-dir", type=Path, help="keep the stores here (default: a temporary directory)")
    ap.add_argument("--scenario", action="append", help="run only these scenario ids")
    ap.add_argument("--without-scope-fix", action="store_true",
                    help="disable the P4-T04 re-acquisition rule in the selective path (shows the original defect)")
    ap.add_argument("--policy", choices=sorted(R.STRUCTURAL_POLICY_NAMES),
                    help="structural-acquisition policy of every run (default: the engine default, 2.1.0 since D25; "
                         "2.0.0 reproduces defect D2)")
    args = ap.parse_args(argv)
    tmp = None
    work = args.work_dir
    if work is None:
        tmp = tempfile.mkdtemp(prefix="ptp-p4t04-")
        work = Path(tmp)
    try:
        rep = run_all(work, args.scenario, args.without_scope_fix, args.policy)
    finally:
        if tmp:
            shutil.rmtree(tmp, ignore_errors=True)
    text = json.dumps(rep, ensure_ascii=False, indent=1, sort_keys=False) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8", newline="\n")
    if args.markdown:
        args.markdown.parent.mkdir(parents=True, exist_ok=True)
        args.markdown.write_text(markdown(rep), encoding="utf-8", newline="\n")
    for r in rep["scenarios"]:
        print(f"{r['id']:40s} {r['verdict']:20s} in-place-vs-scratch: {r.get('full_in_place_vs_scratch', '-')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
