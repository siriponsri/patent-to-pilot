"""P4-T01a: versioned Thai lexical analyzer for the Workbench product profile (owner plan of 23 Nov 2026, section 4).

One analyzer serves every lexical path of the product profile (indexing, normal search, owner requirement matching and
highlighting), so the index side and the query side always segment the same way.

* Segmentation: PyThaiNLP ``newmm-safe`` through the top-level ``word_tokenize`` (the ``Tokenizer`` class does not accept
  that engine), ``keep_whitespace=True``, ``join_broken_num=False``, with ONE dictionary built once per process from the
  immutable PyThaiNLP base word list (a ``frozenset``) plus the small ``DOMAIN_TERMS`` tuple below. The trie is never
  mutated after it is built; its content hash is part of the analyzer identity.
* Alignment: the tokens must join back to the input exactly, else ``AlignmentError``. Offsets are half-open Python
  code-point offsets into the canonical text (not UTF-16). A text that fails the check is never indexed with misaligned
  tokens: the caller uses the declared ``fallback_tokens`` (runs of indexable characters) and counts it.
* Index terms: each word token is split into runs of the characters SQLite's ``unicode61`` tokenizer keeps under
  ``categories 'L* N* Co M*'`` (letters, numbers, private use and combining marks), so a Python term equals one FTS5 token.
  Terms are folded by ``fold``: Thai digits to ASCII digits and per-character lower case, code-point preserving. No Thai
  word is dropped: negation and modal words (ไม่, ห้าม, ต้อง, เว้นแต่) can change a requirement and stay searchable.
* Structured identifiers (``ข้อ ๕(๒)``, ``มาตรา 12``, ``Annex B`` ...) get a digit-normalised lookup key while the original
  spelling and its exact span are kept.

The module imports PyThaiNLP lazily; without it ``available()`` is False and the product profile falls back to the legacy
index (said so in every response).
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import re
import threading
import unicodedata

ANALYZER_NAME = "ptp-thai-lexical"
ANALYZER_VERSION = "1.0.0"
ENGINE = "newmm-safe"
NORMALIZATION_VERSION = "fold-v1"
NORMALIZATION = ("fold-v1: Thai digits U+0E50-U+0E59 -> ASCII 0-9; each character lower-cased when that keeps one code "
                 "point; nothing removed, nothing reordered (code-point preserving)")
FTS_TOKENIZE = "unicode61 categories 'L* N* Co M*' remove_diacritics 0"
# Small, author-declared domain list (legal / patent vocabulary). Kept deliberately short: a long compound added here
# would hide its parts from the word index (the bounded substring fallback still finds them).
DOMAIN_TERMS = ("สิทธิบัตร", "อนุสิทธิบัตร", "ภาคผนวก", "ราชกิจจานุเบกษา", "บัญชีท้าย", "เว้นแต่", "ค่าธรรมเนียม",
                "คำขอ")

_THAI_DIGITS = {ord(c): str(i) for i, c in enumerate("๐๑๒๓๔๕๖๗๘๙")}
THAI_SCRIPT = re.compile(r"[฀-๿]")


class AnalyzerUnavailable(RuntimeError):
    """PyThaiNLP is not importable in this interpreter (optional extra ``thai``)."""


class AlignmentError(ValueError):
    """Tokenizer output does not join back to the canonical text."""


@dataclass(frozen=True)
class Term:
    norm: str      # folded form, equal to the FTS5 token
    start: int     # half-open code-point offsets in the analysed text
    end: int


@dataclass(frozen=True)
class Identifier:
    kind: str
    label: str
    key: str       # digit-normalised lookup key, e.g. "ข้อ:5(2)"
    start: int
    end: int
    text: str      # original spelling


def fold(text: str) -> str:
    out = []
    for c in text.translate(_THAI_DIGITS):
        low = c.lower()
        out.append(low if len(low) == 1 else c)
    return "".join(out)


def indexable(c: str) -> bool:
    cat = unicodedata.category(c)
    return cat[0] in "LNM" or cat == "Co"


def _runs(token: str, offset: int) -> list[Term]:
    out, start = [], None
    for i, c in enumerate(token + "\0"):
        if i < len(token) and indexable(c):
            if start is None:
                start = i
        elif start is not None:
            out.append(Term(fold(token[start:i]), offset + start, offset + i))
            start = None
    return out


def fallback_tokens(text: str) -> list[tuple[str, int, int]]:
    """Declared fallback segmentation (only used when the tokenizer output fails the alignment check)."""
    return [(t.norm, t.start, t.end) for t in _runs(text, 0)]


# ----------------------------------------------------------------------------- structured identifiers
_ID = re.compile(
    r"(?P<kind>มาตรา|ข้อ|วรรค|หมวด|ส่วนที่|ส่วน|ภาคผนวก|บัญชีท้าย"
    r"|(?<![A-Za-z])(?i:section|clause|article|paragraph|annex|appendix|schedule|chapter|part))"
    r"[ \t ]*"
    r"(?P<label>[0-9๐-๙]+(?:[ \t]*\([0-9๐-๙]{1,3}\)|[ \t]*\([ก-ฮa-zA-Z]\))*|[ก-ฮA-Z](?![฀-๿A-Za-z]))")
_SPACE = re.compile(r"[ \t ]+")


def identifiers(text: str) -> list[Identifier]:
    out = []
    for m in _ID.finditer(text):
        kind = m.group("kind")
        label = m.group("label")
        key = f"{fold(kind)}:{_SPACE.sub('', fold(label))}"
        out.append(Identifier(kind, label, key, m.start(), m.end(), m.group(0)))
    return out


def key_matches(query_key: str, found_key: str) -> bool:
    """``ข้อ 5`` matches ``ข้อ ๕`` and its sub-items ``ข้อ ๕(๒)``; ``ข้อ 5`` never matches ``ข้อ 52``."""
    return found_key == query_key or found_key.startswith(query_key + "(")


# ----------------------------------------------------------------------------- the analyzer
class ThaiAnalyzer:
    def __init__(self) -> None:
        try:
            import pythainlp
            from pythainlp.corpus.common import thai_words
            from pythainlp.tokenize import word_tokenize
            from pythainlp.util import Trie
        except ImportError as exc:   # optional extra "thai"
            raise AnalyzerUnavailable(f"PyThaiNLP is not installed ({exc})") from None
        base = thai_words()
        words = frozenset(base) | frozenset(DOMAIN_TERMS)
        self._word_tokenize = word_tokenize
        self._trie = Trie(words)          # built once; never mutated
        base_sha = hashlib.sha256("\n".join(sorted(base)).encode("utf-8")).hexdigest()
        dom_sha = hashlib.sha256("\n".join(sorted(DOMAIN_TERMS)).encode("utf-8")).hexdigest()
        dict_sha = hashlib.sha256("\n".join(sorted(words)).encode("utf-8")).hexdigest()
        self.identity = {
            "name": ANALYZER_NAME, "version": ANALYZER_VERSION, "engine": ENGINE,
            "pythainlp_version": pythainlp.__version__, "entry_point": "pythainlp.tokenize.word_tokenize",
            "options": {"keep_whitespace": True, "join_broken_num": False},
            "base_dictionary": {"source": "pythainlp.corpus.common.thai_words", "words": len(base), "sha256": base_sha},
            "domain_terms": {"words": len(DOMAIN_TERMS), "sha256": dom_sha},
            "dictionary_sha256": dict_sha, "dictionary_words": len(words),
            "normalization": NORMALIZATION, "fts_tokenize": FTS_TOKENIZE,
            "offsets": "half-open Python code points into the canonical text"}
        self.identity_id = (f"{ANALYZER_NAME}/{ANALYZER_VERSION};{ENGINE};pythainlp={pythainlp.__version__};"
                            f"dict={dict_sha[:12]};{NORMALIZATION_VERSION}")

    def tokens(self, text: str) -> list[tuple[str, int, int]]:
        """Word tokens (whitespace dropped) with half-open code-point offsets; raises ``AlignmentError``."""
        toks = self._word_tokenize(text, custom_dict=self._trie, engine=ENGINE, keep_whitespace=True,
                                   join_broken_num=False)
        if "".join(toks) != text:
            raise AlignmentError("tokenizer output cannot be aligned to the canonical text")
        out, cursor = [], 0
        for t in toks:
            end = cursor + len(t)
            if not t.isspace():
                out.append((t, cursor, end))
            cursor = end
        return out

    def terms(self, text: str) -> tuple[list[Term], bool]:
        """Index terms of ``text`` and whether the declared fallback segmentation had to be used."""
        try:
            toks = self.tokens(text)
        except AlignmentError:
            return _runs(text, 0), True
        out: list[Term] = []
        for tok, s, _e in toks:
            out.extend(_runs(tok, s))
        return out, False

    def body(self, text: str) -> tuple[str, bool]:
        terms, fell_back = self.terms(text)
        return " ".join(t.norm for t in terms), fell_back


_LOCK = threading.Lock()
_ANALYZER: ThaiAnalyzer | None = None
_FAILURE: str | None = None


def analyzer() -> ThaiAnalyzer:
    """The process-wide analyzer (built once). Raises ``AnalyzerUnavailable`` without PyThaiNLP."""
    global _ANALYZER, _FAILURE
    if _ANALYZER is not None:
        return _ANALYZER
    with _LOCK:
        if _ANALYZER is None:
            if _FAILURE is not None:
                raise AnalyzerUnavailable(_FAILURE)
            try:
                _ANALYZER = ThaiAnalyzer()
            except AnalyzerUnavailable as exc:
                _FAILURE = str(exc)
                raise
    return _ANALYZER


def available() -> bool:
    try:
        analyzer()
        return True
    except AnalyzerUnavailable:
        return False
