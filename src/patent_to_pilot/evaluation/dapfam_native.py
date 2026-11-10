"""Native DAPFAM TA-query/TAC-corpus semantics for staged development evaluation.

No downloader or split selection: callers must supply only authorized dev data.
IN/OUT partition qrels, never the candidate universe. This is not MTM lane X.
The passage encoder remains a custom backend, not a published-run replication.
"""
import math

from patent_to_pilot.research.mtm_runtime import InputBoundaryError, identifier

MTEB_REVISION = "9242b36a1d400fc8c3af573e6a6e0705c0b96e3d"
DATASET_REVISION = "780f4011d60297fc6e97a4119b0c516d13afea2d"
PAPER1_CUTOFFS = (10, 100, 200)


def native_dev_task(corpus_rows, query_rows, relations, *, partition: str, candidate_policy: str = "full") -> dict:
    if partition not in {"ALL", "IN", "OUT"} or candidate_policy != "full":
        raise InputBoundaryError("native DAPFAM requires a full candidate corpus and a known qrel partition")
    corpus, queries = {}, {}
    for row in corpus_rows:
        key = row["relevant_id"]
        identifier(key)
        if key in corpus:
            raise InputBoundaryError("duplicate corpus family")
        corpus[key] = {"title": row["title_en"],
                       "text": "\n".join(str(row[f]) for f in ("abstract_en", "claims_text") if row.get(f))}
    for row in query_rows:
        key = row["query_id"]
        identifier(key)
        if key in queries:
            raise InputBoundaryError("duplicate query")
        queries[key] = "\n".join(str(row[f]) for f in ("title_en", "abstract_en") if row.get(f))
    qrels, seen = {}, set()
    for relation in relations:
        query, family = relation["query_id"], relation["relevant_id"]
        if query not in queries or family not in corpus or (query, family) in seen:
            raise InputBoundaryError("invalid or duplicate relation identity")
        seen.add((query, family))
        score = float(relation["relevance_score"])
        domain = relation["domain_rel"]
        # Native loader filters nonpositives before domain selection. Their
        # auxiliary domain marker does not enter the positive qrel partitions.
        if not math.isfinite(score) or (score > 0 and domain not in {"IN", "OUT"}):
            raise InputBoundaryError("invalid relation annotation")
        if score > 0 and (partition == "ALL" or domain == partition):
            qrels.setdefault(query, {})[family] = 1
    return {"corpus": corpus, "queries": queries, "qrels": qrels,
            "partition": partition, "candidate_policy": "full", "query_view": "TA", "corpus_view": "TAC",
            "input_queries": len(queries), "eligible_queries": len(qrels),
            "queries_without_partition_positives": len(queries) - len(qrels)}


def evaluate_native_dev(task: dict, rankings: dict[str, list[str]], *, cutoffs=(100,), include_per_query=False) -> dict:
    """Binary NDCG/recall on explicit rankings; missing eligible outputs score zero.

    Unlike a raw backend call on incomplete results, denominators cannot shrink.
    Duplicate/unknown families are rejected, not removed after viewing scores.
    Explicit list order is respected; raw score ties must be resolved upstream.
    """
    if task["candidate_policy"] != "full" or task["partition"] not in {"ALL", "IN", "OUT"}:
        raise InputBoundaryError("not a native DAPFAM task")
    if not cutoffs or any(type(k) is not int or k <= 0 for k in cutoffs) or len(set(cutoffs)) != len(cutoffs):
        raise InputBoundaryError("invalid cutoffs")
    corpus, queries, qrels = task["corpus"], task["queries"], task["qrels"]
    if not qrels or not set(qrels) <= set(queries) or not set(rankings) <= set(queries):
        raise InputBoundaryError("invalid evaluation population")
    for gold in qrels.values():
        if not gold or not set(gold) <= set(corpus) or any(type(v) is not int or v != 1 for v in gold.values()):
            raise InputBoundaryError("native qrels must be binary positives")
    for ranking in rankings.values():
        if type(ranking) is not list:
            raise InputBoundaryError("rankings must be explicit lists")
        for family in ranking:
            identifier(family)
        if len(set(ranking)) != len(ranking) or not set(ranking) <= set(corpus):
            raise InputBoundaryError("duplicate or unknown ranked family")
    totals = {f"{metric}@{k}": 0.0 for metric in ("NDCG", "Recall") for k in cutoffs}
    per_query = {}
    for query, gold in qrels.items():
        ranking = rankings.get(query, [])
        values = {}
        for k in cutoffs:
            hits = [int(family in gold) for family in ranking[:k]]
            dcg = sum(hit / math.log2(rank + 2) for rank, hit in enumerate(hits))
            ideal = sum(1 / math.log2(rank + 2) for rank in range(min(k, len(gold))))
            values[f"NDCG@{k}"] = dcg / ideal
            values[f"Recall@{k}"] = sum(hits) / len(gold)
        for name, value in values.items():
            totals[name] += value
        if include_per_query:
            per_query[query] = values
    result = {"format": "ptp-dapfam-native-dev-metrics-v1", "partition": task["partition"],
            "queries": len(qrels), "input_queries": len(queries),
            "queries_without_partition_positives": len(queries) - len(qrels),
            "missing_rankings": sum(q not in rankings for q in qrels),
            "empty_rankings": sum(q in rankings and not rankings[q] for q in qrels),
            "metrics": {name: round(value / len(qrels), 5) for name, value in totals.items()},
            "failure_policy": "missing_or_empty_eligible_rankings_score_zero"}
    if include_per_query:
        # Private evaluator artifact only: retain full precision for paired
        # analysis; public macro rounding must never become inference input.
        result["per_query"] = per_query
    return result


def evaluate_paper1_dev(task: dict, rankings: dict[str, list[str]]) -> dict:
    """Prospective Paper1 metric bridge; no additional confirmatory endpoint.

    Return value contains dev IDs and belongs only in the private evaluator.
    Missing/empty eligible outputs remain zero, including in paired analysis.
    """
    result = evaluate_native_dev(task, rankings, cutoffs=PAPER1_CUTOFFS, include_per_query=True)
    result["format"] = "ptp-paper1-native-dev-metrics-v1"
    result["metric_contract"] = {
        "primary_partition": "OUT", "primary_metric": "Recall@200",
        "cutoffs": list(PAPER1_CUTOFFS), "gain": "binary_positive_qrels",
        "ideal": "all_known_partition_positives_up_to_cutoff",
        "aggregation": "eligible_query_macro",
        "candidate_policy": "full", "ties": "explicit_upstream_order",
        "ndcg10_role": "descriptive_literature_bridge_not_confirmatory",
        "comparability": "matched_dev_not_published_all_query_replication",
    }
    return result
