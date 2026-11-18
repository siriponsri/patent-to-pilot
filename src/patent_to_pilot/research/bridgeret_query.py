"""Canonical BridgeRet query/passage serialisation (owner split spec SPLIT-SPEC-0.1, section 5).

Canonical text = Title + "\n" + Abstract + "\n" + First Independent Claim.
- First independent claim: the lowest-numbered claim whose PatentsView ``dependent`` field is empty,
  whose text has no dependency reference, and which is not cancelled. If none is found the variant
  is ``claim_fallback_claim1`` (the lowest-numbered non-cancelled claim, verbatim).
- No abstract: Title + "\n" + First Independent Claim, variant ``no_abstract``.
- Token cap (default 512): truncate the claim tail first, then the abstract tail; never the title.
  The tokenizer is injected (``count`` returns the number of tokens of a string), so the same rule
  runs with the real Arctic tokenizer and with a whitespace double in tests.

Stdlib only. Nothing here reads protected data; it serialises whatever rows it is given.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Callable, Iterable, Mapping

CANCELLED = re.compile(r'^\s*\d*\s*\.?\s*\(\s*(canceled|cancelled|deleted|withdrawn)\s*\)\s*\.?\s*$', re.I)
DEPENDENCY = re.compile(r'\b(?:of|in|to|by|with|under)\s+(?:any\s+(?:one\s+)?of\s+)?claims?\s+\d+'
                        r'|\bas\s+(?:claimed|recited|defined|set\s+forth)\s+in\s+(?:any\s+(?:one\s+)?of\s+)?claims?\s+\d+'
                        r'|\bclaims?\s+\d+\s*(?:or|and|-|to)\s*\d+', re.I)
LEADING_NUMBER = re.compile(r'^\s*\d+\s*\.\s*')


@dataclass(frozen=True)
class ClaimRow:
    number: int
    text: str
    dependent: str = ''


def _clean(text: str) -> str:
    return re.sub(r'\s+', ' ', LEADING_NUMBER.sub('', text or '')).strip()


def is_cancelled(text: str) -> bool:
    return bool(CANCELLED.match(text or '')) or not _clean(text)


def first_independent_claim(claims: Iterable[ClaimRow]) -> tuple[str | None, str]:
    """Return (claim text without its leading number, variant)."""
    rows = sorted((c for c in claims if not is_cancelled(c.text)), key=lambda c: c.number)
    if not rows:
        return None, 'no_claims'
    for c in rows:
        if not (c.dependent or '').strip() and not DEPENDENCY.search(c.text):
            return _clean(c.text), 'first_independent'
    return _clean(rows[0].text), 'claim_fallback_claim1'


@dataclass
class SerialisedQuery:
    text: str
    variant: list[str] = field(default_factory=list)
    tokens: int = 0
    truncated: dict = field(default_factory=dict)  # component -> tokens removed


def _cut(text: str, keep_tokens: int, count: Callable[[str], int]) -> str:
    """Longest word prefix of ``text`` with count(prefix) <= keep_tokens (binary search on words)."""
    words = text.split(' ')
    lo, hi = 0, len(words)
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if count(' '.join(words[:mid])) <= keep_tokens:
            lo = mid
        else:
            hi = mid - 1
    return ' '.join(words[:lo])


def serialise(title: str, abstract: str | None, claims: Iterable[ClaimRow],
              count: Callable[[str], int], cap: int = 512) -> SerialisedQuery:
    title = _clean(title)
    if not title:
        raise ValueError('title is required')
    variant: list[str] = []
    abstract = _clean(abstract or '')
    if not abstract:
        variant.append('no_abstract')
    claim, cv = first_independent_claim(claims)
    if cv != 'first_independent':
        variant.append(cv)
    parts = {'title': title, 'abstract': abstract, 'claim': claim or ''}
    join = lambda p: '\n'.join(v for v in (p['title'], p['abstract'], p['claim']) if v)
    truncated: dict[str, int] = {}
    for comp in ('claim', 'abstract'):          # claim tail first, then abstract; never title
        total = count(join(parts))
        if total <= cap or not parts[comp]:
            continue
        before = count(parts[comp])
        rest = dict(parts, **{comp: ''})
        budget = max(cap - count(join(rest)) - 1, 0)   # -1 for the joining newline
        parts[comp] = _cut(parts[comp], budget, count)
        truncated[comp] = before - count(parts[comp]) if parts[comp] else before
    text = join(parts)
    if count(text) > cap:
        variant.append('title_over_cap')     # reported, title is never cut
    return SerialisedQuery(text, variant, count(text), truncated)


def claims_by_document(rows: Iterable[Mapping[str, str]], id_field: str) -> dict[str, list[ClaimRow]]:
    """Group PatentsView ``g_claims``/``pg_claims`` rows (dict per row) by document id."""
    out: dict[str, list[ClaimRow]] = {}
    for r in rows:
        num = r.get('claim_number') or r.get('claim_sequence') or '0'
        try:
            n = int(str(num).strip() or 0)
        except ValueError:
            n = 10 ** 6
        out.setdefault(r[id_field], []).append(ClaimRow(n, r.get('claim_text') or '', r.get('dependent') or ''))
    return out
