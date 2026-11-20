"""Loopback HTTP app for the G01 Workbench: JSON API + bundled static frontend, one Python process.

Every route calls the shared ``EvidenceCore`` (the same service the CLI uses). Static files are served only
from the package's ``static/`` directory; source files, the store and test-only expectations are never mounted.
"""
from __future__ import annotations

import json
import mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import re
import socket
import threading
from urllib.parse import unquote, urlsplit

from patent_to_pilot.workbench.core import CoreError, EvidenceCore

STATIC_DIR = Path(__file__).resolve().parent / "static"
STATIC_FILES = {"/": "index.html", "/index.html": "index.html", "/app.js": "app.js", "/app.css": "app.css"}
_SEG = r"([A-Za-z0-9._-]+)"
ROUTES = [
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
]


class App:
    def __init__(self, core: EvidenceCore, host: str, port: int) -> None:
        self.core, self.host, self.port = core, host, port
        self.lock = threading.Lock()   # one state-changing core operation at a time

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


def make_handler(app: App):
    allowed_hosts = {f"{app.host}:{app.port}", f"localhost:{app.port}", f"127.0.0.1:{app.port}"}

    class Handler(BaseHTTPRequestHandler):
        server_version = "PTP-Workbench/G01"

        def log_message(self, fmt, *args):  # keep the owner's terminal readable
            return

        def _send(self, status: int, payload: bytes, ctype: str) -> None:
            self.send_response(status)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
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
                if n > 65536:
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
                        return self._json(200, getattr(app, name)(body, *[unquote(g) for g in match.groups()]))
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
