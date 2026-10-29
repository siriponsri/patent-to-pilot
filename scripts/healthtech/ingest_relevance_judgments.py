"""Convert an authorized review submission into a validated judgment manifest."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from patent_to_pilot.evaluation.healthtech.judgment_submission import build_relevance_judgment_manifest
from patent_to_pilot.evaluation.healthtech.judgments import validate_relevance_judgment_manifest


def _read_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _read_jsonl(path: Path) -> list[dict]:
    rows = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"expected object at {path}:{line_number}")
        rows.append(value)
    return rows


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packet", type=Path, required=True)
    parser.add_argument("--submission", type=Path, required=True, help="JSONL rows supplied by an authorized reviewer")
    parser.add_argument("--source-manifest", type=Path, required=True)
    parser.add_argument("--authorization-manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists() or args.report.exists():
        parser.error("output or report already exists; choose fresh paths")
    packet = _read_json(args.packet)
    submission = _read_jsonl(args.submission)
    source_manifest = _read_json(args.source_manifest)
    authorization_manifest = _read_json(args.authorization_manifest)
    manifest = build_relevance_judgment_manifest(
        packet,
        submission,
        source_manifest,
        authorization_manifest=authorization_manifest,
        authorization_sha256=_sha256(args.authorization_manifest),
        packet_path=str(args.packet),
        packet_sha256=_sha256(args.packet),
    )
    runtime_query_ids = [row["query_id"] for row in packet["queries"]]
    runtime_universe = [row["patent_id_canonical"] for row in packet["patents"]]
    report = validate_relevance_judgment_manifest(
        manifest,
        runtime_query_ids=runtime_query_ids,
        runtime_universe=runtime_universe,
        runtime_sha256=packet["runtime"]["sha256"],
    )
    report.update({
        "manifest_path": str(args.output),
        "manifest_sha256": hashlib.sha256(json.dumps(manifest, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest(),
        "packet_path": str(args.packet),
        "packet_sha256": _sha256(args.packet),
        "submission_path": str(args.submission),
        "submission_sha256": _sha256(args.submission),
        "authorization_manifest_path": str(args.authorization_manifest),
        "authorization_manifest_sha256": _sha256(args.authorization_manifest),
    })
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": report["status"],
        "output": str(args.output),
        "report": str(args.report),
        "judged_pair_count": report["judged_pair_count"],
        "unjudged_pair_count": report["unjudged_pair_count"],
        "generalization_status": report["generalization_status"],
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
