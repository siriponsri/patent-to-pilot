"""Shared evidence core for PTP-2026-11-21/G01.

One service (``EvidenceCore``) is used by the CLI (``scripts/ptp_run.py``) and the HTTP app
(``patent_to_pilot.workbench.server``). It owns PLAN -> ACQUIRE -> COMMIT over a bounded obligation queue
(one obligation per candidate x requirement), the versioned source ledger, the current-scope FTS5 index and
the source-revision transaction.

Runtime inputs are the sample's ``source_manifest.json``, ``requirements.json`` and the source files listed
there. Test-only expectations are never read here.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import time
import uuid

from patent_to_pilot.workbench import parser as P
from patent_to_pilot.workbench.store import Store, dumps, utc_now

PROGRAM_ID, GOAL_ID = "PTP-2026-11-21", "G01"
CORE_IDENTITY = "patent_to_pilot.workbench.core.EvidenceCore/v1"
SAMPLE_DIR = Path(__file__).resolve().parent / "sample"
SAMPLE_PROJECT_ID = "sample-thermal-module-demo-01"
EXECUTION_MODE = "live_local"
SEARCH_TOP_K = 3
OUTCOME_LABELS = {"meets": "Meets", "does_not_meet": "Does not meet", "unknown": "Unknown",
                  "needs_review": "Needs review"}
OFFSET_CONVENTION = "unicode_code_points_zero_based_end_exclusive_on_unmodified_decoded_utf8"


class CoreError(Exception):
    status = 400
    code = "bad_request"

    def __init__(self, message: str, code: str | None = None) -> None:
        super().__init__(message)
        if code:
            self.code = code


class NotFound(CoreError):
    status = 404
    code = "not_found"


class ValidationFailed(CoreError):
    status = 422
    code = "validation_failed"


class Conflict(CoreError):
    status = 409
    code = "conflict"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def core_code_sha256() -> str:
    here = Path(__file__).resolve().parent
    h = hashlib.sha256()
    for name in ("core.py", "parser.py", "store.py"):
        h.update((here / name).read_bytes())
    return h.hexdigest()


# --------------------------------------------------------------------------- source parsing
_FRONT = re.compile(r"\A---\r?\n(?P<body>.*?)\r?\n---\r?\n", re.S)
_HEADING = re.compile(r"^## (?P<pid>[A-Za-z0-9][A-Za-z0-9_-]*)[ \t]*\r?$", re.M)
_TITLE = re.compile(r"^# (?P<title>.+?)\r?$", re.M)
_BLANK = re.compile(r"\r?\n[ \t]*\r?\n")


def front_matter(text: str) -> dict:
    m = _FRONT.match(text)
    if not m:
        return {}
    out = {}
    for line in m.group("body").splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            out[k.strip()] = v.strip()
    return out


def extract_passages(text: str) -> list[dict]:
    """Passage = text immediately after the '## <ID>' heading's newline up to (excluding) the line break
    that precedes the next blank line, or to the end of the file (a final line break is excluded).
    Offsets are code points in the unmodified decoded text."""
    out, seen = [], set()
    for m in _HEADING.finditer(text):
        pid = m.group("pid")
        if pid in seen:
            raise ValidationFailed(f"duplicate passage heading {pid}", "duplicate_passage")
        seen.add(pid)
        nl = text.find("\n", m.end())
        start = len(text) if nl < 0 else nl + 1
        b = _BLANK.search(text, start)
        end = b.start() if b else len(text.rstrip("\r\n"))
        nxt = _HEADING.search(text, start)
        if nxt and nxt.start() < end:  # a heading without a preceding blank line also ends the passage
            end = nxt.start()
            while end > start and text[end - 1] in "\r\n":
                end -= 1
        end = max(end, start)
        out.append({"passage_id": pid, "start_char": start, "end_char": end, "quote": text[start:end]})
    return out


def fts_phrase(query: str) -> str:
    tokens = re.findall(r"\w+", query, flags=re.UNICODE)
    if not tokens:
        raise ValidationFailed("empty lexical query")
    return '"' + " ".join(tokens) + '"'


# --------------------------------------------------------------------------- the core service
class EvidenceCore:
    def __init__(self, data_dir: str | Path, sample_dir: str | Path = SAMPLE_DIR) -> None:
        self.store = Store(data_dir)
        self.sample_dir = Path(sample_dir)

    # ---------------- capabilities / identity
    def capabilities(self) -> dict:
        return {
            "program_id": PROGRAM_ID, "goal_id": GOAL_ID, "core_identity": CORE_IDENTITY,
            "core_code_sha256": core_code_sha256(),
            "lexical": {"state": "active", "implementation": "sqlite_fts5_unicode61",
                        "description": "Searches the local indexed text. No model required."},
            "local_model": {"state": "disabled", "description": "Not enabled for this goal. Lexical mode remains available."},
            "api_model": {"state": "disabled", "description": "No paid API calls are enabled in this goal."},
            "remote_calls_allowed": False, "model_downloads_allowed": False,
            "parser_profile": P.PARSER_PROFILE, "offset_convention": OFFSET_CONVENTION,
            "store_path": str(self.store.path),
        }

    # ---------------- bootstrap / import
    def _load_sample_inputs(self) -> tuple[dict, dict]:
        manifest = json.loads((self.sample_dir / "source_manifest.json").read_text(encoding="utf-8"))
        mission = json.loads((self.sample_dir / "requirements.json").read_text(encoding="utf-8"))
        if mission.get("allow_remote_models") or mission.get("allow_model_downloads"):
            raise ValidationFailed("G01 mission must not allow remote models or downloads")
        return manifest, mission

    def _read_source_file(self, entry: dict, expect_version: str) -> tuple[bytes, str, dict]:
        rel = Path(entry["path"])
        if rel.is_absolute() or ".." in rel.parts or rel.parts[0] not in ("sources", "incoming"):
            raise ValidationFailed(f"unsupported source path {entry['path']}", "unsupported_path")
        raw = (self.sample_dir / rel).read_bytes()
        if sha256(raw) != entry["sha256"]:
            raise ValidationFailed(f"{entry['source_id']}@{expect_version}: content hash does not match the manifest",
                                   "hash_mismatch")
        text = raw.decode("utf-8", errors="strict")
        fm = front_matter(text)
        if fm.get("source_id") != entry["source_id"] or fm.get("version_id") != expect_version:
            raise ValidationFailed(f"{entry['path']}: front matter identity does not match the manifest",
                                   "identity_mismatch")
        return raw, text, fm

    def _insert_version(self, con, project_id: str, entry: dict, version_id: str, raw: bytes, text: str,
                        event: str, supersedes: str | None) -> list[dict]:
        title_m = _TITLE.search(text)
        passages = extract_passages(text)
        if not passages:
            raise ValidationFailed(f"{entry['source_id']}@{version_id} has no passages", "no_passages")
        now = utc_now()
        con.execute("INSERT INTO source_versions VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (project_id, entry["source_id"], version_id, entry["candidate_id"],
                     title_m.group("title") if title_m else entry["source_id"], entry["source_kind"],
                     entry["license"], supersedes, sha256(raw), raw, text, entry["path"], now, event))
        for p in passages:
            con.execute("INSERT INTO passages VALUES (?,?,?,?,?,?,?)",
                        (project_id, entry["source_id"], version_id, p["passage_id"], p["start_char"],
                         p["end_char"], p["quote"]))
        return passages

    def _make_current(self, con, project_id: str, source_id: str, version_id: str, candidate_id: str,
                      passages: list[dict]) -> None:
        con.execute("DELETE FROM passage_fts WHERE project_id=? AND source_id=?", (project_id, source_id))
        for p in passages:
            con.execute("INSERT INTO passage_fts VALUES (?,?,?,?,?,?)",
                        (project_id, source_id, version_id, p["passage_id"], candidate_id, p["quote"]))
        con.execute("INSERT OR REPLACE INTO current_sources VALUES (?,?,?,?)",
                    (project_id, source_id, version_id, utc_now()))

    def bootstrap_sample(self) -> dict:
        """Create the isolated sample project, or reopen it if it already exists (never resets)."""
        with self.store.read() as con:
            if con.execute("SELECT 1 FROM projects WHERE project_id=?", (SAMPLE_PROJECT_ID,)).fetchone():
                return {"project_id": SAMPLE_PROJECT_ID, "reopened": True}
        manifest, mission = self._load_sample_inputs()
        files = [(e, *self._read_source_file(e, e["version_id"])) for e in manifest["initial_sources"]]
        with self.store.tx() as con:
            if con.execute("SELECT 1 FROM projects WHERE project_id=?", (SAMPLE_PROJECT_ID,)).fetchone():
                return {"project_id": SAMPLE_PROJECT_ID, "reopened": True}
            con.execute("INSERT INTO projects VALUES (?,?,?,?,?,?,?,?,?)",
                        (SAMPLE_PROJECT_ID, PROGRAM_ID, GOAL_ID, manifest["scenario_id"],
                         "Thermal module comparison (sample)", manifest["data_origin"], dumps(mission),
                         dumps(manifest), utc_now()))
            for entry, raw, text, _fm in files:
                passages = self._insert_version(con, SAMPLE_PROJECT_ID, entry, entry["version_id"], raw, text,
                                                "initial_import", None)
                self._make_current(con, SAMPLE_PROJECT_ID, entry["source_id"], entry["version_id"],
                                   entry["candidate_id"], passages)
            for c in mission["candidates"]:
                for r in mission["requirements"]:
                    con.execute("INSERT INTO obligations VALUES (?,?,?,?,?,?)",
                                (SAMPLE_PROJECT_ID, c["candidate_id"], r["requirement_id"], "open",
                                 "initial obligation", utc_now()))
        return {"project_id": SAMPLE_PROJECT_ID, "reopened": False}

    # ---------------- helpers
    def _project(self, con, project_id: str) -> dict:
        row = con.execute("SELECT * FROM projects WHERE project_id=?", (project_id,)).fetchone()
        if not row:
            raise NotFound(f"project {project_id} not found", "project_not_found")
        d = dict(row)
        d["mission"] = json.loads(d.pop("mission_json"))
        d["manifest"] = json.loads(d.pop("manifest_json"))
        return d

    def _config(self, mission: dict) -> tuple[dict, str]:
        cfg = {"requirements": mission["requirements"], "candidates": mission["candidates"],
               "parser_profile": mission["parser_profile"], "limits": mission["limits"],
               "provider_profile": mission["provider_profile"], "search_top_k": SEARCH_TOP_K,
               "core_identity": CORE_IDENTITY}
        return cfg, sha256(dumps(cfg).encode("utf-8"))

    def _current_versions(self, con, project_id: str) -> dict:
        return {r["source_id"]: r["version_id"] for r in
                con.execute("SELECT source_id, version_id FROM current_sources WHERE project_id=?", (project_id,))}

    def _search(self, con, project_id: str, candidate_id: str, query: str) -> list[dict]:
        current = self._current_versions(con, project_id)
        rows = con.execute(
            "SELECT source_id, version_id, passage_id, bm25(passage_fts) AS score FROM passage_fts "
            "WHERE passage_fts MATCH ? AND project_id=? AND candidate_id=? "
            "ORDER BY score, source_id, version_id, passage_id LIMIT ?",
            (fts_phrase(query), project_id, candidate_id, SEARCH_TOP_K)).fetchall()
        hits = []
        for r in rows:
            if current.get(r["source_id"]) != r["version_id"]:
                raise RuntimeError("current lexical index contains a non-current version")
            hits.append({"source_id": r["source_id"], "version_id": r["version_id"],
                         "passage_id": r["passage_id"], "score": round(r["score"], 6)})
        return hits

    def _scope(self, con, project_id: str, candidate_id: str) -> list[tuple[str, str]]:
        return [(r["source_id"], r["version_id"]) for r in con.execute(
            "SELECT c.source_id, c.version_id FROM current_sources c JOIN source_versions v "
            "ON v.project_id=c.project_id AND v.source_id=c.source_id AND v.version_id=c.version_id "
            "WHERE c.project_id=? AND v.candidate_id=? ORDER BY c.source_id", (project_id, candidate_id))]

    def _validate_citation(self, con, project_id: str, cit: dict, require_current: bool) -> None:
        v = con.execute("SELECT raw, text, sha256 FROM source_versions WHERE project_id=? AND source_id=? "
                        "AND version_id=?", (project_id, cit["source_id"], cit["version_id"])).fetchone()
        if not v:
            raise ValidationFailed("citation source version is not in this project", "citation_scope")
        if sha256(v["raw"]) != v["sha256"] or v["raw"].decode("utf-8") != v["text"] or v["sha256"] != cit["sha256"]:
            raise ValidationFailed("citation content hash does not match the stored source", "citation_hash")
        if not (0 <= cit["start_char"] <= cit["end_char"] <= len(v["text"])):
            raise ValidationFailed("citation offsets are outside the source", "citation_bounds")
        if v["text"][cit["start_char"]:cit["end_char"]] != cit["quote"]:
            raise ValidationFailed("citation quote is not the literal source text", "citation_quote")
        if require_current and self._current_versions(con, project_id).get(cit["source_id"]) != cit["version_id"]:
            raise ValidationFailed("citation version is not current", "citation_not_current")

    # ---------------- run engine (PLAN -> ACQUIRE -> COMMIT)
    def _new_run(self, project_id: str, kind: str, invoked_via: str, strategy: str, mission: dict,
                 change_event_id: str | None = None) -> str:
        cfg, cfg_sha = self._config(mission)
        run_id = "run-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S") + "-" + uuid.uuid4().hex[:8]
        with self.store.tx() as con:
            con.execute("INSERT INTO runs VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                        (run_id, project_id, kind, invoked_via, CORE_IDENTITY, EXECUTION_MODE,
                         "synthetic_fixture", strategy, cfg_sha, dumps(mission["limits"]), dumps({}), "running",
                         None, change_event_id, utc_now(), None))
        return run_id

    def _action(self, run_id: str, seq: int, action_type: str, cand: str | None, req: str | None,
                detail: dict, status: str = "ok", started: str | None = None) -> None:
        with self.store.tx() as con:
            con.execute("INSERT INTO actions VALUES (?,?,?,?,?,?,?,?,?)",
                        (run_id, seq, action_type, cand, req, status, started or utc_now(), utc_now(), dumps(detail)))

    def _finish_run(self, run_id: str, status: str, stop_reason: str, counters: dict) -> None:
        with self.store.tx() as con:
            con.execute("UPDATE runs SET status=?, stop_reason=?, counters_json=?, finished_at=? WHERE run_id=?",
                        (status, stop_reason, dumps(counters), utc_now(), run_id))

    def _acquire_and_commit(self, project_id: str, run_id: str, mission: dict, cand: str, req: dict,
                            seq: int, counters: dict, limits: dict, deadline: float) -> tuple[int, str | None]:
        """One obligation. Returns (next seq, stop reason or None)."""
        if counters["acquisition_actions"] >= limits["max_acquisition_actions"]:
            return seq, "budget_exhausted:max_acquisition_actions"
        if time.monotonic() > deadline:
            return seq, "deadline:max_wall_seconds"
        rid = req["requirement_id"]
        t0 = utc_now()
        with self.store.read() as con:
            hits = self._search(con, project_id, cand, req["query"])
            scope = self._scope(con, project_id, cand)
        counters["acquisition_actions"] += 1
        self._action(run_id, seq, "search_current_sources", cand, rid,
                     {"query": req["query"], "fts_match": fts_phrase(req["query"]), "candidate_scope": cand,
                      "scope_versions": [f"{s}@{v}" for s, v in scope], "hits": hits}, started=t0)
        seq += 1
        evidence, reading, issues = None, None, []
        for h in hits:
            if counters["source_reads"] >= limits["max_source_reads"]:
                return seq, "budget_exhausted:max_source_reads"
            t0 = utc_now()
            with self.store.read() as con:
                p = con.execute("SELECT p.*, v.sha256 FROM passages p JOIN source_versions v USING "
                                "(project_id, source_id, version_id) WHERE p.project_id=? AND p.source_id=? AND "
                                "p.version_id=? AND p.passage_id=?",
                                (project_id, h["source_id"], h["version_id"], h["passage_id"])).fetchone()
            counters["source_reads"] += 1
            r = P.read_field(p["quote"], req["field"])
            self._action(run_id, seq, "read_passage", cand, rid,
                         {"passage": f"{h['source_id']}@{h['version_id']}#{h['passage_id']}",
                          "field": req["field"], "field_status": r.status, "line": r.line, "issues": r.issues},
                         started=t0)
            seq += 1
            if r.status == "invalid":
                issues.append({"passage": f"{h['source_id']}@{h['version_id']}#{h['passage_id']}",
                               "issues": r.issues})
                continue
            if r.status == "parsed":
                evidence, reading = dict(p), r
                break
        t0 = utc_now()
        if reading is not None:
            outcome, explanation = P.evaluate(req["predicate"], reading)
        else:
            outcome = "unknown"
            label = P.FIELD_LABELS[req["field"]]
            cand_label = next(c["label"] for c in mission["candidates"] if c["candidate_id"] == cand)
            if issues:
                explanation = (f"A '{label}' statement was found but could not be validated: "
                               + "; ".join(i for x in issues for i in x["issues"]) + ".")
            else:
                explanation = f"No recognized '{label}' statement found in {cand_label}'s current sources."
        self._action(run_id, seq, "check_criterion", cand, rid,
                     {"predicate": req["predicate"], "reading": None if reading is None else reading.value,
                      "outcome": outcome, "explanation": explanation, "validation_issues": issues}, started=t0)
        seq += 1
        citation = None
        if evidence is not None:
            citation = {"source_id": evidence["source_id"], "version_id": evidence["version_id"],
                        "passage_id": evidence["passage_id"], "start_char": evidence["start_char"],
                        "end_char": evidence["end_char"], "quote": evidence["quote"], "sha256": evidence["sha256"]}
        t0 = utc_now()
        result = self._commit(project_id, run_id, mission, cand, req, outcome, explanation, reading, issues,
                              hits, scope, citation)
        self._action(run_id, seq, "commit_assessment", cand, rid, result, started=t0)
        seq += 1
        counters["committed" if result["committed"] == "new_version" else "retained"] += 1
        return seq, None

    def _commit(self, project_id, run_id, mission, cand, req, outcome, explanation, reading, issues, hits, scope,
                citation) -> dict:
        rid = req["requirement_id"]
        req_sha = sha256(dumps(req).encode("utf-8"))
        with self.store.tx() as con:
            if citation is not None:
                self._validate_citation(con, project_id, citation, require_current=True)
            prev = con.execute("SELECT * FROM assessments WHERE project_id=? AND candidate_id=? AND requirement_id=? "
                               "AND state='current'", (project_id, cand, rid)).fetchone()
            prev_cit = None
            if prev:
                c = con.execute("SELECT source_id, version_id, passage_id FROM citations WHERE assessment_id=?",
                                (prev["assessment_id"],)).fetchone()
                prev_cit = dict(c) if c else None
            new_cit = None if citation is None else {k: citation[k] for k in ("source_id", "version_id", "passage_id")}
            pending = con.execute("SELECT state FROM obligations WHERE project_id=? AND candidate_id=? AND "
                                  "requirement_id=?", (project_id, cand, rid)).fetchone()["state"]
            same = (prev is not None and prev["outcome"] == outcome and prev["explanation"] == explanation
                    and prev_cit == new_cit and prev["requirement_sha256"] == req_sha and pending != "needs_review")
            if same:
                con.execute("UPDATE obligations SET state='done', reason=?, updated_at=? WHERE project_id=? AND "
                            "candidate_id=? AND requirement_id=?",
                            (f"re-acquired in {run_id}; identical result retained", utc_now(), project_id, cand, rid))
                return {"committed": "retained_identical", "assessment_id": prev["assessment_id"],
                        "outcome": outcome, "citation": new_cit}
            aid = "asm-" + uuid.uuid4().hex[:12]
            now = utc_now()
            if prev:
                con.execute("UPDATE assessments SET state='superseded' WHERE assessment_id=?", (prev["assessment_id"],))
                con.execute("INSERT INTO assessment_events VALUES (?,?,?,?,?)",
                            (prev["assessment_id"], "superseded", f"superseded by {aid}", run_id, now))
            con.execute("INSERT INTO assessments VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                        (aid, project_id, cand, rid, req_sha, outcome, explanation,
                         dumps(None if reading is None else {"field": reading.field, "value": reading.value,
                                                             "line": reading.line}),
                         dumps(issues), dumps(hits), run_id, prev["assessment_id"] if prev else None, "current", now))
            con.execute("INSERT INTO assessment_events VALUES (?,?,?,?,?)", (aid, "committed", outcome, run_id, now))
            if citation is not None:
                con.execute("INSERT INTO citations VALUES (?,?,?,?,?,?,?,?)",
                            (aid, citation["source_id"], citation["version_id"], citation["passage_id"],
                             citation["start_char"], citation["end_char"], citation["quote"], citation["sha256"]))
                con.execute("INSERT INTO dependencies VALUES (?,?,?,?,?,?)",
                            (aid, "citation", citation["source_id"], citation["version_id"], cand, None))
            for s, v in scope:
                con.execute("INSERT INTO dependencies VALUES (?,?,?,?,?,?)", (aid, "search_scope", s, v, cand, req["query"]))
            con.execute("UPDATE obligations SET state='done', reason=?, updated_at=? WHERE project_id=? AND "
                        "candidate_id=? AND requirement_id=?", (f"committed {aid}", now, project_id, cand, rid))
        return {"committed": "new_version", "assessment_id": aid, "supersedes": prev["assessment_id"] if prev else None,
                "outcome": outcome, "citation": new_cit}

    def run_comparison(self, project_id: str, invoked_via: str = "cli") -> dict:
        """Full comparison: every candidate x requirement obligation is planned and acquired."""
        with self.store.read() as con:
            mission = self._project(con, project_id)["mission"]
        run_id = self._new_run(project_id, "comparison", invoked_via, "full", mission)
        return self._execute(project_id, run_id, mission,
                             [(c["candidate_id"], r) for c in mission["candidates"] for r in mission["requirements"]],
                             reuse=[])

    def _execute(self, project_id: str, run_id: str, mission: dict, work: list, reuse: list) -> dict:
        limits = mission["limits"]
        deadline = time.monotonic() + limits["max_wall_seconds"]
        counters = {"obligations_planned": 0, "acquisition_actions": 0, "source_reads": 0, "committed": 0,
                    "retained": 0, "reused_after_verification": 0, "paid_model_calls": 0, "remote_calls": 0}
        seq, stop = 1, None
        try:
            for item in reuse:  # verification search (really executed) followed by the reuse decision
                self._action(run_id, seq, "search_current_sources", item["candidate_id"], item["requirement_id"],
                             {"query": item["query"], "fts_match": fts_phrase(item["query"]),
                              "purpose": "revalidate search-scope dependency after the source change",
                              "hits": item["hits"]}, started=item["searched_at"])
                seq += 1
                counters["acquisition_actions"] += 1
                self._action(run_id, seq, "reuse_valid_result", item["candidate_id"], item["requirement_id"],
                             {k: item[k] for k in ("assessment_id", "verification")})
                seq += 1
                counters["reused_after_verification"] += 1
            for cand, req in sorted(work, key=lambda x: (x[0], x[1]["requirement_id"])):
                counters["obligations_planned"] += 1
                self._action(run_id, seq, "plan_obligation", cand, req["requirement_id"],
                             {"obligation": f"{cand}/{req['requirement_id']}",
                              "tie_break": "candidate_id, then requirement_id"})
                seq += 1
                seq, stop = self._acquire_and_commit(project_id, run_id, mission, cand, req, seq, counters,
                                                     limits, deadline)
                if stop:
                    break
        except Exception as exc:  # recorded, then re-raised for the caller
            self._action(run_id, seq, "error", None, None, {"error": type(exc).__name__, "message": str(exc)},
                         status="failed")
            self._finish_run(run_id, "failed", f"error:{type(exc).__name__}", counters)
            raise
        status = "completed" if stop is None else "stopped"
        self._finish_run(run_id, status, stop or "all_obligations_processed", counters)
        return self.run_view(run_id)

    # ---------------- source revision (CHANGE-S2-V2)
    def available_changes(self, project_id: str) -> list[dict]:
        with self.store.read() as con:
            proj = self._project(con, project_id)
            applied = {r["event_id"]: dict(r) for r in
                       con.execute("SELECT * FROM change_events WHERE project_id=?", (project_id,))}
        out = []
        for e in proj["manifest"]["incoming_changes"]:
            rec = applied.get(e["event_id"])
            out.append({"event_id": e["event_id"], "event_type": e["event_type"], "source_id": e["source_id"],
                        "version_id": e["version_id"], "supersedes_version_id": e["supersedes_version_id"],
                        "status": rec["status"] if rec else "available",
                        "run_id": rec["run_id"] if rec else None,
                        "result": json.loads(rec["result_json"]) if rec and rec["result_json"] else None})
        return out

    def apply_change(self, project_id: str, event_id: str, invoked_via: str = "cli") -> dict:
        with self.store.read() as con:
            proj = self._project(con, project_id)
            if not con.execute("SELECT 1 FROM runs WHERE project_id=? AND kind='comparison' AND status='completed'",
                               (project_id,)).fetchone():
                raise Conflict("run the comparison before applying a source revision", "no_completed_run")
        mission, manifest = proj["mission"], proj["manifest"]
        entry = next((e for e in manifest["incoming_changes"] if e["event_id"] == event_id), None)
        if entry is None:
            raise NotFound(f"change event {event_id} is not declared for this project", "change_not_found")
        if entry["event_type"] != "source_revision":
            raise ValidationFailed(f"event type {entry['event_type']} is not supported in G01", "unsupported_event")
        with self.store.read() as con:
            rec = con.execute("SELECT * FROM change_events WHERE project_id=? AND event_id=?",
                              (project_id, event_id)).fetchone()
        if rec and rec["status"] == "applied":
            if rec["sha256"] != entry["sha256"]:
                raise Conflict("event was applied with different content", "event_content_conflict")
            return {"already_applied": True, "event_id": event_id, "run_id": rec["run_id"],
                    "result": json.loads(rec["result_json"])}
        if rec is None:
            self._import_revision(project_id, entry)
        return self._process_revision(project_id, entry, mission, invoked_via)

    def _import_revision(self, project_id: str, entry: dict) -> None:
        raw, text, fm = self._read_source_file(entry, entry["version_id"])
        if fm.get("supersedes_version_id") not in (None, entry["supersedes_version_id"]):
            raise ValidationFailed("front matter supersedes_version_id does not match the manifest", "identity_mismatch")
        sid, old, new = entry["source_id"], entry["supersedes_version_id"], entry["version_id"]
        with self.store.tx() as con:
            existing = con.execute("SELECT sha256 FROM source_versions WHERE project_id=? AND source_id=? AND "
                                   "version_id=?", (project_id, sid, new)).fetchone()
            if existing and existing["sha256"] != sha256(raw):
                raise Conflict(f"{sid}@{new} already exists with different content", "version_content_conflict")
            if self._current_versions(con, project_id).get(sid) != old:
                raise Conflict(f"{sid} current version is not {old}", "unexpected_current_version")
            passages = self._insert_version(con, project_id, entry, new, raw, text, entry["event_id"], old)
            self._make_current(con, project_id, sid, new, entry["candidate_id"], passages)
            now = utc_now()
            reasons = {}
            # citation dependents -> needs_review (persisted before any replacement assessment commits)
            for r in con.execute("SELECT DISTINCT a.assessment_id, a.candidate_id, a.requirement_id FROM assessments a "
                                 "JOIN dependencies d ON d.assessment_id=a.assessment_id WHERE a.project_id=? AND "
                                 "a.state='current' AND d.kind='citation' AND d.source_id=? AND d.version_id=?",
                                 (project_id, sid, old)).fetchall():
                reasons[(r["candidate_id"], r["requirement_id"])] = "needs_review"
                con.execute("INSERT INTO assessment_events VALUES (?,?,?,?,?)",
                            (r["assessment_id"], "needs_review", f"cited {sid}@{old} superseded by {new}", None, now))
                con.execute("UPDATE obligations SET state='needs_review', reason=?, updated_at=? WHERE project_id=? "
                            "AND candidate_id=? AND requirement_id=?",
                            (f"cited {sid}@{old} superseded by {new} ({entry['event_id']})", now, project_id,
                             r["candidate_id"], r["requirement_id"]))
            # search-scope dependents (changed source was searched but not cited) -> recheck search
            for r in con.execute("SELECT DISTINCT a.assessment_id, a.candidate_id, a.requirement_id FROM assessments a "
                                 "JOIN dependencies d ON d.assessment_id=a.assessment_id WHERE a.project_id=? AND "
                                 "a.state='current' AND d.kind='search_scope' AND d.source_id=? AND d.version_id=?",
                                 (project_id, sid, old)).fetchall():
                key = (r["candidate_id"], r["requirement_id"])
                if key in reasons:
                    continue
                reasons[key] = "recheck_search"
                con.execute("UPDATE obligations SET state='recheck_search', reason=?, updated_at=? WHERE "
                            "project_id=? AND candidate_id=? AND requirement_id=?",
                            (f"{sid} (searched, not cited) changed to {new}", now, project_id, *key))
            con.execute("INSERT INTO change_events VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                        (project_id, entry["event_id"], entry["event_type"], sid, new, old, sha256(raw), "imported",
                         None, None, now, None))

    def _process_revision(self, project_id: str, entry: dict, mission: dict, invoked_via: str) -> dict:
        reqs = {r["requirement_id"]: r for r in mission["requirements"]}
        with self.store.read() as con:
            obl = {(r["candidate_id"], r["requirement_id"]): dict(r) for r in
                   con.execute("SELECT * FROM obligations WHERE project_id=?", (project_id,))}
            before = self.comparison(project_id, con=con)
        run_id = self._new_run(project_id, "change", invoked_via, "selective_by_dependency", mission,
                               entry["event_id"])
        work, reuse, untouched = [], [], []
        # recheck_search: re-run the search; reuse the assessment only if the evidence identity is unchanged
        for key, o in sorted(obl.items()):
            if o["state"] == "needs_review":
                work.append((key[0], reqs[key[1]]))
            elif o["state"] == "recheck_search":
                searched_at = utc_now()
                with self.store.read() as con:
                    a = con.execute("SELECT * FROM assessments WHERE project_id=? AND candidate_id=? AND "
                                    "requirement_id=? AND state='current'", (project_id, *key)).fetchone()
                    new_hits = self._search(con, project_id, key[0], reqs[key[1]]["query"])
                old_ids = [(h["source_id"], h["version_id"], h["passage_id"]) for h in json.loads(a["search_hits_json"])]
                new_ids = [(h["source_id"], h["version_id"], h["passage_id"]) for h in new_hits]
                if old_ids == new_ids:
                    reuse.append({"candidate_id": key[0], "requirement_id": key[1], "assessment_id": a["assessment_id"],
                                  "query": reqs[key[1]]["query"], "searched_at": searched_at,
                                  "verification": "search re-executed on the new current scope; identical evidence "
                                                  "passages, so the committed assessment is still valid",
                                  "hits": new_hits})
                    with self.store.tx() as con:
                        con.execute("UPDATE obligations SET state='done', reason=?, updated_at=? WHERE project_id=? "
                                    "AND candidate_id=? AND requirement_id=?",
                                    (f"rechecked in {run_id}; evidence unchanged", utc_now(), project_id, *key))
                        con.execute("INSERT INTO assessment_events VALUES (?,?,?,?,?)",
                                    (a["assessment_id"], "revalidated", "search re-executed; same evidence", run_id,
                                     utc_now()))
                else:
                    work.append((key[0], reqs[key[1]]))
            else:
                untouched.append(f"{key[0]}/{key[1]}")
        # the verification searches are real acquisition actions: record them before the reuse entries
        run = self._execute(project_id, run_id, mission, work, reuse)
        with self.store.read() as con:
            after = self.comparison(project_id, con=con)
        b = {f"{x['candidate_id']}/{x['requirement_id']}": x for x in before["cells"]}
        a = {f"{x['candidate_id']}/{x['requirement_id']}": x for x in after["cells"]}
        affected = [{"key": k, "before": b[k], "after": a[k]} for k in sorted(a) if b[k]["assessment_id"] != a[k]["assessment_id"]]
        result = {
            "event_id": entry["event_id"], "source_id": entry["source_id"],
            "from_version": entry["supersedes_version_id"], "to_version": entry["version_id"], "run_id": run_id,
            "execution_strategy": "selective_by_dependency",
            "reacquired": [f"{c}/{r['requirement_id']}" for c, r in work],
            "revalidated_by_search": [f"{x['candidate_id']}/{x['requirement_id']}" for x in reuse],
            "outside_changed_scope": untouched,
            "affected": affected,
            "unchanged": sorted(k for k in a if b[k]["assessment_id"] == a[k]["assessment_id"]),
            "run_status": run["status"],
        }
        with self.store.tx() as con:
            con.execute("UPDATE change_events SET status='applied', run_id=?, result_json=?, applied_at=? WHERE "
                        "project_id=? AND event_id=?", (run_id, dumps(result), utc_now(), project_id, entry["event_id"]))
        return {"already_applied": False, "event_id": entry["event_id"], "run_id": run_id, "result": result}

    # ---------------- read models
    def list_projects(self) -> list[dict]:
        with self.store.read() as con:
            return [dict(r) for r in con.execute(
                "SELECT project_id, title, data_origin, scenario_id, created_at FROM projects ORDER BY created_at")]

    def _cells(self, con, project_id: str, state_filter: str = "current") -> list[dict]:
        out = []
        q = "SELECT * FROM assessments WHERE project_id=?" + (" AND state='current'" if state_filter == "current" else "")
        for r in con.execute(q + " ORDER BY candidate_id, requirement_id, created_at", (project_id,)).fetchall():
            c = con.execute("SELECT source_id, version_id, passage_id, start_char, end_char FROM citations WHERE "
                            "assessment_id=?", (r["assessment_id"],)).fetchone()
            ev = con.execute("SELECT state, reason, at FROM assessment_events WHERE assessment_id=? ORDER BY rowid",
                             (r["assessment_id"],)).fetchall()
            obl = con.execute("SELECT state FROM obligations WHERE project_id=? AND candidate_id=? AND requirement_id=?",
                              (project_id, r["candidate_id"], r["requirement_id"])).fetchone()
            display = "needs_review" if (r["state"] == "current" and obl and obl["state"] == "needs_review") else r["outcome"]
            out.append({"assessment_id": r["assessment_id"], "candidate_id": r["candidate_id"],
                        "requirement_id": r["requirement_id"], "outcome": r["outcome"], "display_outcome": display,
                        "label": OUTCOME_LABELS[display], "explanation": r["explanation"],
                        "reading": json.loads(r["reading_json"]), "validation_issues": json.loads(r["issues_json"]),
                        "citation": dict(c) if c else None, "run_id": r["run_id"], "supersedes_id": r["supersedes_id"],
                        "state": r["state"], "created_at": r["created_at"], "events": [dict(e) for e in ev]})
        return out

    def comparison(self, project_id: str, con=None) -> dict:
        if con is None:
            with self.store.read() as c:
                return self.comparison(project_id, con=c)
        proj = self._project(con, project_id)
        cells = self._cells(con, project_id)
        current = self._current_versions(con, project_id)
        for cell in cells:
            if cell["citation"]:
                cell["citation"]["is_current_version"] = current.get(cell["citation"]["source_id"]) == cell["citation"]["version_id"]
        last = con.execute("SELECT run_id, kind, status, finished_at, execution_mode FROM runs WHERE project_id=? "
                           "ORDER BY started_at DESC LIMIT 1", (project_id,)).fetchone()
        return {"project_id": project_id, "data_origin": proj["data_origin"], "cells": cells,
                "last_run": dict(last) if last else None}

    def history(self, project_id: str) -> list[dict]:
        with self.store.read() as con:
            self._project(con, project_id)
            return self._cells(con, project_id, state_filter="all")

    def project_view(self, project_id: str) -> dict:
        with self.store.read() as con:
            proj = self._project(con, project_id)
            current = self._current_versions(con, project_id)
            sources = []
            for r in con.execute("SELECT source_id, version_id, candidate_id, title, sha256, supersedes_version_id, "
                                 "imported_at, import_event, license FROM source_versions WHERE project_id=? "
                                 "ORDER BY source_id, version_id", (project_id,)):
                d = dict(r)
                d["status"] = "current" if current.get(d["source_id"]) == d["version_id"] else "historical"
                d["passages"] = [x["passage_id"] for x in con.execute(
                    "SELECT passage_id FROM passages WHERE project_id=? AND source_id=? AND version_id=? ORDER BY "
                    "start_char", (project_id, d["source_id"], d["version_id"]))]
                sources.append(d)
            runs = [dict(r) for r in con.execute("SELECT run_id, kind, status, stop_reason, invoked_via, execution_mode, "
                                                 "started_at, finished_at FROM runs WHERE project_id=? ORDER BY started_at",
                                                 (project_id,))]
            n_fts = con.execute("SELECT COUNT(*) FROM passage_fts WHERE project_id=?", (project_id,)).fetchone()[0]
            idx_versions = sorted({f"{r[0]}@{r[1]}" for r in con.execute(
                "SELECT source_id, version_id FROM passage_fts WHERE project_id=?", (project_id,))})
        return {"project_id": project_id, "title": proj["title"], "program_id": proj["program_id"],
                "goal_id": proj["goal_id"], "scenario_id": proj["scenario_id"], "data_origin": proj["data_origin"],
                "mission": proj["mission"], "sources": sources, "current_versions": current,
                "searchable_index": {"passages": n_fts, "source_versions": idx_versions}, "runs": runs,
                "changes": self.available_changes(project_id), "created_at": proj["created_at"]}

    def list_runs(self, project_id: str) -> list[dict]:
        return self.project_view(project_id)["runs"]

    def run_view(self, run_id: str) -> dict:
        with self.store.read() as con:
            r = con.execute("SELECT * FROM runs WHERE run_id=?", (run_id,)).fetchone()
            if not r:
                raise NotFound(f"run {run_id} not found", "run_not_found")
            d = dict(r)
            d["limits"] = json.loads(d.pop("limits_json"))
            d["counters"] = json.loads(d.pop("counters_json"))
            d["actions"] = [{**{k: a[k] for k in ("seq", "action_type", "candidate_id", "requirement_id", "status",
                                                  "started_at", "finished_at")}, "detail": json.loads(a["detail_json"])}
                            for a in con.execute("SELECT * FROM actions WHERE run_id=? ORDER BY seq", (run_id,))]
        d["data_origin"] = "synthetic_fixture"
        return d

    def source_version(self, project_id: str, source_id: str, version_id: str) -> dict:
        with self.store.read() as con:
            self._project(con, project_id)
            if not con.execute("SELECT 1 FROM source_versions WHERE project_id=? AND source_id=?",
                               (project_id, source_id)).fetchone():
                raise NotFound(f"source {source_id} not found", "source_not_found")
            v = con.execute("SELECT * FROM source_versions WHERE project_id=? AND source_id=? AND version_id=?",
                            (project_id, source_id, version_id)).fetchone()
            if not v:
                raise NotFound(f"version {source_id}@{version_id} not found", "version_not_found")
            versions = [x[0] for x in con.execute("SELECT version_id FROM source_versions WHERE project_id=? AND "
                                                  "source_id=? ORDER BY version_id", (project_id, source_id))]
            current = self._current_versions(con, project_id).get(source_id)
            passages = [dict(p) for p in con.execute("SELECT passage_id, start_char, end_char FROM passages WHERE "
                                                     "project_id=? AND source_id=? AND version_id=? ORDER BY start_char",
                                                     (project_id, source_id, version_id))]
        return {"source_id": source_id, "version_id": version_id, "title": v["title"], "text": v["text"],
                "sha256": v["sha256"], "candidate_id": v["candidate_id"], "license": v["license"],
                "status": "current" if current == version_id else "historical", "current_version": current,
                "all_versions": versions, "supersedes_version_id": v["supersedes_version_id"],
                "import_event": v["import_event"], "passages": passages, "data_origin": "synthetic_fixture"}

    def resolve_citation(self, project_id: str, source_id: str, version_id: str, passage_id: str) -> dict:
        sv = self.source_version(project_id, source_id, version_id)
        with self.store.read() as con:
            p = con.execute("SELECT * FROM passages WHERE project_id=? AND source_id=? AND version_id=? AND passage_id=?",
                            (project_id, source_id, version_id, passage_id)).fetchone()
            if not p:
                raise NotFound(f"passage {passage_id} not found in {source_id}@{version_id}", "passage_not_found")
            v = con.execute("SELECT raw FROM source_versions WHERE project_id=? AND source_id=? AND version_id=?",
                            (project_id, source_id, version_id)).fetchone()
            used = [dict(r) for r in con.execute(
                "SELECT a.assessment_id, a.candidate_id, a.requirement_id, a.outcome, a.state FROM citations c "
                "JOIN assessments a ON a.assessment_id=c.assessment_id WHERE a.project_id=? AND c.source_id=? AND "
                "c.version_id=? AND c.passage_id=? ORDER BY a.created_at", (project_id, source_id, version_id, passage_id))]
        text = sv["text"]
        s, e = p["start_char"], p["end_char"]
        if sha256(v["raw"]) != sv["sha256"] or text[s:e] != p["quote"]:
            raise ValidationFailed("stored passage does not match its source version", "citation_integrity")
        return {"source_id": source_id, "version_id": version_id, "passage_id": passage_id, "title": sv["title"],
                "status": sv["status"], "current_version": sv["current_version"], "all_versions": sv["all_versions"],
                "sha256": sv["sha256"], "start_char": s, "end_char": e, "offset_convention": OFFSET_CONVENTION,
                "quote": p["quote"], "text_before": text[:s], "text_after": text[e:], "used_by": used,
                "data_origin": "synthetic_fixture"}
