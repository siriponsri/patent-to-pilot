"""Small append-only SQLite repository for typed records and version history."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel

from .models import Record


CANONICAL_ID_FIELDS = {
    "SourceRecord": "source_id",
    "OrganizationProfile": "profile_id",
    "ConstraintRecord": "constraint_id",
    "EvidenceRecord": "evidence_id",
    "RouteRecord": "route_id",
    "ChangeRecord": "change_id",
    "FeedbackRecord": "feedback_id",
}

T = TypeVar("T", bound=BaseModel)


class SQLiteRecordRepository:
    def __init__(self, path: str | Path = ":memory:") -> None:
        self.path = str(path)
        self.connection = sqlite3.connect(self.path)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        self.connection.execute("""CREATE TABLE IF NOT EXISTS records (
            record_type TEXT NOT NULL, record_id TEXT NOT NULL, version INTEGER NOT NULL,
            payload TEXT NOT NULL, created_at TEXT NOT NULL,
            PRIMARY KEY (record_type, record_id, version)
        )""")
        self.connection.execute("CREATE INDEX IF NOT EXISTS idx_records_current ON records(record_type, record_id, version DESC)")
        self.connection.commit()

    def close(self) -> None:
        self.connection.close()

    def save(self, record: Record) -> Record:
        record_type = record.__class__.__name__
        current = self.connection.execute(
            "SELECT MAX(version) AS version FROM records WHERE record_type=? AND record_id=?",
            (record_type, record.record_id),
        ).fetchone()["version"]
        if current is not None and record.version <= current:
            raise ValueError(f"version must increase for {record_type}/{record.record_id}")
        payload = record.model_dump(mode="json")
        if current is not None:
            previous = self.connection.execute(
                "SELECT payload FROM records WHERE record_type=? AND record_id=? ORDER BY version DESC LIMIT 1",
                (record_type, record.record_id),
            ).fetchone()
            canonical_field = CANONICAL_ID_FIELDS.get(record_type)
            if canonical_field and previous:
                previous_payload = json.loads(previous["payload"])
                if previous_payload.get(canonical_field) != payload.get(canonical_field):
                    raise ValueError(f"canonical {canonical_field} cannot change across versions")
        self.connection.execute(
            "INSERT INTO records(record_type, record_id, version, payload, created_at) VALUES (?, ?, ?, ?, ?)",
            (record_type, record.record_id, record.version, json.dumps(payload, sort_keys=True), record.created_at.isoformat()),
        )
        self.connection.commit()
        return record

    def history(self, record_type: str, record_id: str) -> list[dict]:
        rows = self.connection.execute(
            "SELECT version, payload FROM records WHERE record_type=? AND record_id=? ORDER BY version",
            (record_type, record_id),
        ).fetchall()
        return [{"version": row["version"], "payload": json.loads(row["payload"])} for row in rows]

    def read_latest(self, record_type: str, record_id: str, model: type[T]) -> T | None:
        row = self.connection.execute(
            "SELECT payload FROM records WHERE record_type=? AND record_id=? ORDER BY version DESC LIMIT 1",
            (record_type, record_id),
        ).fetchone()
        return model.model_validate(json.loads(row["payload"])) if row else None

    def iter_latest(self, record_type: str) -> Iterator[dict]:
        rows = self.connection.execute(
            """SELECT r.record_id, r.version, r.payload FROM records r
               JOIN (SELECT record_id, MAX(version) version FROM records
                     WHERE record_type=? GROUP BY record_id) latest
               ON r.record_id=latest.record_id AND r.version=latest.version
               WHERE r.record_type=? ORDER BY r.record_id""",
            (record_type, record_type),
        )
        for row in rows:
            yield {"record_id": row["record_id"], "version": row["version"], "payload": json.loads(row["payload"])}
