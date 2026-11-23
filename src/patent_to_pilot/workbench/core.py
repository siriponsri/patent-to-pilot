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

from patent_to_pilot.workbench import ingest as I
from patent_to_pilot.workbench import parser as P
from patent_to_pilot.workbench.generations import GenerationError, GenerationManager
from patent_to_pilot.workbench.profiles import ProviderRegistry
from patent_to_pilot.workbench.providers import ProviderError
from patent_to_pilot.workbench.store import Store, dumps, utc_now

PROGRAM_ID, GOAL_ID = "PTP-2026-11-21", "G01"
CORE_IDENTITY = "patent_to_pilot.workbench.core.EvidenceCore/v2"
SAMPLE_DIR = Path(__file__).resolve().parent / "sample"
SAMPLE_PROJECT_ID = "sample-thermal-module-demo-01"
EXECUTION_MODE = "live_local"
SEARCH_TOP_K = 3
HYBRID_CHANNEL_K = 10   # candidates taken from each channel before reciprocal-rank fusion
RRF_K = 60
RETRIEVAL_MODES = ("lexical", "hybrid")
_SOURCE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
OUTCOME_LABELS = {"meets": "Meets", "does_not_meet": "Does not meet", "unknown": "Unknown",
                  "needs_review": "Needs review",
                  # P4-T01: a free-text requirement has no bounded field to check, so the engine only reports the
                  # matching passage; a person judges whether it satisfies the requirement.
                  "evidence_found": "Evidence found (not judged)"}
OFFSET_CONVENTION = "unicode_code_points_zero_based_end_exclusive_on_unmodified_decoded_utf8"
# P4-T01: how a requirement's query becomes an FTS5 expression. "phrase" is the G01 behaviour (one exact phrase);
# "terms" ORs the requirement's word tokens (English stopwords dropped) and lets BM25 rank the passages.
MATCH_MODES = ("phrase", "terms")
REQUIREMENT_KINDS = ("bounded_field", "text")
TERM_STOPWORDS = frozenset("a an and are as at be by for from has have in is it its of on or that the this to was "
                           "were what which with".split())
MAX_REQUIREMENTS = 50
# P4-T01b: projects whose requirements can never be removed or restored (their recorded results stay reproducible)
LIFECYCLE_FIXED_ORIGINS = ("synthetic_fixture", "synthetic_demo")


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


def _upload_path(filename: str, pdf: dict | None) -> str:
    """Informational locator of an uploaded source; a PDF keeps its own hash and extractor as provenance."""
    if not pdf:
        return f"upload:{Path(filename).name}"[:200]
    tail = f"#pdf_sha256={pdf['pdf_sha256']};pages={pdf['pages']};{pdf['rule']};pypdf={pdf['pypdf']}"
    return f"upload:{Path(filename).name[:200 - 7 - len(tail)]}{tail}"


def core_code_sha256() -> str:
    here = Path(__file__).resolve().parent
    h = hashlib.sha256()
    for name in ("core.py", "parser.py", "store.py", "providers.py", "profiles.py", "generations.py", "ingest.py"):
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


def fts_terms(query: str) -> str:
    """P4-T01: OR of the query's word tokens, each quoted (FTS5 operators stay inert). English stopwords are dropped
    unless nothing else is left. Thai runs are kept whole (the unicode61 tokenizer does not segment Thai words)."""
    tokens = []
    for t in re.findall(r"\w+", query.lower(), flags=re.UNICODE):
        if t not in tokens:
            tokens.append(t)
    if not tokens:
        raise ValidationFailed("empty lexical query")
    kept = [t for t in tokens if t not in TERM_STOPWORDS] or tokens
    return " OR ".join(f'"{t}"' for t in kept)


def requirement_match(req: dict) -> str:
    """The FTS5 expression a requirement searches with (G01 requirements have no ``match`` key: phrase)."""
    return fts_terms(req["query"]) if req.get("match") == "terms" else fts_phrase(req["query"])


def requirement_kind(req: dict) -> str:
    return "text" if req.get("kind") == "text" or not req.get("field") else "bounded_field"


def normalize_requirement(r, requirement_id: str | None = None) -> dict:
    """Validate one requirement and return its stored form.

    * bounded field (G01 grammar): ``requirement_id, label, query, field, predicate`` (+ optional ``match``);
    * free text (P4-T01): ``label`` and optional ``query`` (default: the label); no field, no predicate. The engine
      searches with ``match`` (default ``terms``) and reports the top passage as evidence without judging it.
    """
    if not isinstance(r, dict):
        raise ValidationFailed("a requirement must be an object", "bad_requirement")
    rid = requirement_id or r.get("requirement_id")
    if not isinstance(rid, str) or not _SOURCE_ID.match(rid):
        raise ValidationFailed("requirement_id must be letters, digits, . _ - (max 64)", "bad_requirement_id")
    label = r.get("label")
    if not isinstance(label, str) or not label.strip() or len(label) > 200:
        raise ValidationFailed("label must be 1-200 characters", "bad_requirement_label")
    query = r.get("query")
    if query is None or (isinstance(query, str) and not query.strip()):
        query = label
    if not isinstance(query, str) or len(query) > 500:
        raise ValidationFailed("query must be text of at most 500 characters", "bad_requirement_query")
    if not re.findall(r"\w+", query, flags=re.UNICODE):
        raise ValidationFailed("query needs at least one word (letters or digits)", "bad_requirement_query")
    field = r.get("field")
    kind = r.get("kind") or ("bounded_field" if field else "text")
    if kind not in REQUIREMENT_KINDS:
        raise ValidationFailed(f"kind must be one of {list(REQUIREMENT_KINDS)}", "bad_requirement_kind")
    match = r.get("match")
    out = {"requirement_id": rid, "label": label.strip(), "query": query.strip()}
    if kind == "text":
        if field is not None or r.get("predicate") is not None:
            raise ValidationFailed("a free-text requirement has no field or predicate", "bad_requirement_kind")
        match = match or "terms"
        if match not in MATCH_MODES:
            raise ValidationFailed(f"match must be one of {list(MATCH_MODES)}", "bad_requirement_match")
        out.update(kind="text", match=match)
        return out
    pred = r.get("predicate")
    if field not in P.FIELD_LABELS or not isinstance(pred, dict):
        raise ValidationFailed(f"a bounded requirement needs a field of {sorted(P.FIELD_LABELS)} and a predicate",
                               "bad_requirement_field")
    op = pred.get("operator")
    if field == "supported_temperature_range":
        nums = [pred.get("minimum"), pred.get("maximum")]
        if op != "contains_interval" or not all(isinstance(x, (int, float)) and not isinstance(x, bool) for x in nums) \
                or nums[0] > nums[1] or pred.get("unit") != "degC":
            raise ValidationFailed("the temperature range needs contains_interval with minimum <= maximum and unit "
                                   "degC", "bad_requirement_predicate")
    elif op != "equals" or not isinstance(pred.get("value"), bool):
        raise ValidationFailed("a yes/no field needs an equals predicate with a true/false value",
                               "bad_requirement_predicate")
    out.update(field=field, predicate=pred)
    if match is not None:
        if match not in MATCH_MODES:
            raise ValidationFailed(f"match must be one of {list(MATCH_MODES)}", "bad_requirement_match")
        out["match"] = match
    return out


# --------------------------------------------------------------------------- the core service
class EvidenceCore:
    def __init__(self, data_dir: str | Path, sample_dir: str | Path = SAMPLE_DIR) -> None:
        self.store = Store(data_dir)
        self.sample_dir = Path(sample_dir)
        self.registry = ProviderRegistry(self.store)
        self.generations = GenerationManager(self.store, self.registry, P.PARSER_PROFILE)

    # ---------------- capabilities / identity
    def capabilities(self) -> dict:
        profiles = self.registry.list()

        def role_state(role: str, local: bool | None = None) -> dict:
            ps = [p for p in profiles if p["role"] == role and (local is None or (p["locality"] == "local") == local)]
            ready = [p["profile_id"] for p in ps if p["status"] == "ready"]
            if ready:
                return {"state": "ready", "profiles": ready}
            if ps:
                return {"state": "configured_not_ready", "profiles": [f"{p['profile_id']}:{p['status']}" for p in ps]}
            return {"state": "not_configured", "profiles": []}

        return {
            "program_id": PROGRAM_ID, "goal_id": "G02", "core_identity": CORE_IDENTITY,
            "core_code_sha256": core_code_sha256(),
            "lexical": {"state": "active", "implementation": "sqlite_fts5_unicode61",
                        "description": "Searches the local indexed text. No model required. Always available."},
            "chat": role_state("chat"), "embedding": role_state("embedding"), "rerank": role_state("rerank"),
            "local_model": {**role_state("embedding", local=True),
                            "description": "A local model is used only after its connection check passes."},
            "api_model": {"state": "blocked_without_envelope" if not any(
                p["paid_route"] and p["spend_cap_usd"] > 0 for p in profiles) else "envelope_recorded",
                "description": "Paid routes need a recorded spending envelope on the profile."},
            "ingestion": {"text_markdown": {"state": "active", "max_bytes": I.MAX_BYTES},
                          "pdf": I.pdf_capability()},
            "remote_calls_allowed": "per_profile_allow_remote", "model_downloads_allowed": False,
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
                        event: str, supersedes: str | None, passages: list[dict] | None = None,
                        title: str | None = None) -> list[dict]:
        if passages is None:
            title_m = _TITLE.search(text)
            title = title_m.group("title") if title_m else None
            passages = extract_passages(text)
        if not passages:
            raise ValidationFailed(f"{entry['source_id']}@{version_id} has no passages", "no_passages")
        now = utc_now()
        con.execute("INSERT INTO source_versions VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (project_id, entry["source_id"], version_id, entry["candidate_id"],
                     title or entry["source_id"], entry["source_kind"],
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

    def _lexical(self, con, project_id: str, candidate_id: str, query: str, k: int,
                 match: str | None = None) -> list[dict]:
        """FTS5 BM25 over the current-scope index. ``match`` (P0-T06) is an explicit FTS5 MATCH expression built by
        the caller; by default the query is one phrase (G01 behaviour, unchanged)."""
        current = self._current_versions(con, project_id)
        rows = con.execute(
            "SELECT source_id, version_id, passage_id, bm25(passage_fts) AS score FROM passage_fts "
            "WHERE passage_fts MATCH ? AND project_id=? AND candidate_id=? "
            "ORDER BY score, source_id, version_id, passage_id LIMIT ?",
            (match if match is not None else fts_phrase(query), project_id, candidate_id, k)).fetchall()
        hits = []
        for r in rows:
            if current.get(r["source_id"]) != r["version_id"]:
                raise RuntimeError("current lexical index contains a non-current version")
            hits.append({"source_id": r["source_id"], "version_id": r["version_id"],
                         "passage_id": r["passage_id"], "score": round(r["score"], 6)})
        return hits

    def _search(self, con, project_id: str, candidate_id: str, query: str, ctx: dict | None = None,
                match: str | None = None) -> list[dict]:
        """Lexical (G01 behaviour, unchanged) unless the run's retrieval context is hybrid: then FTS5 and dense
        cosine over the active, fresh index generation are fused by reciprocal rank. The mode actually used is
        written to ``ctx['last_search']`` so the caller can record it and bind the dependency. ``match`` (P4-T01) is
        the requirement's FTS5 expression; by default the query is one phrase (G01)."""
        if not ctx or ctx["effective"] != "hybrid":
            if ctx is not None:
                ctx["last_search"] = "lexical"
            return self._lexical(con, project_id, candidate_id, query, SEARCH_TOP_K, match=match)
        lex = self._lexical(con, project_id, candidate_id, query, HYBRID_CHANNEL_K, match=match)
        try:
            qv = ctx["query_vectors"].get(query)
            if qv is None:
                qv = ctx["client"].embed([query], "query")[0]
                ctx["query_vectors"][query] = qv
            dense = self.generations.search(ctx["generation_id"], qv, candidate_id, HYBRID_CHANNEL_K)
        except (ProviderError, GenerationError) as exc:
            ctx["effective"] = "lexical_fallback"
            ctx["reason"] = f"dense channel failed during the run ({type(exc).__name__}: {exc}); lexical only from here"
            ctx["last_search"] = "lexical_fallback"
            return self._lexical(con, project_id, candidate_id, query, SEARCH_TOP_K, match=match)
        current = self._current_versions(con, project_id)
        fused: dict[tuple, dict] = {}
        for rank, h in enumerate(lex, start=1):
            key = (h["source_id"], h["version_id"], h["passage_id"])
            fused[key] = {"lexical_rank": rank, "bm25": h["score"], "dense_rank": None, "cosine": None}
        for rank, h in enumerate(dense, start=1):
            key = (h["source_id"], h["version_id"], h["passage_id"])
            if current.get(key[0]) != key[1]:
                raise RuntimeError("active index generation contains a non-current version")
            fused.setdefault(key, {"lexical_rank": None, "bm25": None, "dense_rank": None, "cosine": None})
            fused[key].update(dense_rank=rank, cosine=h["cosine"])
        scored = []
        for key, f in fused.items():
            s = sum(1.0 / (RRF_K + r) for r in (f["lexical_rank"], f["dense_rank"]) if r is not None)
            scored.append((s, key, f))
        scored.sort(key=lambda x: (-x[0], x[1]))
        ctx["last_search"] = "hybrid"
        return [{"source_id": k[0], "version_id": k[1], "passage_id": k[2], "score": round(s, 6), "channels": f}
                for s, k, f in scored[:SEARCH_TOP_K]]

    def _retrieval_context(self, project_id: str) -> dict:
        """Resolve the retrieval mode for one run. Hybrid needs a ready embedding profile and an active index
        generation for the current corpus; a stale generation is rebuilt (reusing unchanged vectors) and switched
        before the run searches. Any failure falls back to lexical with the reason recorded."""
        with self.store.read() as con:
            s = self.generations.settings(con, project_id)
        ctx = {"mode": s["retrieval_mode"], "effective": "lexical", "generation_id": None,
               "embedding_space_id": None, "profile_id": s["embedding_profile_id"], "reason": None,
               "refreshed_from": None, "query_vectors": {}}
        if s["retrieval_mode"] != "hybrid":
            return ctx
        pid = s["embedding_profile_id"]
        if not pid or not s["active_generation_id"]:
            ctx["reason"] = "hybrid mode without an active index generation"
            return ctx
        try:
            if not self.registry.is_ready(pid):
                raise GenerationError(f"embedding profile {pid} is not ready ({self.registry.status(pid)})")
            with self.store.read() as con:
                gen = self.generations.generation(con, s["active_generation_id"])
                fresh = self.generations.freshness(con, project_id, gen)
            if fresh != "fresh":
                new = self.generations.build(project_id, pid)
                if new["generation_id"] != gen["generation_id"]:
                    with self.store.tx() as con:
                        self._switch_generation(con, project_id, new["generation_id"], pid,
                                                "corpus changed: index generation rebuilt before searching")
                    ctx["refreshed_from"] = gen["generation_id"]
                gen = new
            ctx.update(effective="hybrid", generation_id=gen["generation_id"],
                       embedding_space_id=gen["embedding_space_id"], client=self.registry.client(pid))
        except (GenerationError, ProviderError) as exc:
            ctx["reason"] = f"dense channel unavailable: {exc}"
        return ctx

    @staticmethod
    def _ctx_public(ctx: dict | None) -> dict | None:
        if ctx is None:
            return None
        return {k: ctx[k] for k in ("mode", "effective", "generation_id", "embedding_space_id", "profile_id",
                                    "reason", "refreshed_from")}

    def _switch_generation(self, con, project_id: str, generation_id: str, profile_id: str, reason: str) -> str | None:
        """Activate a generation inside the caller's transaction and reopen the searches that depended on the
        previous one (search re-executed; result reused only if the evidence is unchanged)."""
        prev = self.generations.activate(con, project_id, generation_id, profile_id)
        if prev and prev != generation_id:
            now = utc_now()
            for r in con.execute("SELECT DISTINCT a.candidate_id, a.requirement_id FROM assessments a JOIN dependencies "
                                 "d ON d.assessment_id=a.assessment_id WHERE a.project_id=? AND a.state='current' AND "
                                 "d.kind='index_generation' AND d.source_id=?", (project_id, prev)).fetchall():
                con.execute("UPDATE obligations SET state='recheck_search', reason=?, updated_at=? WHERE project_id=? "
                            "AND candidate_id=? AND requirement_id=? AND state='done'",
                            (f"{reason} ({prev} -> {generation_id})", now, project_id, r[0], r[1]))
        return prev

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
            origin = con.execute("SELECT data_origin FROM projects WHERE project_id=?", (project_id,)).fetchone()[0]
            con.execute("INSERT INTO runs VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                        (run_id, project_id, kind, invoked_via, CORE_IDENTITY, EXECUTION_MODE,
                         origin, strategy, cfg_sha, dumps(mission["limits"]), dumps({}), "running",
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
                            seq: int, counters: dict, limits: dict, deadline: float,
                            ctx: dict | None = None) -> tuple[int, str | None]:
        """One obligation. Returns (next seq, stop reason or None)."""
        if counters["acquisition_actions"] >= limits["max_acquisition_actions"]:
            return seq, "budget_exhausted:max_acquisition_actions"
        if time.monotonic() > deadline:
            return seq, "deadline:max_wall_seconds"
        rid = req["requirement_id"]
        t0 = utc_now()
        match = requirement_match(req)
        free_text = requirement_kind(req) == "text"
        with self.store.read() as con:
            hits = self._search(con, project_id, cand, req["query"], ctx, match=match)
            scope = self._scope(con, project_id, cand)
        counters["acquisition_actions"] += 1
        detail = {"query": req["query"], "fts_match": match, "candidate_scope": cand,
                  "scope_versions": [f"{s}@{v}" for s, v in scope], "hits": hits}
        if free_text:
            detail["requirement_kind"] = "text"
        if ctx and ctx["mode"] == "hybrid":
            detail["retrieval"] = {"used": ctx["last_search"], "generation_id": ctx["generation_id"]}
        self._action(run_id, seq, "search_current_sources", cand, rid, detail, started=t0)
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
            if free_text:  # P4-T01: no bounded field to read; the top-ranked passage is reported, not judged
                self._action(run_id, seq, "read_passage", cand, rid,
                             {"passage": f"{h['source_id']}@{h['version_id']}#{h['passage_id']}",
                              "requirement_kind": "text", "rule": "top lexical match is reported as evidence"},
                             started=t0)
                seq += 1
                evidence = dict(p)
                break
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
        cand_name = next(c["label"] for c in mission["candidates"] if c["candidate_id"] == cand)
        if free_text:
            if evidence is not None:
                outcome = "evidence_found"
                explanation = (f"Best-matching passage in {cand_name}'s current sources for the requirement terms. "
                               "The engine does not judge whether it satisfies the requirement; review the quote.")
            else:
                outcome = "unknown"
                explanation = f"No passage in {cand_name}'s current sources matches the requirement terms."
        elif reading is not None:
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
                     {"predicate": req.get("predicate"), "reading": None if reading is None else reading.value,
                      "outcome": outcome, "explanation": explanation, "validation_issues": issues}, started=t0)
        seq += 1
        citation = None
        if evidence is not None:
            citation = {"source_id": evidence["source_id"], "version_id": evidence["version_id"],
                        "passage_id": evidence["passage_id"], "start_char": evidence["start_char"],
                        "end_char": evidence["end_char"], "quote": evidence["quote"], "sha256": evidence["sha256"]}
        t0 = utc_now()
        gen_dep = None
        if ctx and ctx.get("last_search") == "hybrid":
            gen_dep = (ctx["generation_id"], ctx["embedding_space_id"])
        result = self._commit(project_id, run_id, mission, cand, req, outcome, explanation, reading, issues,
                              hits, scope, citation, gen_dep)
        self._action(run_id, seq, "commit_assessment", cand, rid, result, started=t0)
        seq += 1
        key = {"new_version": "committed", "rejected_stale": "rejected_stale"}.get(result["committed"], "retained")
        counters[key] = counters.get(key, 0) + 1   # P4-T01b: a stale in-flight result is counted, never committed
        return seq, None

    def _commit(self, project_id, run_id, mission, cand, req, outcome, explanation, reading, issues, hits, scope,
                citation, gen_dep=None) -> dict:
        rid = req["requirement_id"]
        req_sha = sha256(dumps(req).encode("utf-8"))
        with self.store.tx() as con:
            stale = self._stale_requirement(con, project_id, req, run_id=run_id, cand=cand)   # P4-T01b commit recheck
            if stale:
                return {"committed": "rejected_stale", "reason": stale, "outcome": outcome, "requirement_sha256": req_sha}
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
                # the retained assessment now also rests on this search: record any receipt it did not have yet
                have = {(d["kind"], d["source_id"], d["version_id"]) for d in con.execute(
                    "SELECT kind, source_id, version_id FROM dependencies WHERE assessment_id=?", (prev["assessment_id"],))}
                new_deps = [("search_scope", s, v) for s, v in scope]
                if gen_dep is not None:
                    new_deps.append(("index_generation", gen_dep[0], gen_dep[1]))
                for kind, s, v in new_deps:
                    if (kind, s, v) not in have:
                        con.execute("INSERT INTO dependencies VALUES (?,?,?,?,?,?)",
                                    (prev["assessment_id"], kind, s, v, cand, req["query"]))
                # keep the latest supporting search receipt, so a later recheck compares against what was
                # actually searched last (not the search of the run that first committed the result)
                if json.loads(prev["search_hits_json"]) != hits:
                    con.execute("UPDATE assessments SET search_hits_json=? WHERE assessment_id=?",
                                (dumps(hits), prev["assessment_id"]))
                    con.execute("INSERT INTO assessment_events VALUES (?,?,?,?,?)",
                                (prev["assessment_id"], "revalidated", "re-acquired with a different search receipt; "
                                 "identical result retained", run_id, utc_now()))
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
            if gen_dep is not None:  # dense search receipt: bound to the generation and its embedding space
                con.execute("INSERT INTO dependencies VALUES (?,?,?,?,?,?)",
                            (aid, "index_generation", gen_dep[0], gen_dep[1], cand, req["query"]))
            con.execute("UPDATE obligations SET state='done', reason=?, updated_at=? WHERE project_id=? AND "
                        "candidate_id=? AND requirement_id=?", (f"committed {aid}", now, project_id, cand, rid))
        return {"committed": "new_version", "assessment_id": aid, "supersedes": prev["assessment_id"] if prev else None,
                "outcome": outcome, "citation": new_cit}

    def run_comparison(self, project_id: str, invoked_via: str = "cli") -> dict:
        """Full comparison: every candidate x requirement obligation is planned and acquired."""
        with self.store.read() as con:
            mission = self._project(con, project_id)["mission"]
        run_id = self._new_run(project_id, "comparison", invoked_via, "full", mission)
        ctx = self._retrieval_context(project_id)
        return self._execute(project_id, run_id, mission,
                             [(c["candidate_id"], r) for c in mission["candidates"] for r in mission["requirements"]],
                             reuse=[], ctx=ctx)

    def _execute(self, project_id: str, run_id: str, mission: dict, work: list, reuse: list,
                 ctx: dict | None = None) -> dict:
        limits = mission["limits"]
        deadline = time.monotonic() + limits["max_wall_seconds"]
        counters = {"obligations_planned": 0, "acquisition_actions": 0, "source_reads": 0, "committed": 0,
                    "retained": 0, "reused_after_verification": 0, "paid_model_calls": 0, "remote_calls": 0}
        seq, stop = 1, None
        if ctx and ctx["mode"] == "hybrid":
            self._action(run_id, seq, "retrieval_setup", None, None, self._ctx_public(ctx),
                         status="ok" if ctx["effective"] == "hybrid" else "fallback")
            seq += 1
        try:
            for item in reuse:  # verification search (really executed) followed by the reuse decision
                self._action(run_id, seq, "search_current_sources", item["candidate_id"], item["requirement_id"],
                             {"query": item["query"], "fts_match": item.get("fts_match") or fts_phrase(item["query"]),
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
                with self.store.read() as con:   # P4-T01b: the lifecycle state this obligation is planned against
                    lifecycle = self._plan_lifecycle(con, project_id, req)
                self._action(run_id, seq, "plan_obligation", cand, req["requirement_id"],
                             {"obligation": f"{cand}/{req['requirement_id']}",
                              "tie_break": "candidate_id, then requirement_id", **lifecycle["record"]})
                seq += 1
                if lifecycle["stale"]:
                    self._action(run_id, seq, "skip_stale_obligation", cand, req["requirement_id"],
                                 {"reason": lifecycle["stale"]}, status="skipped")
                    seq += 1
                    counters["skipped_stale"] = counters.get("skipped_stale", 0) + 1
                    continue
                seq, stop = self._acquire_and_commit(project_id, run_id, mission, cand, req, seq, counters,
                                                     limits, deadline, ctx)
                if stop:
                    break
        except Exception as exc:  # recorded, then re-raised for the caller
            self._action(run_id, seq, "error", None, None, {"error": type(exc).__name__, "message": str(exc)},
                         status="failed")
            self._finish_run(run_id, "failed", f"error:{type(exc).__name__}", counters)
            raise
        if ctx and ctx["mode"] == "hybrid":
            counters["retrieval_effective"] = ctx["effective"]
            client = ctx.get("client")
            if client is not None:
                counters["query_embeddings"] = len(ctx["query_vectors"])
                if not client.profile.local:
                    counters["remote_calls"] = len(ctx["query_vectors"])
                if client.profile.paid:
                    counters["paid_model_calls"] = len(ctx["query_vectors"])
            if ctx["effective"] != "hybrid" or ctx.get("reason"):
                counters["retrieval_note"] = ctx["reason"]
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
        declared = {e["event_id"] for e in proj["manifest"]["incoming_changes"]}
        for rec in sorted(applied.values(), key=lambda r: r["created_at"]):  # recorded events (ingestion, retrieval)
            if rec["event_id"] in declared:
                continue
            out.append({"event_id": rec["event_id"], "event_type": rec["event_type"], "source_id": rec["source_id"],
                        "version_id": rec["version_id"], "supersedes_version_id": rec["supersedes_version_id"],
                        "status": rec["status"], "run_id": rec["run_id"],
                        "result": json.loads(rec["result_json"]) if rec["result_json"] else None})
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
        self._import_source(project_id, entry, raw, text)

    def _import_source(self, project_id: str, entry: dict, raw: bytes, text: str, passages: list[dict] | None = None,
                       title: str | None = None, extra=None) -> None:
        """Persist a new immutable version (revision) or a new source (addition), switch the current pointer and
        index, and mark affected work, all in one transaction.

        * revision: citation dependents -> needs_review; search-scope dependents -> recheck_search.
        * addition: the candidate's search scope grew, so every current result for that candidate gets
          recheck_search (a new uncited document can overturn an earlier "nothing found").

        ``extra(con)`` (P0-T06) writes additive records of the same version (original bytes, pages, nodes) inside the
        same transaction, so a version is never visible without them."""
        sid, old, new = entry["source_id"], entry["supersedes_version_id"], entry["version_id"]
        with self.store.tx() as con:
            existing = con.execute("SELECT sha256 FROM source_versions WHERE project_id=? AND source_id=? AND "
                                   "version_id=?", (project_id, sid, new)).fetchone()
            if existing and existing["sha256"] != sha256(raw):
                raise Conflict(f"{sid}@{new} already exists with different content", "version_content_conflict")
            if self._current_versions(con, project_id).get(sid) != old:
                raise Conflict(f"{sid} current version is not {old}", "unexpected_current_version")
            passages = self._insert_version(con, project_id, entry, new, raw, text, entry["event_id"], old,
                                            passages, title)
            self._make_current(con, project_id, sid, new, entry["candidate_id"], passages)
            if extra is not None:
                extra(con)
            now = utc_now()
            reasons = {}
            if old is None:  # source_addition
                for r in con.execute("SELECT candidate_id, requirement_id FROM obligations WHERE project_id=? AND "
                                     "candidate_id=? AND state='done'", (project_id, entry["candidate_id"])).fetchall():
                    con.execute("UPDATE obligations SET state='recheck_search', reason=?, updated_at=? WHERE "
                                "project_id=? AND candidate_id=? AND requirement_id=?",
                                (f"new source {sid}@{new} joined the search scope ({entry['event_id']})", now,
                                 project_id, r[0], r[1]))
            # citation dependents -> needs_review (persisted before any replacement assessment commits)
            for r in con.execute("SELECT DISTINCT a.assessment_id, a.candidate_id, a.requirement_id FROM assessments a "
                                 "JOIN dependencies d ON d.assessment_id=a.assessment_id WHERE a.project_id=? AND "
                                 "a.state='current' AND d.kind='citation' AND d.source_id=? AND d.version_id=?",
                                 (project_id, sid, old)).fetchall():
                reasons[(r["candidate_id"], r["requirement_id"])] = "needs_review"
                con.execute("INSERT INTO assessment_events VALUES (?,?,?,?,?)",
                            (r["assessment_id"], "needs_review", f"cited {sid}@{old} superseded by {new}", None, now))
                con.execute("UPDATE obligations SET state='needs_review', reason=?, updated_at=? WHERE project_id=? "
                            "AND candidate_id=? AND requirement_id=? AND state!='retired'",
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
                            "project_id=? AND candidate_id=? AND requirement_id=? AND state!='retired'",
                            (f"{sid} (searched, not cited) changed to {new}", now, project_id, *key))
            con.execute("INSERT INTO change_events VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                        (project_id, entry["event_id"], entry["event_type"], sid, new, old, sha256(raw), "imported",
                         None, None, now, None))

    def _process_revision(self, project_id: str, entry: dict, mission: dict, invoked_via: str) -> dict:
        reqs = {r["requirement_id"]: r for r in mission["requirements"]}
        with self.store.read() as con:
            before = self.comparison(project_id, con=con)
        run_id = self._new_run(project_id, "change", invoked_via, "selective_by_dependency", mission,
                               entry["event_id"])
        ctx = self._retrieval_context(project_id)  # may rebuild a stale index generation and reopen its searches
        with self.store.read() as con:
            obl = {(r["candidate_id"], r["requirement_id"]): dict(r) for r in
                   con.execute("SELECT * FROM obligations WHERE project_id=?", (project_id,))}
        work, reuse, untouched = [], [], []
        # recheck_search: re-run the search; reuse the assessment only if the evidence identity is unchanged
        for key, o in sorted(obl.items()):
            if o["state"] == "retired" or key[1] not in reqs:   # P4-T01b: removed requirements are never re-planned
                continue
            if o["state"] in ("needs_review", "open"):
                work.append((key[0], reqs[key[1]]))
            elif o["state"] == "recheck_search":
                searched_at = utc_now()
                with self.store.read() as con:
                    a = con.execute("SELECT * FROM assessments WHERE project_id=? AND candidate_id=? AND "
                                    "requirement_id=? AND state='current'", (project_id, *key)).fetchone()
                    new_hits = self._search(con, project_id, key[0], reqs[key[1]]["query"], ctx,
                                            match=requirement_match(reqs[key[1]]))
                if a is None:
                    work.append((key[0], reqs[key[1]]))
                    continue
                old_ids = [(h["source_id"], h["version_id"], h["passage_id"]) for h in json.loads(a["search_hits_json"])]
                new_ids = [(h["source_id"], h["version_id"], h["passage_id"]) for h in new_hits]
                if old_ids == new_ids and ctx.get("last_search") == "hybrid":
                    with self.store.tx() as con:  # the reused result now rests on this generation's search too
                        if not con.execute("SELECT 1 FROM dependencies WHERE assessment_id=? AND kind='index_generation' "
                                           "AND source_id=?", (a["assessment_id"], ctx["generation_id"])).fetchone():
                            con.execute("INSERT INTO dependencies VALUES (?,?,?,?,?,?)",
                                        (a["assessment_id"], "index_generation", ctx["generation_id"],
                                         ctx["embedding_space_id"], key[0], reqs[key[1]]["query"]))
                if old_ids == new_ids:
                    reuse.append({"candidate_id": key[0], "requirement_id": key[1], "assessment_id": a["assessment_id"],
                                  "query": reqs[key[1]]["query"], "fts_match": requirement_match(reqs[key[1]]),
                                  "searched_at": searched_at,
                                  "verification": "search re-executed on the new current scope; identical evidence "
                                                  "passages, so the committed assessment is still valid",
                                  "hits": new_hits})
                    with self.store.tx() as con:
                        con.execute("UPDATE obligations SET state='done', reason=?, updated_at=? WHERE project_id=? "
                                    "AND candidate_id=? AND requirement_id=? AND state!='retired'",
                                    (f"rechecked in {run_id}; evidence unchanged", utc_now(), project_id, *key))
                        con.execute("INSERT INTO assessment_events VALUES (?,?,?,?,?)",
                                    (a["assessment_id"], "revalidated", "search re-executed; same evidence", run_id,
                                     utc_now()))
                else:
                    work.append((key[0], reqs[key[1]]))
            else:
                untouched.append(f"{key[0]}/{key[1]}")
        # the verification searches are real acquisition actions: record them before the reuse entries
        run = self._execute(project_id, run_id, mission, work, reuse, ctx)
        with self.store.read() as con:
            after = self.comparison(project_id, con=con)
        b = {f"{x['candidate_id']}/{x['requirement_id']}": x for x in before["cells"]}
        a = {f"{x['candidate_id']}/{x['requirement_id']}": x for x in after["cells"]}
        affected = [{"key": k, "before": b.get(k), "after": a[k]} for k in sorted(a)
                    if (b.get(k) or {}).get("assessment_id") != a[k]["assessment_id"]]
        result = {
            "event_id": entry["event_id"], "source_id": entry["source_id"],
            "from_version": entry["supersedes_version_id"], "to_version": entry["version_id"], "run_id": run_id,
            "execution_strategy": "selective_by_dependency",
            "reacquired": [f"{c}/{r['requirement_id']}" for c, r in work],
            "revalidated_by_search": [f"{x['candidate_id']}/{x['requirement_id']}" for x in reuse],
            "outside_changed_scope": untouched,
            "affected": affected,
            "unchanged": sorted(k for k in a if (b.get(k) or {}).get("assessment_id") == a[k]["assessment_id"]),
            "run_status": run["status"],
        }
        if ctx["mode"] == "hybrid":
            result["retrieval"] = self._ctx_public(ctx)
        with self.store.tx() as con:
            con.execute("UPDATE change_events SET status='applied', run_id=?, result_json=?, applied_at=? WHERE "
                        "project_id=? AND event_id=?", (run_id, dumps(result), utc_now(), project_id, entry["event_id"]))
        return {"already_applied": False, "event_id": entry["event_id"], "run_id": run_id, "result": result}

    # ---------------- G02: owner projects, ingestion, providers and index generations
    def _has_completed_run(self, con, project_id: str) -> bool:
        return con.execute("SELECT 1 FROM runs WHERE project_id=? AND kind='comparison' AND status='completed'",
                           (project_id,)).fetchone() is not None

    def _new_event_id(self, prefix: str) -> str:
        return f"{prefix}-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}-{uuid.uuid4().hex[:6]}"

    def _record_internal_event(self, con, project_id: str, event_id: str, event_type: str, subject: str,
                               version: str, previous: str | None, digest: str) -> None:
        con.execute("INSERT INTO change_events VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                    (project_id, event_id, event_type, subject, version, previous, digest, "imported", None, None,
                     utc_now(), None))

    def _settle_event(self, project_id: str, entry: dict, mission: dict, invoked_via: str) -> dict:
        """Process the reopened work selectively if the project already has results; otherwise just close the
        event (there is nothing earlier to re-check)."""
        with self.store.read() as con:
            has_run = self._has_completed_run(con, project_id)
        if has_run:
            return self._process_revision(project_id, entry, mission, invoked_via)
        result = {"event_id": entry["event_id"], "note": "no earlier results in this project; nothing to re-check"}
        with self.store.tx() as con:
            con.execute("UPDATE change_events SET status='applied', result_json=?, applied_at=? WHERE project_id=? "
                        "AND event_id=?", (dumps(result), utc_now(), project_id, entry["event_id"]))
        return {"already_applied": False, "event_id": entry["event_id"], "run_id": None, "result": result}

    def create_project(self, title: str, candidates: list[dict] | None = None,
                       requirements: list[dict] | None = None) -> dict:
        """An owner project for owner-supplied files. Without explicit candidates/requirements it starts from the
        sample's requirement template (the bounded fixture grammar); it never copies sample sources."""
        if not isinstance(title, str) or not title.strip() or len(title) > 120:
            raise ValidationFailed("title must be 1-120 characters", "bad_title")
        _manifest, template = self._load_sample_inputs()
        mission = json.loads(dumps(template))
        mission.update(goal_id="G02", scenario_id="OWNER-PROJECT", data_origin="owner_files", mission=title.strip())
        if candidates is not None:
            if not isinstance(candidates, list) or not candidates:
                raise ValidationFailed("candidates must be a non-empty list", "bad_candidates")
            for c in candidates:
                if not isinstance(c, dict) or not _SOURCE_ID.match(str(c.get("candidate_id", ""))) or not c.get("label"):
                    raise ValidationFailed("each candidate needs candidate_id and label", "bad_candidates")
            mission["candidates"] = [{"candidate_id": c["candidate_id"], "label": str(c["label"])} for c in candidates]
        if requirements is not None:
            if not isinstance(requirements, list) or not requirements:
                raise ValidationFailed("requirements must be a non-empty list", "bad_requirements")
            if len(requirements) > MAX_REQUIREMENTS:
                raise ValidationFailed(f"at most {MAX_REQUIREMENTS} requirements", "bad_requirements")
            normalized = []
            for r in requirements:
                try:  # P4-T01: a bounded-field requirement (G01 grammar) or an explicit free-text requirement
                    normalized.append(normalize_requirement(r))
                except ValidationFailed as exc:
                    raise ValidationFailed("each requirement needs requirement_id and label, and either a field of "
                                           f"the bounded grammar {sorted(P.FIELD_LABELS)} with an equals/"
                                           f"contains_interval predicate or free text ({exc})", "bad_requirements") from None
            if len({r["requirement_id"] for r in normalized}) != len(normalized):
                raise ValidationFailed("requirement ids must be unique", "bad_requirements")
            mission["requirements"] = normalized
        slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:24] or "project"
        project_id = f"prj-{slug}-{uuid.uuid4().hex[:6]}"
        manifest = {"scenario_id": "OWNER-PROJECT", "data_origin": "owner_files", "initial_sources": [],
                    "incoming_changes": []}
        with self.store.tx() as con:
            con.execute("INSERT INTO projects VALUES (?,?,?,?,?,?,?,?,?)",
                        (project_id, PROGRAM_ID, "G02", "OWNER-PROJECT", title.strip(), "owner_files", dumps(mission),
                         dumps(manifest), utc_now()))
            for c in mission["candidates"]:
                for r in mission["requirements"]:
                    con.execute("INSERT INTO obligations VALUES (?,?,?,?,?,?)",
                                (project_id, c["candidate_id"], r["requirement_id"], "open", "initial obligation",
                                 utc_now()))
        return {"project_id": project_id, "title": title.strip(), "data_origin": "owner_files"}

    def ingest_document(self, project_id: str, filename: str, raw: bytes, candidate_id: str,
                        source_id: str | None = None, invoked_via: str = "cli") -> dict:
        """Add a text/Markdown file as a new source (source_addition) or a new version of an existing source
        (source_revision). Re-ingesting identical bytes is a no-op. Affected results are re-checked through the
        same selective path as the G01 revision."""
        with self.store.read() as con:
            proj = self._project(con, project_id)
        if proj["data_origin"] in ("synthetic_fixture", "synthetic_demo"):
            raise Conflict("the sample project is fixed; create a project for your own files", "sample_is_fixed")
        mission = proj["mission"]
        if candidate_id not in {c["candidate_id"] for c in mission["candidates"]}:
            raise ValidationFailed(f"unknown candidate {candidate_id}", "unknown_candidate")
        try:
            prep = I.prepare(filename, raw, extract_passages)
        except I.IngestError as exc:
            raise ValidationFailed(str(exc), exc.code) from None
        sid = source_id or I.slug_source_id(filename)
        if not _SOURCE_ID.match(sid):
            raise ValidationFailed("source_id must be letters, digits, . _ - (max 64)", "bad_source_id")
        # a PDF is stored as its canonical extracted text (ingest.py); the PDF's own hash goes into the path
        stored = prep.get("stored_raw", raw)
        digest = sha256(stored)
        with self.store.read() as con:
            cur = con.execute("SELECT v.version_id, v.sha256, v.candidate_id FROM current_sources c JOIN source_versions "
                              "v USING (project_id, source_id, version_id) WHERE c.project_id=? AND c.source_id=?",
                              (project_id, sid)).fetchone()
            n_versions = con.execute("SELECT COUNT(*) FROM source_versions WHERE project_id=? AND source_id=?",
                                     (project_id, sid)).fetchone()[0]
        if cur and cur["sha256"] == digest:
            return {"status": "unchanged", "source_id": sid, "version_id": cur["version_id"], "sha256": digest}
        if cur and cur["candidate_id"] != candidate_id:
            raise Conflict(f"{sid} belongs to {cur['candidate_id']}; use another source_id", "source_candidate_conflict")
        version = f"v{n_versions + 1}"
        entry = {"event_id": self._new_event_id("ING"),
                 "event_type": "source_revision" if cur else "source_addition", "source_id": sid,
                 "version_id": version, "supersedes_version_id": cur["version_id"] if cur else None,
                 "candidate_id": candidate_id, "source_kind": prep["source_kind"], "license": "owner_supplied",
                 "path": _upload_path(filename, prep.get("pdf")), "sha256": digest}
        media = {".pdf": "application/pdf", ".md": "text/markdown", ".markdown": "text/markdown",
                 ".txt": "text/plain"}[Path(filename).suffix.lower()]

        def keep_original(con):  # P0-T06: the uploaded bytes themselves (a PDF is otherwise only its canonical text)
            con.execute("INSERT OR REPLACE INTO original_artifacts VALUES (?,?,?,?,?,?,?,?,?)",
                        (project_id, sid, version, media, sha256(raw), len(raw), raw,
                         f"sqlite:original_artifacts/{project_id}/{sid}@{version}", utc_now()))
        self._import_source(project_id, entry, stored, prep["text"], prep["passages"], prep["title"], keep_original)
        out = self._settle_event(project_id, entry, mission, invoked_via)
        return {"status": "ingested", "source_id": sid, "version_id": version, "sha256": digest,
                "event_type": entry["event_type"], "passage_rule": prep["passage_rule"],
                "passages": len(prep["passages"]), **({"pdf": prep["pdf"]} if prep.get("pdf") else {}), **out}

    def retrieval_status(self, project_id: str) -> dict:
        with self.store.read() as con:
            self._project(con, project_id)
        return self.generations.status(project_id)

    def build_index(self, project_id: str, profile_id: str, invoked_via: str = "cli") -> dict:
        """Build a new index generation beside the active one, validate it, then switch the pointer. Searches that
        depended on the previous generation are re-checked if the project is in hybrid mode."""
        with self.store.read() as con:
            proj = self._project(con, project_id)
        try:
            gen = self.generations.build(project_id, profile_id)
        except (GenerationError, ProviderError) as exc:
            raise Conflict(str(exc), "index_build_failed") from None
        event = {"event_id": self._new_event_id("IDX"), "event_type": "index_generation_switch",
                 "source_id": gen["generation_id"], "version_id": gen["embedding_space_id"],
                 "supersedes_version_id": None}
        with self.store.tx() as con:
            prev = self._switch_generation(con, project_id, gen["generation_id"], profile_id,
                                           "dense index generation switched")
            event["supersedes_version_id"] = prev
            self._record_internal_event(con, project_id, event["event_id"], event["event_type"], gen["generation_id"],
                                        gen["embedding_space_id"], prev, gen["vectors_sha256"])
        summary = {k: gen[k] for k in ("generation_id", "embedding_space_id", "n_vectors", "dimension",
                                       "reused_vectors", "embedded_vectors", "reused_generation")}
        out = self._settle_event(project_id, event, proj["mission"], invoked_via)
        return {"generation": summary, "previous_generation_id": prev, **out}

    def set_retrieval_mode(self, project_id: str, mode: str, invoked_via: str = "cli") -> dict:
        if mode not in RETRIEVAL_MODES:
            raise ValidationFailed(f"mode must be one of {list(RETRIEVAL_MODES)}", "bad_mode")
        with self.store.read() as con:
            proj = self._project(con, project_id)
            s = self.generations.settings(con, project_id)
        if s["retrieval_mode"] == mode:
            return {"unchanged": True, "retrieval_mode": mode}
        if mode == "hybrid" and not s["active_generation_id"]:
            raise Conflict("build an index generation with a ready embedding profile first", "no_index_generation")
        event = {"event_id": self._new_event_id("RET"), "event_type": "retrieval_mode_change",
                 "source_id": "retrieval_mode", "version_id": mode, "supersedes_version_id": s["retrieval_mode"]}
        now = utc_now()
        with self.store.tx() as con:
            con.execute("INSERT OR REPLACE INTO project_settings VALUES (?,?,?,?,?)",
                        (project_id, mode, s["embedding_profile_id"], s["active_generation_id"], now))
            con.execute("UPDATE obligations SET state='recheck_search', reason=?, updated_at=? WHERE project_id=? AND "
                        "state='done'", (f"retrieval mode {s['retrieval_mode']} -> {mode}", now, project_id))
            self._record_internal_event(con, project_id, event["event_id"], event["event_type"], "retrieval_mode", mode,
                                        s["retrieval_mode"], sha256(mode.encode()))
        return {"retrieval_mode": mode, **self._settle_event(project_id, event, proj["mission"], invoked_via)}

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
        active = {r["requirement_id"] for r in proj["mission"]["requirements"]}   # P4-T01b: active requirements only
        cells = [c for c in self._cells(con, project_id) if c["requirement_id"] in active]
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
        return d

    def source_version(self, project_id: str, source_id: str, version_id: str) -> dict:
        with self.store.read() as con:
            origin = self._project(con, project_id)["data_origin"]
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
            orig = con.execute("SELECT media_type, sha256, size_bytes, storage_ref FROM original_artifacts WHERE "
                               "project_id=? AND source_id=? AND version_id=?",
                               (project_id, source_id, version_id)).fetchone()
        return {"source_id": source_id, "version_id": version_id, "title": v["title"], "text": v["text"],
                "sha256": v["sha256"], "candidate_id": v["candidate_id"], "license": v["license"],
                "status": "current" if current == version_id else "historical", "current_version": current,
                "all_versions": versions, "supersedes_version_id": v["supersedes_version_id"],
                "import_event": v["import_event"], "passages": passages, "data_origin": origin,
                "source_kind": v["source_kind"], "origin_path": v["origin_path"],
                "original_artifact": dict(orig) if orig else None}

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
                "data_origin": sv["data_origin"]}

    # ---------------- P4-T01b: requirement lifecycle (Remove / Undo)
    # ``projects.mission_json`` holds the ACTIVE requirements, so planning, comparison, revision processing and the
    # current-cell reads see only active ones. A removed requirement keeps its stable ID, snapshot and content hash in
    # ``requirement_lifecycle``; its obligations are 'retired' and its current assessments become 'retired' history
    # (citations and events kept). Nothing is physically deleted.
    @staticmethod
    def requirement_sha256(req: dict) -> str:
        return sha256(dumps(req).encode("utf-8"))

    def _lifecycle_row(self, con, project_id: str, requirement_id: str) -> dict | None:
        r = con.execute("SELECT * FROM requirement_lifecycle WHERE project_id=? AND requirement_id=?",
                        (project_id, requirement_id)).fetchone()
        return dict(r) if r else None

    def requirement_revision(self, con, project_id: str, requirement_id: str) -> int:
        """Monotonic lifecycle revision of one requirement (0 = never changed since the project was created)."""
        row = self._lifecycle_row(con, project_id, requirement_id)
        return row["lifecycle_revision"] if row else 0

    def mission_revision(self, con, project_id: str) -> int:
        r = con.execute("SELECT revision FROM mission_lifecycle WHERE project_id=?", (project_id,)).fetchone()
        return r[0] if r else 0

    def _advance_lifecycle(self, con, project_id: str, req: dict, state: str, position: int, event_id: str,
                           now: str) -> int:
        rev = self.requirement_revision(con, project_id, req["requirement_id"]) + 1
        con.execute("INSERT INTO requirement_lifecycle VALUES (?,?,?,?,?,?,?,?,?) ON CONFLICT(project_id, requirement_id) "
                    "DO UPDATE SET state=excluded.state, lifecycle_revision=excluded.lifecycle_revision, "
                    "content_sha256=excluded.content_sha256, snapshot_json=excluded.snapshot_json, "
                    "position=excluded.position, updated_at=excluded.updated_at, last_event_id=excluded.last_event_id",
                    (project_id, req["requirement_id"], state, rev, self.requirement_sha256(req), dumps(req), position,
                     now, event_id))
        return rev

    def _advance_mission(self, con, project_id: str, now: str) -> int:
        rev = self.mission_revision(con, project_id) + 1
        con.execute("INSERT OR REPLACE INTO mission_lifecycle VALUES (?,?,?)", (project_id, rev, now))
        return rev

    def _stale_requirement(self, con, project_id: str, req: dict, run_id: str | None = None,
                           cand: str | None = None) -> str | None:
        """Why a result for ``req`` may not be committed now, or None. Checks, inside the caller's transaction:
        the requirement is still active, its content hash is unchanged, and (when the run recorded its plan) its
        lifecycle revision has not moved since planning (this catches remove-then-restore of identical text)."""
        rid = req["requirement_id"]
        mission = self._project(con, project_id)["mission"]
        cur = next((r for r in mission["requirements"] if r["requirement_id"] == rid), None)
        if cur is None:
            return f"requirement {rid} is not active (removed after this work was planned)"
        if self.requirement_sha256(cur) != self.requirement_sha256(req):
            return f"requirement {rid} was edited after this work was planned (content hash changed)"
        if run_id is not None:
            plan = con.execute("SELECT detail_json FROM actions WHERE run_id=? AND action_type='plan_obligation' AND "
                               "candidate_id=? AND requirement_id=? ORDER BY seq DESC LIMIT 1",
                               (run_id, cand, rid)).fetchone()
            planned = json.loads(plan[0]).get("requirement_lifecycle_revision") if plan else None
            now_rev = self.requirement_revision(con, project_id, rid)
            if planned is not None and now_rev != planned:
                return (f"requirement {rid} lifecycle revision moved from {planned} to {now_rev} after this work was "
                        "planned (removed, restored or edited in between)")
        return None

    def _plan_lifecycle(self, con, project_id: str, req: dict) -> dict:
        return {"stale": self._stale_requirement(con, project_id, req),
                "record": {"requirement_lifecycle_revision": self.requirement_revision(con, project_id,
                                                                                       req["requirement_id"]),
                           "requirement_sha256": self.requirement_sha256(req)}}

    def requirement_lifecycle(self, project_id: str, con=None) -> dict:
        """Read model: mission revision, each active requirement's lifecycle revision, and the removed ones."""
        if con is None:
            with self.store.read() as c:
                return self.requirement_lifecycle(project_id, con=c)
        proj = self._project(con, project_id)
        rows = {r["requirement_id"]: dict(r) for r in con.execute(
            "SELECT * FROM requirement_lifecycle WHERE project_id=?", (project_id,))}
        removed = []
        for rid, r in sorted(rows.items(), key=lambda x: (x[1]["updated_at"], x[0])):
            if r["state"] == "removed":
                removed.append({"requirement": json.loads(r["snapshot_json"]), "requirement_id": rid,
                                "lifecycle_revision": r["lifecycle_revision"], "content_sha256": r["content_sha256"],
                                "removed_at": r["updated_at"], "event_id": r["last_event_id"]})
        return {"project_id": project_id, "mission_revision": self.mission_revision(con, project_id),
                "active": {r["requirement_id"]: (rows.get(r["requirement_id"]) or {}).get("lifecycle_revision", 0)
                           for r in proj["mission"]["requirements"]},
                "removed": removed}

    @staticmethod
    def _expected_revision(body: dict | None) -> int | None:
        exp = body.get("expected_revision") if isinstance(body, dict) else None
        if exp is not None and (not isinstance(exp, int) or isinstance(exp, bool) or exp < 0):
            raise ValidationFailed("expected_revision must be a non-negative integer", "bad_expected_revision")
        return exp

    def _lifecycle_project(self, con, project_id: str) -> dict:
        proj = self._project(con, project_id)
        if proj["data_origin"] in LIFECYCLE_FIXED_ORIGINS:
            raise Conflict("the sample and synthetic projects are fixed; create a project for your own requirements",
                           "project_is_fixed")
        return proj

    def archive_requirement(self, project_id: str, requirement_id: str, body: dict | None = None) -> dict:
        """Remove (archive) one active requirement in one transaction. Idempotent: removing a removed requirement
        returns ``already_removed`` and writes nothing."""
        expected = self._expected_revision(body)
        with self.store.tx() as con:
            proj = self._lifecycle_project(con, project_id)
            mission = proj["mission"]
            reqs = list(mission["requirements"])
            pos = next((i for i, r in enumerate(reqs) if r["requirement_id"] == requirement_id), None)
            row = self._lifecycle_row(con, project_id, requirement_id)
            if pos is None:
                if row and row["state"] == "removed":
                    return {"status": "already_removed", "requirement_id": requirement_id,
                            "lifecycle_revision": row["lifecycle_revision"], "event_id": row["last_event_id"],
                            "mission_revision": self.mission_revision(con, project_id)}
                raise NotFound(f"requirement {requirement_id} not found", "requirement_not_found")
            rev = row["lifecycle_revision"] if row else 0
            if expected is not None and expected != rev:
                raise Conflict(f"requirement {requirement_id} is at revision {rev}, not {expected}; reload and retry",
                               "revision_conflict")
            req = reqs.pop(pos)
            now, event_id = utc_now(), self._new_event_id("REQ")
            reason = f"requirement {requirement_id} removed ({event_id})"
            con.execute("UPDATE projects SET mission_json=? WHERE project_id=?",
                        (dumps({**mission, "requirements": reqs}), project_id))
            obligations = [dict(r) for r in con.execute(
                "SELECT candidate_id, state FROM obligations WHERE project_id=? AND requirement_id=? ORDER BY "
                "candidate_id", (project_id, requirement_id))]
            con.execute("UPDATE obligations SET state='retired', reason=?, updated_at=? WHERE project_id=? AND "
                        "requirement_id=?", (reason, now, project_id, requirement_id))
            retired = [r[0] for r in con.execute(
                "SELECT assessment_id FROM assessments WHERE project_id=? AND requirement_id=? AND state='current' "
                "ORDER BY candidate_id", (project_id, requirement_id))]
            for aid in retired:   # history and citations stay; only the 'current' state is withdrawn
                con.execute("UPDATE assessments SET state='retired' WHERE assessment_id=?", (aid,))
                con.execute("INSERT INTO assessment_events VALUES (?,?,?,?,?)", (aid, "retired", reason, None, now))
            new_rev = self._advance_lifecycle(con, project_id, req, "removed", pos, event_id, now)
            mrev = self._advance_mission(con, project_id, now)
            content = self.requirement_sha256(req)
            result = {"event_id": event_id, "requirement_id": requirement_id, "action": "removed",
                      "requirement": req, "content_sha256": content, "lifecycle_revision": new_rev,
                      "previous_lifecycle_revision": rev, "mission_revision": mrev,
                      "retired_obligations": [f"{o['candidate_id']}/{requirement_id} (was {o['state']})"
                                              for o in obligations],
                      "retired_assessments": retired,
                      "note": f"Requirement {requirement_id} removed. Its earlier results stay readable in history; "
                              "Undo restores it with the same ID and text."}
            con.execute("INSERT INTO change_events VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                        (project_id, event_id, "requirement_removed", requirement_id, f"lifecycle-r{new_rev}",
                         f"lifecycle-r{rev}", content, "applied", None, dumps(result), now, now))
        return {"status": "removed", **result}

    def restore_requirement(self, project_id: str, requirement_id: str, body: dict | None = None) -> dict:
        """Undo: restore a removed requirement with its recorded ID and content in one transaction. Its obligations
        are reopened by upsert (the obligation key is (project, candidate, requirement)); its retired assessments
        stay history until a fresh run checks current sources. Idempotent: restoring an active requirement returns
        ``already_active`` and writes nothing."""
        expected = self._expected_revision(body)
        with self.store.tx() as con:
            proj = self._lifecycle_project(con, project_id)
            mission = proj["mission"]
            reqs = list(mission["requirements"])
            row = self._lifecycle_row(con, project_id, requirement_id)
            if any(r["requirement_id"] == requirement_id for r in reqs):
                return {"status": "already_active", "requirement_id": requirement_id,
                        "lifecycle_revision": row["lifecycle_revision"] if row else 0,
                        "mission_revision": self.mission_revision(con, project_id)}
            if not row or row["state"] != "removed":
                raise NotFound(f"requirement {requirement_id} not found", "requirement_not_found")
            if expected is not None and expected != row["lifecycle_revision"]:
                raise Conflict(f"requirement {requirement_id} is at revision {row['lifecycle_revision']}, not "
                               f"{expected}; reload and retry", "revision_conflict")
            if len(reqs) >= MAX_REQUIREMENTS:
                raise ValidationFailed(f"at most {MAX_REQUIREMENTS} requirements per project", "too_many_requirements")
            req = json.loads(row["snapshot_json"])
            if req.get("requirement_id") != requirement_id or self.requirement_sha256(req) != row["content_sha256"]:
                raise ValidationFailed("stored requirement snapshot does not match its hash", "lifecycle_integrity")
            pos = min(row["position"], len(reqs))
            reqs.insert(pos, req)
            now, event_id = utc_now(), self._new_event_id("REQ")
            reason = f"requirement {requirement_id} restored ({event_id})"
            con.execute("UPDATE projects SET mission_json=? WHERE project_id=?",
                        (dumps({**mission, "requirements": reqs}), project_id))
            reopened = []
            for c in mission["candidates"]:
                con.execute("INSERT INTO obligations VALUES (?,?,?,?,?,?) ON CONFLICT(project_id, candidate_id, "
                            "requirement_id) DO UPDATE SET state=excluded.state, reason=excluded.reason, "
                            "updated_at=excluded.updated_at",
                            (project_id, c["candidate_id"], requirement_id, "open", reason, now))
                reopened.append(f"{c['candidate_id']}/{requirement_id}")
            historical = [r[0] for r in con.execute(
                "SELECT assessment_id FROM assessments WHERE project_id=? AND requirement_id=? ORDER BY created_at",
                (project_id, requirement_id))]
            new_rev = self._advance_lifecycle(con, project_id, req, "active", pos, event_id, now)
            mrev = self._advance_mission(con, project_id, now)
            result = {"event_id": event_id, "requirement_id": requirement_id, "action": "restored",
                      "requirement": req, "content_sha256": row["content_sha256"], "lifecycle_revision": new_rev,
                      "previous_lifecycle_revision": row["lifecycle_revision"], "mission_revision": mrev,
                      "reopened_obligations": reopened, "historical_assessments_kept": historical,
                      "note": f"Requirement {requirement_id} restored; {len(reopened)} obligation(s) reopened. Earlier "
                              "results stay in history; run the comparison to assess it against current sources."}
            con.execute("INSERT INTO change_events VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                        (project_id, event_id, "requirement_restored", requirement_id, f"lifecycle-r{new_rev}",
                         f"lifecycle-r{row['lifecycle_revision']}", row["content_sha256"], "applied", None,
                         dumps(result), now, now))
        return {"status": "restored", **result}
