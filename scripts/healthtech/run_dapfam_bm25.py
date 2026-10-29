"""Run a deterministic DAPFAM BM25 title+abstract retrieval diagnostic.

The DAPFAM corpus, queries, and qrels are research-only inputs. This runner
keeps raw exports in a temporary directory and writes only rankings, metrics,
and a provenance manifest to the ignored HealthTech results directory.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import subprocess
import sys
import tempfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[2]
TOKEN_RE = re.compile(r"\w+", re.UNICODE)


def tokenize(text: str) -> list[str]:
    """Use the declared lowercase word-token policy for both views."""

    return TOKEN_RE.findall((text or "").lower())


class SparseBM25:
    """BM25Okapi-equivalent scorer backed by term postings.

    The reference rank_bm25 implementation scans every document for every
    query term. This implementation preserves its IDF and denominator
    contract while touching only documents present in each term's postings.
    """

    def __init__(self, corpus: list[list[str]], *, k1: float, b: float, epsilon: float) -> None:
        try:
            import numpy as np
        except ImportError as exc:
            raise RuntimeError("numpy is required for the DAPFAM component runner") from exc

        if not corpus:
            raise ValueError("corpus must not be empty")
        self.np = np
        self.k1 = k1
        self.b = b
        self.epsilon = epsilon
        self.corpus_size = len(corpus)
        self.doc_len = np.asarray([len(document) for document in corpus], dtype=np.float64)
        self.avgdl = float(self.doc_len.mean())
        if self.avgdl <= 0:
            raise ValueError("corpus has no tokens")

        postings: dict[str, list[tuple[int, int]]] = defaultdict(list)
        document_frequency: Counter[str] = Counter()
        for doc_id, document in enumerate(corpus):
            counts = Counter(document)
            for term, frequency in counts.items():
                postings[term].append((doc_id, frequency))
                document_frequency[term] += 1

        idf: dict[str, float] = {}
        negative_terms: list[str] = []
        idf_sum = 0.0
        for term, frequency in document_frequency.items():
            value = math.log(self.corpus_size - frequency + 0.5) - math.log(frequency + 0.5)
            idf[term] = value
            idf_sum += value
            if value < 0:
                negative_terms.append(term)
        average_idf = idf_sum / len(idf) if idf else 0.0
        floor = epsilon * average_idf
        for term in negative_terms:
            idf[term] = floor
        self.idf = idf
        self.postings = {
            term: (
                np.asarray([doc_id for doc_id, _ in values], dtype=np.int32),
                np.asarray([frequency for _, frequency in values], dtype=np.float64),
            )
            for term, values in postings.items()
        }

    def get_scores(self, query: list[str]):
        scores = self.np.zeros(self.corpus_size, dtype=self.np.float64)
        for term in query:
            posting = self.postings.get(term)
            if posting is None:
                continue
            doc_ids, term_frequencies = posting
            denominator = term_frequencies + self.k1 * (
                1.0 - self.b + self.b * self.doc_len[doc_ids] / self.avgdl
            )
            scores[doc_ids] += self.idf[term] * (
                term_frequencies * (self.k1 + 1.0) / denominator
            )
        return scores


def top_indices(scores, k: int) -> list[int]:
    """Return deterministic top-k indices, resolving score ties by index."""

    import numpy as np

    if k >= len(scores):
        candidates = np.arange(len(scores), dtype=np.int32)
    else:
        threshold = float(np.partition(scores, -k)[-k])
        candidates = np.flatnonzero(scores >= threshold)
    ordered = np.lexsort((candidates, -scores[candidates]))
    return candidates[ordered[:k]].tolist()


def sql_literal(path: Path) -> str:
    return str(path.resolve()).replace("\\", "/").replace("'", "''")


def export_parquet(duckdb: Path, source: Path, destination: Path, columns: str) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    sql = (
        f"COPY (SELECT {columns} FROM read_parquet('{sql_literal(source)}')) "
        f"TO '{sql_literal(destination)}' "
        "(FORMAT CSV, HEADER TRUE, DELIMITER '\\t');"
    )
    subprocess.run(
        [str(duckdb), ":memory:", "-c", sql],
        cwd=ROOT,
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
    )


def read_rows(path: Path) -> Iterable[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        yield from csv.DictReader(handle, delimiter="\t")


def read_corpus(path: Path) -> tuple[list[str], list[list[str]]]:
    ids: list[str] = []
    documents: list[list[str]] = []
    for row in read_rows(path):
        ids.append(row["relevant_id"])
        text = f"{row.get('title_en') or ''} {row.get('abstract_en') or ''}"
        documents.append(tokenize(text))
    if len(ids) != len(set(ids)):
        raise ValueError("corpus contains duplicate relevant_id values")
    return ids, documents


def read_queries(path: Path) -> tuple[list[str], list[list[str]]]:
    ids: list[str] = []
    queries: list[list[str]] = []
    for row in read_rows(path):
        ids.append(row["query_id"])
        text = f"{row.get('title_en') or ''} {row.get('abstract_en') or ''}"
        queries.append(tokenize(text))
    if len(ids) != len(set(ids)):
        raise ValueError("queries contains duplicate query_id values")
    return ids, queries


def read_qrels(path: Path) -> tuple[dict[str, dict[str, float]], dict[str, dict[str, set[str]]]]:
    qrels: dict[str, dict[str, float]] = defaultdict(dict)
    domain_positives: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    for row in read_rows(path):
        query_id = row["query_id"]
        relevant_id = row["relevant_id"]
        if relevant_id in qrels[query_id]:
            raise ValueError(f"duplicate qrel pair: {query_id} / {relevant_id}")
        score = float(row["relevance_score"])
        qrels[query_id][relevant_id] = score
        if score > 0:
            domain = row.get("domain_rel") or "UNKNOWN"
            domain_positives[domain][query_id].add(relevant_id)
    return qrels, domain_positives


def dcg_at_k(ranked_ids: list[str], labels: dict[str, float], k: int) -> float:
    total = 0.0
    for rank, relevant_id in enumerate(ranked_ids[:k], start=1):
        relevance = labels.get(relevant_id, 0.0)
        total += (2.0**relevance - 1.0) / math.log2(rank + 1.0)
    return total


def ndcg_at_k(ranked_ids: list[str], labels: dict[str, float], k: int) -> float:
    ideal = sorted(labels.values(), reverse=True)[:k]
    ideal_dcg = sum((2.0**relevance - 1.0) / math.log2(rank + 1.0) for rank, relevance in enumerate(ideal, start=1))
    return dcg_at_k(ranked_ids, labels, k) / ideal_dcg if ideal_dcg else 0.0


def evaluate(
    ranked_by_query: dict[str, list[str]],
    qrels: dict[str, dict[str, float]],
    *,
    k: int,
) -> dict[str, float | int]:
    recalls: list[float] = []
    ndcgs: list[float] = []
    total_hits = 0
    total_positives = 0
    for query_id, labels in qrels.items():
        ranked = ranked_by_query.get(query_id, [])
        positives = {relevant_id for relevant_id, relevance in labels.items() if relevance > 0}
        hits = len(set(ranked[:k]) & positives)
        recalls.append(hits / len(positives) if positives else 0.0)
        ndcgs.append(ndcg_at_k(ranked, labels, k))
        total_hits += hits
        total_positives += len(positives)
    return {
        "query_count": len(qrels),
        "macro_recall_at_k": sum(recalls) / len(recalls) if recalls else 0.0,
        "micro_recall_at_k": total_hits / total_positives if total_positives else 0.0,
        "macro_ndcg_at_k": sum(ndcgs) / len(ndcgs) if ndcgs else 0.0,
        "positive_qrels": total_positives,
        "hits_at_k": total_hits,
        "k": k,
    }


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def git_revision() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def git_worktree_dirty() -> bool:
    result = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=all"],
        cwd=ROOT,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return bool(result.stdout.strip())


def code_provenance() -> dict[str, object]:
    entrypoint = Path(__file__).resolve()
    return {
        "entrypoint": display_path(entrypoint),
        "sha256": sha256_file(entrypoint),
        "git_revision": git_revision(),
        "working_tree_dirty": git_worktree_dirty(),
    }


def run(args: argparse.Namespace) -> dict[str, object]:
    output = args.output.resolve()
    if output.exists() and any(output.iterdir()):
        raise FileExistsError(f"output directory is not empty: {output}")
    output.mkdir(parents=True, exist_ok=True)

    corpus_path = args.corpus.resolve()
    queries_path = args.queries.resolve()
    qrels_path = args.qrels.resolve()
    for path in (corpus_path, queries_path, qrels_path):
        if not path.is_file():
            raise FileNotFoundError(path)

    with tempfile.TemporaryDirectory(prefix="dapfam-bm25-") as temp_dir:
        temp = Path(temp_dir)
        corpus_csv = temp / "corpus.csv"
        queries_csv = temp / "queries.csv"
        qrels_csv = temp / "qrels.csv"
        export_parquet(args.duckdb, corpus_path, corpus_csv, "relevant_id, title_en, abstract_en")
        export_parquet(args.duckdb, queries_path, queries_csv, "query_id, title_en, abstract_en")
        export_parquet(args.duckdb, qrels_path, qrels_csv, "query_id, relevant_id, relevance_score, domain_rel")

        corpus_ids, corpus_documents = read_corpus(corpus_csv)
        query_ids, query_documents = read_queries(queries_csv)
        qrels, domain_positives = read_qrels(qrels_csv)

    corpus_id_set = set(corpus_ids)
    query_id_set = set(query_ids)
    qrel_query_ids = set(qrels)
    qrel_target_ids = {relevant_id for labels in qrels.values() for relevant_id in labels}
    if qrel_query_ids != query_id_set:
        raise ValueError("qrels/query ID coverage mismatch")
    if not qrel_target_ids.issubset(corpus_id_set):
        raise ValueError("qrels/corpus ID coverage mismatch")

    bm25 = SparseBM25(corpus_documents, k1=args.k1, b=args.b, epsilon=args.epsilon)
    ranked_by_query: dict[str, list[str]] = {}
    score_by_query: dict[str, list[float]] = {}
    rankings_path = output / "rankings.jsonl"
    with rankings_path.open("w", encoding="utf-8") as handle:
        for query_id, query_tokens in zip(query_ids, query_documents):
            scores = bm25.get_scores(query_tokens)
            order = top_indices(scores, args.k)
            ranked = [corpus_ids[index] for index in order]
            ranked_scores = [float(scores[index]) for index in order]
            ranked_by_query[query_id] = ranked
            score_by_query[query_id] = ranked_scores
            handle.write(json.dumps({"query_id": query_id, "ranked_ids": ranked, "scores": ranked_scores}) + "\n")

    metrics = evaluate(ranked_by_query, qrels, k=args.k)
    domain_metrics = {
        domain: evaluate(
            ranked_by_query,
            {query_id: {relevant_id: 1.0 for relevant_id in ids} for query_id, ids in per_query.items()},
            k=args.k,
        )
        for domain, per_query in domain_positives.items()
        if domain != "NC"
    }
    summary = {
        "status": "PASS",
        "task": "DAPFAM patent-family retrieval diagnostic",
        "query_view": "TA",
        "target_view": "TA",
        "candidate_count": len(corpus_ids),
        "query_count": len(query_ids),
        "qrel_query_count": len(qrels),
        "qrel_pair_count": sum(len(labels) for labels in qrels.values()),
        "metrics_all_qrels": metrics,
        "positive_recall_by_domain": domain_metrics,
        "unjudged_policy": "qrels-only evaluation; unlisted pairs are not treated as negatives",
        "ht_t1_boundary": "separate component; not semantic device-product gold",
    }
    (output / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    manifest = {
        "run_id": output.name,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "code_revision": git_revision(),
        "code_provenance": code_provenance(),
        "inputs": {
            "corpus": {"path": display_path(corpus_path), "bytes": corpus_path.stat().st_size, "sha256": sha256_file(corpus_path)},
            "queries": {"path": display_path(queries_path), "bytes": queries_path.stat().st_size, "sha256": sha256_file(queries_path)},
            "qrels": {"path": display_path(qrels_path), "bytes": qrels_path.stat().st_size, "sha256": sha256_file(qrels_path)},
        },
        "method": {
            "name": "BM25Okapi",
            "query_view": "title_en + abstract_en",
            "target_view": "title_en + abstract_en",
            "tokenizer": "lowercase Unicode word tokens via re\\w+",
            "k": args.k,
            "k1": args.k1,
            "b": args.b,
            "epsilon": args.epsilon,
            "tie_break": "stable corpus order after descending score",
            "automatic_retries": 0,
            "provider_calls": 0,
        },
        "runtime": {
            "python": sys.version,
            "numpy": __import__("numpy").__version__,
        },
        "outputs": {
            "rankings": display_path(rankings_path),
            "summary": display_path(output / "summary.json"),
        },
        "limits": [
            "Citation-based family qrels are not semantic device-product judgments.",
            "Unlisted query-target pairs remain unjudged and are excluded from relevance claims.",
            "This is a deterministic lexical component diagnostic, not HT-B4 or an adaptive result.",
        ],
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--duckdb", type=Path, required=True)
    parser.add_argument("--corpus", type=Path, default=ROOT / "methodology/datasets/research-only-nc/corpus.parquet")
    parser.add_argument("--queries", type=Path, default=ROOT / "methodology/datasets/research-only-nc/queries.parquet")
    parser.add_argument("--qrels", type=Path, default=ROOT / "methodology/datasets/research-only-nc/qrels_all.parquet")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--k", type=int, default=100)
    parser.add_argument("--k1", type=float, default=1.5)
    parser.add_argument("--b", type=float, default=0.75)
    parser.add_argument("--epsilon", type=float, default=0.25)
    args = parser.parse_args()
    if args.k <= 0:
        parser.error("--k must be positive")
    summary = run(args)
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
