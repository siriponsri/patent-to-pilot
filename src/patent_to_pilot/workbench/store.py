"""SQLite store for the G01 workbench: versioned sources, current-scope FTS5 index, runs, actions,
assessments, dependencies and change events. Append-only for history; explicit current pointers."""
from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
import json
import sqlite3
from pathlib import Path

SCHEMA_VERSION = "ptp-workbench-store-v1"

SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS projects (
  project_id TEXT PRIMARY KEY, program_id TEXT NOT NULL, goal_id TEXT NOT NULL, scenario_id TEXT NOT NULL,
  title TEXT NOT NULL, data_origin TEXT NOT NULL, mission_json TEXT NOT NULL, manifest_json TEXT NOT NULL,
  created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS source_versions (
  project_id TEXT NOT NULL, source_id TEXT NOT NULL, version_id TEXT NOT NULL, candidate_id TEXT NOT NULL,
  title TEXT NOT NULL, source_kind TEXT NOT NULL, license TEXT NOT NULL, supersedes_version_id TEXT,
  sha256 TEXT NOT NULL, raw BLOB NOT NULL, text TEXT NOT NULL, origin_path TEXT NOT NULL,
  imported_at TEXT NOT NULL, import_event TEXT NOT NULL,
  PRIMARY KEY (project_id, source_id, version_id));
CREATE TABLE IF NOT EXISTS current_sources (
  project_id TEXT NOT NULL, source_id TEXT NOT NULL, version_id TEXT NOT NULL, updated_at TEXT NOT NULL,
  PRIMARY KEY (project_id, source_id));
CREATE TABLE IF NOT EXISTS passages (
  project_id TEXT NOT NULL, source_id TEXT NOT NULL, version_id TEXT NOT NULL, passage_id TEXT NOT NULL,
  start_char INTEGER NOT NULL, end_char INTEGER NOT NULL, quote TEXT NOT NULL,
  PRIMARY KEY (project_id, source_id, version_id, passage_id));
CREATE VIRTUAL TABLE IF NOT EXISTS passage_fts USING fts5(
  project_id UNINDEXED, source_id UNINDEXED, version_id UNINDEXED, passage_id UNINDEXED,
  candidate_id UNINDEXED, body, tokenize='unicode61');
CREATE TABLE IF NOT EXISTS obligations (
  project_id TEXT NOT NULL, candidate_id TEXT NOT NULL, requirement_id TEXT NOT NULL, state TEXT NOT NULL,
  reason TEXT NOT NULL, updated_at TEXT NOT NULL, PRIMARY KEY (project_id, candidate_id, requirement_id));
CREATE TABLE IF NOT EXISTS runs (
  run_id TEXT PRIMARY KEY, project_id TEXT NOT NULL, kind TEXT NOT NULL, invoked_via TEXT NOT NULL,
  core_identity TEXT NOT NULL, execution_mode TEXT NOT NULL, data_origin TEXT NOT NULL,
  strategy TEXT NOT NULL, config_sha256 TEXT NOT NULL, limits_json TEXT NOT NULL, counters_json TEXT NOT NULL,
  status TEXT NOT NULL, stop_reason TEXT, change_event_id TEXT, started_at TEXT NOT NULL, finished_at TEXT);
CREATE TABLE IF NOT EXISTS actions (
  run_id TEXT NOT NULL, seq INTEGER NOT NULL, action_type TEXT NOT NULL, candidate_id TEXT,
  requirement_id TEXT, status TEXT NOT NULL, started_at TEXT NOT NULL, finished_at TEXT,
  detail_json TEXT NOT NULL, PRIMARY KEY (run_id, seq));
CREATE TABLE IF NOT EXISTS assessments (
  assessment_id TEXT PRIMARY KEY, project_id TEXT NOT NULL, candidate_id TEXT NOT NULL,
  requirement_id TEXT NOT NULL, requirement_sha256 TEXT NOT NULL, outcome TEXT NOT NULL,
  explanation TEXT NOT NULL, reading_json TEXT NOT NULL, issues_json TEXT NOT NULL,
  search_hits_json TEXT NOT NULL, run_id TEXT NOT NULL, supersedes_id TEXT, state TEXT NOT NULL,
  created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS assessment_events (
  assessment_id TEXT NOT NULL, state TEXT NOT NULL, reason TEXT NOT NULL, run_id TEXT, at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS citations (
  assessment_id TEXT NOT NULL, source_id TEXT NOT NULL, version_id TEXT NOT NULL, passage_id TEXT NOT NULL,
  start_char INTEGER NOT NULL, end_char INTEGER NOT NULL, quote TEXT NOT NULL, sha256 TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS dependencies (
  assessment_id TEXT NOT NULL, kind TEXT NOT NULL, source_id TEXT NOT NULL, version_id TEXT NOT NULL,
  candidate_id TEXT NOT NULL, query TEXT);
CREATE TABLE IF NOT EXISTS change_events (
  project_id TEXT NOT NULL, event_id TEXT NOT NULL, event_type TEXT NOT NULL, source_id TEXT NOT NULL,
  version_id TEXT NOT NULL, supersedes_version_id TEXT, sha256 TEXT NOT NULL, status TEXT NOT NULL,
  run_id TEXT, result_json TEXT, created_at TEXT NOT NULL, applied_at TEXT,
  PRIMARY KEY (project_id, event_id));
"""


# G02 additions. Created in place on existing G01 stores (CREATE IF NOT EXISTS): no G01 table changes.
SCHEMA_G02 = """
CREATE TABLE IF NOT EXISTS provider_profiles (
  profile_id TEXT PRIMARY KEY, role TEXT NOT NULL, adapter TEXT NOT NULL, config_json TEXT NOT NULL,
  created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS provider_checks (
  profile_id TEXT NOT NULL, config_sha256 TEXT NOT NULL, overall TEXT NOT NULL, result_json TEXT NOT NULL,
  checked_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS provider_usage (
  profile_id TEXT NOT NULL, operation TEXT NOT NULL, billable INTEGER NOT NULL, status TEXT NOT NULL,
  usage_json TEXT, latency_ms REAL, detail TEXT, at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS index_generations (
  generation_id TEXT PRIMARY KEY, project_id TEXT NOT NULL, profile_id TEXT NOT NULL,
  embedding_space_id TEXT NOT NULL, identity_json TEXT NOT NULL, status TEXT NOT NULL, n_vectors INTEGER NOT NULL,
  dimension INTEGER, vectors_path TEXT, vectors_sha256 TEXT, reused_vectors INTEGER NOT NULL DEFAULT 0,
  embedded_vectors INTEGER NOT NULL DEFAULT 0, created_at TEXT NOT NULL, activated_at TEXT, retired_at TEXT,
  detail_json TEXT);
CREATE TABLE IF NOT EXISTS project_settings (
  project_id TEXT PRIMARY KEY, retrieval_mode TEXT NOT NULL, embedding_profile_id TEXT,
  active_generation_id TEXT, updated_at TEXT NOT NULL);
"""


# P0-T06 additions (owner note 22 Nov 2026): source-bound structure and evidence-trace records. Additive only:
# CREATE IF NOT EXISTS on existing stores, no change to any G01/G02 table. Original bytes are kept beside the canonical
# text that ``source_versions.raw`` already holds; nodes belong to one immutable source version; hypotheses and source
# evidence are separate tables and an id can never be both (triggers below).
SCHEMA_P0T06 = """
CREATE TABLE IF NOT EXISTS original_artifacts (
  project_id TEXT NOT NULL, source_id TEXT NOT NULL, version_id TEXT NOT NULL, media_type TEXT NOT NULL,
  sha256 TEXT NOT NULL, size_bytes INTEGER NOT NULL, raw BLOB NOT NULL, storage_ref TEXT NOT NULL,
  created_at TEXT NOT NULL, PRIMARY KEY (project_id, source_id, version_id));
CREATE TABLE IF NOT EXISTS source_pages (
  project_id TEXT NOT NULL, source_id TEXT NOT NULL, version_id TEXT NOT NULL, page INTEGER NOT NULL,
  display_width_pt REAL NOT NULL, display_height_pt REAL NOT NULL, rotation_degrees INTEGER NOT NULL,
  PRIMARY KEY (project_id, source_id, version_id, page));
CREATE TABLE IF NOT EXISTS doc_nodes (
  project_id TEXT NOT NULL, node_id TEXT NOT NULL, source_id TEXT NOT NULL, version_id TEXT NOT NULL,
  anchor TEXT NOT NULL, kind TEXT NOT NULL, start_char INTEGER, end_char INTEGER, regions_json TEXT NOT NULL,
  alignment_json TEXT, parser_id TEXT NOT NULL, PRIMARY KEY (project_id, node_id));
CREATE TABLE IF NOT EXISTS doc_relations (
  project_id TEXT NOT NULL, relation_id TEXT NOT NULL, kind TEXT NOT NULL, from_node_id TEXT NOT NULL,
  to_node_id TEXT NOT NULL, scope_json TEXT NOT NULL, provenance_json TEXT NOT NULL, state TEXT NOT NULL,
  created_at TEXT NOT NULL, superseded_reason TEXT, PRIMARY KEY (project_id, relation_id));
CREATE TABLE IF NOT EXISTS source_evidence (
  project_id TEXT NOT NULL, evidence_id TEXT NOT NULL, node_id TEXT NOT NULL, start_char INTEGER NOT NULL,
  end_char INTEGER NOT NULL, quote TEXT NOT NULL, created_at TEXT NOT NULL, PRIMARY KEY (project_id, evidence_id));
CREATE TABLE IF NOT EXISTS search_hypotheses (
  project_id TEXT NOT NULL, hypothesis_id TEXT NOT NULL, text TEXT NOT NULL, generator_id TEXT NOT NULL,
  generation_config_sha256 TEXT, source_evidence_ids_json TEXT NOT NULL, created_at TEXT NOT NULL,
  PRIMARY KEY (project_id, hypothesis_id));
CREATE TABLE IF NOT EXISTS bound_requirements (
  project_id TEXT NOT NULL, requirement_id TEXT NOT NULL, query_id TEXT NOT NULL, query_text TEXT NOT NULL,
  start_char INTEGER NOT NULL, end_char INTEGER NOT NULL, text TEXT NOT NULL, created_at TEXT NOT NULL,
  PRIMARY KEY (project_id, requirement_id));
CREATE TABLE IF NOT EXISTS runtime_assessments (
  project_id TEXT NOT NULL, assessment_id TEXT NOT NULL, requirement_id TEXT NOT NULL, status TEXT NOT NULL,
  timing TEXT NOT NULL, evidence_ids_json TEXT NOT NULL, assessor_id TEXT NOT NULL, run_id TEXT NOT NULL,
  detail_json TEXT NOT NULL, created_at TEXT NOT NULL, PRIMARY KEY (project_id, assessment_id));
CREATE TABLE IF NOT EXISTS trace_events (
  project_id TEXT NOT NULL, trace_id TEXT NOT NULL, run_id TEXT NOT NULL, action_seq INTEGER NOT NULL,
  action_kind TEXT NOT NULL, event_json TEXT NOT NULL, event_sha256 TEXT NOT NULL, created_at TEXT NOT NULL,
  PRIMARY KEY (project_id, trace_id));
CREATE TRIGGER IF NOT EXISTS evidence_id_is_not_hypothesis BEFORE INSERT ON source_evidence
  WHEN EXISTS (SELECT 1 FROM search_hypotheses h WHERE h.project_id=NEW.project_id AND h.hypothesis_id=NEW.evidence_id)
  BEGIN SELECT RAISE(ABORT, 'id already names a generated search hypothesis'); END;
CREATE TRIGGER IF NOT EXISTS hypothesis_id_is_not_evidence BEFORE INSERT ON search_hypotheses
  WHEN EXISTS (SELECT 1 FROM source_evidence e WHERE e.project_id=NEW.project_id AND e.evidence_id=NEW.hypothesis_id)
  BEGIN SELECT RAISE(ABORT, 'id already names source evidence'); END;
"""


# P4-T01b additions (requirement Remove/Undo): additive only. ``projects.mission_json`` keeps the ACTIVE requirements;
# a removed requirement keeps its stable ID, full snapshot and content hash here. ``lifecycle_revision`` advances on
# every add, edit, removal and restoration (also when the restored text is identical), so a result planned against an
# earlier revision can be refused at commit. ``mission_lifecycle`` holds the project's monotonic mission revision.
SCHEMA_P4T01B = """
CREATE TABLE IF NOT EXISTS requirement_lifecycle (
  project_id TEXT NOT NULL, requirement_id TEXT NOT NULL, state TEXT NOT NULL, lifecycle_revision INTEGER NOT NULL,
  content_sha256 TEXT NOT NULL, snapshot_json TEXT NOT NULL, position INTEGER NOT NULL, updated_at TEXT NOT NULL,
  last_event_id TEXT, PRIMARY KEY (project_id, requirement_id));
CREATE TABLE IF NOT EXISTS mission_lifecycle (
  project_id TEXT PRIMARY KEY, revision INTEGER NOT NULL, updated_at TEXT NOT NULL);
"""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def dumps(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


class Store:
    """One SQLite file per data directory. Each call uses a short-lived connection (thread-safe enough
    for a loopback single-user server); writes use explicit transactions."""

    def __init__(self, data_dir: str | Path) -> None:
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.path = self.data_dir / "workbench.sqlite3"
        with self.connect() as con:
            con.executescript(SCHEMA)
            con.executescript(SCHEMA_G02)
            con.executescript(SCHEMA_P0T06)
            con.executescript(SCHEMA_P4T01B)
            con.execute("INSERT OR IGNORE INTO meta(key, value) VALUES ('schema_version', ?)", (SCHEMA_VERSION,))
            stored = con.execute("SELECT value FROM meta WHERE key='schema_version'").fetchone()[0]
            if stored != SCHEMA_VERSION:
                raise RuntimeError(f"store schema {stored} is not {SCHEMA_VERSION}")

    def connect(self) -> sqlite3.Connection:
        con = sqlite3.connect(self.path, timeout=10, isolation_level=None)
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA journal_mode=WAL")
        con.execute("PRAGMA foreign_keys=ON")
        con.execute("PRAGMA synchronous=FULL")
        return con

    @contextmanager
    def tx(self):
        con = self.connect()
        try:
            con.execute("BEGIN IMMEDIATE")
            yield con
            con.execute("COMMIT")
        except BaseException:
            con.execute("ROLLBACK")
            raise
        finally:
            con.close()

    @contextmanager
    def read(self):
        con = self.connect()
        try:
            yield con
        finally:
            con.close()

    def backup(self, target: str | Path) -> Path:
        """Consistent copy through SQLite's online backup API (safe while the server runs)."""
        target = Path(target)
        target.parent.mkdir(parents=True, exist_ok=True)
        src = self.connect()
        dst = sqlite3.connect(target)
        try:
            src.backup(dst)
        finally:
            dst.close()
            src.close()
        return target
