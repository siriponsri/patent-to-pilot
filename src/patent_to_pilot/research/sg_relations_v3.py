"""Deterministic action/operand candidates v3 (design frozen in GRAPH-EXTRACTOR-V3-20261112.md).

Lexical keys only: never accepted edges, never semantic equivalence. Records keep exact spans
and the complete unit; screening is still required before any edge is used.
"""
import hashlib
import re
from .mtm_runtime import InputBoundaryError, exact_fields, identifier

VERSION = 'sg-action-operand-v3'
LEMMAS = ('receive', 'transmit', 'detect', 'generate', 'control', 'adjust', 'store', 'convert', 'reduce',
          'prevent', 'measure', 'filter', 'remove', 'separate', 'connect', 'move', 'heat', 'cool', 'rotate',
          'transfer', 'compress', 'expand', 'increase', 'decrease', 'produce', 'provide', 'supply', 'deliver',
          'inject', 'pump', 'drive', 'actuate', 'regulate', 'monitor', 'sense', 'determine', 'calculate',
          'estimate', 'identify', 'classify', 'display', 'emit', 'absorb', 'reflect', 'illuminate', 'scan',
          'analyze', 'encode', 'decode', 'encrypt', 'authenticate', 'verify', 'select',
          'sort', 'mix', 'dissolve', 'coat', 'deposit', 'etch', 'polish', 'cut', 'grind', 'weld', 'bond', 'seal',
          'clamp', 'hold', 'lift', 'guide', 'align', 'position', 'attach', 'couple', 'lock', 'release',
          'open', 'close', 'stop', 'switch', 'charge', 'discharge', 'stabilize', 'protect', 'inhibit', 'treat',
          'shape', 'mold', 'print', 'assemble', 'fasten', 'insert', 'extract', 'purify', 'recover',
          'recycle', 'clean', 'wash', 'dry', 'evaporate', 'condense', 'ferment', 'synthesize', 'polymerize',
          'oxidize', 'drill', 'transport', 'convey', 'distribute', 'collect', 'capture', 'track', 'communicate',
          'modulate', 'amplify', 'transform', 'limit', 'maintain', 'enhance', 'administer', 'stimulate')
# 'support', 'record', 'process', 'form' excluded before any output: their -s forms are common nouns.
assert len(LEMMAS) == len(set(LEMMAS)) == 120
DOUBLE = {'control', 'transmit', 'stop', 'cut', 'emit', 'drop'}
DETERMINERS = {'a', 'an', 'the', 'said', 'each', 'one', 'or', 'more', 'at', 'least', 'any', 'such'}
STOP = {'for', 'from', 'with', 'without', 'at', 'in', 'into', 'by', 'to', 'through', 'under', 'when', 'while',
        'where', 'which', 'that', 'and', 'or', 'of', 'on', 'so', 'as', 'such', 'than', 'via', 'is', 'are', 'be',
        'being', 'its', 'their', 'thereof', 'wherein', 'whereby'}
CUES = {'configured', 'adapted', 'operable', 'arranged', 'designed', 'capable', 'used'}
CONFIG = {'version': VERSION, 'fields_corpus': ['title', 'abstract', 'claims'], 'lemmas': len(LEMMAS),
          'patterns': ['cue+to/for/of+verb', 'for+verb-ing', 'to+verb', 'verb-s/es finite'],
          'operand': 'skip determiners; up to 3 word tokens; head = last token, plural s stripped',
          'maximum_records_per_family': 16, 'maximum_unit_chars': 4000,
          'semantic_status': 'UNSCREENED_NO_EDGES_ALLOWED'}
BOUNDARY = re.compile(r'\n+|;|(?<=[.!?])\s+(?=[A-Z])')
TOKEN = re.compile(r"[A-Za-z][A-Za-z\-]*|\d+(?:\.\d+)?|[^\sA-Za-z\d]")


def _ing(lemma):
    if lemma in DOUBLE: return lemma + lemma[-1] + 'ing'
    if lemma.endswith('e') and not lemma.endswith('ee'): return lemma[:-1] + 'ing'
    return lemma + 'ing'


def _third(lemma):
    if lemma.endswith('y') and lemma[-2:-1] not in 'aeiou': return lemma[:-1] + 'ies'
    if lemma.endswith(('s', 'x', 'z', 'ch', 'sh', 'o')): return lemma + 'es'
    return lemma + 's'


BASE = {l: l for l in LEMMAS}
ING = {_ing(l): l for l in LEMMAS}
THIRD = {_third(l): l for l in LEMMAS}


def _hash(text): return hashlib.sha256(text.encode('utf-8')).hexdigest()


def _head(word):
    w = word.lower()
    return w[:-1] if len(w) > 3 and w.endswith('s') and not w.endswith('ss') else w


def extract_family_v3(row, fields=('title', 'abstract', 'claims')):
    exact_fields(row, {'id', 'title', 'abstract', 'claims'}); identifier(row['id'])
    if any(type(row[k]) is not str for k in ('title', 'abstract', 'claims')):
        raise InputBoundaryError('invalid source fields')
    records, counts = [], {'units': 0, 'verb_matches': 0, 'unresolved_operand': 0, 'over_length': 0, 'cap_omitted': 0}
    for field in fields:
        text = row[field]; spans, start = [], 0
        for b in BOUNDARY.finditer(text):
            spans.append((start, b.start())); start = b.end()
        spans.append((start, len(text)))
        for a, b in spans:
            unit = text[a:b]
            if not unit.strip(): continue
            counts['units'] += 1
            if len(unit) > CONFIG['maximum_unit_chars']:
                counts['over_length'] += 1; continue
            toks = [(m.group(), a + m.start(), a + m.end()) for m in TOKEN.finditer(unit)]
            for i, (word, ws, we) in enumerate(toks):
                low, prev = word.lower(), toks[i - 1][0].lower() if i else ''
                lemma = cue = None
                if low in ING and (prev == 'for' or (prev == 'of' and i > 1 and toks[i - 2][0].lower() == 'capable')):
                    lemma, cue = ING[low], i - 1
                elif low in BASE and prev == 'to':
                    lemma, cue = BASE[low], i - 1
                elif low in THIRD and prev != 'to':
                    lemma, cue = THIRD[low], i
                if lemma is None: continue
                counts['verb_matches'] += 1
                j = i + 1
                while j < len(toks) and toks[j][0].lower() in DETERMINERS: j += 1
                words = []
                while j < len(toks) and len(words) < 3 and toks[j][0][0].isalpha() and toks[j][0].lower() not in STOP:
                    words.append(toks[j]); j += 1
                if not words:
                    counts['unresolved_operand'] += 1; continue
                if len(records) >= CONFIG['maximum_records_per_family']:
                    counts['cap_omitted'] += 1; continue
                key = lemma + '|' + _head(words[-1][0])
                def span(x, y): return {'start': x, 'end': y, 'text': text[x:y]}
                records.append({'relation_id': _hash(f'{VERSION}|{row["id"]}|{field}|{ws}|{_hash(text)}'),
                    'family_id': row['id'], 'source_field': field, 'source_sha256': _hash(text),
                    'source_span': span(a, b), 'cue_span': span(toks[cue][1], toks[cue][2]),
                    'action_span': span(ws, we), 'operand_span': span(words[0][1], words[-1][2]),
                    'trailing_context_span': span(words[-1][2], b), 'alias_key': _hash(key), 'alias_descriptor': key,
                    'condition_policy': 'retain complete unit; no inferred compatibility',
                    'unresolved_roles': ['subject_attachment', 'condition_attachment', 'cross_record_compatibility'],
                    'semantic_status': 'UNSCREENED_NO_EDGES_ALLOWED'})
    return {'format': VERSION, 'family_id': row['id'], 'records': records, 'counts': counts, 'empty': not records}
