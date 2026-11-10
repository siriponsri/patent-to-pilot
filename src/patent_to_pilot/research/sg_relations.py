"""Deterministic explicit functional-clause candidates, never semantic PASS.

This high-precision candidate configuration deliberately abstains from implied
roles, synonyms and conditions. Coverage and graph usefulness must be measured.
"""
import hashlib
import re

from patent_to_pilot.research.mtm_runtime import InputBoundaryError, exact_fields, identifier

VERSION = 'sg-explicit-functional-clause-v1'
CONFIG = {'version': VERSION, 'fields': ['abstract', 'claims'], 'max_records_per_family': 8,
          'max_sentence_chars': 4000, 'subject_max_chars': 200,
          'cues': ['configured to', 'adapted to', 'operable to'],
          'alias_policy': 'exact_case_sensitive_action_clause_identity_only',
          'semantic_acceptance': 'requires_automated_screen_and_solo_review'}
# Split only at newline or sentence punctuation followed by whitespace+uppercase.
# Decimal points are not boundaries. Abbreviation ambiguity remains a review risk.
BOUNDARY = re.compile(r'\n+|(?<=[.!?])\s+(?=[A-Z])')
RELATION = re.compile(r'(?P<subject>\S[^\n]{0,199}?)\s+(?P<cue>(?:is |are )?(?:configured|adapted|operable) to)\s+(?P<action>\S[\s\S]*)\Z')


def extract_family(row):
    exact_fields(row, {'id', 'title', 'abstract', 'claims'})
    identifier(row['id'])
    if any(type(row[k]) is not str for k in ('title', 'abstract', 'claims')):
        raise InputBoundaryError('invalid source fields')
    records, counts = [], {'sentences': 0, 'cue_sentences': 0, 'over_length': 0, 'cap_omitted': 0}
    for field in CONFIG['fields']:
        text = row[field]
        start = 0
        spans = []
        for boundary in BOUNDARY.finditer(text):
            spans.append((start, boundary.start()))
            start = boundary.end()
        spans.append((start, len(text)))
        for a, b in spans:
            while a < b and text[a].isspace(): a += 1
            while b > a and text[b - 1].isspace(): b -= 1
            if a == b: continue
            sentence = text[a:b]
            counts['sentences'] += 1
            if not any(cue in sentence for cue in CONFIG['cues']): continue
            counts['cue_sentences'] += 1
            if len(sentence) > CONFIG['max_sentence_chars']:
                counts['over_length'] += 1
                continue
            match = RELATION.fullmatch(sentence)
            if not match: continue
            if len(records) >= CONFIG['max_records_per_family']:
                counts['cap_omitted'] += 1
                continue
            source_hash = hashlib.sha256(text.encode()).hexdigest()
            rid = hashlib.sha256(f'{VERSION}|{row["id"]}|{field}|{a}|{b}|{source_hash}'.encode()).hexdigest()
            role_spans = {role: {'start': a + match.start(role), 'end': a + match.end(role),
                                 'text': match[role]} for role in ('subject', 'cue', 'action')}
            records.append({'relation_id': rid, 'family_id': row['id'], 'source_field': field,
                'source_sha256': source_hash, 'source_span': {'start': a, 'end': b, 'text': sentence},
                'roles': role_spans, 'operand': None, 'effect': None,
                'condition_policy': 'retained_verbatim_in_full_clause_not_separately_attached',
                'unresolved_roles': ['operand', 'effect', 'condition_attachment'],
                'alias_key': hashlib.sha256(('action_clause|' + match['action']).encode()).hexdigest(),
                'semantic_status': 'UNSCREENED_NO_EDGES_ALLOWED'})
    return {'format': VERSION, 'family_id': row['id'], 'records': records, 'counts': counts,
            'empty': not records, 'publication_metadata': 'NOT_AVAILABLE_IN_STAGED_CORPUS_NO_INVENTED_IDS'}
