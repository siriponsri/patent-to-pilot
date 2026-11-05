"""Pure helpers for the organization-adaptive DAPFAM acquisition study.

Protocol: docs/healthtech/research/ORG_ADAPTIVE_CROSS_DOMAIN_PROTOCOL_DRAFT_20261105_EN.md.
The dense baseline uses PatEmbed-large with its published ``retrieval_OUT`` prompt pair, 384/64-term
title+abstract+claims passages and MaxP family aggregation.
No function here reads qrels except the split builder and the evaluator.
"""
from __future__ import annotations

from collections import defaultdict
import random
from typing import Iterable, Mapping, Sequence
import unicodedata

DENSE_CHUNK_SIZE = 384
DENSE_CHUNK_OVERLAP = 64
DENSE_DOCUMENT_PREFIX = "encode document for different retrieval: "
DENSE_QUERY_PREFIX = "encode query for different document retrieval: "
POOL_DEPTH = 200
SPLIT_SEED = 20261105


def _nfkc_whitespace(value: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", value).split())


def dense_passages(title: str | None, abstract: str | None, claims: str | None) -> list[str]:
    """Dense document view: NFKC/whitespace TAC, 384-term windows, 64-term overlap."""
    text = _nfkc_whitespace(" ".join((title or "", abstract or "", claims or "")))
    if not text:
        return []
    tokens = text.split(" ")
    step = DENSE_CHUNK_SIZE - DENSE_CHUNK_OVERLAP
    return [DENSE_DOCUMENT_PREFIX + " ".join(tokens[offset:offset + DENSE_CHUNK_SIZE])
            for offset in range(0, len(tokens), step)]


def _query_body(title: str | None, abstract: str | None, claims: str | None) -> str:
    return " ".join(" ".join(str(value or "").split()) for value in (title, abstract, claims))


def dense_query_text(title: str | None, abstract: str | None, claims: str | None) -> str:
    """Single-window dense query view: per-field whitespace normalization, space-joined (no NFKC).

    The encoder truncates at 512 tokens, so for most DAPFAM queries only the title, abstract and the
    start of the claims are seen. ``dense_query_windows`` covers the whole query.
    """
    return DENSE_QUERY_PREFIX + _query_body(title, abstract, claims)


def dense_query_windows(title: str | None, abstract: str | None, claims: str | None) -> list[str]:
    """Multi-window dense query view: the same body cut into 384/64-term windows, each prefixed."""
    tokens = [token for token in _query_body(title, abstract, claims).split(" ") if token]
    if not tokens:
        return []
    step = DENSE_CHUNK_SIZE - DENSE_CHUNK_OVERLAP
    return [DENSE_QUERY_PREFIX + " ".join(tokens[offset:offset + DENSE_CHUNK_SIZE])
            for offset in range(0, len(tokens), step)]


def maxp_top_k(passage_scores: Sequence[float], passage_family: Sequence[int], family_ids: Sequence[str],
               k: int = POOL_DEPTH) -> list[tuple[str, float]]:
    """MaxP family aggregation with a lexical family-id tie break."""
    best: dict[int, float] = {}
    for score, family in zip(passage_scores, passage_family, strict=True):
        if family not in best or score > best[family]:
            best[family] = float(score)
    ordered = sorted(((family_ids[index], score) for index, score in best.items()), key=lambda item: (-item[1], item[0]))
    return ordered[:k]


def budgeted_merge(lists: Sequence[Sequence[str]], budget: int = POOL_DEPTH) -> list[str]:
    """Interleave ranked lists round-robin by rank, dropping duplicates, until ``budget`` unique families."""
    pool: list[str] = []
    seen: set[str] = set()
    for rank in range(max((len(ranked) for ranked in lists), default=0)):
        for ranked in lists:
            if rank < len(ranked) and ranked[rank] not in seen:
                seen.add(ranked[rank])
                pool.append(ranked[rank])
                if len(pool) == budget:
                    return pool
    return pool


def assign_folds(strata: Mapping[str, str], k: int = 5, seed: int = SPLIT_SEED) -> dict[str, int]:
    """Stratified query-level folds: shuffle each stratum with ``seed`` and deal queries round-robin."""
    by_stratum: dict[str, list[str]] = defaultdict(list)
    for query in sorted(strata):
        by_stratum[strata[query]].append(query)
    rng = random.Random(seed)
    folds: dict[str, int] = {}
    offset = 0
    for stratum in sorted(by_stratum):
        queries = by_stratum[stratum]
        rng.shuffle(queries)
        for index, query in enumerate(queries):
            folds[query] = (offset + index) % k
        offset += len(queries)
    return folds


def crossfit_select(scores: Mapping[str, Mapping[str, float]], folds: Mapping[str, int],
                    cost: Mapping[str, tuple[int, int]], groups: Mapping[str, str] | None = None,
                    min_group: int = 20) -> dict[str, str]:
    """Pick a mix for each query using only the other folds' labels.

    Without ``groups`` one global mix is chosen per fold. With ``groups`` each group gets its own
    mix when it has at least ``min_group`` training queries, otherwise the global mix. Ties go to
    the lower ``cost`` tuple, then the lexically smaller mix name.
    """
    def best(train: list[str]) -> str:
        return min(cost, key=lambda mix: (-sum(scores[q][mix] for q in train) / len(train), cost[mix], mix))

    chosen: dict[str, str] = {}
    for fold in sorted(set(folds.values())):
        train = [q for q in scores if folds[q] != fold]
        held = [q for q in scores if folds[q] == fold]
        global_mix = best(train)
        for query in held:
            mix = global_mix
            if groups is not None:
                group_train = [q for q in train if groups[q] == groups[query]]
                if len(group_train) >= min_group:
                    mix = best(group_train)
            chosen[query] = mix
    return chosen


class CompactBM25:
    """BM25Okapi with the rank_bm25 IDF floor over integer postings.

    Scores match ``scripts/healthtech/run_dapfam_bm25.SparseBM25`` (a query term counts once per
    occurrence) but store postings as flat arrays, so full title+abstract+claims texts fit in memory.
    """

    def __init__(self, documents: Iterable[Sequence[str]], *, k1: float = 1.5, b: float = 0.75, epsilon: float = 0.25):
        import numpy as np

        self.np = np
        self.vocab: dict[str, int] = {}
        terms, freqs, lengths = [], [], []
        for document in documents:
            ids = np.fromiter((self.vocab.setdefault(t, len(self.vocab)) for t in document), dtype=np.int64,
                              count=len(document))
            unique, counts = np.unique(ids, return_counts=True)
            terms.append(unique)
            freqs.append(counts)
            lengths.append(len(document))
        if not lengths or sum(lengths) == 0:
            raise ValueError("corpus has no tokens")
        self.corpus_size = len(lengths)
        doc_len = np.asarray(lengths, dtype=np.float64)
        avgdl = float(doc_len.mean())
        flat_terms = np.concatenate(terms)
        flat_docs = np.repeat(np.arange(self.corpus_size, dtype=np.int32), [len(t) for t in terms])
        flat_tf = np.concatenate(freqs).astype(np.float64)
        order = np.argsort(flat_terms, kind="stable")
        flat_terms = flat_terms[order]
        self.doc_ids = flat_docs[order]
        tf = flat_tf[order]
        self.weights = tf * (k1 + 1.0) / (tf + k1 * (1.0 - b + b * doc_len[self.doc_ids] / avgdl))
        self.offsets = np.searchsorted(flat_terms, np.arange(len(self.vocab) + 1))
        df = np.diff(self.offsets).astype(np.float64)
        idf = np.log(self.corpus_size - df + 0.5) - np.log(df + 0.5)
        floor = epsilon * float(idf.mean())
        self.idf = np.where(idf < 0, floor, idf)

    def get_scores(self, query: Sequence[str]):
        from collections import Counter

        scores = self.np.zeros(self.corpus_size, dtype=self.np.float64)
        for term, count in Counter(query).items():
            index = self.vocab.get(term)
            if index is None:
                continue
            start, end = self.offsets[index], self.offsets[index + 1]
            scores[self.doc_ids[start:end]] += count * self.idf[index] * self.weights[start:end]
        return scores


def positive_relations(qrels: Iterable[Mapping[str, object]]) -> dict[str, dict[str, set[str]]]:
    """query_id -> {'IN': targets, 'OUT': targets} for relevance_score > 0; unlisted pairs stay unjudged."""
    out: dict[str, dict[str, set[str]]] = defaultdict(lambda: {"IN": set(), "OUT": set()})
    for row in qrels:
        if float(row["relevance_score"]) > 0:
            domain = str(row["domain_rel"]).upper()
            if domain not in ("IN", "OUT"):
                raise ValueError(f"unknown domain_rel: {row['domain_rel']!r}")
            out[str(row["query_id"])][domain].add(str(row["relevant_id"]))
    return dict(out)


def recall_at(ranked: Sequence[str], relevant: set[str], k: int) -> float:
    if not relevant:
        raise ValueError("recall is undefined for an empty relevant set")
    return len(set(ranked[:k]) & relevant) / len(relevant)


def macro_recall(rankings: Mapping[str, Sequence[str]], relevant_by_query: Mapping[str, set[str]], k: int,
                 queries: Iterable[str] | None = None) -> tuple[float, int]:
    """Macro recall over queries with a non-empty relevant set; a missing ranking scores 0."""
    eligible = [q for q in (queries if queries is not None else relevant_by_query) if relevant_by_query.get(q)]
    if not eligible:
        raise ValueError("no eligible queries")
    total = sum(recall_at(rankings.get(q, ()), relevant_by_query[q], k) for q in eligible)
    return total / len(eligible), len(eligible)


def query_components(positives: Mapping[str, Mapping[str, set[str]]], query_ids: Iterable[str]) -> dict[str, str]:
    """Union queries that share any positive target; returns query_id -> component id (smallest member)."""
    parent = {q: q for q in query_ids}

    def find(item: str) -> str:
        while parent[item] != item:
            parent[item] = parent[parent[item]]
            item = parent[item]
        return item

    owner: dict[str, str] = {}
    for query in sorted(parent):
        for target in sorted(positives.get(query, {}).get("IN", set()) | positives.get(query, {}).get("OUT", set())):
            if target in owner:
                left, right = find(owner[target]), find(query)
                if left != right:
                    parent[max(left, right)] = min(left, right)
            else:
                owner[target] = query
    return {q: find(q) for q in parent}


def first_ipc_section(ipc3_codes: Sequence[str] | None) -> str:
    for code in ipc3_codes or ():
        if code and code[0].isalpha():
            return code[0].upper()
    return "?"


LARGE_COMPONENT_THRESHOLD = 50


def component_split(components: Mapping[str, str], sections: Mapping[str, str], *, dev_fraction: float = 1 / 3,
                    seed: int = SPLIT_SEED, large_component_threshold: int = LARGE_COMPONENT_THRESHOLD) -> dict[str, str]:
    """Assign whole components to dev/test.

    Components with at least ``large_component_threshold`` queries go to dev, because one large
    cluster in test would dominate the component bootstrap. Remaining components are shuffled
    within their majority first-IPC section and moved to dev until that section's dev query
    count (large components included) reaches ``dev_fraction`` of its queries.
    """
    members: dict[str, list[str]] = defaultdict(list)
    for query, component in components.items():
        members[component].append(query)
    assignment: dict[str, str] = {}
    dev_by_section: dict[str, int] = defaultdict(int)
    total_by_section: dict[str, int] = defaultdict(int)
    for query in components:
        total_by_section[sections.get(query, "?")] += 1
    strata: dict[str, list[str]] = defaultdict(list)
    for component in sorted(members):
        queries = members[component]
        if len(queries) >= large_component_threshold:
            for query in queries:
                assignment[query] = "dev"
                dev_by_section[sections.get(query, "?")] += 1
            continue
        counts: dict[str, int] = defaultdict(int)
        for query in queries:
            counts[sections.get(query, "?")] += 1
        strata[sorted(counts.items(), key=lambda item: (-item[1], item[0]))[0][0]].append(component)
    rng = random.Random(seed)
    for stratum in sorted(strata):
        comps = list(strata[stratum])
        rng.shuffle(comps)
        target = round(total_by_section[stratum] * dev_fraction)
        for component in comps:
            split = "dev" if dev_by_section[stratum] < target else "test"
            for query in members[component]:
                assignment[query] = split
                if split == "dev":
                    dev_by_section[sections.get(query, "?")] += 1
    return assignment
