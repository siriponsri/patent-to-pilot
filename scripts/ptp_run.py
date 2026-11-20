"""Patent-to-Pilot Workbench launcher and support commands (PTP-2026-11-21 / G01).

  python scripts/ptp_run.py                    serve the Workbench on 127.0.0.1 (default port 8765, or the next free one)
  python scripts/ptp_run.py --open             same, and open the browser after the health check
  python scripts/ptp_run.py --doctor           environment, store, lexical search, assets, port and provider report
  python scripts/ptp_run.py --smoke            full sample workflow in a fresh temporary store (owner data untouched)
  python scripts/ptp_run.py --run              run the sample comparison through the shared core (CLI path)
  python scripts/ptp_run.py --apply-change CHANGE-S2-V2
  python scripts/ptp_run.py --backup PATH      consistent copy of the store (SQLite backup API)

Data directory: --data-dir, else %PTP_DATA_DIR%, else %LOCALAPPDATA%\\PatentToPilot\\workbench.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import socket
import sqlite3
import sys
import tempfile
import threading
import time
import urllib.request
import webbrowser

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from patent_to_pilot.workbench import core as C  # noqa: E402
from patent_to_pilot.workbench.guard import loopback_only  # noqa: E402
from patent_to_pilot.workbench.server import STATIC_DIR, create_server  # noqa: E402

DEFAULT_PORT = 8765


def default_data_dir() -> Path:
    if os.environ.get("PTP_DATA_DIR"):
        return Path(os.environ["PTP_DATA_DIR"])
    base = os.environ.get("LOCALAPPDATA") or str(Path.home() / ".local" / "share")
    return Path(base) / "PatentToPilot" / "workbench"


def port_free(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex((host, port)) != 0


def bind_server(core, host: str, port: int, tries: int = 20):
    last = None
    for p in range(port, port + tries):
        try:
            return create_server(core, host, p)
        except OSError as exc:  # occupied: try the next port; never touch the other process
            last = exc
    raise SystemExit(f"No free port in {port}-{port + tries - 1} on {host}: {last}")


def http_json(method: str, url: str, body=None):
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(url, data=data, method=method, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


# ------------------------------------------------------------------ commands
def doctor(args) -> int:
    rep = {"program_id": C.PROGRAM_ID, "goal_id": C.GOAL_ID, "python": sys.executable,
           "python_version": platform.python_version(), "platform": platform.platform(),
           "sqlite_version": sqlite3.sqlite_version}
    ok = True
    try:
        con = sqlite3.connect(":memory:")
        con.execute("CREATE VIRTUAL TABLE t USING fts5(x, tokenize='unicode61')")
        rep["lexical_search"] = "sqlite_fts5_unicode61 available"
    except sqlite3.OperationalError as exc:
        rep["lexical_search"] = f"FTS5 unavailable: {exc}"
        ok = False
    data_dir = Path(args.data_dir) if args.data_dir else default_data_dir()
    try:
        data_dir.mkdir(parents=True, exist_ok=True)
        probe = data_dir / ".write-probe"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
        rep["data_dir"] = f"{data_dir} (writable)"
    except OSError as exc:
        rep["data_dir"] = f"{data_dir} NOT writable: {exc}"
        ok = False
    rep["frontend_assets"] = {n: (STATIC_DIR / n).is_file() for n in ("index.html", "app.js", "app.css")}
    ok &= all(rep["frontend_assets"].values())
    manifest = json.loads((C.SAMPLE_DIR / "source_manifest.json").read_text(encoding="utf-8"))
    hashes = {}
    for e in manifest["initial_sources"] + manifest["incoming_changes"]:
        h = hashlib.sha256((C.SAMPLE_DIR / e["path"]).read_bytes()).hexdigest()
        hashes[e["path"]] = "ok" if h == e["sha256"] else "HASH MISMATCH (check line endings)"
    rep["sample_inputs"] = hashes
    ok &= all(v == "ok" for v in hashes.values())
    rep["port"] = {"default": DEFAULT_PORT, "free": port_free(args.host, args.port)}
    rep["providers"] = {"lexical": "active", "local_model": "disabled", "api_model": "disabled",
                        "remote_calls": "not allowed", "model_downloads": "not allowed"}
    rep["result"] = "OK" if ok else "PROBLEM"
    print(json.dumps(rep, indent=2, ensure_ascii=False))
    return 0 if ok else 1


def smoke(args) -> int:
    """Real sample workflow in a fresh temporary store; checks invariants (no expected-answer file is read)."""
    tmp = Path(tempfile.mkdtemp(prefix="ptp-g01-smoke-"))
    checks, attempts = [], []

    def check(name, cond, detail=""):
        checks.append({"check": name, "pass": bool(cond), "detail": detail})

    t0 = time.time()
    with loopback_only(attempts):
        core = C.EvidenceCore(tmp)
        boot = core.bootstrap_sample()
        pv = core.project_view(boot["project_id"])
        check("initial searchable index = 4 versions, no incoming revision",
              pv["searchable_index"]["source_versions"] == ["DEMO-S1@v1", "DEMO-S2@v1", "DEMO-S3@v1", "DEMO-S4@v1"],
              str(pv["searchable_index"]))
        run = core.run_comparison(boot["project_id"], invoked_via="cli")
        check("CLI comparison run completed", run["status"] == "completed", run["stop_reason"])
        cells = core.comparison(boot["project_id"])["cells"]
        check("six assessments committed", len(cells) == 6)
        bad = []
        for cell in cells:
            if cell["outcome"] != "unknown":
                c = cell["citation"]
                if not c:
                    bad.append(cell["assessment_id"]); continue
                r = core.resolve_citation(boot["project_id"], c["source_id"], c["version_id"], c["passage_id"])
                full = core.source_version(boot["project_id"], c["source_id"], c["version_id"])["text"]
                if full[r["start_char"]:r["end_char"]] != r["quote"]:
                    bad.append(cell["assessment_id"])
        check("every non-unknown assessment has a literal, resolvable citation", not bad, str(bad))
        thai = core.resolve_citation(boot["project_id"], "DEMO-S3", "v1", "S3-P1")["quote"]
        check("Thai text preserved", "แคปซูลกักเก็บความร้อน" in thai)
        srv = bind_server(core, "127.0.0.1", 18765)
        url = f"http://127.0.0.1:{srv.server_address[1]}"
        th = threading.Thread(target=srv.serve_forever, daemon=True)
        th.start()
        try:
            check("HTTP health", http_json("GET", url + "/api/health")["status"] == "ok")
            ch = http_json("POST", url + f"/api/projects/{boot['project_id']}/changes", {"event_id": "CHANGE-S2-V2"})
            check("HTTP change applied through the same core", ch["already_applied"] is False, ch["run_id"])
            again = http_json("POST", url + f"/api/projects/{boot['project_id']}/changes", {"event_id": "CHANGE-S2-V2"})
            check("duplicate change is idempotent", again["already_applied"] is True)
            via = http_json("GET", url + f"/api/runs/{ch['run_id']}")["invoked_via"]
            check("change run recorded as invoked via http", via == "http")
            page = urllib.request.urlopen(url + "/", timeout=10).read().decode("utf-8")
            check("Workbench page served", "Patent-to-Pilot Workbench" in page)
        finally:
            srv.shutdown()
            srv.server_close()
        res = ch["result"]
        check("affected obligations come from stored dependencies", res["reacquired"] == ["CONCEPT-A/R2"], str(res["reacquired"]))
        pv2 = core.project_view(boot["project_id"])
        check("v2 current, v1 kept", pv2["current_versions"]["DEMO-S2"] == "v2" and
              any(s["source_id"] == "DEMO-S2" and s["version_id"] == "v1" and s["status"] == "historical" for s in pv2["sources"]))
        check("historical v1 citation still resolves", "40 to 70 °C" in
              core.resolve_citation(boot["project_id"], "DEMO-S2", "v1", "S2-P1")["quote"])
        core2 = C.EvidenceCore(tmp)    # restart: a new core instance on the same store
        pv3 = core2.project_view(boot["project_id"])
        check("restart restores runs, versions and change", len(pv3["runs"]) == 2 and
              pv3["changes"][0]["status"] == "applied" and len(pv3["sources"]) == 5)
    check("no remote connection attempted", not attempts, str(attempts))
    report = {"program_id": C.PROGRAM_ID, "goal_id": C.GOAL_ID, "data_origin": "synthetic_fixture",
              "execution_mode": "live_local", "temp_store": str(tmp), "seconds": round(time.time() - t0, 2),
              "checks": checks, "passed": all(c["pass"] for c in checks)}
    out = tmp / "smoke-report.json"
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    for c in checks:
        print(("PASS " if c["pass"] else "FAIL ") + c["check"])
    print(f"Smoke {'PASSED' if report['passed'] else 'FAILED'} in {report['seconds']} s. Report: {out}")
    return 0 if report["passed"] else 1


def serve(args) -> int:
    data_dir = Path(args.data_dir) if args.data_dir else default_data_dir()
    core = C.EvidenceCore(data_dir)
    srv = bind_server(core, args.host, args.port)
    url = f"http://{args.host}:{srv.server_address[1]}/"
    th = threading.Thread(target=srv.serve_forever, daemon=True)
    th.start()
    try:
        health = http_json("GET", url + "api/health")
    except Exception as exc:  # pragma: no cover - surfaced to the owner
        print(f"Server did not answer its health check: {exc}")
        return 1
    print("Patent-to-Pilot Workbench (PTP-2026-11-21 / G01) — lexical mode, sample data, no paid calls")
    print(f"  URL:        {url}")
    print(f"  Data store: {health['store']}")
    if srv.server_address[1] != args.port:
        print(f"  Note: port {args.port} was busy, so {srv.server_address[1]} is used.")
    print("  Stop with Ctrl+C (closing the browser does not stop the server).")
    if args.open and not os.environ.get("PTP_NO_BROWSER"):
        webbrowser.open(url)
    try:
        while th.is_alive():
            th.join(0.5)
    except KeyboardInterrupt:
        print("Stopping…")
    finally:
        srv.shutdown()
        srv.server_close()
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Patent-to-Pilot Workbench (PTP-2026-11-21 / G01)")
    ap.add_argument("--doctor", action="store_true")
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--run", action="store_true", help="run the sample comparison via the CLI path")
    ap.add_argument("--apply-change", metavar="EVENT_ID")
    ap.add_argument("--backup", metavar="PATH")
    ap.add_argument("--serve", action="store_true", help="serve (default when no other command is given)")
    ap.add_argument("--open", action="store_true", help="open the browser after the health check")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=DEFAULT_PORT)
    ap.add_argument("--data-dir")
    args = ap.parse_args(argv)
    if args.doctor:
        return doctor(args)
    if args.smoke:
        return smoke(args)
    if args.run or args.apply_change or args.backup:
        core = C.EvidenceCore(Path(args.data_dir) if args.data_dir else default_data_dir())
        if args.backup:
            print(f"Backup written: {core.store.backup(args.backup)}")
            return 0
        pid = core.bootstrap_sample()["project_id"]
        with loopback_only():
            out = (core.run_comparison(pid, invoked_via="cli") if args.run
                   else core.apply_change(pid, args.apply_change, invoked_via="cli"))
        print(json.dumps(out, indent=2, ensure_ascii=False))
        return 0
    return serve(args)


if __name__ == "__main__":
    sys.exit(main())
