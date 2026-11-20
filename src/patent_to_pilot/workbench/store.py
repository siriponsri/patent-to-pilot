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
