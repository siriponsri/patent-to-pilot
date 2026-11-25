"""Loopback HTTP app for the G01 Workbench: JSON API + bundled static frontend, one Python process.

Every route calls the shared ``EvidenceCore`` (the same service the CLI uses). Static files are served only
from the package's ``static/`` directory; source files, the store and test-only expectations are never mounted.
"""
from __future__ import annotations

import base64
import binascii
import json
import mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import re
import socket
import threading
from urllib.parse import unquote, urlsplit

from patent_to_pilot.workbench.core import CoreError, EvidenceCore
from patent_to_pilot.workbench.providers import ADAPTERS, ProviderError
from patent_to_pilot.workbench.scope_reader import ScopeReader
from patent_to_pilot.workbench.workflow import Workflow

STATIC_DIR = Path(__file__).resolve().parent / "static"
STATIC_FILES = {"/": "index.html", "/index.html": "index.html", "/app.js": "app.js", "/app.css": "app.css",
                "/scope.js": "scope.js"}
_SEG = r"([A-Za-z0-9._-]+)"
ROUTES = [
    ("GET", r"/api/scope/catalog", "scope_catalog"),
    ("POST", r"/api/scope/run", "scope_run"),
    ("GET", rf"/api/scope/run/{_SEG}", "scope_replay"),
    ("GET", r"/api/health", "health"),
    ("GET", r"/api/capabilities", "capabilities"),
    ("GET", r"/api/projects", "projects"),
    ("POST", r"/api/demo/bootstrap", "bootstrap"),
    ("GET", rf"/api/projects/{_SEG}", "project"),
    ("GET", rf"/api/projects/{_SEG}/comparison", "comparison"),
    ("GET", rf"/api/projects/{_SEG}/history", "history"),
    ("POST", rf"/api/projects/{_SEG}/runs", "run"),
    ("GET", rf"/api/projects/{_SEG}/runs", "runs"),
    ("GET", rf"/api/runs/{_SEG}", "run_view"),
    ("GET", rf"/api/projects/{_SEG}/changes", "changes"),
    ("POST", rf"/api/projects/{_SEG}/changes", "apply_change"),
    ("GET", rf"/api/projects/{_SEG}/sources/{_SEG}/versions/{_SEG}", "source_version"),
    ("GET", rf"/api/projects/{_SEG}/sources/{_SEG}/versions/{_SEG}/passages/{_SEG}", "citation"),
    # G02
    ("GET", r"/api/providers", "providers"),
    ("POST", r"/api/providers", "save_provider"),
    ("POST", rf"/api/providers/{_SEG}/check", "check_provider"),
    ("POST", rf"/api/providers/{_SEG}/delete", "delete_provider"),
    ("GET", rf"/api/providers/{_SEG}/usage", "provider_usage"),
    ("POST", r"/api/projects", "create_project"),
    ("POST", rf"/api/projects/{_SEG}/documents", "ingest"),
    ("GET", rf"/api/projects/{_SEG}/retrieval", "retrieval"),
    ("POST", rf"/api/projects/{_SEG}/retrieval", "set_retrieval"),
    ("POST", rf"/api/projects/{_SEG}/index", "build_index"),
    # P0-T06: read-only synthetic workflow example (runs in a temporary store; the owner's store is not touched)
    ("GET", r"/api/synthetic/trace-slice", "trace_slice"),
    # P4-T01: Search, Compare and Inspect on the same store and core
    ("POST", rf"/api/projects/{_SEG}/search", "search"),
    ("GET", rf"/api/projects/{_SEG}/requirements", "requirements"),
    ("POST", rf"/api/projects/{_SEG}/requirements", "save_requirement"),
    ("POST", rf"/api/projects/{_SEG}/compare", "compare"),
    ("GET", rf"/api/projects/{_SEG}/sources/{_SEG}/versions/{_SEG}/spans/{_SEG}/{_SEG}", "inspect"),
    ("GET", rf"/api/projects/{_SEG}/sources/{_SEG}/versions/{_SEG}/original", "original"),
    ("POST", r"/api/synthetic/relation-search", "synthetic_relation_search"),
    # P4-T01b: requirement Remove / Undo (same POST guards: loopback Host, same Origin, JSON body, size limit)
    ("POST", rf"/api/projects/{_SEG}/requirements/{_SEG}/archive", "archive_requirement"),
    ("POST", rf"/api/projects/{_SEG}/requirements/{_SEG}/restore", "restore_requirement"),
    # P4-T02: execution mode, exact model, missing capabilities, credential presence (read-only, no network).
    # There is deliberately no route that accepts a credential value.
    ("GET", r"/api/execution-mode", "execution_mode"),
    ("GET", rf"/api/projects/{_SEG}/execution-mode", "execution_mode"),
    ("GET", r"/api/credentials", "credentials"),
]
UPLOAD_LIMIT = 3_000_000  # base64 of the 2 MB ingestion limit, plus JSON overhead
BODY_LIMIT = 65536


def _provider_call(fn, *args):
    try:
        return fn(*args)
    except ProviderError as exc:
        status = {"config": 422, "blocked": 409, "missing_credential": 409}.get(exc.kind, 502)
        err = CoreError(str(exc), f"provider_{exc.kind}")
        err.status = status
        raise err from None


class Raw:
    """A non-JSON response (P4-T01: the stored original bytes of a source version)."""

    def __init__(self, data: bytes, media_type: str, filename: str) -> None:
        self.data, self.media_type, self.filename = data, media_type, filename


class App:
    def __init__(self, core: EvidenceCore, host: str, port: int) -> None:
        self.core, self.host, self.port = core, host, port
        self.lock = threading.Lock()   # one state-changing core operation at a time
        self.workflow = Workflow(core)
        self.scope_reader = ScopeReader(core.store)

    def scope_catalog(self, _body):
        return self.scope_reader.catalog()

    def scope_run(self, body):
        with self.lock:
            return self.scope_reader.run(body)

    def scope_replay(self, _body, run_id):
        return self.scope_reader.replay(run_id)

    def health(self, _body):
        return {"status": "ok", "store": str(self.core.store.path), "url": f"http://{self.host}:{self.port}/"}

    def capabilities(self, _body):
        return self.core.capabilities()

    def projects(self, _body):
        return {"projects": self.core.list_projects()}

    def bootstrap(self, _body):
        with self.lock:
            return self.core.bootstrap_sample()

    def project(self, _body, pid):
        return self.core.project_view(pid)

    def comparison(self, _body, pid):
        return self.core.comparison(pid)

    def history(self, _body, pid):
        return {"assessments": self.core.history(pid)}

    def run(self, _body, pid):
        with self.lock:
            return self.core.run_comparison(pid, invoked_via="http")

    def runs(self, _body, pid):
        return {"runs": self.core.list_runs(pid)}

    def run_view(self, _body, rid):
        return self.core.run_view(rid)

    def changes(self, _body, pid):
        return {"changes": self.core.available_changes(pid)}

    def apply_change(self, body, pid):
        event_id = (body or {}).get("event_id")
        if not isinstance(event_id, str) or not event_id:
            raise CoreError("body must contain event_id", "missing_event_id")
        with self.lock:
            return self.core.apply_change(pid, event_id, invoked_via="http")

    def source_version(self, _body, pid, sid, vid):
        return self.core.source_version(pid, sid, vid)

    def citation(self, _body, pid, sid, vid, passage):
        return self.core.resolve_citation(pid, sid, vid, passage)

    # ---------------- G02
    def providers(self, _body):
        return {"profiles": self.core.registry.list(), "templates": self.core.registry.templates(),
                "adapters": {k: {"roles": list(v["roles"]), "default_endpoint": v["default_endpoint"]}
                             for k, v in ADAPTERS.items()}}

    def save_provider(self, body):
        with self.lock:
            return _provider_call(self.core.registry.save, body or {})

    def check_provider(self, _body, profile_id):
        with self.lock:
            return _provider_call(self.core.registry.check, profile_id)

    def delete_provider(self, _body, profile_id):
        with self.lock:
            return _provider_call(self.core.registry.delete, profile_id)

    def provider_usage(self, _body, profile_id):
        _provider_call(self.core.registry.get, profile_id)
        return {"profile_id": profile_id, "requests_counted": self.core.registry.usage_count(profile_id),
                "events": self.core.registry.usage(profile_id)}

    def create_project(self, body):
        body = body or {}
        with self.lock:
            return self.core.create_project(body.get("title"), body.get("candidates"), body.get("requirements"))

    def ingest(self, body, pid):
        body = body or {}
        try:
            raw = base64.b64decode(body.get("content_base64") or "", validate=True)
        except (binascii.Error, ValueError):
            raise CoreError("content_base64 is not valid base64", "bad_base64") from None
        filename = body.get("filename")
        if not isinstance(filename, str) or not filename:
            raise CoreError("filename is required", "missing_filename")
        with self.lock:
            return self.core.ingest_document(pid, filename, raw, body.get("candidate_id"), body.get("source_id") or None,
                                             invoked_via="http")

    def retrieval(self, _body, pid):
        return self.core.retrieval_status(pid)

    def set_retrieval(self, body, pid):
        with self.lock:
            return _provider_call(self.core.set_retrieval_mode, pid, (body or {}).get("mode"), "http")

    def build_index(self, body, pid):
        with self.lock:
            return _provider_call(self.core.build_index, pid, (body or {}).get("profile_id"), "http")

    # ---------------- P0-T06
    def trace_slice(self, _body):
        from patent_to_pilot.workbench.trace_slice import run_synthetic_slice
        return run_synthetic_slice()   # fresh temporary store per request; synthetic packet only

    # ---------------- P4-T01
    def search(self, body, pid):
        return self.workflow.search(pid, body or {})

    def requirements(self, _body, pid):
        return self.workflow.requirements(pid)

    def save_requirement(self, body, pid):
        with self.lock:
            return self.workflow.save_requirement(pid, body or {})

    def archive_requirement(self, body, pid, rid):
        with self.lock:
            return self.workflow.archive_requirement(pid, rid, body or {})

    def restore_requirement(self, body, pid, rid):
        with self.lock:
            return self.workflow.restore_requirement(pid, rid, body or {})

    def compare(self, body, pid):
        with self.lock:
            return self.workflow.compare(pid, body or {}, invoked_via="http")

    def inspect(self, _body, pid, sid, vid, start, end):
        return self.workflow.inspect(pid, sid, vid, start, end)

    def original(self, _body, pid, sid, vid):
        return Raw(*self.workflow.original(pid, sid, vid))

    def synthetic_relation_search(self, _body):
        with self.lock:
            return self.workflow.load_synthetic_example()

    # ---------------- P4-T02
    def execution_mode(self, _body, pid=None):
        from patent_to_pilot.workbench.modes import execution_status
        return execution_status(self.core, pid)

    def credentials(self, _body):
        from patent_to_pilot.workbench.modes import execution_status
        out = execution_status(self.core)
        return {"credentials": out["credentials"], "secrets_policy": out["secrets_policy"]}


def make_handler(app: App):
    allowed_hosts = {f"{app.host}:{app.port}", f"localhost:{app.port}", f"127.0.0.1:{app.port}"}

    class Handler(BaseHTTPRequestHandler):
        server_version = "PTP-Workbench/G01"

        def log_message(self, fmt, *args):  # keep the owner's terminal readable
            return

        def _send(self, status: int, payload: bytes, ctype: str, extra: dict | None = None) -> None:
            self.send_response(status)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            for k, v in (extra or {}).items():
                self.send_header(k, v)
            self.end_headers()
            self.wfile.write(payload)

        def _json(self, status: int, obj) -> None:
            self._send(status, json.dumps(obj, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")

        def _dispatch(self, method: str) -> None:
            if self.headers.get("Host") not in allowed_hosts:
                return self._json(403, {"error": "forbidden_host", "message": "loopback host required"})
            path = urlsplit(self.path).path
            if method == "GET" and path in STATIC_FILES:
                f = STATIC_DIR / STATIC_FILES[path]
                ctype = (mimetypes.guess_type(f.name)[0] or "text/plain") + "; charset=utf-8"
                return self._send(200, f.read_bytes(), ctype)
            body = None
            if method == "POST":
                origin = self.headers.get("Origin")
                if origin and urlsplit(origin).netloc not in allowed_hosts:
                    return self._json(403, {"error": "forbidden_origin", "message": "cross-origin request refused"})
                if not (self.headers.get("Content-Type") or "").startswith("application/json"):
                    return self._json(415, {"error": "json_required", "message": "POST requires application/json"})
                n = int(self.headers.get("Content-Length") or 0)
                if n > (UPLOAD_LIMIT if path.endswith("/documents") else BODY_LIMIT):
                    return self._json(413, {"error": "too_large", "message": "request body too large"})
                raw = self.rfile.read(n) if n else b"{}"
                try:
                    body = json.loads(raw.decode("utf-8") or "{}")
                except (UnicodeDecodeError, json.JSONDecodeError):
                    return self._json(400, {"error": "bad_json", "message": "request body is not valid JSON"})
            for m, pattern, name in ROUTES:
                match = re.fullmatch(pattern, path)
                if m == method and match:
                    try:
                        out = getattr(app, name)(body, *[unquote(g) for g in match.groups()])
                        if isinstance(out, Raw):  # owner-supplied bytes: shown inline, never run as a page
                            ctype = "application/pdf" if out.media_type == "application/pdf" else "text/plain; charset=utf-8"
                            return self._send(200, out.data, ctype, {
                                "Content-Disposition": f'inline; filename="{out.filename}"',
                                "Content-Security-Policy": "sandbox"})
                        return self._json(200, out)
                    except CoreError as exc:
                        return self._json(exc.status, {"error": exc.code, "message": str(exc)})
                    except Exception as exc:  # no stack traces to the browser; details stay in the terminal
                        print(f"[workbench] internal error on {method} {path}: {type(exc).__name__}: {exc}")
                        return self._json(500, {"error": "internal_error", "message": type(exc).__name__})
            return self._json(404, {"error": "no_route", "message": f"{method} {path} is not a route"})

        def do_GET(self):  # noqa: N802
            self._dispatch("GET")

        def do_POST(self):  # noqa: N802
            self._dispatch("POST")

    return Handler


class ExclusiveServer(ThreadingHTTPServer):
    """Never share a port with another process. HTTPServer sets SO_REUSEADDR, which on Windows lets a second
    process bind a port that is already in use (observed during G01 QA). Use exclusive binding instead."""

    allow_reuse_address = False
    daemon_threads = True

    def server_bind(self):
        if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        super().server_bind()


def create_server(core: EvidenceCore, host: str = "127.0.0.1", port: int = 8765) -> ThreadingHTTPServer:
    if host not in ("127.0.0.1", "localhost", "::1"):
        raise ValueError("the workbench binds to loopback only")
    srv = ExclusiveServer((host, port), None)
    real_port = srv.server_address[1]
    srv.RequestHandlerClass = make_handler(App(core, host, real_port))
    return srv
