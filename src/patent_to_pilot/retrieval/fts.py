"""SQLite FTS5 lexical baseline over normalized, source-linked documents."""

from __future__ import annotations

import json
import re
import sqlite3
import ast
from pathlib import Path

from pydantic import BaseModel

from patent_to_pilot.ingestion.pls import PatentDocument


class SearchHit(BaseModel):
    document_id: str
    source_id: str
    source_version: str
    family_id: str | None
    publication_id: str | None
    title: str
    labels: str
    source_locator: str
    rank: float


class FTSIndex:
    def __init__(self, path: str | Path = ":memory:", source_id: str | None = None, source_version: str | None = None) -> None:
        self.path = str(path)
        self.connection = sqlite3.connect(self.path)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("""CREATE TABLE IF NOT EXISTS documents (
            document_id TEXT PRIMARY KEY, source_id TEXT NOT NULL, source_version TEXT NOT NULL,
            family_id TEXT, publication_id TEXT, title TEXT NOT NULL, abstract TEXT NOT NULL,
            claims TEXT NOT NULL, description TEXT NOT NULL, cpc TEXT NOT NULL, ipc TEXT NOT NULL,
            labels TEXT NOT NULL, source_locator TEXT NOT NULL, source_sha256 TEXT NOT NULL
        )""")
        self.connection.execute("""CREATE VIRTUAL TABLE IF NOT EXISTS document_fts USING fts5(
            document_id UNINDEXED, title, abstract, claims, description, cpc, ipc, labels, tokenize='unicode61'
        )""")
        self.connection.execute("CREATE TABLE IF NOT EXISTS document_labels (document_id TEXT NOT NULL, label TEXT NOT NULL, PRIMARY KEY(document_id, label))")
        self.connection.execute("CREATE TABLE IF NOT EXISTS index_scope (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
        existing_scope = dict(self.connection.execute("SELECT key, value FROM index_scope").fetchall())
        existing_rows = self.connection.execute("SELECT DISTINCT source_id, source_version FROM documents").fetchall()
        existing_pairs = {(row[0], row[1]) for row in existing_rows}
        if len(existing_pairs) > 1:
            raise ValueError("existing index contains multiple source identity/version pairs")
        if existing_pairs:
            existing_source_id, existing_source_version = next(iter(existing_pairs))
            existing_scope.setdefault("source_id", existing_source_id)
            existing_scope.setdefault("source_version", existing_source_version)
        self.source_id = source_id or existing_scope.get("source_id")
        self.source_version = source_version or existing_scope.get("source_version")
        if source_id and existing_scope.get("source_id") and source_id != existing_scope["source_id"]:
            raise ValueError("index source_id scope does not match existing index")
        if source_version and existing_scope.get("source_version") and source_version != existing_scope["source_version"]:
            raise ValueError("index source_version scope does not match existing index")
        if self.source_id:
            self.connection.execute("INSERT OR REPLACE INTO index_scope(key, value) VALUES ('source_id', ?)", (self.source_id,))
        if self.source_version:
            self.connection.execute("INSERT OR REPLACE INTO index_scope(key, value) VALUES ('source_version', ?)", (self.source_version,))
        self.connection.commit()

    def close(self) -> None: self.connection.close()

    def add(self, document: PatentDocument) -> None:
        if self.source_id is None:
            self.source_id = document.source_id
            self.connection.execute("INSERT OR REPLACE INTO index_scope(key, value) VALUES ('source_id', ?)", (self.source_id,))
        if self.source_version is None:
            self.source_version = document.source_version
            self.connection.execute("INSERT OR REPLACE INTO index_scope(key, value) VALUES ('source_version', ?)", (self.source_version,))
        if document.source_id != self.source_id or document.source_version != self.source_version:
            raise ValueError("document source identity/version is outside this index scope")
        self.connection.execute("INSERT OR REPLACE INTO documents VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (
            document.document_id, document.source_id, document.source_version, document.family_id, document.publication_id,
            document.title, document.abstract, document.claims, document.description, document.cpc, document.ipc,
            document.labels, document.source_locator, document.source_sha256))
        self.connection.execute("DELETE FROM document_fts WHERE document_id=?", (document.document_id,))
        self.connection.execute("DELETE FROM document_labels WHERE document_id=?", (document.document_id,))
        for label in self._parse_labels(document.labels):
            self.connection.execute("INSERT OR IGNORE INTO document_labels(document_id, label) VALUES (?, ?)", (document.document_id, label))
        self.connection.execute("INSERT INTO document_fts(document_id, title, abstract, claims, description, cpc, ipc, labels) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (
            document.document_id, document.title, document.abstract, document.claims, document.description,
            document.cpc, document.ipc, document.labels))

    def add_jsonl(self, path: str | Path, commit_every: int = 100) -> int:
        count = 0
        with Path(path).open("r", encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    self.add(PatentDocument.model_validate(json.loads(line))); count += 1
                    if count % commit_every == 0: self.connection.commit()
        self.connection.commit(); return count

    @staticmethod
    def _match_query(query: str) -> str:
        terms = re.findall(r"[\w-]+", query, flags=re.UNICODE)
        if not terms: raise ValueError("query must contain searchable terms")
        return " AND ".join('"' + term.replace('"', '""') + '"' for term in terms)

    @staticmethod
    def _parse_labels(labels: str) -> set[str]:
        try:
            parsed = ast.literal_eval(labels)
            if isinstance(parsed, list):
                return {str(value).strip() for value in parsed if str(value).strip()}
            if isinstance(parsed, str) and parsed.strip():
                return {parsed.strip()}
        except (SyntaxError, ValueError):
            pass
        return {part.strip() for part in re.split(r"[,;|]", labels) if part.strip()}

    def search(self, query: str, limit: int = 10, source_id: str | None = None, label: str | None = None) -> list[SearchHit]:
        if limit < 1: raise ValueError("limit must be positive")
        sql = "SELECT d.*, bm25(document_fts) AS score FROM document_fts f JOIN documents d ON d.document_id=f.document_id WHERE document_fts MATCH ?"
        params: list[object] = [self._match_query(query)]
        if source_id: sql += " AND d.source_id=?"; params.append(source_id)
        if label:
            sql += " AND EXISTS (SELECT 1 FROM document_labels dl WHERE dl.document_id=d.document_id AND dl.label=?)"; params.append(label)
        sql += " ORDER BY score, d.document_id LIMIT ?"; params.append(limit)
        rows = self.connection.execute(sql, params).fetchall()
        return [SearchHit(document_id=row["document_id"], source_id=row["source_id"], source_version=row["source_version"], family_id=row["family_id"], publication_id=row["publication_id"], title=row["title"], labels=row["labels"], source_locator=row["source_locator"], rank=float(row["score"])) for row in rows]
