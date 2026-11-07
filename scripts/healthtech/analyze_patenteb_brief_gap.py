"""E5 of the frozen Solution Scout protocol: title brief vs full text on PatenTEB retrieval_OUT test.

  build    corpus.jsonl {id, title, abstract, claims=""} from all pos/neg families; queries-full.jsonl and
           queries-title.jsonl {id, text} with the dense query prompt; positives.json {query: [families]}.
           Every query or candidate family that is a DAPFAM query or corpus family is dropped (pre-declared).
  analyze  T - full on Recall@20 and @200 from two dense runner rankings (run once; first output final).
PatenTEB texts are "title [SEP] abstract"; split at the first [SEP]. No IPC codes exist here, so only the
brief-cost contrast (E2b) is replicated. Protocol: docs/healthtech/research/SOLUTION_SCOUT_FROZEN_PROTOCOL_20261106_EN.md.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from patent_to_pilot.evaluation.dapfam_acquisition import DENSE_QUERY_PREFIX, POOL_DEPTH  # noqa: E402
from patent_to_pilot.evaluation.scout_frozen import brief_gap  # noqa: E402


def split_text(text: str) -> tuple[str, str]:
    title, _, abstract = (text or "").partition("[SEP]")
    return " ".join(title.split()), " ".join(abstract.split())


def build(args: argparse.Namespace) -> int:
    import pyarrow.parquet as pq

    dapfam = {str(v) for v in pq.read_table(args.dapfam_queries, columns=["query_id"]).column("query_id").to_pylist()}
    dapfam |= {str(v) for v in pq.read_table(args.dapfam_corpus, columns=["relevant_id"]).column("relevant_id").to_pylist()}
    rows = pq.read_table(args.patenteb).to_pylist()
    docs: dict[str, str] = {}
    queries: dict[str, str] = {}
    positives: dict[str, set[str]] = {}
    for r in rows:
        docs.setdefault(r["pos"], r["pos_text"])
        docs.setdefault(r["neg"], r["neg_text"])
        queries.setdefault(r["q"], r["q_text"])
        positives.setdefault(r["q"], set()).add(r["pos"])
    kept_docs = {d: t for d, t in docs.items() if d not in dapfam}
    kept_q = {q: t for q, t in queries.items() if q not in dapfam}
    kept_pos = {q: sorted(p & set(kept_docs)) for q, p in positives.items() if q in kept_q}
    kept_pos = {q: p for q, p in kept_pos.items() if p}
    args.output_dir.mkdir(parents=True, exist_ok=True)
    corpus = args.output_dir / "corpus.jsonl"
    with corpus.open("w", encoding="utf-8") as handle:
        for d in sorted(kept_docs):
            title, abstract = split_text(kept_docs[d])
            handle.write(json.dumps({"id": d, "title": title, "abstract": abstract, "claims": ""}, ensure_ascii=False) + "\n")
    for view in ("full", "title"):
        with (args.output_dir / f"queries-{view}.jsonl").open("w", encoding="utf-8") as handle:
            for q in sorted(kept_pos):
                title, abstract = split_text(kept_q[q])
                text = title if view == "title" else " ".join(x for x in (title, abstract) if x)
                handle.write(json.dumps({"id": q, "text": DENSE_QUERY_PREFIX + text}, ensure_ascii=False) + "\n")
    (args.output_dir / "positives.json").write_text(json.dumps(kept_pos, indent=0) + "\n", encoding="utf-8")
    summary = {"triplets": len(rows), "queries": len(queries), "candidates": len(docs),
               "dropped_dapfam_queries": len(queries) - len(kept_q), "dropped_dapfam_candidates": len(docs) - len(kept_docs),
               "queries_kept": len(kept_pos), "candidates_kept": len(kept_docs),
               "patenteb_sha256": hashlib.sha256(args.patenteb.read_bytes()).hexdigest(),
               "corpus_sha256": hashlib.sha256(corpus.read_bytes()).hexdigest()}
    (args.output_dir / "build.summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=1))
    return 0


def analyze(args: argparse.Namespace) -> int:
    if args.output.exists():
        raise SystemExit("output exists: the frozen analysis runs once; write an amendment instead of overwriting")
    positives = {q: set(p) for q, p in json.loads(args.positives.read_text(encoding="utf-8")).items()}

    def load(path: Path) -> dict[str, list[str]]:
        return {r["query_id"]: r["families"][:POOL_DEPTH]
                for r in map(json.loads, path.read_text(encoding="utf-8").splitlines()) if r}

    result = {"format": "ptp-scout-patenteb-e5-v1",
              "inputs_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (args.positives, args.full, args.title)},
              **brief_gap(load(args.full), load(args.title), positives)}
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=1))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    b = sub.add_parser("build")
    b.add_argument("--patenteb", type=Path, required=True, help="retrieval_OUT/test/data.parquet")
    b.add_argument("--dapfam-queries", type=Path, default=ROOT / "methodology/datasets/research-only-nc/queries.parquet")
    b.add_argument("--dapfam-corpus", type=Path, default=ROOT / "methodology/datasets/research-only-nc/corpus.parquet")
    b.add_argument("--output-dir", type=Path, required=True)
    a = sub.add_parser("analyze")
    a.add_argument("--positives", type=Path, required=True)
    a.add_argument("--full", type=Path, required=True, help="dense rankings for queries-full.jsonl")
    a.add_argument("--title", type=Path, required=True, help="dense rankings for queries-title.jsonl")
    a.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    return build(args) if args.command == "build" else analyze(args)


if __name__ == "__main__":
    raise SystemExit(main())
