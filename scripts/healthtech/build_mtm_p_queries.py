"""Turn Qwen P-brief outputs (run_qwen_scout_actions.py generate --actions P) into MTM dense query rows.

Each parsed brief becomes {"id", "text": DENSE_QUERY_PREFIX + brief}. A failed brief (parse error) gets no row, so
analyze_mtm.py scores that query 0 (rules §7: no retries). Prints counts; refuses to overwrite.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from patent_to_pilot.evaluation.dapfam_acquisition import DENSE_QUERY_PREFIX  # noqa: E402


def p_rows(lines, key: str = "P") -> tuple[list[dict], int]:
    rows, failed = [], 0
    for line in lines:
        if not line.strip():
            continue
        record = json.loads(line)
        brief = (record.get(key) or {}).get("parsed")
        if brief:
            rows.append({"id": record["id"], "text": DENSE_QUERY_PREFIX + brief})
        else:
            failed += 1
    return rows, failed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generated", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--key", default="P", help="generated field to use: P, or F_P for the MTM V6 function text")
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit("output exists: refusing to overwrite")
    rows, failed = p_rows(args.generated.read_text(encoding="utf-8").splitlines(), args.key)
    args.output.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    print(json.dumps({"queries": len(rows), "failed_briefs": failed,
                      "generated_sha256": hashlib.sha256(args.generated.read_bytes()).hexdigest(),
                      "output_sha256": hashlib.sha256(args.output.read_bytes()).hexdigest()}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
