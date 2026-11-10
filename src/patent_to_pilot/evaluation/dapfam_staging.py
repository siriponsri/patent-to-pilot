"""Owner-curator projection of pinned DAPFAM sources; never a runtime import.

The owner executes this boundary outside the development agent. No new split,
protected exports, encoding, scores or physical isolation claims are produced.
"""
import hashlib
import json
import math
from pathlib import Path

from patent_to_pilot.research.mtm_runtime import InputBoundaryError, identifier
from patent_to_pilot.evaluation.dapfam_native import DATASET_REVISION, MTEB_REVISION


def jsonl_bytes(rows):
    return "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows).encode("utf-8")


def stage_native_dev(corpus_rows, query_rows, relations, assignment, destination: Path, *,
                     source_hashes: dict, expected_dev: int, expected_protected: int,
                     expected_corpus: int, expected_corpus_sha256: str) -> dict:
    if destination.exists():
        raise InputBoundaryError("preserve existing staging attempt")
    if not isinstance(assignment, dict) or set(assignment.values()) != {"dev", "test"}:
        raise InputBoundaryError("invalid preserved split")
    if not source_hashes or any(not isinstance(v, str) or len(v) != 64 or
                               any(c not in '0123456789abcdef' for c in v) for v in source_hashes.values()):
        raise InputBoundaryError("invalid pinned source hashes")
    for key in assignment:
        identifier(key)
    if (sum(v == "dev" for v in assignment.values()) != expected_dev or
            sum(v == "test" for v in assignment.values()) != expected_protected):
        raise InputBoundaryError("preserved split count mismatch")
    corpus, corpus_ids = [], set()
    for row in corpus_rows:
        key = str(row["relevant_id"])
        identifier(key)
        if key in corpus_ids:
            raise InputBoundaryError("duplicate corpus family")
        corpus_ids.add(key)
        fields = [row[f] for f in ("title_en", "abstract_en", "claims_text")]
        if any(v is not None and not isinstance(v, str) for v in fields):
            raise InputBoundaryError("invalid corpus text")
        corpus.append(dict(zip(("id", "title", "abstract", "claims"), [key, *[v or "" for v in fields]])))
    if len(corpus) != expected_corpus:
        raise InputBoundaryError("corpus count mismatch")
    corpus_payload = jsonl_bytes(sorted(corpus, key=lambda r: r["id"]))
    if hashlib.sha256(corpus_payload).hexdigest() != expected_corpus_sha256:
        raise InputBoundaryError("corpus differs from historical vector input")
    dev_queries, seen_queries = [], set()
    for row in query_rows:
        key = str(row["query_id"])
        identifier(key)
        if key in seen_queries or key not in assignment:
            raise InputBoundaryError("invalid query population")
        seen_queries.add(key)
        if assignment[key] == "dev":
            fields = [row[f] for f in ("title_en", "abstract_en")]
            if any(v is not None and not isinstance(v, str) for v in fields):
                raise InputBoundaryError("invalid native TA query")
            text = "\n".join(v for v in fields if v)
            if not text.strip():
                raise InputBoundaryError("empty native query; no silent denominator reduction")
            dev_queries.append({"id": key, "text": text})
    if seen_queries != set(assignment):
        raise InputBoundaryError("missing assigned queries")
    dev_ids = {r["id"] for r in dev_queries}
    qrels, seen_relations = [], set()
    eligible = {p: set() for p in ("ALL", "IN", "OUT")}
    for row in relations:
        query, family = str(row["query_id"]), str(row["relevant_id"])
        if query not in assignment or family not in corpus_ids or (query, family) in seen_relations:
            raise InputBoundaryError("invalid relation identity")
        seen_relations.add((query, family))
        if query not in dev_ids:
            continue  # Never export protected labels, scores, IDs or statistics.
        score, domain = float(row["relevance_score"]), row["domain_rel"]
        if not math.isfinite(score) or domain not in {"IN", "OUT"}:
            raise InputBoundaryError("invalid dev annotation")
        qrels.append({"query_id": query, "relevant_id": family, "relevance_score": score, "domain_rel": domain})
        if score > 0:
            eligible["ALL"].add(query)
            eligible[domain].add(query)
    destination.mkdir(parents=True, exist_ok=False)
    runtime, evaluator = destination / "runtime-dev", destination / "dev-evaluation"
    runtime.mkdir()
    evaluator.mkdir()
    def write(path, payload):
        with path.open("xb") as handle:
            handle.write(payload)
        return hashlib.sha256(payload).hexdigest()
    runtime_files = {
        "corpus.jsonl": write(runtime / "corpus.jsonl", corpus_payload),
        "queries-ta.jsonl": write(runtime / "queries-ta.jsonl", jsonl_bytes(sorted(dev_queries, key=lambda r: r["id"]))),
    }
    evaluator_files = {"qrels-dev.jsonl": write(evaluator / "qrels-dev.jsonl", jsonl_bytes(
        sorted(qrels, key=lambda r: (r["query_id"], r["relevant_id"]))))}
    common = {"dataset_revision": DATASET_REVISION, "mteb_revision": MTEB_REVISION,
              "source_sha256": source_hashes, "split": "dev", "query_view": "TA", "corpus_view": "TAC",
              "input_queries": len(dev_queries), "corpus_families": len(corpus), "candidate_policy": "full"}
    def manifest(folder, value):
        return write(folder / "manifest.json", (json.dumps(value, sort_keys=True, indent=2) + "\n").encode())
    runtime_digest = manifest(runtime, {**common, "format": "ptp-dapfam-runtime-dev-v1", "files": runtime_files})
    evaluator_digest = manifest(evaluator, {**common, "format": "ptp-dapfam-evaluator-dev-v1", "files": evaluator_files,
        "eligible_queries": {p: len(v) for p, v in eligible.items()}, "runtime_manifest_sha256": runtime_digest})
    receipt = {"format": "ptp-dapfam-curator-receipt-v1", "status": "PREPARED_NOT_ISOLATION_ATTESTED",
               "runtime_manifest_sha256": runtime_digest, "evaluator_manifest_sha256": evaluator_digest,
               "input_queries": len(dev_queries), "corpus_families": len(corpus),
               "source_sha256": source_hashes, "protected_exports": 0,
               "vector_binding": "CORPUS_BYTES_MATCH;VECTOR_AND_QUERY_BASELINE_VERIFICATION_PENDING"}
    write(destination / "owner-complete.json", (json.dumps(receipt, indent=2) + "\n").encode())
    return receipt
