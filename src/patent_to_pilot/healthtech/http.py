"""Loopback HTTP jobs for the local HealthTech dossier engine.

This adapter deliberately exposes only the local offline engine. Paid provider
dispatch stays fail-closed until its durable budget ledger is reconciled.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import os
from pathlib import Path
import re
import tempfile
import threading
import time
import traceback
from typing import Any, Callable
from urllib.parse import parse_qs, unquote, urlsplit
from uuid import uuid4

from patent_to_pilot.healthtech.contracts import content_hash
from patent_to_pilot.healthtech.engine import (
    DossierInput,
    export_markdown,
    run_dossier,
    serialize_dossier,
)
from patent_to_pilot.healthtech.history import (
    DossierHistoryError,
    append_user_edits,
    history_manifest,
    load_versions,
    save_version,
    select_version,
    source_view,
)
from patent_to_pilot.healthtech.rights import RightsBoundaryError
from patent_to_pilot.healthtech.vector_http import ConfiguredVectorSearch


JOB_ID = re.compile(r"^[a-f0-9]{32}$")
IDEMPOTENCY_KEY = re.compile(r"^[A-Za-z0-9._:-]{1,160}$")


def _utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _json_hash(payload: Any) -> str:
    return hashlib.sha256(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    ).hexdigest()


class HTTPJobError(ValueError):
    """A sanitized API error with an HTTP status code."""

    def __init__(self, status: int, code: str, message: str, *, details: Any = None):
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message
        self.details = details


def _atomic_write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, staging_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".staging", dir=path.parent)
    staging = Path(staging_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2, allow_nan=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        staging.replace(path)
    finally:
        try:
            staging.unlink()
        except FileNotFoundError:
            pass


class JobStore:
    """Durable job metadata and idempotency records under one owned root."""

    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.jobs_root = self.root / "jobs"
        self.index_path = self.root / "idempotency.json"
        self.root.mkdir(parents=True, exist_ok=True)
        self.jobs_root.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()

    def _job_dir(self, job_id: str) -> Path:
        if not JOB_ID.fullmatch(job_id):
            raise HTTPJobError(400, "invalid_job_id", "job_id is invalid")
        return self.jobs_root / job_id

    def _record_path(self, job_id: str) -> Path:
        return self._job_dir(job_id) / "job.json"

    def _load_index(self) -> dict[str, str]:
        if not self.index_path.exists():
            return {}
        try:
            value = json.loads(self.index_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise HTTPJobError(500, "store_corrupt", "job idempotency index is unreadable") from exc
        if not isinstance(value, dict) or any(not isinstance(k, str) or not isinstance(v, str) for k, v in value.items()):
            raise HTTPJobError(500, "store_corrupt", "job idempotency index is invalid")
        return value

    def _save_index(self, value: dict[str, str]) -> None:
        _atomic_write_json(self.index_path, value)

    def read(self, job_id: str) -> dict[str, Any]:
        with self._lock:
            path = self._record_path(job_id)
            try:
                record = json.loads(path.read_text(encoding="utf-8"))
            except FileNotFoundError as exc:
                raise HTTPJobError(404, "job_not_found", "job was not found") from exc
            except (OSError, json.JSONDecodeError) as exc:
                raise HTTPJobError(500, "store_corrupt", "job record is unreadable") from exc
            if not isinstance(record, dict):
                raise HTTPJobError(500, "store_corrupt", "job record is invalid")
            return record

    def write(self, record: dict[str, Any]) -> None:
        with self._lock:
            _atomic_write_json(self._record_path(record["job_id"]), record)

    def create(self, *, job_id: str, idempotency_key: str, request_hash: str, project_id: str,
               provider: dict[str, Any], input_payload: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            index = self._load_index()
            existing_id = index.get(idempotency_key)
            if existing_id:
                existing = self.read(existing_id)
                if existing["request_hash"] != request_hash:
                    raise HTTPJobError(409, "idempotency_conflict", "idempotency key was reused for different input")
                return {**existing, "duplicate": True}
            record = {
                "format": "ht-http-job-v1",
                "job_id": job_id,
                "idempotency_key": idempotency_key,
                "request_hash": request_hash,
                "project_id": project_id,
                "state": "queued",
                "reason": None,
                "error": None,
                "attempt": 0,
                "cancel_requested": False,
                "preserved_result": False,
                "created_at": _utc(),
                "updated_at": _utc(),
                "provider": provider,
                "cost": {
                    "billing_status": "not_billable_local",
                    "actual_usd": 0.0,
                    "reserved_usd": 0.0,
                    "unknown_usd": 0.0,
                    "local_elapsed_seconds": None,
                },
                "input_path": "input.json",
                "history_path": "history",
                "artifacts": None,
                "attempts": [],
                "duplicate": False,
            }
            job_dir = self._job_dir(job_id)
            job_dir.mkdir(parents=True, exist_ok=False)
            _atomic_write_json(job_dir / "input.json", input_payload)
            self.write(record)
            index[idempotency_key] = job_id
            self._save_index(index)
            return record

    def mutate(self, job_id: str, fn: Callable[[dict[str, Any]], dict[str, Any]]) -> dict[str, Any]:
        with self._lock:
            record = self.read(job_id)
            updated = fn(record)
            updated["updated_at"] = _utc()
            self.write(updated)
            return updated


class HealthTechJobService:
    """Local job coordinator with one worker and no browser-controlled paths."""

    def __init__(self, root: str | Path, *, code_commit: str = "unknown", max_workers: int = 1,
                 runner: Callable[..., tuple[Any, list[Any], Any]] = run_dossier,
                 execution_delay_seconds: float = 0.0,
                 vector_search: ConfiguredVectorSearch | None = None):
        if max_workers != 1:
            raise ValueError("HealthTech local service requires one worker")
        if execution_delay_seconds < 0:
            raise ValueError("execution delay must be non-negative")
        self.store = JobStore(root)
        self.code_commit = code_commit
        self.runner = runner
        self.execution_delay_seconds = execution_delay_seconds
        self.vector_search = vector_search
        self.executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="healthtech-job")

    def close(self) -> None:
        self.executor.shutdown(wait=True, cancel_futures=False)

    def provider_catalog(self) -> dict[str, Any]:
        providers = [
                {
                    "id": "local",
                    "label": "Local offline engine",
                    "available": self.vector_search is None,
                    "model": "offline-lexical-v1" if self.vector_search is None else None,
                    "billing_status": "not_billable_local",
                    "actual_usd": 0.0,
                    "reserved_usd": 0.0,
                    "unknown_usd": 0.0,
                    "resource_usage": "measured_local_resources",
                    **({"reason": "vector engine configured; use local-vector"} if self.vector_search else {}),
                },
            ]
        if self.vector_search is not None:
            providers.insert(0, self.vector_search.describe())
        providers.append(
                {
                    "id": "openrouter",
                    "label": "OpenRouter",
                    "available": False,
                    "model": "qwen/qwen3-32b",
                    "billing_status": "unknown_pending",
                    "actual_usd": None,
                    "reserved_usd": None,
                    "unknown_usd": None,
                    "reason": "paid ledger reconciliation and explicit dispatch authorization are required",
                },
        )
        return {
            "providers": providers,
            "budget_gate": {
                "paid_dispatch": "closed",
                "authorized_ceiling_usd": "unknown",
                "actual_usd": "unknown",
                "reserved_usd": "unknown",
                "unknown_pending_usd": "unknown",
            },
        }

    def submit(self, body: dict[str, Any], header_idempotency_key: str | None = None) -> dict[str, Any]:
        if not isinstance(body, dict):
            raise HTTPJobError(400, "invalid_json", "request body must be a JSON object")
        allowed = {"input", "provider", "idempotency_key"}
        unexpected = sorted(set(body) - allowed)
        if unexpected:
            raise HTTPJobError(400, "unsupported_field", "request contains unsupported fields", details=unexpected)
        key = header_idempotency_key or body.get("idempotency_key")
        if not isinstance(key, str) or not IDEMPOTENCY_KEY.fullmatch(key):
            raise HTTPJobError(400, "invalid_idempotency_key", "a bounded idempotency key is required")
        provider = body.get("provider") or {"id": "local"}
        if not isinstance(provider, dict) or provider.get("id") not in {"local", "local-vector"}:
            raise HTTPJobError(409, "provider_blocked", "only configured local providers are available; paid dispatch is fail-closed")
        if provider.get("id") == "local-vector" and self.vector_search is None:
            raise HTTPJobError(409, "provider_unavailable", "local-vector is not configured on this server")
        if provider.get("id") == "local" and self.vector_search is not None:
            raise HTTPJobError(409, "provider_unavailable", "the configured server requires the local-vector provider")
        raw_input = body.get("input")
        if not isinstance(raw_input, dict):
            raise HTTPJobError(400, "invalid_input", "input must be a DossierInput object")
        try:
            parsed = DossierInput.model_validate(raw_input)
        except Exception as exc:
            raise HTTPJobError(422, "invalid_input", "input failed HealthTech contract validation", details=str(exc)) from exc
        if self.vector_search is not None:
            try:
                self.vector_search.validate_input(parsed)
            except Exception as exc:
                raise HTTPJobError(422, "vector_input_mismatch", "input does not match the configured vector runtime", details=str(exc)) from exc
        input_payload = parsed.model_dump(mode="json")
        request_hash = _json_hash({"input": input_payload, "provider": provider})
        job_id = uuid4().hex
        provider_record = self.vector_search.describe() if self.vector_search is not None else {
            "id": "local", "model": "offline-lexical-v1"
        }
        record = self.store.create(
            job_id=job_id,
            idempotency_key=key,
            request_hash=request_hash,
            project_id=parsed.query.brief.project_id,
            provider=provider_record,
            input_payload=input_payload,
        )
        if not record.get("duplicate"):
            self.executor.submit(self._execute, job_id)
        public = self._public(record)
        public["duplicate"] = bool(record.get("duplicate"))
        return public

    def _public(self, record: dict[str, Any]) -> dict[str, Any]:
        copy = json.loads(json.dumps(record, ensure_ascii=False))
        copy.pop("idempotency_key", None)
        copy.pop("input_path", None)
        copy.pop("history_path", None)
        copy.pop("duplicate", None)
        return copy

    def _execute(self, job_id: str) -> None:
        started = _utc()

        def start(record: dict[str, Any]) -> dict[str, Any]:
            if record["state"] == "cancelled":
                return record
            record["state"] = "running"
            record["attempt"] += 1
            record["cancel_requested"] = False
            record["reason"] = None
            record["error"] = None
            record["attempts"].append({
                "attempt": record["attempt"],
                "state": "running",
                "started_at": started,
                "ended_at": None,
                "error": None,
            })
            return record

        record = self.store.mutate(job_id, start)
        if record["state"] == "cancelled":
            return
        try:
            if self.execution_delay_seconds:
                time.sleep(self.execution_delay_seconds)
            input_path = self.store._job_dir(job_id) / "input.json"
            data = DossierInput.model_validate_json(input_path.read_text(encoding="utf-8"))
            if self.vector_search is None:
                dossier, events, manifest = self.runner(
                    data, run_id=f"job-{job_id}-a{record['attempt']}", code_commit=self.code_commit
                )
            else:
                dossier, events, manifest = self.runner(
                    data,
                    run_id=f"job-{job_id}-a{record['attempt']}",
                    code_commit=self.code_commit,
                    vector_search=self.vector_search.for_input(data),
                )
            current = self.store.read(job_id)
            if current.get("cancel_requested"):
                ended = _utc()
                current["state"] = "cancelled"
                current["reason"] = "cancelled_before_commit"
                current["preserved_result"] = False
                current["cost"]["local_elapsed_seconds"] = manifest.elapsed_seconds
                current["attempts"][-1].update({"state": "cancelled", "ended_at": ended})
                self.store.write(current)
                return
            job_dir = self.store._job_dir(job_id)
            history_dir = job_dir / "history"
            save_version(history_dir, dossier)
            _atomic_write_json(job_dir / "manifest.json", manifest.model_dump(mode="json"))
            events_path = job_dir / "acquisition_events.jsonl"
            events_path.write_text("".join(item.model_dump_json() + "\n" for item in events), encoding="utf-8")
            current = self.store.read(job_id)
            cancelled = bool(current.get("cancel_requested"))
            ended = _utc()
            current["state"] = "cancelled" if cancelled else "succeeded"
            current["reason"] = "cancel_acknowledged_after_commit" if cancelled else None
            current["preserved_result"] = cancelled
            current["cost"]["local_elapsed_seconds"] = manifest.elapsed_seconds
            current["artifacts"] = {
                "manifest": "manifest.json",
                "events": "acquisition_events.jsonl",
                "history": "history",
            }
            current["attempts"][-1].update({"state": current["state"], "ended_at": ended})
            self.store.write(current)
        except Exception as exc:  # durable failure, sanitized in the public record
            ended = _utc()
            current = self.store.read(job_id)
            current["state"] = "failed"
            current["reason"] = "local_job_failed"
            current["error"] = {"type": type(exc).__name__, "message": str(exc)[:500]}
            if current.get("attempts"):
                current["attempts"][-1].update({"state": "failed", "ended_at": ended, "error": current["error"]})
            self.store.write(current)

    def status(self, job_id: str) -> dict[str, Any]:
        return self._public(self.store.read(job_id))

    def cancel(self, job_id: str) -> dict[str, Any]:
        def change(record: dict[str, Any]) -> dict[str, Any]:
            if record["state"] == "queued":
                record["state"] = "cancelled"
                record["reason"] = "cancelled_before_dispatch"
            elif record["state"] == "running":
                record["state"] = "cancel_requested"
                record["cancel_requested"] = True
                record["reason"] = "cancel_requested"
            elif record["state"] == "cancel_requested":
                return record
            elif record["state"] in {"succeeded", "failed", "cancelled"}:
                raise HTTPJobError(409, "job_not_cancellable", f"job is already {record['state']}")
            return record
        return self._public(self.store.mutate(job_id, change))

    def resume(self, job_id: str) -> dict[str, Any]:
        def change(record: dict[str, Any]) -> dict[str, Any]:
            if record["state"] not in {"failed", "interrupted", "unknown", "cancelled"}:
                raise HTTPJobError(409, "job_not_resumable", f"job state {record['state']} cannot be resumed")
            if record.get("artifacts"):
                raise HTTPJobError(409, "result_already_committed", "committed results are preserved; start a new job for a new run")
            record["state"] = "queued"
            record["cancel_requested"] = False
            record["reason"] = "resume_requested"
            record["error"] = None
            return record
        record = self.store.mutate(job_id, change)
        self.executor.submit(self._execute, job_id)
        return self._public(record)

    def _require_result(self, job_id: str) -> dict[str, Any]:
        record = self.store.read(job_id)
        if not record.get("artifacts"):
            raise HTTPJobError(409, "result_not_ready", "job has no committed dossier result")
        return record

    def history(self, job_id: str) -> dict[str, Any]:
        record = self._require_result(job_id)
        manifest = history_manifest(self.store._job_dir(job_id) / record["artifacts"]["history"])
        return {"job": self._public(record), "history": manifest}

    def version(self, job_id: str, version: int | None = None) -> dict[str, Any]:
        record = self._require_result(job_id)
        dossier = select_version(self.store._job_dir(job_id) / record["artifacts"]["history"], version)
        return serialize_dossier(dossier)

    def result(self, job_id: str) -> dict[str, Any]:
        record = self._require_result(job_id)
        root = self.store._job_dir(job_id)
        dossier = select_version(root / record["artifacts"]["history"])
        manifest = json.loads((root / record["artifacts"]["manifest"]).read_text(encoding="utf-8"))
        events = [json.loads(line) for line in (root / record["artifacts"]["events"]).read_text(encoding="utf-8").splitlines() if line.strip()]
        return {
            "job": self._public(record),
            "dossier": serialize_dossier(dossier),
            "manifest": manifest,
            "events": events,
        }

    def edit(self, job_id: str, body: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(body, dict) or set(body) - {"edits", "expected_parent_version"}:
            raise HTTPJobError(400, "invalid_edit", "edit body must contain edits and expected_parent_version")
        edits = body.get("edits")
        expected = body.get("expected_parent_version")
        if not isinstance(edits, dict) or not edits or not isinstance(expected, int) or expected < 1:
            raise HTTPJobError(400, "invalid_edit", "edits and expected_parent_version are required")
        record = self._require_result(job_id)
        try:
            dossier = append_user_edits(
                self.store._job_dir(job_id) / record["artifacts"]["history"],
                {str(k): str(v) for k, v in edits.items()},
                expected_parent_version=expected,
            )
        except DossierHistoryError as exc:
            raise HTTPJobError(409, "version_conflict", str(exc)) from exc
        return {"version": dossier.version, "parent_version": dossier.parent_version, "dossier": serialize_dossier(dossier)}

    def source(self, job_id: str, source_id: str, version: int | None = None, field: str | None = None) -> dict[str, Any]:
        record = self._require_result(job_id)
        dossier = select_version(self.store._job_dir(job_id) / record["artifacts"]["history"], version)
        try:
            return source_view(dossier, source_id, field)
        except (DossierHistoryError, RightsBoundaryError) as exc:
            raise HTTPJobError(409, "source_unavailable", str(exc)) from exc

    def export(self, job_id: str, *, version: int | None, language: str, format_name: str,
               purpose: str) -> tuple[Any, str]:
        record = self._require_result(job_id)
        dossier = select_version(self.store._job_dir(job_id) / record["artifacts"]["history"], version)
        if format_name == "json":
            try:
                return serialize_dossier(dossier, purpose=purpose), "application/json; charset=utf-8"
            except RightsBoundaryError as exc:
                raise HTTPJobError(409, "export_blocked", str(exc)) from exc
        if format_name == "markdown" and language in {"en", "th", "auto"}:
            try:
                return export_markdown(dossier, language=language, purpose=purpose), "text/markdown; charset=utf-8"
            except RightsBoundaryError as exc:
                raise HTTPJobError(409, "export_blocked", str(exc)) from exc
        raise HTTPJobError(400, "invalid_export", "format must be json or markdown and language must be en, th, or auto")

    def route(self, method: str, raw_path: str, body: Any = None, *, headers: dict[str, str] | None = None) -> tuple[int, Any, str]:
        headers = headers or {}
        parsed = urlsplit(raw_path)
        path = [unquote(part) for part in parsed.path.split("/") if part]
        query = parse_qs(parsed.query)
        if method == "GET" and parsed.path == "/healthz":
            return 200, {"status": "ok", "service": "healthtech-local-http-v1"}, "application/json; charset=utf-8"
        if method == "GET" and parsed.path == "/providers":
            return 200, self.provider_catalog(), "application/json; charset=utf-8"
        if method == "POST" and path == ["jobs"]:
            result = self.submit(body, headers.get("Idempotency-Key"))
            return 200 if result.get("duplicate") else 202, {"job": result}, "application/json; charset=utf-8"
        if len(path) >= 2 and path[0] == "jobs":
            job_id = path[1]
            if method == "GET" and len(path) == 2:
                return 200, {"job": self.status(job_id)}, "application/json; charset=utf-8"
            if method == "POST" and path[2:] == ["cancel"]:
                return 202, {"job": self.cancel(job_id)}, "application/json; charset=utf-8"
            if method == "POST" and path[2:] == ["resume"]:
                return 202, {"job": self.resume(job_id)}, "application/json; charset=utf-8"
            if method == "GET" and path[2:] == ["history"]:
                return 200, self.history(job_id), "application/json; charset=utf-8"
            if method == "GET" and len(path) == 4 and path[2] == "history":
                return 200, self.version(job_id, int(path[3])), "application/json; charset=utf-8"
            if method == "GET" and path[2:] == ["result"]:
                return 200, self.result(job_id), "application/json; charset=utf-8"
            if method == "POST" and len(path) == 5 and path[2] == "history" and path[4] == "edits":
                return 200, self.edit(job_id, body), "application/json; charset=utf-8"
            if method == "GET" and len(path) == 3 and path[2] == "export":
                version = int(query["version"][0]) if query.get("version") else None
                language = query.get("language", ["auto"])[0]
                format_name = query.get("format", ["json"])[0]
                purpose = query.get("purpose", ["local_research"])[0]
                value, content_type = self.export(job_id, version=version, language=language, format_name=format_name, purpose=purpose)
                return 200, value, content_type
            if method == "GET" and len(path) == 4 and path[2] == "source":
                version = int(query["version"][0]) if query.get("version") else None
                field = query.get("field", [None])[0]
                return 200, self.source(job_id, path[3], version, field), "application/json; charset=utf-8"
        raise HTTPJobError(404, "route_not_found", "route was not found")


class _Handler(BaseHTTPRequestHandler):
    service: HealthTechJobService

    @staticmethod
    def _is_loopback_origin(origin: str) -> bool:
        try:
            parsed = urlsplit(origin)
        except ValueError:
            return False
        return parsed.scheme in {"http", "https"} and parsed.hostname in {"127.0.0.1", "localhost", "::1"}

    def _cors_origin(self) -> str | None:
        origin = self.headers.get("Origin")
        return origin if origin and self._is_loopback_origin(origin) else None

    def _send(self, status: int, value: Any, content_type: str) -> None:
        if content_type.startswith("application/json"):
            payload = json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False).encode("utf-8")
        else:
            payload = str(value).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        origin = self._cors_origin()
        if origin:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Access-Control-Allow-Headers", "Content-Type, Idempotency-Key")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Vary", "Origin")
        self.end_headers()
        self.wfile.write(payload)

    def _preflight(self) -> None:
        origin = self._cors_origin()
        requested_headers = {item.strip().lower() for item in self.headers.get("Access-Control-Request-Headers", "").split(",") if item.strip()}
        if not origin or not requested_headers.issubset({"content-type", "idempotency-key"}):
            self._send(403, {"error": {"code": "cors_blocked", "message": "only loopback browser origins are allowed"}}, "application/json; charset=utf-8")
            return
        self._send(204, "", "text/plain; charset=utf-8")

    def _handle(self, method: str) -> None:
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length > 8 * 1024 * 1024:
                raise HTTPJobError(413, "body_too_large", "request body exceeds 8 MiB")
            raw = self.rfile.read(length) if length else b""
            body = json.loads(raw.decode("utf-8")) if raw else None
            status, value, content_type = self.service.route(
                method, self.path, body, headers={key: value for key, value in self.headers.items()}
            )
            self._send(status, value, content_type)
        except HTTPJobError as exc:
            self._send(exc.status, {"error": {"code": exc.code, "message": exc.message, "details": exc.details}}, "application/json; charset=utf-8")
        except (ValueError, json.JSONDecodeError):
            self._send(400, {"error": {"code": "invalid_json", "message": "request body is not valid JSON"}}, "application/json; charset=utf-8")
        except Exception:
            self._send(500, {"error": {"code": "internal_error", "message": "internal server error"}}, "application/json; charset=utf-8")

    def do_GET(self) -> None:  # noqa: N802
        self._handle("GET")

    def do_POST(self) -> None:  # noqa: N802
        self._handle("POST")

    def do_OPTIONS(self) -> None:  # noqa: N802
        self._preflight()

    def log_message(self, format: str, *args: Any) -> None:
        return


def create_server(
    host: str,
    port: int,
    root: str | Path,
    *,
    code_commit: str = "unknown",
    execution_delay_seconds: float = 0.0,
    vector_config: str | Path | None = None,
) -> ThreadingHTTPServer:
    configured_vectors = None if vector_config is None else ConfiguredVectorSearch.from_config(vector_config)
    service = HealthTechJobService(
        root,
        code_commit=code_commit,
        execution_delay_seconds=execution_delay_seconds,
        vector_search=configured_vectors,
    )

    class BoundHandler(_Handler):
        pass

    BoundHandler.service = service
    server = ThreadingHTTPServer((host, port), BoundHandler)
    server.healthtech_service = service  # type: ignore[attr-defined]
    return server

