"""P2-T04 lexical backend using the frozen P2-T02 BM25-full ranking rules.

The caller supplies the verified full-text passages in their original unit order and
their publication dates. Compare the original-query top-1000 runs with P2-T02 before
using the rebuilt index for the screen.
"""
from __future__ import annotations

import hashlib
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import date
from types import MappingProxyType

from patent_to_pilot.workbench.relation_search import EligibilityMask, ExpansionQuery, RerankRequest
from scripts.healthtech.bm25_bridgeret import B, K1, TOPK, dint

_TOKEN_PATTERN = r"[a-z0-9]+"


def _checked_date(value: str | None) -> int:
    """The archived route maps absent publication dates to zero."""
    if value in (None, ""):
        return 0
    parsed = date.fromisoformat(value)
    if parsed.isoformat() != value:
        raise ValueError("date must be an ISO YYYY-MM-DD string")
    return dint(value)


def _bm25_weights(term_counts):
    """Return the float32, vocabulary-by-document scoring matrix from BM25-full."""
    import numpy as np

    n = term_counts.shape[0]
    dl = np.asarray(term_counts.sum(axis=1)).ravel()
    df = np.bincount(term_counts.indices, minlength=term_counts.shape[1])
    idf = np.log1p((n - df + 0.5) / (df + 0.5)).astype(np.float32)
    norm = K1 * (1 - B + B * dl / dl.mean())
    rows = np.repeat(np.arange(n), np.diff(term_counts.indptr))
    term_counts.data = (
        term_counts.data * (K1 + 1) / (term_counts.data + norm[rows]) * idf[term_counts.indices]
    ).astype(np.float32)
    return term_counts.T.tocsr()


def _rank_positions(scores, limit: int):
    import numpy as np

    # Selecting at a narrower K can change which tie members enter the shortlist.
    # Rank the native shortlist first, then take the requested prefix.
    top = np.argpartition(-scores, TOPK)[:TOPK] if TOPK < len(scores) else np.arange(len(scores))
    top = top[np.lexsort((top, -scores[top]))]
    return top[np.isfinite(scores[top]) & (scores[top] > 0)][:limit]


@dataclass(frozen=True, init=False)
class BM25FullEligibility(EligibilityMask):
    """Filing-date and self-unit mask backed by the index's shared publication table."""

    _index: BM25FullIndex = field(repr=False, compare=False)
    _filing_day: int

    def __init__(self, index: BM25FullIndex, app_id: str, filing_date: str):
        filing_day = _checked_date(filing_date)
        if not isinstance(app_id, str) or not app_id or not filing_day:
            raise ValueError("the original app id and filing date are required")
        super().__init__(
            "challenge1m-bm25-full-date-and-self",
            exclude_ids={"A:" + app_id},
            date_cutoff=filing_date,
            missing_date="include",
        )
        object.__setattr__(self, "_index", index)
        object.__setattr__(self, "_filing_day", filing_day)

    def reason(self, cid: str) -> str | None:
        if cid in self.exclude_ids:
            return "excluded_id"
        row = self._index.unit_rows.get(cid)
        if row is None:
            return "unit_absent_from_corpus"
        return "date_not_before_cutoff" if self._index.publication_days[row] >= self._filing_day else None

    def describe(self) -> dict:
        return {
            **super().describe(),
            "ordered_unit_publication_sha256": self._index.publication_sha256,
            "publication_table_format": "UTF-8 corpus-order unit_id<TAB>YYYYMMDD-or-0<LF>",
        }


class BM25FullIndex:
    """Shared index for lexical acquisition, with candidate-only reranking by original text."""

    def __init__(self, passages: Iterable[tuple[str, str]], publication_dates: Mapping[str, str | None]):
        import numpy as np
        from sklearn.feature_extraction.text import CountVectorizer

        unit_ids, unit_rows, publication_days = [], {}, []
        metadata = hashlib.sha256()

        def texts():
            for unit_id, text in passages:
                if (not isinstance(unit_id, str) or not unit_id
                        or any(char in unit_id for char in "\t\r\n") or unit_id in unit_rows):
                    raise ValueError(f"invalid or repeated unit id {unit_id!r}")
                if unit_id not in publication_dates:
                    raise ValueError(f"publication metadata is absent for {unit_id!r}")
                publication_day = _checked_date(publication_dates[unit_id])
                unit_rows[unit_id] = len(unit_ids)
                unit_ids.append(unit_id)
                publication_days.append(publication_day)
                metadata.update(f"{unit_id}\t{publication_day}\n".encode("utf-8"))
                yield text

        self._vectorizer = CountVectorizer(token_pattern=_TOKEN_PATTERN, lowercase=True, dtype=np.float32)
        self._weights = _bm25_weights(self._vectorizer.fit_transform(texts()).tocsr())
        self.unit_ids = tuple(unit_ids)
        self.unit_rows = MappingProxyType(unit_rows)
        self.publication_days = np.asarray(publication_days, dtype=np.int64)
        self.publication_days.flags.writeable = False
        self.publication_sha256 = metadata.hexdigest()
        self._last_rerank = None

    def eligibility_for(self, app_id: str, filing_date: str) -> BM25FullEligibility:
        return BM25FullEligibility(self, app_id, filing_date)

    def _scores(self, text: str):
        import numpy as np

        query = self._vectorizer.transform([text]).astype(np.float32)
        return (query @ self._weights).toarray()[0]

    def retrieve(self, text: str, limit: int, eligibility: EligibilityMask) -> list[tuple[str, float]]:
        """Mask before argpartition and return positive-score hits within the declared depth."""
        import numpy as np

        if type(limit) is not int or not (1 <= limit <= TOPK):
            raise ValueError(f"retrieval depth must be between 1 and the native depth {TOPK}")
        if not isinstance(eligibility, BM25FullEligibility) or eligibility._index is not self:
            raise ValueError("use this index's filing-date and self-unit mask")
        scores = self._scores(text)
        scores[self.publication_days >= eligibility._filing_day] = -np.inf
        for own_id in eligibility.exclude_ids:
            if own_id in self.unit_rows:
                scores[self.unit_rows[own_id]] = -np.inf
        return [(self.unit_ids[row], float(scores[row])) for row in _rank_positions(scores, limit)]

    def search(self, query: ExpansionQuery, limit: int, eligibility: EligibilityMask) -> list[tuple[str, float]]:
        """Feed the expansion's literal terms to the frozen bag-of-words tokenizer."""
        return self.retrieve("\n".join(query.phrases), limit, eligibility)

    def original(self, request: RerankRequest, eligibility: BM25FullEligibility) -> list[tuple[str, float]]:
        """Run the original-query top-1000 reproduction gate against the archived P2-T02 run."""
        return self.retrieve(request.query_text, TOPK, eligibility)

    def rerank(self, request: RerankRequest, candidate_ids: Sequence[str]) -> dict[str, float]:
        """Return scores for the given pool using the complete original query text."""
        if not candidate_ids:
            return {}
        rows = [self.unit_rows[unit_id] for unit_id in candidate_ids]
        cached = self._last_rerank
        if cached is None or cached[0] != request.query_text:
            cached = (request.query_text, self._scores(request.query_text))
            self._last_rerank = cached
        return dict(zip(candidate_ids, map(float, cached[1][rows])))
