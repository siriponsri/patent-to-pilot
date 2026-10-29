"""Stage an already-authorized local semantic source within declared bounds."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from patent_to_pilot.evaluation.healthtech.source_acquisition import (
    stage_authorized_semantic_source,
)


def _read_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--authorization-manifest", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, required=True, help="Local authorized snapshot; no URL fetch is performed")
    parser.add_argument("--destination-root", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    receipt = stage_authorized_semantic_source(
        args.source_root,
        args.destination_root,
        _read_json(args.authorization_manifest),
        authorization_sha256=_sha256(args.authorization_manifest),
        receipt_path=args.receipt,
    )
    print(json.dumps({
        "status": receipt["status"],
        "source_id": receipt["source_id"],
        "source_sha256": receipt["source_sha256"],
        "completed_files": receipt["completed_files"],
        "actual_bytes": receipt["actual_bytes"],
        "receipt": str(args.receipt),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
