"""Transparent offline policy helpers used by HealthTech development baselines."""
from __future__ import annotations

import re
from typing import Mapping

from patent_to_pilot.retrieval.fts import SearchHit


def token_set(text: str) -> set[str]:
    return {token.lower() for token in re.findall(r"[\w-]+", text, flags=re.UNICODE) if len(token) > 1}


def token_overlap_score(query: str, document_text: str) -> float:
    query_terms = token_set(query)
    if not query_terms:
        return 0.0
    return len(query_terms & token_set(document_text)) / len(query_terms)


def fixed_hybrid_rerank(
    query: str,
    hits: list[SearchHit],
    document_texts: Mapping[str, str],
    *,
    limit: int,
) -> list[tuple[SearchHit, float, float]]:
    """Fuse lexical rank and transparent token overlap with fixed weights.

    This is a local lexical/token-overlap approximation, not a dense reranker
    reproduction. The caller must report it as an engineering baseline.
    """
    scored = []
    for rank, hit in enumerate(hits, 1):
        lexical = 1.0 / (1.0 + rank)
        overlap = token_overlap_score(query, document_texts.get(hit.document_id, hit.title))
        scored.append((hit, 0.7 * lexical + 0.3 * overlap, overlap))
    scored.sort(key=lambda row: (-row[1], row[0].document_id))
    return scored[:limit]
