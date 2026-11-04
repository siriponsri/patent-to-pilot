"""Write label-free PAR4PC text inputs for remote encoding (no gold/silver/negative fields).

Query formulations (fixed before any dense scoring):
- full:  title + abstract + all claims of the application (as the lexical baseline)
- claim: target claim + title + abstract (target claim first so it survives truncation)
Options: title + abstract + claims, one row per unique patent_id.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pyarrow.parquet as parquet


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def join(*parts: object) -> str:
    return " ".join(str(p).strip() for p in parts if p)


def target_claim(context: dict, claim_number: int) -> str:
    claims = context.get("claims") or []
    if not 1 <= claim_number <= len(claims):
        raise ValueError("claim_number outside context claims")
    return str(claims[claim_number - 1])


def build(split_path: Path, out_dir: Path, split: str) -> dict:
    rows = parquet.read_table(split_path, columns=["application_number", "claim_number", "context", "options"]).to_pylist()
    queries_full, queries_claim, options = {}, {}, {}
    for row in rows:
        app, ctx = str(row["application_number"]), row["context"]
        queries_full.setdefault(app, join(ctx.get("title"), ctx.get("abstract"), *(ctx.get("claims") or [])))
        queries_claim[f"{app}:{row['claim_number']}"] = join(target_claim(ctx, row["claim_number"]), ctx.get("title"), ctx.get("abstract"))
        for option in row["options"].values():
            options.setdefault(str(option["patent_id"]), join(option.get("title"), option.get("abstract"), *(option.get("claims") or [])))
    out_dir.mkdir(parents=True, exist_ok=True)
    counts = {}
    for name, items in (("queries_full", queries_full), ("queries_claim", queries_claim), ("options", options)):
        path = out_dir / f"par4pc-{split}-{name}.jsonl"
        with path.open("x", encoding="utf-8") as handle:
            for key in sorted(items):
                handle.write(json.dumps({"id": key, "text": items[key], "text_sha256": sha(items[key])}, ensure_ascii=False) + "\n")
        counts[name] = {"rows": len(items), "file_sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
    return counts


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--par4pc-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    receipt = {split: build(args.par4pc_dir / f"{split}.parquet", args.output_dir, split) for split in ("validation", "test")}
    receipt["labels_included"] = False
    (args.output_dir / "inputs-receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
