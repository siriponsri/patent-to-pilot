"""Turn solution-scout Qwen outputs into label-free retrieval inputs (dev only).

For each brief type b in {T (title), P (problem brief)} writes, in --output-dir:
  d-b.jsonl   {id, text}                  dense query: the brief
  x-b.jsonl   {id, text, excluded_ipc3}   cross-domain lane: the brief, families sharing an own IPC3 code dropped
  f-b.jsonl / fx-b.jsonl                  the function text, plain and cross-domain lane
  s-b.jsonl / sx-b.jsonl                  the other-industry solution sketch, plain and cross-domain lane
  bm25-b.jsonl {id, text}                 BM25 query: the brief without the dense prefix
A failed generation produces no row, so that arm contributes an empty list for that query.
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


def _write(path: Path, rows: list[dict]) -> dict:
    path.write_text("".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows), encoding="utf-8")
    return {"rows": len(rows), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--records", type=Path, required=True, help="build output of run_qwen_scout_actions.py")
    parser.add_argument("--qwen-output", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    own = {r["id"]: r["own_ipc3"] for r in map(json.loads, args.records.read_text(encoding="utf-8").splitlines()) if r}
    outputs = [json.loads(line) for line in args.qwen_output.read_text(encoding="utf-8").splitlines() if line.strip()]
    files: dict[str, list[dict]] = {}
    for row in outputs:
        qid = row["id"]
        briefs = {"T": row["title"], "P": (row.get("P") or {}).get("parsed")}
        for b, brief in briefs.items():
            texts = {"d": brief,
                     "f": ((row.get(f"F_{b}") or {}).get("parsed")),
                     "s": ((row.get(f"S_{b}") or {}).get("parsed"))}
            for arm, text in texts.items():
                if not text:
                    continue
                files.setdefault(f"{arm}-{b}", []).append({"id": qid, "text": DENSE_QUERY_PREFIX + text})
                lane = "x" if arm == "d" else f"{arm}x"
                files.setdefault(f"{lane}-{b}", []).append({"id": qid, "text": DENSE_QUERY_PREFIX + text,
                                                            "excluded_ipc3": own[qid]})
                if arm == "d":
                    files.setdefault(f"bm25-{b}", []).append({"id": qid, "text": text})
    args.output_dir.mkdir(parents=True, exist_ok=True)
    summary = {"qwen_output_sha256": hashlib.sha256(args.qwen_output.read_bytes()).hexdigest(),
               "records_sha256": hashlib.sha256(args.records.read_bytes()).hexdigest(), "queries": len(outputs),
               "files": {name: _write(args.output_dir / f"{name}.jsonl", rows) for name, rows in sorted(files.items())},
               "queries_without_own_ipc3": sum(1 for q in own.values() if not q), "labels_used": False}
    (args.output_dir / "scout-inputs.summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
