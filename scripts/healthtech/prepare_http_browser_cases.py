"""Prepare temporary named-device DossierInput cases for browser acceptance."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from patent_to_pilot.healthtech.abbott import build_abbott_case_inputs  # noqa: E402


CASE_ORDER = ["HT-DEV-MITRACLIP", "HT-DEV-TENDYNE", "HT-DEV-TRICLIP"]


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cohort", type=Path, required=True)
    parser.add_argument("--rights-matrix", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    cases = build_abbott_case_inputs(args.cohort, rights_matrix_path=args.rights_matrix)
    missing = [case_id for case_id in CASE_ORDER if case_id not in cases]
    if missing:
        raise ValueError(f"Abbott cohort is missing cases: {missing}")
    payload = {
        "format": "ht-browser-abbott-cases-v1",
        "case_order": CASE_ORDER,
        "cohort_runtime_sha256": _sha256_file(args.cohort / "runtime.json"),
        "cases": {case_id: cases[case_id].model_dump(mode="json") for case_id in CASE_ORDER},
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "PASS_PREPARED_TEMP_BROWSER_CASES", "cases": CASE_ORDER}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
