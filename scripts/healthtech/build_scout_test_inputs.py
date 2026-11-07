"""Frozen-protocol retrieval inputs for the DAPFAM test split (label-free).

For each query view b in {P (Qwen problem brief), T (title), R2 (Stage 0 full-patent query)} writes:
  u-b.jsonl  {id, text}                 full candidate set
  o-b.jsonl  {id, text, allowed_ipc3}   own field: families sharing an own IPC3 code
  x-b.jsonl  {id, text, excluded_ipc3}  other fields: families sharing none
A failed P brief writes no row, so that query's P rankings are empty (scored 0), as the protocol says.
Protocol: docs/healthtech/research/SOLUTION_SCOUT_FROZEN_PROTOCOL_20261106_EN.md.
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


def _rows(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def views(records: list[dict], qwen: dict[str, dict], full: dict[str, str]) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {}
    for record in records:
        qid, own = record["id"], record["own_ipc3"]
        texts = {"P": (qwen.get(qid, {}).get("P") or {}).get("parsed"), "T": record["title"], "R2": full.get(qid)}
        for view, text in texts.items():
            if not text:
                continue
            query = text if view == "R2" else DENSE_QUERY_PREFIX + text
            out.setdefault(f"u-{view}", []).append({"id": qid, "text": query})
            if own:
                out.setdefault(f"o-{view}", []).append({"id": qid, "text": query, "allowed_ipc3": own})
                out.setdefault(f"x-{view}", []).append({"id": qid, "text": query, "excluded_ipc3": own})
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--records", type=Path, required=True, help="run_qwen_scout_actions.py build --split-name test")
    parser.add_argument("--qwen-output", type=Path, required=True, help="generate --actions P output")
    parser.add_argument("--full-queries", type=Path, required=True, help="Stage 0 queries-dense.jsonl (R2 view)")
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    records = _rows(args.records)
    ids = {r["id"] for r in records}
    qwen = {r["id"]: r for r in _rows(args.qwen_output)}
    full = {r["id"]: r["text"] for r in _rows(args.full_queries) if r["id"] in ids}
    files = views(records, qwen, full)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    summary = {"queries": len(records), "p_failed": sum(1 for r in records if not (qwen.get(r["id"], {}).get("P") or {}).get("parsed")),
               "without_own_ipc3": sum(1 for r in records if not r["own_ipc3"]), "labels_used": False, "files": {}}
    for name, rows in sorted(files.items()):
        path = args.output_dir / f"{name}.jsonl"
        path.write_text("".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows), encoding="utf-8")
        summary["files"][name] = {"rows": len(rows), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
    (args.output_dir / "test-inputs.summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
