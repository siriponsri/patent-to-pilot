"""Run the three named Abbott cases through the loopback HTTP/vector path."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import http.client
import json
from pathlib import Path
import tempfile
import time
from threading import Thread
from typing import Any
from urllib.parse import urlencode

ROOT = Path(__file__).resolve().parents[2]
import sys

sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from patent_to_pilot.healthtech.abbott import build_abbott_case_inputs
from patent_to_pilot.healthtech.http import create_server


CASE_ORDER = ["HT-DEV-MITRACLIP", "HT-DEV-TENDYNE", "HT-DEV-TRICLIP"]


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _request(server: Any, method: str, path: str, payload: Any = None, headers: dict[str, str] | None = None) -> tuple[int, Any]:
    host, port = server.server_address[:2]
    connection = http.client.HTTPConnection(host, port, timeout=60)
    body = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request_headers = {"Accept": "application/json", "Content-Type": "application/json"}
    request_headers.update(headers or {})
    connection.request(method, path, body=body, headers=request_headers)
    response = connection.getresponse()
    raw = response.read()
    content_type = response.getheader("Content-Type", "")
    connection.close()
    value = json.loads(raw.decode("utf-8")) if "json" in content_type else raw.decode("utf-8")
    return response.status, value


def _wait_for(server: Any, job_id: str) -> dict[str, Any]:
    for _ in range(600):
        status, payload = _request(server, "GET", f"/jobs/{job_id}")
        if status != 200:
            raise RuntimeError(f"status failed: {status} {payload}")
        job = payload["job"]
        if job["state"] in {"succeeded", "failed", "cancelled"}:
            return job
        time.sleep(0.05)
    raise TimeoutError(f"job did not reach a terminal state: {job_id}")


def _config_file(args: argparse.Namespace, directory: Path) -> Path:
    config = {
        "format": "ht-http-vector-config-v1",
        "corpus_bundle": str(args.corpus_bundle.resolve()),
        "query_bundle": str(args.query_bundle.resolve()),
        "corpus_runtime": str(args.corpus_runtime.resolve()),
        "query_runtime": str(args.query_runtime.resolve()),
    }
    path = directory / "vector-config.json"
    path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    return path


def run(args: argparse.Namespace) -> dict[str, Any]:
    cases = build_abbott_case_inputs(args.cohort, rights_matrix_path=args.rights_matrix)
    missing = [case_id for case_id in CASE_ORDER if case_id not in cases]
    if missing:
        raise ValueError(f"Abbott cohort is missing cases: {missing}")
    with tempfile.TemporaryDirectory(prefix="ht-http-device-cases-") as temp_dir:
        vector_config = _config_file(args, Path(temp_dir))
        server = create_server(
            "127.0.0.1",
            0,
            Path(temp_dir) / "jobs",
            code_commit=args.code_commit,
            vector_config=vector_config,
        )
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        results: list[dict[str, Any]] = []
        try:
            provider_status, provider_catalog = _request(server, "GET", "/providers")
            if provider_status != 200:
                raise RuntimeError(f"provider catalog failed: {provider_status} {provider_catalog}")
            vector_provider = next(item for item in provider_catalog["providers"] if item["id"] == "local-vector")
            for case_id in CASE_ORDER:
                case = cases[case_id]
                payload = {
                    "input": case.model_dump(mode="json"),
                    "provider": {"id": "local-vector"},
                }
                status, submitted = _request(
                    server,
                    "POST",
                    "/jobs",
                    payload,
                    {"Idempotency-Key": f"real-{case_id.lower()}"},
                )
                if status not in {200, 202}:
                    raise RuntimeError(f"submit failed for {case_id}: {status} {submitted}")
                job_id = submitted["job"]["job_id"]
                job = _wait_for(server, job_id)
                if job["state"] != "succeeded":
                    raise RuntimeError(f"case failed for {case_id}: {job}")
                _, result = _request(server, "GET", f"/jobs/{job_id}/result")
                dossier = result["dossier"]
                manifest = result["manifest"]
                events = result["events"]
                source_id = case.query.selected_comparator_source_id
                source_status, source = _request(
                    server,
                    "GET",
                    f"/jobs/{job_id}/source/{source_id}?field=trade_name",
                )
                edit_status, edit = _request(
                    server,
                    "POST",
                    f"/jobs/{job_id}/history/1/edits",
                    {"edits": {"review_note": "reviewed through real vector HTTP case"}, "expected_parent_version": 1},
                )
                history_status, history = _request(server, "GET", f"/jobs/{job_id}/history")
                export_hashes: dict[str, str] = {}
                export_versions: dict[str, int] = {}
                for language in ("json", "th", "en"):
                    query = {"version": "2", "format": "json" if language == "json" else "markdown", "language": "auto" if language == "json" else language, "purpose": "local_research"}
                    export_status, exported = _request(server, "GET", f"/jobs/{job_id}/export?{urlencode(query)}")
                    if export_status != 200:
                        raise RuntimeError(f"export failed for {case_id}/{language}: {export_status} {exported}")
                    encoded = json.dumps(exported, ensure_ascii=False, sort_keys=True).encode("utf-8") if language == "json" else str(exported).encode("utf-8")
                    export_hashes[language] = _sha256_bytes(encoded)
                    export_versions[language] = int(exported["version"]) if language == "json" else 2
                dense_count = sum(1 for candidate in dossier["candidates"] if "dense_cosine" in candidate.get("scores", {}))
                results.append({
                    "case_id": case_id,
                    "job_id": job_id,
                    "state": job["state"],
                    "provider": job["provider"],
                    "source_inspection": {"status": source_status, "field": "trade_name", "payload_present": bool(source.get("payload"))},
                    "history": {"status": history_status, "versions": history["history"]["versions"], "edit_status": edit_status, "edited_version": edit["version"]},
                    "dossier": {
                        "candidate_count": len(dossier["candidates"]),
                        "dense_candidate_count": dense_count,
                        "evidence_count": len(dossier["evidence"]),
                        "event_count": len(events),
                        "vector_errors": [error for event in events for error in event.get("errors", []) if "vector" in error],
                        "stop_reason": manifest["stop_reason"],
                    },
                    "exports": {"status": "PASS", "versions": export_versions, "sha256": export_hashes},
                    "provider_calls": 0,
                    "paid_cost_usd": 0.0,
                })
        finally:
            server.shutdown()
            thread.join(timeout=5)
            server.healthtech_service.close()
    return {
        "format": "ht-real-http-vector-device-cases-v1",
        "status": "PASS_REAL_HTTP_VECTOR_DEVICE_CASES",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "code_commit": args.code_commit,
        "provider": vector_provider,
        "cases": results,
        "counts": {"cases": len(results), "passed": sum(item["state"] == "succeeded" for item in results)},
        "inputs": {
            "cohort_sha256": _sha256_bytes(args.cohort.joinpath("runtime.json").read_bytes()),
            "corpus_runtime_sha256": _sha256_bytes(args.corpus_runtime.read_bytes()),
            "query_runtime_sha256": _sha256_bytes(args.query_runtime.read_bytes()),
            "corpus_manifest_sha256": _sha256_bytes((args.corpus_bundle / "manifest.json").read_bytes()),
            "query_manifest_sha256": _sha256_bytes((args.query_bundle / "manifest.json").read_bytes()),
        },
        "boundaries": [
            "The browser did not receive server-owned vector paths or raw vector bundles.",
            "The three Abbott cases are public-source local-research engineering cases; product-level disclosure is not semantic claim relevance gold.",
            "No local Qwen generation was dispatched by this HTTP runner; the existing frozen-pack generation receipt is a separate artifact.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cohort", type=Path, required=True)
    parser.add_argument("--rights-matrix", type=Path, required=True)
    parser.add_argument("--corpus-runtime", type=Path, required=True)
    parser.add_argument("--query-runtime", type=Path, required=True)
    parser.add_argument("--corpus-bundle", type=Path, required=True)
    parser.add_argument("--query-bundle", type=Path, required=True)
    parser.add_argument("--code-commit", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run(args)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "cases": result["counts"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
