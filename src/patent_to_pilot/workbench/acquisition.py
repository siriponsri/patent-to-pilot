"""P4-T03: structural acquisition inside the real assessment path (owner fix plan of 23 Nov 2026, section 5.3).

``EvidenceCore._acquire_and_commit`` calls ``Acquisition.acquire`` after the seed search of every obligation of an owner
project and BEFORE the assessment is read and committed:

    seed search -> observable gap? -> at most ONE scoped structural action (policy v2) -> merge + original-requirement
    rerank -> read/assess against the original requirement -> commit assessment, citation, dependencies and receipt

* Gap signals and the four action kinds are those of ``relation_search.POLICY_V2`` / ``POLICY_V2_1`` (pinned). The
  pure operator ``relation_search.structural_action_step`` executes the action; this module supplies the Workbench
  backends: the persisted document structure (``structure.StructureStore``) for reference resolution and context recovery, and the
  product Thai index (``passage_fts_th_v1``, P4-T01a analyzer) for scoped search. Legacy ``trace_slice`` helpers and the
  frozen P0-T06 / P2 routes are not used or changed.
* Scope: every route is restricted to the project, the obligation's candidate, the candidate's CURRENT source versions
  and an optional declared date rule; the eligibility mask is re-checked after merging, and ``EvidenceCore._commit``
  refuses a citation from another candidate's source.
* Each obligation gets one persisted action receipt (``acquisition_receipts``, also written as the run action
  ``structural_acquisition``) linked to the assessment it fed; the UI reads these persisted receipts.
* ``baseline`` mode runs the unchanged pre-P4-T03 path (no action); its receipt records the observed gaps only, so the two
  modes can be compared on the same store.
* Policy version (owner decision D25, P4-T04 defect D2): runs use ``relation_search.POLICY_V2_1``
  (``ptp-structural-acquisition/2.1.0``) by default. The only rule it changes is the anchor of a requirement whose own
  seed pool is empty: 2.0.0 took the source cited by the candidate's stored current assessments of other requirements
  (history- and order-dependent); 2.1.0 takes it from the seed hits of the candidate's other active requirements,
  recomputed on the current corpus in the same run (``_sibling_seeds``). The run option
  ``{"policy": "ptp-structural-acquisition/2.0.0"}`` still selects the old rule, for reproduction only.
"""
from __future__ import annotations

from datetime import date
import json
import re

from patent_to_pilot.workbench import parser as P
from patent_to_pilot.workbench import product_lexical as PL
from patent_to_pilot.workbench import relation_search as R
from patent_to_pilot.workbench import structure as S
from patent_to_pilot.workbench import thai_analyzer as TA
from patent_to_pilot.workbench.core import (TERM_STOPWORDS, ValidationFailed, fts_phrase, fts_terms, requirement_kind,
                                            requirement_match, sha256)
from patent_to_pilot.workbench.store import dumps, utc_now

TASK_ID = "P4-T03"
MODES = ("structural", "baseline")
DEFAULT_MODE = "structural"
ACTION_FETCH_LIMIT = 20
ACTION_RESULT_LIMIT = 5
MAX_REFERENCES = 40
SUBSTRING_MIN_CHARS = 2
DATE_FIELDS = ("effective", "publication")
OPTION_KEYS = ("mode", "declared_missing", "date_cutoff", "date_field", "source_dates", "missing_date", "policy")
DEFAULT_POLICY = R.CURRENT_STRUCTURAL_POLICY.name     # D25: ptp-structural-acquisition/2.1.0
SIBLING_ANCHOR_MAX = 3
SCHEMA = """
CREATE TABLE IF NOT EXISTS acquisition_receipts (
  project_id TEXT NOT NULL, run_id TEXT NOT NULL, seq INTEGER NOT NULL, candidate_id TEXT NOT NULL,
  requirement_id TEXT NOT NULL, requirement_sha256 TEXT NOT NULL, requirement_lifecycle_revision INTEGER NOT NULL,
  mode TEXT NOT NULL, policy TEXT NOT NULL, policy_sha256 TEXT NOT NULL, action TEXT, outcome TEXT NOT NULL,
  receipt_json TEXT NOT NULL, receipt_sha256 TEXT NOT NULL, assessment_id TEXT, commit_status TEXT NOT NULL,
  created_at TEXT NOT NULL, committed_at TEXT, PRIMARY KEY (run_id, seq));
"""
SUMMARIES = {
    "no_gap": "No evidence gap was observed after the seed search, so no extra action ran.",
    "no_actionable_gap": "A gap was observed, but no eligible action could run (see the visible states).",
    "budget_exhausted": "A gap was observed, but the declared action budget was already spent.",
    "no_new_units": "One structural action ran; it found no unit that was not already in the pool.",
    "baseline_no_action": "Baseline mode: the unchanged assessment path ran without any structural action.",
}


def unit_id(sid: str, vid: str, pid: str) -> str:
    return f"{sid}@{vid}#{pid}"


def split_unit(uid: str) -> tuple[str, str, str]:
    sv, pid = uid.split("#", 1)
    sid, vid = sv.split("@", 1)
    return sid, vid, pid


def _iso(value, what: str) -> str:
    try:
        return date.fromisoformat(value).isoformat()
    except (TypeError, ValueError):
        raise ValidationFailed(f"{what} must be an ISO date YYYY-MM-DD", "bad_acquisition_date") from None


class Acquisition:
    def __init__(self, core) -> None:
        self.core, self.store = core, core.store
        con = self.store.connect()
        try:   # additive migration: one new table
            con.executescript(SCHEMA)
        finally:
            con.close()

    # ------------------------------------------------------------------ run options
    def options(self, origin: str, mission: dict, raw=None) -> dict:
        """Validated acquisition options of one run. Only owner projects take part; the G01 sample and the synthetic
        projects keep their recorded path unchanged (mode ``off``)."""
        if origin != "owner_files":
            return {"mode": "off", "reason": "structural acquisition applies to owner projects only; the sample and "
                                             "synthetic projects keep their recorded path"}
        raw = {} if raw is None else ({"mode": raw} if isinstance(raw, str) else raw)
        if not isinstance(raw, dict):
            raise ValidationFailed("acquisition must be a mode name or an object", "bad_acquisition")
        unknown = sorted(set(raw) - set(OPTION_KEYS))
        if unknown:
            raise ValidationFailed(f"unknown acquisition options {unknown}", "bad_acquisition")
        mode = raw.get("mode") or DEFAULT_MODE
        if mode not in MODES:
            raise ValidationFailed(f"acquisition mode must be one of {list(MODES)}", "bad_acquisition_mode")
        active = {r["requirement_id"] for r in mission["requirements"]}
        cands = {c["candidate_id"] for c in mission["candidates"]}
        declared = []
        for d in raw.get("declared_missing") or []:
            if not isinstance(d, dict) or d.get("candidate_id") not in cands:
                raise ValidationFailed("declared_missing needs a known candidate_id", "unknown_candidate")
            if d.get("requirement_id") not in active:
                raise ValidationFailed("declared_missing needs an active requirement_id", "unknown_requirement")
            declared.append([d["candidate_id"], d["requirement_id"]])
        cutoff = raw.get("date_cutoff")
        field = raw.get("date_field")
        dates: dict = {}
        if cutoff is not None:
            cutoff = _iso(cutoff, "date_cutoff")
            if field not in DATE_FIELDS:
                raise ValidationFailed(f"date_field must be one of {list(DATE_FIELDS)} (effective and publication "
                                       "dates are distinct)", "bad_acquisition_date")
        src = raw.get("source_dates") or {}
        if not isinstance(src, dict):
            raise ValidationFailed("source_dates must map a source to {effective, publication}", "bad_acquisition_date")
        for k, v in src.items():
            if not isinstance(v, dict) or set(v) - set(DATE_FIELDS):
                raise ValidationFailed("each source_dates entry is {effective?, publication?}", "bad_acquisition_date")
            dates[k] = {f: _iso(d, f"source_dates.{k}.{f}") for f, d in v.items() if d is not None}
        missing = raw.get("missing_date") or "exclude"
        if missing not in ("exclude", "include"):
            raise ValidationFailed("missing_date must be 'exclude' or 'include'", "bad_acquisition_date")
        policy = raw.get("policy") or DEFAULT_POLICY
        if policy not in R.STRUCTURAL_POLICY_NAMES:
            raise ValidationFailed(f"policy must be one of {sorted(R.STRUCTURAL_POLICY_NAMES)}", "bad_acquisition_policy")
        limits = mission["limits"]
        return {"mode": mode, "policy": policy, "policy_sha256": R.PINNED_POLICY_SHA256[policy],
                "structure_ruleset": S.RULESET, "structure_profile": S.PROFILE, "declared_missing": sorted(declared),
                "date_cutoff": cutoff, "date_field": field if cutoff else None, "source_dates": dates,
                "missing_date": missing,
                "max_structural_actions": int(limits.get("max_structural_actions", limits["max_acquisition_actions"])),
                "fetch_limit": ACTION_FETCH_LIMIT, "result_limit": ACTION_RESULT_LIMIT}

    @staticmethod
    def setup_record(opts: dict) -> dict:
        return {**opts, "task": TASK_ID, "claim_boundary": R.V2_CLAIM_BOUNDARY,
                "per_obligation_budget": R.POLICIES[opts["policy"]].max_expansion_searches}

    # ------------------------------------------------------------------ scope
    def _scope(self, con, project_id: str, cand: str, opts: dict):
        current = self.core._scope(con, project_id, cand)           # this candidate's current versions only
        every = [(r[0], r[1]) for r in con.execute("SELECT source_id, version_id FROM source_versions WHERE "
                                                   "project_id=?", (project_id,))]
        dates = {}
        if opts.get("date_cutoff"):
            for s, v in current:
                d = opts["source_dates"].get(f"{s}@{v}") or opts["source_dates"].get(s) or {}
                dates[f"{s}@{v}"] = d.get(opts["date_field"])
        mask = R.EligibilityMask(
            profile_id=f"candidate-current-scope:{cand}" + (f";{opts['date_field']}<{opts['date_cutoff']}"
                                                            if opts.get("date_cutoff") else ""),
            exclude_groups=frozenset(f"{s}@{v}" for s, v in every if (s, v) not in set(current)),
            grouping="source_id@version_id (project, candidate, current version)",
            group_of=lambda u: u.split("#", 1)[0], dates=dates, date_cutoff=opts.get("date_cutoff"),
            missing_date=opts.get("missing_date", "exclude"))
        eligible = [(s, v) for s, v in current if not mask.reason(f"{s}@{v}#-")]
        return eligible, mask

    @staticmethod
    def _unit(con, project_id: str, uid: str) -> dict:
        sid, vid, pid = split_unit(uid)
        r = con.execute("SELECT p.start_char, p.end_char, p.quote, v.candidate_id, v.text FROM passages p JOIN "
                        "source_versions v USING (project_id, source_id, version_id) WHERE p.project_id=? AND "
                        "p.source_id=? AND p.version_id=? AND p.passage_id=?", (project_id, sid, vid, pid)).fetchone()
        if r is None:
            raise ValidationFailed(f"unit {uid} is not a stored passage", "unknown_unit")
        if r["text"][r["start_char"]:r["end_char"]] != r["quote"]:
            raise ValidationFailed(f"{uid}: stored passage does not match its source", "citation_integrity")
        return {"unit_id": uid, "source_id": sid, "version_id": vid, "passage_id": pid, "start_char": r["start_char"],
                "end_char": r["end_char"], "quote": r["quote"], "candidate_id": r["candidate_id"]}

    # ------------------------------------------------------------------ policy 2.1.0 sibling-seed anchor (D25)
    def _sibling_seeds(self, con, project_id: str, cand: str, rid: str, ctx: dict | None,
                       counters: dict) -> list[tuple[str, list[dict]]]:
        """Seed hits of every other active requirement of the candidate on the CURRENT corpus, in requirement_id
        order. A seed already searched in this run (``ctx['seed_hits']``, filled by ``EvidenceCore._acquire_and_commit``
        and by this method) is reused; any other is searched now, exactly as the obligation's own seed search would
        (same ``EvidenceCore._search`` route, query and match expression). Stored assessments, citations and earlier
        runs are never read, so the result does not depend on run order or store history."""
        reqs = sorted((r for r in self.core._project(con, project_id)["mission"]["requirements"]
                       if r["requirement_id"] != rid), key=lambda r: r["requirement_id"])
        cache = ctx.setdefault("seed_hits", {}) if ctx is not None else {}
        out = []
        for r in reqs:
            key = (cand, r["requirement_id"])
            if key not in cache:
                # a shallow copy keeps the caller's last_search / last_lexical (recorded for its own seed) untouched
                local = None if ctx is None else {**ctx}
                cache[key] = self.core._search(con, project_id, cand, r["query"], local, match=requirement_match(r))
                counters["sibling_seed_searches"] = counters.get("sibling_seed_searches", 0) + 1
            out.append((r["requirement_id"], cache[key]))
        return out

    def _sibling_seed_anchor(self, con, project_id: str, eligible, seeds) -> tuple[tuple | None, tuple]:
        """Policy 2.1.0 S1a: each other requirement votes once for the source version of its first eligible seed unit;
        most votes wins, ties by source_id then version_id; the anchors are the voting units of that source version in
        requirement_id order (at most ``SIBLING_ANCHOR_MAX``)."""
        allowed = set(eligible)
        votes: dict = {}
        for rid, hits in seeds:
            first = next((h for h in hits if (h["source_id"], h["version_id"]) in allowed), None)
            if first is not None:
                votes.setdefault((first["source_id"], first["version_id"]), []).append((rid, first))
        if not votes:
            return None, ()
        anchor = sorted(votes, key=lambda k: (-len(votes[k]), k[0], k[1]))[0]
        spans = []
        for rid, h in votes[anchor][:SIBLING_ANCHOR_MAX]:
            u = self._unit(con, project_id, unit_id(h["source_id"], h["version_id"], h["passage_id"]))
            spans.append({"source_id": anchor[0], "version_id": anchor[1], "start": u["start_char"],
                          "end": u["end_char"], "text": u["quote"][:80], "kind": "sibling_seed_unit",
                          "requirement_id": rid})
        return anchor, tuple(spans)

    # ------------------------------------------------------------------ gap detection and candidate actions
    def _detect(self, con, project_id: str, cand: str, req: dict, pool: list[dict], eligible, titles: dict,
                opts: dict, sibling_seeds=None) -> tuple[list[str], list[R.ActionCandidate]]:
        rid = req["requirement_id"]
        pool_ids = [u["unit_id"] for u in pool]
        signals: set = set()
        out: list[R.ActionCandidate] = []
        st = self.core.structure
        # ---- explicit references in the seed units
        n_refs = 0
        for rank, u in enumerate(pool):
            if st.build_state(con, project_id, u["source_id"], u["version_id"]) != "built":
                continue
            heads = {n["head_start"] for n in st.nodes(con, project_id, u["source_id"], u["version_id"])
                     if n["kind"] in ("unit", "subitem")}
            for ref in S.parse_references(u["quote"], u["start_char"], heads):
                if n_refs >= MAX_REFERENCES:
                    break
                n_refs += 1
                res = st.resolve(con, project_id, ref, u["source_id"], u["version_id"], eligible, titles)
                targets = [{**t, "unit_id": unit_id(t["source_id"], t["version_id"], t["passage_id"])}
                           for t in res["targets"] if t["passage_id"]]
                units = list(dict.fromkeys(t["unit_id"] for t in targets))
                state = res["state"]
                if state in ("resolved", "resolved_parent") and units and all(x in pool_ids for x in units):
                    state = "resolved_in_pool"
                actionable = state in ("resolved", "resolved_parent") and len(units) == 1
                if state not in ("resolved_in_pool", "self_reference"):
                    signals.add("unresolved_reference")
                note = f"; {res['note']}" if res.get("note") else ""
                out.append(R.ActionCandidate(
                    action_key=f"resolve_reference:{u['source_id']}@{u['version_id']}[{ref.start}:{ref.end}]",
                    requirement_id=rid, action="resolve_reference", signal="unresolved_reference", state=state,
                    actionable=actionable,
                    reason=f"reference '{ref.text}' in seed unit {rank + 1} is {state}{note}"
                           + (f" (instrument '{ref.instrument}')" if ref.external else ""),
                    signal_rank=rank, signal_start=ref.start,
                    target_key=targets[0]["qualified_key"] if len(targets) == 1 else (ref.key or ref.text),
                    anchors=({"source_id": u["source_id"], "version_id": u["version_id"], "start": ref.start,
                              "end": ref.end, "text": ref.text, "kind": "reference_span"},),
                    target=tuple({**t, "rule": res["rule"], "confidence": res["confidence"]} for t in targets)))
        # ---- parser-exposed bindings of the top seed unit
        if pool:
            u = pool[0]
            for b in st.bindings(con, project_id, u["source_id"], u["version_id"], u):
                n = b["node"]
                tid = unit_id(u["source_id"], u["version_id"], n["passage_id"])
                state = "resolved_in_pool" if tid in pool_ids else "bound"
                if state == "bound":
                    signals.add("unresolved_reference")
                out.append(R.ActionCandidate(
                    action_key=f"recover_context:{b['binding']}:{u['source_id']}@{u['version_id']}#{n['node_key']}",
                    requirement_id=rid, action="recover_context", signal="unresolved_reference", state=state,
                    actionable=state == "bound",
                    reason=f"the top seed unit is bound to a {b['binding'].replace('_', ' ')} in another passage "
                           f"({n['section_path'] or n['kind']}; rule {b['rule']})",
                    signal_rank=0, signal_start=b["span_start"],
                    target_key=f"{u['source_id']}@{u['version_id']}#{n['section_path'] or n['node_key']}",
                    anchors=({"source_id": u["source_id"], "version_id": u["version_id"], "start": b["span_start"],
                              "end": b["span_end"], "text": b["text"], "kind": b["binding"]},),
                    target=({"source_id": u["source_id"], "version_id": u["version_id"], "node_key": n["node_key"],
                             "section_path": n["section_path"], "passage_id": n["passage_id"], "unit_id": tid,
                             "rule": b["rule"], "confidence": S.RULES[b["rule"]]},)))
        # ---- missing evidence for the active requirement
        if not pool:
            signals.add("no_hit")
        if requirement_kind(req) == "bounded_field" and pool and all(
                P.read_field(u["quote"], req["field"]).status == "absent" for u in pool):
            signals.add("absent_bounded_field")
        if [cand, rid] in opts.get("declared_missing", []):
            signals.add("user_declared_missing")
        search_gaps = [g for g in R.GAP_SIGNALS if g in signals and g != "unresolved_reference"]
        if search_gaps and eligible:
            anchor, anchors = None, ()
            if pool:
                anchor = (pool[0]["source_id"], pool[0]["version_id"])
                anchors = ({"source_id": anchor[0], "version_id": anchor[1], "start": pool[0]["start_char"],
                            "end": pool[0]["end_char"], "text": pool[0]["quote"][:80], "kind": "first_seed_unit"},)
            elif opts.get("policy", DEFAULT_POLICY) != R.POLICY_V2.name:
                # policy 2.1.0 S1a (D25): vote by the current seed hits of the other active requirements
                anchor, anchors = self._sibling_seed_anchor(con, project_id, eligible, sibling_seeds() if sibling_seeds
                                                            else [])
            else:   # policy 2.0.0 (kept for reproduction): stored current citations of other requirements (D2)
                active = [r["requirement_id"] for r in self.core._project(con, project_id)["mission"]["requirements"]
                          if r["requirement_id"] != rid]
                cited: dict = {}
                spans: dict = {}
                for r in con.execute(
                        "SELECT c.source_id, c.version_id, c.start_char, c.end_char, c.quote, a.requirement_id FROM "
                        "assessments a JOIN citations c ON c.assessment_id=a.assessment_id WHERE a.project_id=? AND "
                        "a.candidate_id=? AND a.state='current' ORDER BY a.requirement_id",
                        (project_id, cand)).fetchall():
                    if r["requirement_id"] in active and (r["source_id"], r["version_id"]) in set(eligible):
                        k = (r["source_id"], r["version_id"])
                        cited[k] = cited.get(k, 0) + 1
                        spans.setdefault(k, []).append({"source_id": k[0], "version_id": k[1],
                                                        "start": r["start_char"], "end": r["end_char"],
                                                        "text": r["quote"][:80], "kind": "sibling_citation",
                                                        "requirement_id": r["requirement_id"]})
                if cited:
                    anchor = sorted(cited, key=lambda k: (-cited[k], k[0], k[1]))[0]
                    anchors = tuple(spans[anchor][:3])
            gap = search_gaps[0]
            if anchor is not None:
                out.append(R.ActionCandidate(
                    action_key=f"search_within_source:{anchor[0]}@{anchor[1]}", requirement_id=rid,
                    action="search_within_source", signal=gap, state="gap", actionable=True,
                    reason=f"missing evidence for an active requirement ({', '.join(search_gaps)}); search the anchor "
                           f"source {anchor[0]}@{anchor[1]}",
                    signal_rank=len(pool), target_key=f"{anchor[0]}@{anchor[1]}", anchors=anchors,
                    target=({"source_id": anchor[0], "version_id": anchor[1]},)))
            out.append(R.ActionCandidate(
                action_key=f"search_eligible_corpus:{cand}", requirement_id=rid, action="search_eligible_corpus",
                signal=gap, state="gap", actionable=True,
                reason=f"missing evidence for an active requirement ({', '.join(search_gaps)}); search the "
                       f"candidate's eligible scope ({len(eligible)} current source version(s))",
                signal_rank=len(pool), target_key=f"candidate:{cand}",
                target=tuple({"source_id": s, "version_id": v} for s, v in eligible)))
        gaps = [g for g in R.GAP_SIGNALS if g in signals]
        return gaps, out

    # ------------------------------------------------------------------ action backends
    def _scoped_search(self, con, project_id: str, cand: str, req: dict, versions, fetch: int, an, st) -> dict:
        vset = set(versions)
        current = self.core._current_versions(con, project_id)
        bounded = requirement_kind(req) == "bounded_field"
        if an is not None:
            tq = [t.norm for t in an.terms(req["query"])[0]]
            kept = list(dict.fromkeys(t for t in tq if t not in TERM_STOPWORDS)) or list(dict.fromkeys(tq))
            parts = [f'"{t}"' for t in kept]
            if bounded:
                lt = [t.norm for t in an.terms(P.FIELD_LABELS[req["field"]])[0]]
                if lt:
                    parts.insert(0, '"' + " ".join(lt) + '"')
            table, needles = PL.INDEX_NAME, kept
            index_generation = (f"{PL.INDEX_NAME}:generation-{st['generation']}:corpus-{st['corpus_revision']}:"
                                f"{an.identity_id}")
        else:
            parts = []
            try:
                parts.append(fts_terms(req["query"]))
            except ValidationFailed:
                pass
            if bounded:
                parts.insert(0, fts_phrase(P.FIELD_LABELS[req["field"]]))
            table = "passage_fts"
            needles = list(dict.fromkeys(w.lower() for w in re.findall(r"\w+", req["query"])))
            index_generation = "passage_fts:unicode61 (legacy index; Thai analyzer unavailable)"
        match = " OR ".join(parts) if parts else None
        ranked = []
        if match:
            for r in con.execute(f"SELECT source_id, version_id, passage_id, bm25({table}) AS score FROM {table} "
                                 f"WHERE {table} MATCH ? AND project_id=? AND candidate_id=? ORDER BY score, source_id, "
                                 "version_id, passage_id LIMIT 5000", (match, project_id, cand)):
                if current.get(r[0]) != r[1]:
                    raise RuntimeError(f"{table} contains a non-current version")
                if (r[0], r[1]) in vset:
                    ranked.append((unit_id(r[0], r[1], r[2]), round(-r[3], 6)))
                if len(ranked) >= fetch:
                    break
        fallback = {"triggered": False}
        if not ranked:
            folded = [TA.fold(n) for n in needles if len(n) >= SUBSTRING_MIN_CHARS]
            scanned = 0
            for r in con.execute("SELECT p.source_id, p.version_id, p.passage_id, p.quote FROM passages p JOIN "
                                 "current_sources c ON c.project_id=p.project_id AND c.source_id=p.source_id AND "
                                 "c.version_id=p.version_id WHERE p.project_id=? ORDER BY p.source_id, p.version_id, "
                                 "p.start_char", (project_id,)):
                if (r[0], r[1]) not in vset:
                    continue
                if scanned >= PL.FALLBACK_SCAN_MAX or len(ranked) >= fetch:
                    break
                scanned += 1
                q = TA.fold(r[3])
                if any(n in q for n in folded):
                    ranked.append((unit_id(r[0], r[1], r[2]), None))
            fallback = {"triggered": True, "reason": "no index match in the scope", "needles": folded,
                        "scanned": scanned, "scan_cap": PL.FALLBACK_SCAN_MAX, "returned": len(ranked)}
        return {"ranked": ranked, "query": match, "index_generation": index_generation,
                "route": f"{table} scoped to {len(vset)} source version(s) + bounded substring fallback",
                "fallback": fallback, "searched_versions": sorted(f"{s}@{v}" for s, v in vset)}

    def _execute(self, con, project_id: str, cand: str, req: dict, c: R.ActionCandidate, fetch: int, eligible,
                 an, st) -> dict:
        if c.action in ("resolve_reference", "recover_context"):
            t = c.target[0]
            anchor = c.anchors[0]["text"] if c.anchors else ""
            return {"ranked": [(t["unit_id"], None)],
                    "query": f"structural lookup: '{anchor}' -> {c.target_key}",
                    "scope": {"project_id": project_id, "candidate_id": cand, "source_id": t["source_id"],
                              "version_id": t["version_id"]},
                    "index_generation": f"{S.RULESET}:{t['source_id']}@{t['version_id']}",
                    "route": f"persisted structure lookup (rule {t.get('rule')})",
                    "searched_versions": [f"{t['source_id']}@{t['version_id']}"]}
        if c.action == "search_within_source":
            t = c.target[0]
            versions = [(t["source_id"], t["version_id"])]
            scope = {"project_id": project_id, "candidate_id": cand, "source_id": t["source_id"],
                     "version_id": t["version_id"]}
        else:
            versions = list(eligible)
            scope = {"project_id": project_id, "candidate_id": cand,
                     "source_versions": [f"{s}@{v}" for s, v in versions]}
        out = self._scoped_search(con, project_id, cand, req, versions, fetch, an, st)
        out["scope"] = scope
        return out

    def _terms_of(self, an):
        def terms(text: str) -> set:
            if an is not None:
                return {t.norm for t in an.terms(text)[0]}
            return {w.lower() for w in re.findall(r"\w+", text)}
        return terms

    def _rerank(self, con, project_id: str, an):
        terms = self._terms_of(an)

        def rerank(request: R.RerankRequest, ids: tuple) -> dict:
            want = set()
            for t in request.requirement_texts:
                want |= terms(t)
            want -= TERM_STOPWORDS
            return {u: float(len(want & terms(self._unit(con, project_id, u)["quote"]))) for u in ids}
        return rerank

    # ------------------------------------------------------------------ one obligation
    def acquire(self, project_id: str, run_id: str, seq: int, cand: str, req: dict, seed_hits: list[dict],
                opts: dict, counters: dict, ctx: dict | None = None) -> dict:
        """``ctx`` is the run's retrieval context; policy 2.1.0 keeps the run's seed hits in ``ctx['seed_hits']``."""
        rid = req["requirement_id"]
        policy = R.POLICIES[opts.get("policy", DEFAULT_POLICY)]
        with self.store.read() as con:
            current = self.core._scope(con, project_id, cand)
        self.core.structure.ensure(project_id, current)       # stores created before P4-T03: build once, then reuse
        try:
            st, an = self.core.product_lexical.ensure(project_id)
        except TA.AnalyzerUnavailable:
            st, an = None, None
        with self.store.read() as con:
            eligible, mask = self._scope(con, project_id, cand, opts)
            titles = {(r[0], r[1]): r[2] for r in con.execute(
                "SELECT source_id, version_id, title FROM source_versions WHERE project_id=?", (project_id,))}
            seed_ids = list(dict.fromkeys(unit_id(h["source_id"], h["version_id"], h["passage_id"]) for h in seed_hits))
            pool_excluded = [{"unit_id": u, "reason": mask.reason(u)} for u in seed_ids if mask.reason(u)]
            pool_ids = [u for u in seed_ids if not mask.reason(u)]
            pool = [self._unit(con, project_id, u) for u in pool_ids]
            gaps, candidates = self._detect(
                con, project_id, cand, req, pool, eligible, titles, opts,
                sibling_seeds=lambda: self._sibling_seeds(con, project_id, cand, rid, ctx, counters))
            q = req["query"]
            qr = R.QueryRequirements(f"{project_id}:{cand}:{rid}", q, (R.Requirement(rid, 0, len(q), q),))
            if opts["mode"] == "baseline":
                receipt = {"record_schema": R.RECEIPT_SCHEMA, "claim_boundary": R.V2_CLAIM_BOUNDARY,
                           "requirement_id": rid, "requirement_version": qr.sha256(), "requirements": qr.as_record(),
                           "policy_version": policy.name, "policy_sha256": policy.fingerprint(),
                           "gaps": gaps, "selection": {"selected_action_key": None, "considered": [], "skipped": [],
                                                       "candidates": [c.as_record() for c in candidates]},
                           "action": None, "action_key": None, "reason": None, "anchors": [], "scope": None,
                           "query": None, "index_generation": None, "search_calls": 0, "pool_before": pool_ids,
                           "new_unit_ids": [], "new_document_ids": [], "same_document_unit_ids": [],
                           "final_ids": pool_ids, "rerank": None, "outcome": "baseline_no_action",
                           "eligibility": {**mask.describe(), "sha256": mask.fingerprint(), "trace_id": mask.trace_id}}
            else:
                allowed = counters.get("structural_actions", 0) < opts["max_structural_actions"]
                receipt = R.structural_action_step(
                    requirements=qr, candidates=candidates, pool_before=pool_ids,
                    execute=lambda c, fetch: self._execute(con, project_id, cand, req, c, fetch, eligible, an, st),
                    rerank=self._rerank(con, project_id, an), budget=R.ActionBudget(1 if allowed else 0),
                    eligibility=mask, unit_document=lambda u: split_unit(u)[0], gaps=gaps, policy=policy,
                    result_limit=ACTION_RESULT_LIMIT, fetch_limit=ACTION_FETCH_LIMIT)
                if not allowed:
                    receipt["budget_note"] = f"run cap of {opts['max_structural_actions']} structural actions reached"
            scores = {r["unit_id"]: r["score"] for r in (receipt.get("rerank") or {}).get("ranking", [])}
            new = [u for u in receipt["final_ids"] if u in set(receipt["new_unit_ids"])]
            units = {u: self._unit(con, project_id, u) for u in new}
            lifecycle_rev = self.core.requirement_revision(con, project_id, rid)
        if any(units[u]["candidate_id"] != cand for u in new):     # defence in depth: the mask already excludes them
            raise ValidationFailed("an acquired unit belongs to another candidate", "acquisition_scope")
        receipt.update(
            project_id=project_id, candidate_id=cand, run_id=run_id, seq=seq, mode=opts["mode"],
            requirement_sha256=self.core.requirement_sha256(req), requirement_lifecycle_revision=lifecycle_rev,
            structure_ruleset=S.RULESET, analyzer=an.identity_id if an is not None else None,
            pool_excluded_ineligible=pool_excluded, eligible_scope=[f"{s}@{v}" for s, v in eligible],
            scope_dependencies=sorted(set(self._searched(receipt))) if receipt["search_calls"] else [],
            gain={"new_units": len(new), "same_document_context_units": len(receipt["same_document_unit_ids"]),
                  "new_document_units": len(new) - len(receipt["same_document_unit_ids"]),
                  "new_documents": len(receipt["new_document_ids"]), "family": "not defined for owner documents",
                  "relevance": "not judged (newly acquired does not mean relevant)"})
        if receipt["search_calls"]:
            counters["structural_actions"] = counters.get("structural_actions", 0) + 1
        counters["structural_new_units"] = counters.get("structural_new_units", 0) + len(new)
        counters["same_document_context_units"] = (counters.get("same_document_context_units", 0)
                                                   + len(receipt["same_document_unit_ids"]))
        counters["new_document_units"] = (counters.get("new_document_units", 0)
                                          + len(new) - len(receipt["same_document_unit_ids"]))
        if gaps:
            counters["gap_obligations"] = counters.get("gap_obligations", 0) + 1
        free_text = requirement_kind(req) == "text"
        read_units = []
        for u in new:
            if free_text and (seed_hits or not scores.get(u)):
                continue     # R3: a free-text requirement cites a new unit only when the seed found nothing
            gain = "same_document" if u in receipt["same_document_unit_ids"] else "new_document"
            read_units.append({"source_id": units[u]["source_id"], "version_id": units[u]["version_id"],
                               "passage_id": units[u]["passage_id"], "score": scores.get(u),
                               "acquired": {"action": receipt["action"], "receipt": f"{run_id}:{seq}",
                                            "rerank_score": scores.get(u), "gain": gain}})
        deps = [("acquisition_scope", s, v, receipt.get("query")) for s, v in
                (x.split("@", 1) for x in receipt["scope_dependencies"])]
        return {"receipt": receipt, "read_units": read_units, "deps": deps, "new_units": new}

    split_unit = staticmethod(split_unit)

    @staticmethod
    def _searched(receipt: dict) -> list[str]:
        scope = receipt.get("scope") or {}
        if "source_versions" in scope:
            return list(scope["source_versions"])
        if scope.get("source_id"):
            return [f"{scope['source_id']}@{scope['version_id']}"]
        return []

    @staticmethod
    def explain(acq: dict, evidence: dict | None) -> str:
        r = acq["receipt"]
        if r["outcome"] != "acquired":
            return ""
        ev = unit_id(evidence["source_id"], evidence["version_id"], evidence["passage_id"]) if evidence else None
        if ev in r["new_unit_ids"]:
            return (f"This passage was acquired after the seed search by one structural action ({r['action']}, policy "
                    f"{r['policy_version']}): {r['reason']}.")
        return (f"One structural action ({r['action']}) also acquired {len(r['new_unit_ids'])} related unit(s) as "
                f"context ({', '.join(r['new_unit_ids'])}); they are not judged.")

    # ------------------------------------------------------------------ persistence
    def record(self, project_id: str, run_id: str, seq: int, cand: str, req: dict, receipt: dict) -> str:
        js = dumps(receipt)
        digest = sha256(js.encode("utf-8"))
        with self.store.tx() as con:
            con.execute("INSERT INTO acquisition_receipts VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                        (project_id, run_id, seq, cand, req["requirement_id"], receipt["requirement_sha256"],
                         receipt["requirement_lifecycle_revision"], receipt["mode"], receipt["policy_version"],
                         receipt["policy_sha256"], receipt["action"], receipt["outcome"], js, digest, None, "pending",
                         utc_now(), None))
        return digest

    def link(self, run_id: str, seq: int, result: dict) -> None:
        with self.store.tx() as con:
            con.execute("UPDATE acquisition_receipts SET assessment_id=?, commit_status=?, committed_at=? WHERE "
                        "run_id=? AND seq=?", (result.get("assessment_id"), result["committed"], utc_now(), run_id, seq))

    # ------------------------------------------------------------------ read models (the UI reads these)
    def receipts(self, project_id: str, candidate_id: str | None = None, requirement_id: str | None = None,
                 run_id: str | None = None) -> list[dict]:
        sql, args = "SELECT * FROM acquisition_receipts WHERE project_id=?", [project_id]
        for col, val in (("candidate_id", candidate_id), ("requirement_id", requirement_id), ("run_id", run_id)):
            if val is not None:
                sql += f" AND {col}=?"
                args.append(val)
        with self.store.read() as con:
            rows = [dict(r) for r in con.execute(sql + " ORDER BY created_at DESC, run_id DESC, seq DESC", args)]
        for r in rows:
            js = r.pop("receipt_json")
            r["integrity"] = "verified" if sha256(js.encode("utf-8")) == r["receipt_sha256"] else "MISMATCH"
            r["receipt"] = json.loads(js)
        return rows

    def trace_for(self, project_id: str, requirement_id: str, cells: list[dict]) -> list[dict]:
        """Per candidate: the persisted receipt of the assessment currently shown (else the latest receipt)."""
        out = []
        with self.store.read() as con:
            for c in cells:
                cell = c["cell"]
                rows = self.receipts(project_id, c["candidate_id"], requirement_id)
                pick = next((r for r in rows if cell and r["assessment_id"] == cell["assessment_id"]), None)
                matches = pick is not None
                pick = pick or (rows[0] if rows else None)
                if pick is None:
                    out.append({"candidate_id": c["candidate_id"], "state": "no_receipt",
                                "summary": "No acquisition receipt is recorded for this cell (assessed before P4-T03, "
                                           "or not assessed yet)."})
                    continue
                rec = pick["receipt"]
                cards = []
                for u in rec["new_unit_ids"]:
                    try:
                        p = self._unit(con, project_id, u)
                    except ValidationFailed:
                        continue
                    p.pop("candidate_id", None)
                    cards.append({**p, "gain": "same_document" if u in rec["same_document_unit_ids"]
                                  else "new_document"})
                out.append({"candidate_id": c["candidate_id"], "state": "recorded", "run_id": pick["run_id"],
                            "seq": pick["seq"], "mode": pick["mode"], "outcome": pick["outcome"],
                            "commit_status": pick["commit_status"], "assessment_id": pick["assessment_id"],
                            "matches_current_assessment": matches, "receipt_sha256": pick["receipt_sha256"],
                            "integrity": pick["integrity"], "summary": self.summary(rec), "receipt": rec,
                            "new_units": cards})
        return out

    @staticmethod
    def summary(rec: dict) -> str:
        if rec["outcome"] == "acquired":
            g = rec["gain"]
            return (f"One {rec['action'].replace('_', ' ')} acquired {g['new_units']} unit(s): "
                    f"{g['same_document_context_units']} from documents already in the pool (context), "
                    f"{g['new_document_units']} from {g['new_documents']} new document(s). Not judged.")
        return SUMMARIES.get(rec["outcome"], rec["outcome"])

    def run_usage(self, run_id: str) -> dict:
        """Provider dispatch measured directly: rows of ``provider_usage`` (every request any provider client made,
        ok, failed or blocked) recorded inside this run's time window."""
        with self.store.read() as con:
            r = con.execute("SELECT started_at, finished_at FROM runs WHERE run_id=?", (run_id,)).fetchone()
            if r is None or r["finished_at"] is None:
                return {"state": "unknown", "reason": "run not finished"}
            rows = con.execute("SELECT billable, status, usage_json FROM provider_usage WHERE at >= ? AND at <= ?",
                               (r["started_at"], r["finished_at"])).fetchall()
        cost = 0.0
        for x in rows:
            u = json.loads(x["usage_json"]) if x["usage_json"] else {}
            if isinstance(u.get("cost_usd"), (int, float)):
                cost += float(u["cost_usd"])
        return {"state": "measured", "provider_requests": len(rows),
                "billable_requests": sum(1 for x in rows if x["billable"]),
                "sent_requests": sum(1 for x in rows if x["status"] not in ("blocked", "missing_credential")),
                "reported_cost_usd": round(cost, 8),
                "basis": "provider_usage rows recorded between the run's start and finish (all profiles)"}
