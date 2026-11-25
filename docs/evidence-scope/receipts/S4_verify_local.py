"""Verify launcher, recovery and source pins against a disposable Windows store.

Run from the checkout with its release venv. The output directory must be new.
Supply the S2 originals directory to verify its local source archives.
"""
from contextlib import contextmanager
import argparse
import hashlib
import json
import os
from pathlib import Path
import socket
import sqlite3
import subprocess
import sys
from urllib.error import HTTPError
from urllib.request import Request, urlopen

REPO = Path(__file__).resolve().parents[3]
LAUNCHER = REPO / "scripts" / "ptp_run.py"
SAMPLES = REPO / "src" / "patent_to_pilot" / "workbench" / "sample"


def fetch(url, path, payload=None):
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = Request(url + path, data=body, headers={"Content-Type": "application/json"})
    with urlopen(req, timeout=10) as response:
        return json.load(response)


@contextmanager
def launch(store, port=0):
    args = ["--port", str(port), "--data-dir", str(store)]
    command = [sys.executable, str(LAUNCHER), "--serve"]
    env = dict(os.environ, PYTHONUTF8="1", PYTHONUNBUFFERED="1", PTP_NO_BROWSER="1")
    with subprocess.Popen([*command, *args], cwd=REPO, env=env, encoding="utf-8",
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT) as process:
        lines = []
        try:
            for line in process.stdout:
                lines.append(line.rstrip())
                if line.strip().startswith("URL:"):
                    yield line.split("URL:", 1)[1].strip().rstrip("/"), lines
                    return
            raise AssertionError(lines)
        finally:
            if process.poll() is None:
                process.terminate()
            process.wait(timeout=10)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def rebuild_without_one_source(work):
    def cli(store, *args):
        proc = subprocess.run([sys.executable, str(LAUNCHER), "--data-dir", str(store), *args],
                              capture_output=True, check=True, encoding="utf-8", timeout=30)
        return json.loads(proc.stdout)

    def compare(store, names):
        pid = cli(store, "--create-project", "S4 fictional comparison")["project_id"]
        for name in names:
            cli(store, "--ingest", str(SAMPLES / "sources" / f"{name}-v1.md"),
                "--source-id", name, "--project", pid, "--candidate", "CONCEPT-A")
        assert cli(store, "--run", "--project", pid)["status"] == "completed"
        with launch(store) as (url, _):
            path = f"/api/projects/{pid}"
            cells = {c["requirement_id"]: c for c in fetch(url, path + "/comparison")["cells"]
                     if c["candidate_id"] == "CONCEPT-A"}
            citations = {}
            for rid in ("R1", "R2"):
                citation = cells[rid]["citation"]
                if citation:
                    source = f"{path}/sources/{citation['source_id']}/versions/{citation['version_id']}"
                    resolved = fetch(url, f"{source}/passages/{citation['passage_id']}")
                    assert fetch(url, source)["text"][resolved["start_char"]:resolved["end_char"]] == resolved["quote"]
                    citations[rid] = resolved["quote"]
            return {rid: cells[rid]["outcome"] for rid in ("R1", "R2")}, citations

    before = compare(work / "pre-withdrawal", ("DEMO-S1", "DEMO-S2"))
    retained = compare(work / "retained-only", ("DEMO-S1",))
    assert before[0] == {"R1": "meets", "R2": "meets"} and "R2" in before[1]
    assert retained[0] == {"R1": "meets", "R2": "unknown"} and retained[1] == {"R1": before[1]["R1"]}
    return {"before": before[0], "rebuilt": retained[0]}


def run(work, originals):
    artifacts = {}
    catalogue = json.loads((SAMPLES / "scope_reader.json").read_text(encoding="utf-8-sig"))
    entries = {entry["id"]: entry for entry in catalogue["examples"]}
    store, restored = work / "store", work / "restored"
    restored.mkdir()
    with socket.socket() as busy:
        busy.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        busy.bind(("127.0.0.1", 0))
        busy.listen()
        occupied = busy.getsockname()[1]
        with launch(store, occupied) as (url, log):
            assert url != f"http://127.0.0.1:{occupied}" and fetch(url, "/api/health")["status"] == "ok"
            if os.environ.get("S4_REQUIRE_GUARD"):
                assert any("S4 LOOPBACK GUARD ACTIVE" in line for line in log)
            with socket.create_connection(("127.0.0.1", occupied), timeout=2):
                pass
            saved = {}
            for eid in ("pharma-15", "pharma-18", "eta-2544", "eta-2562-no3", "eta-case", "drug-print"):
                trace = fetch(url, "/api/scope/run", {"example_id": eid})
                entry = entries[eid]
                assert trace["source_sha256"] == digest(entry["text"].encode("utf-8"))
                for evidence in trace["evidence"]:
                    quote = entry["text"][evidence["start"]:evidence["end"]]
                    assert evidence["quote"] == quote
                    assert evidence["quote_sha256"] == digest(quote.encode("utf-8"))
                    assert (evidence["source_id"], evidence["version"], evidence["sha256"]) == (
                        entry["source_id"], entry["version"], trace["source_sha256"])
                saved[eid] = trace
            assert saved["eta-case"]["status"] == "qualified"
            assert [r["status"] for r in saved["eta-case"]["requirements"]] == ["bound", "unresolved"]
            assert saved["drug-print"]["effective_date"] is None
            with (work / "launcher.log").open("w", encoding="utf-8") as output:
                print(*log, sep="\n", file=output)
            backup = restored / "workbench.sqlite3"
            p = subprocess.run([sys.executable, str(LAUNCHER), "--backup", str(backup), "--data-dir", str(store)],
                               capture_output=True, encoding="utf-8", check=True, timeout=20)
            artifacts["backup_command_stdout"] = p.stdout.strip()
            with sqlite3.connect(backup) as db:
                assert db.execute("PRAGMA integrity_check").fetchone() == ("ok",)
            artifacts["backup_sha256"] = digest(backup.read_bytes())
            artifacts["occupied_port"] = occupied
            artifacts["selected_port"] = int(url.rsplit(":", 1)[1])
    for directory in (store, restored):
        with launch(directory) as (url, log):
            if os.environ.get("S4_REQUIRE_GUARD"):
                assert any("S4 LOOPBACK GUARD ACTIVE" in line for line in log)
            assert {r["id"] for r in fetch(url, "/api/scope/catalog")["runs"]} == {t["id"] for t in saved.values()}
            for trace in saved.values():
                assert fetch(url, "/api/scope/run/" + trace["id"]) == trace
            try:
                fetch(url, "/api/scope/run/missing")
                raise AssertionError("missing export resolved")
            except HTTPError as exc:
                assert exc.code == 404 and json.load(exc)["error"] == "missing_run"
    if originals:
        manifest = json.loads(Path(__file__).with_name("S2-sources.json").read_text(encoding="utf-8"))
        for item in manifest["originals"].values():
            content = (originals / item["file"]).read_bytes()
            assert (len(content), digest(content)) == (item["bytes"], item["sha256"])
        artifacts["originals_checked"] = len(manifest["originals"])
    artifacts["checks"] = ["occupied port preserved", "canonical citations", "partial signer evidence",
                           "unknown commencement", "online backup integrity", "restart replay",
                           "restored replay", "missing export rejected"]
    artifacts["rebuilt_without_one_source"] = rebuild_without_one_source(work)
    (work / "traces.json").write_text(json.dumps(saved, ensure_ascii=False, indent=2), encoding="utf-8")
    (work / "report.json").write_text(json.dumps(artifacts, indent=2), encoding="utf-8")
    print(json.dumps(artifacts, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("work", type=Path)
    parser.add_argument("--originals", type=Path)
    options = parser.parse_args()
    options.work.mkdir(parents=True)
    run(options.work, options.originals)
