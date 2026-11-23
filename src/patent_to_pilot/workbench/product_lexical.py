"""P4-T01a: product-profile lexical index and Thai-aware retrieval (owner plan of 23 Nov 2026, section 4).

A NEW derived FTS5 table, ``passage_fts_th_v1``, holds the analyzer's segmented derivative of every current passage. The
canonical quote stays in ``passages`` / ``source_versions``; citations, quotes and highlight offsets always come from
that canonical text. The legacy ``passage_fts`` table (``unicode61``) and every path that reads it -- the G01 sample's
assessments, the frozen P0-T06 / P2 trace and relation-search routes, ``Workflow.relation_action`` and the advanced
``terms`` / ``phrase`` / ``literal`` search modes -- are unchanged.

Product profile (``PROFILE``) users:

* indexing: ``EvidenceCore._make_current`` calls ``on_source_current`` inside its own transaction, so a version is never
  current without its derivative rows (incremental replace of that source, or a full project rebuild);
* the Workbench Search default mode ``auto`` (``auto_search``);
* requirement matching of owner projects (``requirement_hits``, called from ``EvidenceCore._search``);
* highlighting (``marks``).

Index state is explicit: ``lexical_index_state`` names the active index per project, its generation, the analyzer
identity (name, version, PyThaiNLP version, dictionary hash, normalization) and the corpus revision it was built from;
``lexical_index_generations`` keeps one history row per generation. A full rebuild runs in one transaction: the old
derivative stays active until the new one commits. A derivative that is missing, stale, or built by another analyzer
identity is rebuilt on demand before it is searched. Without PyThaiNLP the product routes fall back to the legacy index
and say so.
"""
from __future__ import annotations

import re
import time

from patent_to_pilot.workbench import thai_analyzer as TA
from patent_to_pilot.workbench.store import dumps, utc_now

TASK_ID = "P4-T01a"
PROFILE = "product-thai-lexical-v1"
INDEX_NAME = "passage_fts_th_v1"
LEGACY_INDEX = "passage_fts"
SCHEMA = f"""
CREATE VIRTUAL TABLE IF NOT EXISTS {INDEX_NAME} USING fts5(
  project_id UNINDEXED, source_id UNINDEXED, version_id UNINDEXED, passage_id UNINDEXED, candidate_id UNINDEXED,
  segmentation UNINDEXED, body, tokenize = "{TA.FTS_TOKENIZE}");
CREATE TABLE IF NOT EXISTS lexical_index_state (
  project_id TEXT PRIMARY KEY, active_index TEXT NOT NULL, generation INTEGER NOT NULL, analyzer_id TEXT NOT NULL,
  analyzer_json TEXT NOT NULL, corpus_revision TEXT NOT NULL, n_passages INTEGER NOT NULL,
  alignment_fallbacks INTEGER NOT NULL, status TEXT NOT NULL, reason TEXT NOT NULL, updated_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS lexical_index_generations (
  project_id TEXT NOT NULL, generation INTEGER NOT NULL, index_name TEXT NOT NULL, analyzer_id TEXT NOT NULL,
  corpus_revision TEXT NOT NULL, n_passages INTEGER NOT NULL, alignment_fallbacks INTEGER NOT NULL, kind TEXT NOT NULL,
  reason TEXT NOT NULL, created_at TEXT NOT NULL, PRIMARY KEY (project_id, generation));
"""
SHORT_QUERY_CHARS = 3          # FTS5 trigram MATCH needs 3 characters; shorter input goes to the substring route too
FALLBACK_SCAN_MAX = 20_000     # bounded substring route: at most this many current passages are scanned per query
IDENTIFIER_CANDIDATES = 200    # FTS5 candidates verified per recognised identifier
MAX_QUERY_IDENTIFIERS = 5
RANKING_RULE = ("route order identifier > all_words (or phrase) > any_word > substring; inside a route FTS5 BM25 "
                "ascending (lower is better) or, for substring, source_id, version_id and passage start; ties by "
                "source_id, version_id, passage_id; a passage keeps its first (best) route")
FALLBACK_RULE = (f"bounded substring check of the whole query (fold-v1, case-insensitive for ASCII, Thai digits = ASCII "
                 f"digits) over at most {FALLBACK_SCAN_MAX} current passages, run when: short_query (< "
                 f"{SHORT_QUERY_CHARS} non-space characters), no_index_terms, no_word_hits, thai_partial_coverage (Thai "
                 "query with fewer word-index results than the limit: a typed word can sit inside a longer dictionary "
                 "word), or analyzer_unavailable")
_WORD = re.compile(r"\w+", re.UNICODE)


def _corpus(con, project_id: str) -> list[str]:
    return sorted(f"{r[0]}@{r[1]}" for r in con.execute(
        "SELECT source_id, version_id FROM current_sources WHERE project_id=?", (project_id,)))


def _revision(versions: list[str]) -> str:
    import hashlib
    return hashlib.sha256(dumps(versions).encode("utf-8")).hexdigest()[:16]


def _quoted(terms) -> list[str]:
    # every term is a run of letters / numbers / marks / private-use characters only, so it contains no '"' and no
    # FTS5 operator character; quoting makes AND / OR / NOT / NEAR typed by a user plain words
    return [f'"{t}"' for t in terms]


def _phrase(terms) -> str:
    return '"' + " ".join(terms) + '"'


def _stopwords() -> frozenset:
    from patent_to_pilot.workbench.core import TERM_STOPWORDS   # English only; no Thai word is ever dropped
    return TERM_STOPWORDS


class ProductLexical:
    def __init__(self, store) -> None:
        self.store = store
        con = store.connect()
        try:   # additive migration: new tables only; nothing existing is altered
            con.executescript(SCHEMA)
        finally:
            con.close()

    # ------------------------------------------------------------------ state
    @staticmethod
    def state(con, project_id: str) -> dict | None:
        r = con.execute("SELECT * FROM lexical_index_state WHERE project_id=?", (project_id,)).fetchone()
        return dict(r) if r else None

    def status(self, con, project_id: str) -> dict:
        st = self.state(con, project_id)
        try:
            an = TA.analyzer()
            analyzer = {"available": True, "identity_id": an.identity_id}
        except TA.AnalyzerUnavailable as exc:
            analyzer = {"available": False, "reason": str(exc)}
        out = {"profile": PROFILE, "index": INDEX_NAME, "analyzer": analyzer}
        if st:
            out.update({k: st[k] for k in ("active_index", "generation", "analyzer_id", "corpus_revision",
                                            "n_passages", "alignment_fallbacks", "status", "reason", "updated_at")})
        else:
            out.update(active_index=LEGACY_INDEX, generation=0, status="not_built")
        return out

    def _set_state(self, con, project_id: str, generation: int, an, revision: str, n: int, fallbacks: int, kind: str,
                   reason: str) -> None:
        now = utc_now()
        con.execute("INSERT OR REPLACE INTO lexical_index_state VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                    (project_id, INDEX_NAME, generation, an.identity_id, dumps(an.identity), revision, n, fallbacks,
                     "active", reason, now))
        con.execute("INSERT INTO lexical_index_generations VALUES (?,?,?,?,?,?,?,?,?,?)",
                    (project_id, generation, INDEX_NAME, an.identity_id, revision, n, fallbacks, kind, reason, now))

    def _insert(self, con, project_id: str, rows, an) -> int:
        fallbacks = 0
        for sid, vid, pid, cand, quote in rows:
            body, fell_back = an.body(quote)
            fallbacks += fell_back
            con.execute(f"INSERT INTO {INDEX_NAME} VALUES (?,?,?,?,?,?,?)",
                        (project_id, sid, vid, pid, cand, "fallback_runs" if fell_back else TA.ENGINE, body))
        return fallbacks

    def _counts(self, con, project_id: str) -> tuple[int, int]:
        r = con.execute(f"SELECT COUNT(*), SUM(segmentation='fallback_runs') FROM {INDEX_NAME} WHERE project_id=?",
                        (project_id,)).fetchone()
        return r[0], r[1] or 0

    def _rebuild(self, con, project_id: str, an, reason: str) -> dict:
        """Full rebuild of one project's derivative inside the caller's transaction (all-or-nothing)."""
        st = self.state(con, project_id)
        con.execute(f"DELETE FROM {INDEX_NAME} WHERE project_id=?", (project_id,))
        rows = con.execute(
            "SELECT c.source_id, c.version_id, p.passage_id, v.candidate_id, p.quote FROM current_sources c "
            "JOIN source_versions v ON v.project_id=c.project_id AND v.source_id=c.source_id AND v.version_id=c.version_id "
            "JOIN passages p ON p.project_id=c.project_id AND p.source_id=c.source_id AND p.version_id=c.version_id "
            "WHERE c.project_id=? ORDER BY c.source_id, p.start_char", (project_id,)).fetchall()
        self._insert(con, project_id, rows, an)
        n, fb = self._counts(con, project_id)
        self._set_state(con, project_id, (st["generation"] if st else 0) + 1, an, _revision(_corpus(con, project_id)),
                        n, fb, "full_rebuild", reason)
        return self.state(con, project_id)

    def rebuild(self, project_id: str, reason: str = "explicit rebuild") -> dict:
        an = TA.analyzer()
        with self.store.tx() as con:
            return self._rebuild(con, project_id, an, reason)

    def on_source_current(self, con, project_id: str, source_id: str, version_id: str, candidate_id: str,
                          passages: list[dict]) -> None:
        """Called by ``EvidenceCore._make_current`` inside its transaction, after the current pointer moved."""
        try:
            an = TA.analyzer()
        except TA.AnalyzerUnavailable as exc:
            con.execute(f"DELETE FROM {INDEX_NAME} WHERE project_id=? AND source_id=?", (project_id, source_id))
            con.execute("UPDATE lexical_index_state SET status='stale', reason=?, updated_at=? WHERE project_id=?",
                        (f"{source_id}@{version_id} became current without the analyzer ({exc})", utc_now(),
                         project_id))
            return
        st = self.state(con, project_id)
        if st and st["status"] == "active" and st["analyzer_id"] == an.identity_id and st["active_index"] == INDEX_NAME:
            con.execute(f"DELETE FROM {INDEX_NAME} WHERE project_id=? AND source_id=?", (project_id, source_id))
            self._insert(con, project_id, [(source_id, version_id, p["passage_id"], candidate_id, p["quote"])
                                           for p in passages], an)
            versions = _corpus(con, project_id)
            indexed = sorted(f"{r[0]}@{r[1]}" for r in con.execute(
                f"SELECT DISTINCT source_id, version_id FROM {INDEX_NAME} WHERE project_id=?", (project_id,)))
            if indexed == versions:   # the derivative still equals the current scope: incremental is exact
                n, fb = self._counts(con, project_id)
                self._set_state(con, project_id, st["generation"] + 1, an, _revision(versions), n, fb, "incremental",
                                f"{source_id}@{version_id} became current")
                return
        self._rebuild(con, project_id, an, f"{source_id}@{version_id} became current; project derivative rebuilt")

    def ensure(self, project_id: str):
        """Return (state, analyzer), rebuilding the derivative first when it is missing or stale. Raises
        ``AnalyzerUnavailable`` without PyThaiNLP."""
        an = TA.analyzer()

        def why(con) -> str | None:
            st = self.state(con, project_id)
            if st is None:
                return "no derivative index for this project yet (existing store or new project)"
            if st["active_index"] != INDEX_NAME or st["status"] != "active":
                return f"derivative index is {st['status']} ({st['reason']})"
            if st["analyzer_id"] != an.identity_id:
                return f"analyzer identity changed ({st['analyzer_id']} -> {an.identity_id})"
            if st["corpus_revision"] != _revision(_corpus(con, project_id)):
                return "current sources changed since the derivative was built"
            return None
        with self.store.read() as con:
            reason = why(con)
            if reason is None:
                return self.state(con, project_id), an
        with self.store.tx() as con:
            reason = why(con)    # re-checked under the write lock
            st = self._rebuild(con, project_id, an, f"on demand: {reason}") if reason else self.state(con, project_id)
        return st, an

    # ------------------------------------------------------------------ retrieval
    @staticmethod
    def _fts(con, table: str, project_id: str, match: str, limit: int, candidate_id: str | None,
             current: dict) -> list[dict]:
        sql = (f"SELECT source_id, version_id, passage_id, candidate_id, bm25({table}) AS score FROM {table} "
               f"WHERE {table} MATCH ? AND project_id=?")
        args: list = [match, project_id]
        if candidate_id is not None:
            sql += " AND candidate_id=?"
            args.append(candidate_id)
        out = []
        for r in con.execute(sql + " ORDER BY score, source_id, version_id, passage_id LIMIT ?", (*args, limit)):
            if current.get(r["source_id"]) != r["version_id"]:
                raise RuntimeError(f"{table} contains a non-current version")
            out.append({"source_id": r["source_id"], "version_id": r["version_id"], "passage_id": r["passage_id"],
                        "candidate_id": r["candidate_id"], "bm25": round(r["score"], 6)})
        return out

    @staticmethod
    def _quote(con, project_id: str, h: dict) -> str:
        return con.execute("SELECT quote FROM passages WHERE project_id=? AND source_id=? AND version_id=? AND "
                           "passage_id=?", (project_id, h["source_id"], h["version_id"], h["passage_id"])).fetchone()[0]

    @staticmethod
    def _substring(con, project_id: str, needle: str, want: int, candidate_id: str | None, skip: set) -> tuple:
        folded = TA.fold(needle)
        sql = ("SELECT c.source_id, c.version_id, p.passage_id, v.candidate_id, p.quote FROM current_sources c "
               "JOIN source_versions v ON v.project_id=c.project_id AND v.source_id=c.source_id AND "
               "v.version_id=c.version_id JOIN passages p ON p.project_id=c.project_id AND p.source_id=c.source_id AND "
               "p.version_id=c.version_id WHERE c.project_id=?")
        args: list = [project_id]
        if candidate_id is not None:
            sql += " AND v.candidate_id=?"
            args.append(candidate_id)
        rows = con.execute(sql + " ORDER BY c.source_id, c.version_id, p.start_char LIMIT ?",
                           (*args, FALLBACK_SCAN_MAX + 1)).fetchall()
        capped = len(rows) > FALLBACK_SCAN_MAX
        out = []
        for r in rows[:FALLBACK_SCAN_MAX]:
            key = (r["source_id"], r["version_id"], r["passage_id"])
            if key in skip or not folded or TA.fold(r["quote"]).find(folded) < 0:
                continue
            out.append({"source_id": key[0], "version_id": key[1], "passage_id": key[2],
                        "candidate_id": r["candidate_id"], "bm25": None})
            if len(out) >= want:
                break
        return out, min(len(rows), FALLBACK_SCAN_MAX), capped

    def retrieve(self, con, project_id: str, text: str, *, limit: int, candidate_id: str | None = None,
                 mode: str = "auto", state: dict | None = None, an=None) -> tuple[list[dict], dict]:
        """Thai-aware retrieval over the current scope. ``mode``: ``auto`` (identifiers, all words, any word) or
        ``phrase``; both end with the bounded substring fallback when a declared condition holds. ``an=None`` means
        the analyzer is unavailable: the legacy index is searched with the legacy terms expression."""
        current = {r[0]: r[1] for r in con.execute(
            "SELECT source_id, version_id FROM current_sources WHERE project_id=?", (project_id,))}
        out: list[dict] = []
        seen: set = set()
        issued: list[dict] = []

        def add(rows: list[dict], route: str, match: str, **extra) -> None:
            kept = 0
            for r in rows:
                key = (r["source_id"], r["version_id"], r["passage_id"])
                if key in seen or len(out) >= limit:
                    continue
                seen.add(key)
                out.append({**r, "route": route})
                kept += 1
            issued.append({"route": route, "match": match, "returned": len(rows), "kept": kept, **extra})

        query_terms: list[str] = []
        idents: list[dict] = []
        if an is not None:
            table = INDEX_NAME
            terms, fell_back = an.terms(text)
            ordered = [t.norm for t in terms]
            query_terms = list(dict.fromkeys(ordered))
            if mode == "auto":
                for ident in TA.identifiers(text)[:MAX_QUERY_IDENTIFIERS]:
                    it = [t.norm for t in an.terms(ident.text)[0]]
                    idents.append({"text": ident.text, "key": ident.key, "start": ident.start, "end": ident.end})
                    if not it:
                        continue
                    match = _phrase(it)
                    rows = [r for r in self._fts(con, table, project_id, match, IDENTIFIER_CANDIDATES, candidate_id,
                                                 current)
                            if any(TA.key_matches(ident.key, f.key)
                                   for f in TA.identifiers(self._quote(con, project_id, r)))]
                    add(rows, "identifier", match, key=ident.key)
            if query_terms:
                if mode == "phrase":
                    add(self._fts(con, table, project_id, _phrase(ordered), limit + len(out), candidate_id, current),
                        "phrase", _phrase(ordered))
                else:
                    stop = _stopwords()
                    kept = [t for t in query_terms if t not in stop] or query_terms
                    if len(kept) > 1:
                        m = " AND ".join(_quoted(kept))
                        add(self._fts(con, table, project_id, m, limit + len(out), candidate_id, current),
                            "all_words", m)
                    m = " OR ".join(_quoted(kept))
                    add(self._fts(con, table, project_id, m, limit + len(out), candidate_id, current), "any_word", m)
            analyzer = {"identity_id": an.identity_id, "alignment_fallback": fell_back}
        else:
            table = LEGACY_INDEX
            fell_back = None
            from patent_to_pilot.workbench.core import ValidationFailed, fts_terms
            try:
                m = fts_terms(text)
            except ValidationFailed:
                m = None
            if m:
                query_terms = [t for t in dict.fromkeys(w.lower() for w in _WORD.findall(text))]
                add(self._fts(con, table, project_id, m, limit, candidate_id, current), "legacy_any_word", m)
            analyzer = {"identity_id": None, "unavailable": True}
        reasons = []
        if an is None:
            reasons.append("analyzer_unavailable")
        if len("".join(text.split())) < SHORT_QUERY_CHARS:
            reasons.append("short_query")
        if not query_terms:
            reasons.append("no_index_terms")
        elif not out:
            reasons.append("no_word_hits")
        if TA.THAI_SCRIPT.search(text) and len(out) < limit:
            reasons.append("thai_partial_coverage")
        fallback = {"triggered": bool(reasons), "reasons": reasons, "needle": text.strip(), "rule": FALLBACK_RULE,
                    "scan_cap": FALLBACK_SCAN_MAX, "scanned": 0, "capped": False, "returned": 0}
        if reasons and len(out) < limit and text.strip():
            rows, scanned, capped = self._substring(con, project_id, text.strip(), limit - len(out), candidate_id, seen)
            fallback.update(scanned=scanned, capped=capped, returned=len(rows))
            add(rows, "substring", text.strip())
        st = state or {}
        trace = {"profile": PROFILE, "index": table, "generation": st.get("generation"),
                 "corpus_revision": st.get("corpus_revision"), "analyzer": analyzer, "mode": mode,
                 "query_terms": query_terms, "identifiers": idents, "issued": issued, "fallback": fallback,
                 "ranking_rule": RANKING_RULE}
        return out, trace

    # ------------------------------------------------------------------ highlighting
    @staticmethod
    def marks(an, quote: str, trace: dict) -> list[tuple[int, int]]:
        """Offsets inside ``quote`` (canonical text) of what matched: query terms (same analyzer and fold as the
        index), recognised identifiers with the same key, and literal occurrences of the whole query (fold-v1)."""
        spans = []
        want = set(trace["query_terms"])
        if an is not None:
            spans += [(t.start, t.end) for t in an.terms(quote)[0] if t.norm in want]
        else:
            spans += [(m.start(), m.end()) for m in _WORD.finditer(quote) if m.group(0).lower() in want]
        for q in trace["identifiers"]:
            spans += [(f.start, f.end) for f in TA.identifiers(quote) if TA.key_matches(q["key"], f.key)]
        needle = TA.fold(trace["fallback"]["needle"])
        if needle:
            hay, i = TA.fold(quote), 0
            while (i := hay.find(needle, i)) >= 0:
                spans.append((i, i + len(needle)))
                i += len(needle)
        merged: list[list[int]] = []
        for a, b in sorted(spans):
            if merged and a <= merged[-1][1]:
                merged[-1][1] = max(merged[-1][1], b)
            else:
                merged.append([a, b])
        return [(a, b) for a, b in merged]

    # ------------------------------------------------------------------ owner requirement matching
    def requirement_hits(self, con, project_id: str, candidate_id: str, query: str, k: int, match: str | None,
                         ctx: dict | None = None) -> list[dict] | None:
        """Requirement matching of an owner project through the product analyzer. ``match`` is the requirement's
        legacy expression (``requirement_match``): its terms form maps to ``auto``, its phrase form to ``phrase``. Any
        other expression, or a missing analyzer, returns None and the caller keeps the legacy index."""
        from patent_to_pilot.workbench.core import ValidationFailed, fts_phrase, fts_terms

        def expr(fn):
            try:
                return fn(query)
            except ValidationFailed:
                return None
        if match is not None and match == expr(fts_terms):
            mode = "auto"
        elif match is None or match == expr(fts_phrase):
            mode = "phrase"
        else:
            return None
        try:
            st, an = self.ensure(project_id)
        except TA.AnalyzerUnavailable:
            return None
        hits, trace = self.retrieve(con, project_id, query, limit=k, candidate_id=candidate_id, mode=mode, state=st,
                                    an=an)
        if ctx is not None:
            ctx["last_lexical"] = {k_: trace[k_] for k_ in ("profile", "index", "generation", "corpus_revision", "mode",
                                                            "query_terms", "issued", "fallback")}
            ctx["last_lexical"]["analyzer"] = an.identity_id
        return [{"source_id": h["source_id"], "version_id": h["version_id"], "passage_id": h["passage_id"],
                 "score": h["bm25"], "lexical": {"index": INDEX_NAME, "analyzer": an.identity_id, "route": h["route"]}}
                for h in hits]


# ---------------------------------------------------------------------- Workbench Search, default mode
def auto_search(workflow, project_id: str, proj: dict, query: str, candidate_id: str | None, limit: int) -> dict:
    """The one-box Workbench search: automatic Thai handling, canonical quotes, exact offsets."""
    from patent_to_pilot.workbench.core import OFFSET_CONVENTION
    pl = workflow.core.product_lexical
    notes = []
    t0 = time.perf_counter()
    try:
        st, an = pl.ensure(project_id)
    except TA.AnalyzerUnavailable as exc:
        st, an = None, None
        notes.append("Thai word segmentation (PyThaiNLP, optional extra 'thai') is not installed here, so the legacy "
                     f"word index was searched and a bounded text check was added ({exc}).")
    texts: dict = {}
    with workflow.store.read() as con:
        index = workflow._index(con, project_id)
        hits, trace = pl.retrieve(con, project_id, query, limit=limit, candidate_id=candidate_id, state=st, an=an)
        results = []
        for rank, h in enumerate(hits, start=1):
            p = workflow._passage(con, project_id, h["source_id"], h["version_id"], h["passage_id"], texts)
            marks = pl.marks(an, p["quote"], trace)
            results.append({"rank": rank, **p, "score_bm25": h["bm25"], "route": h["route"],
                            "data_origin": proj["data_origin"], "offset_convention": OFFSET_CONVENTION,
                            "matches": [{"start_char": p["start_char"] + a, "end_char": p["start_char"] + b}
                                        for a, b in marks],
                            **workflow._snippet(p, marks)})
        index["lexical_index"] = pl.status(con, project_id)
    elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)
    fb = trace["fallback"]
    n_sub = sum(1 for h in hits if h["route"] == "substring")
    if n_sub:
        notes.append(f"{n_sub} result(s) were found as text inside longer words by the bounded text check "
                     f"(reason: {', '.join(fb['reasons'])}).")
    if fb["capped"]:
        notes.append(f"The bounded text check stopped after {fb['scan_cap']} passages.")
    if not index["passages"]:
        notes.append("This project has no searchable passages yet. Add documents on the Evidence page.")
    elif not results:
        notes.append("No current passage matched. Try fewer words, or the Advanced modes.")
    primary = next((x["match"] for x in trace["issued"] if x["route"] in ("all_words", "any_word", "phrase",
                                                                         "legacy_any_word")), None)
    route = (f"{PROFILE}: identifiers + Thai word index {trace['index']}"
             + (f" (generation {trace['generation']})" if trace["generation"] else "")
             + " + bounded substring fallback")
    return {"task": workflow_task(), "subtask": TASK_ID, "project_id": project_id, "query": query, "mode": "auto",
            "route": route, "fts_match": primary, "candidate_id": candidate_id, "limit": limit, "index": index,
            "results": results, "result_count": len(results), "notes": notes, "lexical_trace": trace,
            "elapsed_ms": elapsed_ms, "paid_model_calls": 0, "remote_calls": 0}


def workflow_task() -> str:
    from patent_to_pilot.workbench.workflow import TASK_ID as WF_TASK
    return WF_TASK


def capability() -> dict:
    try:
        an = TA.analyzer()
        return {"profile": PROFILE, "index": INDEX_NAME, "state": "active", "analyzer": an.identity}
    except TA.AnalyzerUnavailable as exc:
        return {"profile": PROFILE, "index": INDEX_NAME, "state": "analyzer_unavailable", "reason": str(exc),
                "fallback": f"legacy {LEGACY_INDEX} plus the bounded substring check"}
