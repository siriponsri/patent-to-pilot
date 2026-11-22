"""Index generations for dense retrieval (G02).

* **Embedding-space identity** binds adapter, model ID, served model name/digest, dimension, normalisation,
  pooling and the query/document prefixes. Vectors from different spaces are never compared.
* **Index-generation identity** adds the parser profile, the passage rules and a manifest of the exact current
  passages (source, version, passage, offsets, text hash). Any corpus or chunking change gives a new generation.
* A new generation is built beside the old one, validated, then activated by switching a pointer. Old
  generations are retired, never deleted or overwritten. Vectors of unchanged passages are reused only from a
  generation in the same embedding space.

Vectors are stored as little-endian float32 files under ``<data_dir>/generations/<generation_id>/``. Search is
exact cosine over L2-normalised vectors (no approximate index), which is sufficient for Workbench-sized projects.
"""
from __future__ import annotations

from array import array
import hashlib
import json
import math
from pathlib import Path
import sys

from patent_to_pilot.workbench.profiles import ProviderRegistry
from patent_to_pilot.workbench.providers import ProviderError
from patent_to_pilot.workbench.store import Store, dumps, utc_now

NORMALIZATION = "l2_by_ptp"
POOLING = "provider_default"
PASSAGE_RULES = {"authored_technical_note": "fixture_heading_passages_v1",
                 "owner_markdown": "paragraph_blocks_v1", "owner_text": "paragraph_blocks_v1"}


def _sha(obj) -> str:
    return hashlib.sha256(dumps(obj).encode("utf-8")).hexdigest()


def text_sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class GenerationError(Exception):
    pass


class GenerationManager:
    def __init__(self, store: Store, registry: ProviderRegistry, parser_profile: str) -> None:
        self.store, self.registry, self.parser_profile = store, registry, parser_profile
        self.root = store.data_dir / "generations"
        self._cache: dict[str, tuple[list[dict], list[array]]] = {}

    # ---------------- identities
    def corpus_rows(self, con, project_id: str) -> list[dict]:
        return [dict(r) for r in con.execute(
            "SELECT p.source_id, p.version_id, p.passage_id, p.start_char, p.end_char, p.quote, v.candidate_id, "
            "v.source_kind FROM current_sources c JOIN passages p ON p.project_id=c.project_id AND "
            "p.source_id=c.source_id AND p.version_id=c.version_id JOIN source_versions v ON "
            "v.project_id=c.project_id AND v.source_id=c.source_id AND v.version_id=c.version_id "
            "WHERE c.project_id=? ORDER BY p.source_id, p.version_id, p.start_char, p.passage_id", (project_id,))]

    def corpus_manifest(self, rows: list[dict]) -> str:
        return _sha([[r["source_id"], r["version_id"], r["passage_id"], r["start_char"], r["end_char"],
                      text_sha(r["quote"])] for r in rows])

    def embedding_space(self, profile_id: str) -> dict:
        p = self.registry.get(profile_id)
        last = self.registry.last_check(profile_id) or {}
        facts = last.get("facts", {})
        return {"adapter": p.adapter, "model_id": p.model_id, "served_model_name": facts.get("served_model_name"),
                "model_digest": facts.get("model_digest"), "requested_dimensions": p.dimensions,
                "dimension": facts.get("dimension"), "normalization": NORMALIZATION, "pooling": POOLING,
                "query_prefix": p.query_prefix, "document_prefix": p.document_prefix}

    def identity(self, con, project_id: str, profile_id: str) -> tuple[dict, list[dict]]:
        rows = self.corpus_rows(con, project_id)
        space = self.embedding_space(profile_id)
        ident = {"project_id": project_id, "embedding_space": space, "embedding_space_id": _sha(space)[:16],
                 "parser_profile": self.parser_profile,
                 "passage_rules": sorted({PASSAGE_RULES.get(r["source_kind"], r["source_kind"]) for r in rows}),
                 "corpus_manifest_sha256": self.corpus_manifest(rows), "passages": len(rows)}
        return ident, rows

    # ---------------- settings and status
    def settings(self, con, project_id: str) -> dict:
        r = con.execute("SELECT * FROM project_settings WHERE project_id=?", (project_id,)).fetchone()
        return dict(r) if r else {"project_id": project_id, "retrieval_mode": "lexical", "embedding_profile_id": None,
                                  "active_generation_id": None, "updated_at": None}

    def generation(self, con, generation_id: str) -> dict | None:
        r = con.execute("SELECT * FROM index_generations WHERE generation_id=?", (generation_id,)).fetchone()
        if not r:
            return None
        d = dict(r)
        d["identity"] = json.loads(d.pop("identity_json"))
        d["detail"] = json.loads(d.pop("detail_json") or "null")
        return d

    def freshness(self, con, project_id: str, gen: dict | None) -> str:
        """fresh | stale_corpus | none"""
        if gen is None:
            return "none"
        rows = self.corpus_rows(con, project_id)
        return "fresh" if gen["identity"]["corpus_manifest_sha256"] == self.corpus_manifest(rows) else "stale_corpus"

    def status(self, project_id: str) -> dict:
        with self.store.read() as con:
            s = self.settings(con, project_id)
            active = self.generation(con, s["active_generation_id"]) if s["active_generation_id"] else None
            gens = [self.generation(con, r[0]) for r in con.execute(
                "SELECT generation_id FROM index_generations WHERE project_id=? ORDER BY created_at", (project_id,))]
            fresh = self.freshness(con, project_id, active)
        return {"project_id": project_id, "retrieval_mode": s["retrieval_mode"],
                "embedding_profile_id": s["embedding_profile_id"], "active_generation_id": s["active_generation_id"],
                "active_freshness": fresh, "generations": gens}

    # ---------------- build / activate
    def build(self, project_id: str, profile_id: str) -> dict:
        """Build (or reuse) the generation for the project's current corpus and this embedding profile.
        Does not activate it. Returns the generation record plus counts of reused and newly embedded vectors."""
        profile = self.registry.get(profile_id)
        if profile.role != "embedding":
            raise GenerationError(f"{profile_id} is not an embedding profile")
        if not self.registry.is_ready(profile_id):
            raise GenerationError(f"run a passing connection check for {profile_id} first "
                                  f"(status: {self.registry.status(profile_id)})")
        with self.store.read() as con:
            ident, rows = self.identity(con, project_id, profile_id)
        if not rows:
            raise GenerationError("the project has no current passages to index")
        gen_id = "gen-" + _sha(ident)[:16]
        with self.store.read() as con:
            existing = self.generation(con, gen_id)
        if existing and existing["status"] in ("ready", "active", "retired"):
            return {**existing, "reused_generation": True}
        reuse = self._reusable_vectors(project_id, ident["embedding_space_id"])
        vectors: list[list[float] | None] = [None] * len(rows)
        todo = []
        for i, r in enumerate(rows):
            v = reuse.get(text_sha(r["quote"]))
            if v is not None:
                vectors[i] = v
            else:
                todo.append(i)
        client = self.registry.client(profile_id, profile)
        if todo:
            try:
                fresh = client.embed([rows[i]["quote"] for i in todo], "document")
            except ProviderError as exc:
                raise GenerationError(f"embedding failed ({exc.kind}): {exc}") from None
            for i, v in zip(todo, fresh):
                vectors[i] = v
        dims = {len(v) for v in vectors if v is not None}
        if len(dims) != 1 or any(v is None for v in vectors):
            raise GenerationError(f"validation failed: inconsistent or missing vectors (dimensions {sorted(dims)})")
        dim = dims.pop()
        expected = ident["embedding_space"]["dimension"]
        if expected and expected != dim:
            raise GenerationError(f"validation failed: dimension {dim} differs from the checked dimension {expected}")
        for v in vectors:
            n = math.sqrt(sum(x * x for x in v))
            if not math.isfinite(n) or abs(n - 1.0) > 1e-3:
                raise GenerationError("validation failed: a vector is not finite or not unit length")
        folder = self.root / gen_id
        folder.mkdir(parents=True, exist_ok=True)
        flat = array("f", [x for v in vectors for x in v])
        if sys.byteorder != "little":
            flat.byteswap()
        blob = flat.tobytes()
        (folder / "vectors.f32").write_bytes(blob)
        manifest = {"generation_id": gen_id, "identity": ident, "dimension": dim, "dtype": "float32",
                    "byteorder": "little",
                    "rows": [{k: r[k] for k in ("source_id", "version_id", "passage_id", "candidate_id")}
                             | {"text_sha256": text_sha(r["quote"])} for r in rows]}
        (folder / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
        vec_sha = hashlib.sha256(blob).hexdigest()
        with self.store.tx() as con:
            con.execute("INSERT INTO index_generations VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                        (gen_id, project_id, profile_id, ident["embedding_space_id"], dumps(ident), "ready", len(rows),
                         dim, str(folder.relative_to(self.store.data_dir).as_posix()), vec_sha, len(rows) - len(todo),
                         len(todo), utc_now(), None, None, dumps({"validated": ["count", "dimension", "unit_norm"]})))
        with self.store.read() as con:
            return {**self.generation(con, gen_id), "reused_generation": False}

    def _reusable_vectors(self, project_id: str, space_id: str) -> dict[str, list[float]]:
        out: dict[str, list[float]] = {}
        with self.store.read() as con:
            ids = [r[0] for r in con.execute("SELECT generation_id FROM index_generations WHERE project_id=? AND "
                                             "embedding_space_id=? AND status IN ('ready','active','retired') "
                                             "ORDER BY created_at", (project_id, space_id))]
        for gid in ids:
            rows, vecs = self.load(gid)
            for r, v in zip(rows, vecs):
                out.setdefault(r["text_sha256"], list(v))
        return out

    def activate(self, con, project_id: str, generation_id: str, profile_id: str) -> str | None:
        """Switch the active pointer inside the caller's transaction; returns the previous generation id."""
        g = self.generation(con, generation_id)
        if g is None or g["project_id"] != project_id or g["status"] not in ("ready", "retired", "active"):
            raise GenerationError(f"generation {generation_id} cannot be activated for {project_id}")
        s = self.settings(con, project_id)
        prev = s["active_generation_id"]
        now = utc_now()
        if prev and prev != generation_id:
            con.execute("UPDATE index_generations SET status='retired', retired_at=? WHERE generation_id=?", (now, prev))
        con.execute("UPDATE index_generations SET status='active', activated_at=?, retired_at=NULL WHERE "
                    "generation_id=?", (now, generation_id))
        con.execute("INSERT OR REPLACE INTO project_settings VALUES (?,?,?,?,?)",
                    (project_id, s["retrieval_mode"], profile_id, generation_id, now))
        return prev

    # ---------------- vectors and search
    def load(self, generation_id: str) -> tuple[list[dict], list[array]]:
        if generation_id in self._cache:
            return self._cache[generation_id]
        with self.store.read() as con:
            g = self.generation(con, generation_id)
        if g is None:
            raise GenerationError(f"generation {generation_id} not found")
        folder = self.store.data_dir / g["vectors_path"]
        blob = (folder / "vectors.f32").read_bytes()
        if hashlib.sha256(blob).hexdigest() != g["vectors_sha256"]:
            raise GenerationError(f"vector file of {generation_id} does not match its recorded hash")
        manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
        flat = array("f")
        flat.frombytes(blob)
        if sys.byteorder != "little":
            flat.byteswap()
        dim = g["dimension"]
        vecs = [flat[i * dim:(i + 1) * dim] for i in range(g["n_vectors"])]
        self._cache[generation_id] = (manifest["rows"], vecs)
        return self._cache[generation_id]

    def search(self, generation_id: str, query_vec: list[float], candidate_id: str, k: int) -> list[dict]:
        rows, vecs = self.load(generation_id)
        if vecs and len(query_vec) != len(vecs[0]):
            raise GenerationError("query vector dimension does not match the generation")
        scored = [(sum(a * b for a, b in zip(query_vec, v)), r) for r, v in zip(rows, vecs)
                  if r["candidate_id"] == candidate_id]
        scored.sort(key=lambda x: (-x[0], x[1]["source_id"], x[1]["version_id"], x[1]["passage_id"]))
        return [{"source_id": r["source_id"], "version_id": r["version_id"], "passage_id": r["passage_id"],
                 "cosine": round(s, 6)} for s, r in scored[:k]]
