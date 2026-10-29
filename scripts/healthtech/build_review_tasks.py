"""Build a local-only reviewer task export from an unlabeled review packet."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from patent_to_pilot.evaluation.healthtech.review_tasks import (
    build_review_task_pack,
    validate_review_task_pack,
)
from patent_to_pilot.evaluation.healthtech.review_packet import validate_relevance_review_packet


def _read_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packet", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("output already exists; choose a fresh directory")

    packet = _read_json(args.packet)
    validate_relevance_review_packet(packet)
    task_pack = build_review_task_pack(
        packet,
        packet_path=str(args.packet),
        packet_sha256=_sha256(args.packet),
    )
    validate_review_task_pack(task_pack)
    args.output.mkdir(parents=True, exist_ok=True)

    tasks_path = args.output / "tasks.jsonl"
    tasks_path.write_text(
        "".join(json.dumps(task, ensure_ascii=False, sort_keys=True) + "\n" for task in task_pack["tasks"]),
        encoding="utf-8",
    )
    manifest = {key: value for key, value in task_pack.items() if key != "tasks"}
    manifest["artifacts"] = {
        "tasks": {
            "path": "tasks.jsonl",
            "sha256": _sha256(tasks_path),
        },
    }
    manifest_path = args.output / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": "PASS",
        "output": str(args.output),
        "task_count": task_pack["counts"]["task_count"],
        "response_count": task_pack["counts"]["response_count"],
        "semantic_label_count": task_pack["counts"]["semantic_label_count"],
        "manifest_sha256": _sha256(manifest_path),
        "tasks_sha256": _sha256(tasks_path),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
