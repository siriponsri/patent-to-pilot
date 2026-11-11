"""Prospective explicit function/operand candidates, never accepted graph edges.

New configuration: semicolon-aware units and lexical action/operand alias keys.
Full unit evidence and trailing context stay attached; role/compatibility claims
still require semantic screening and the frozen owner review gate.
"""
import hashlib
import re

from .mtm_runtime import InputBoundaryError, exact_fields, identifier

VERSION = 'sg-explicit-action-operand-v2'
VERBS = ('receive','transmit','detect','generate','control','adjust','store','convert',
         'reduce','prevent','measure','filter','remove','separate','connect','move',
         'heat','cool','rotate','transfer','compress','expand')
CONFIG = {'version':VERSION,'fields':['abstract','claims'],'maximum_unit_chars':4000,
          'maximum_records_per_family':8,'maximum_operand_words':8,'verbs':list(VERBS),
          'cues':['configured to','adapted to','operable to'],
          'boundaries':'newline;semicolon;sentence punctuation followed by whitespace and uppercase',
          'alias_policy':'same literal action plus operand; casefold/whitespace/leading article only',
          'semantic_status':'UNSCREENED_NO_EDGES_ALLOWED'}
BOUNDARY = re.compile(r'\n+|;|(?<=[.!?])\s+(?=[A-Z])')
CUE = re.compile(r'\b(?:configured|adapted|operable)\s+to\s+',re.IGNORECASE)
ROLE = re.compile(r'(?P<action>[A-Za-z]+)\s+(?P<rest>\S[\s\S]*)')
TAIL = re.compile(r'\s+(?:for|from|with|without|at|in|into|by|to|through|under|when|while|where|which|that|and|or)\b|[,:!?]|(?<!\d)\.|\.(?!\d)',re.IGNORECASE)


def _hash(text): return hashlib.sha256(text.encode('utf-8')).hexdigest()


def extract_family_v2(row):
    exact_fields(row,{'id','title','abstract','claims'}); identifier(row['id'])
    if any(type(row[k]) is not str for k in ('title','abstract','claims')):
        raise InputBoundaryError('invalid source fields')
    records=[]
    counts={'units':0,'cue_occurrences':0,'over_length':0,'unsupported_action':0,
            'unresolved_operand':0,'cap_omitted':0}
    for field in CONFIG['fields']:
        text=row[field]; spans=[]; start=0
        for boundary in BOUNDARY.finditer(text):
            spans.append((start,boundary.start())); start=boundary.end()
        spans.append((start,len(text)))
        for a,b in spans:
            while a<b and text[a].isspace(): a+=1
            while b>a and text[b-1].isspace(): b-=1
            if a==b: continue
            counts['units']+=1; unit=text[a:b]
            for cue in CUE.finditer(unit):
                counts['cue_occurrences']+=1
                if len(unit)>CONFIG['maximum_unit_chars']:
                    counts['over_length']+=1; continue
                match=ROLE.fullmatch(unit[cue.end():])
                if not match or match['action'].casefold() not in VERBS:
                    counts['unsupported_action']+=1; continue
                rest=match['rest']; tail=TAIL.search(rest)
                operand=rest[:tail.start() if tail else len(rest)].rstrip()
                words=operand.split()
                lexical=words[1:] if words and words[0].casefold() in ('a','an','the') else words
                if not lexical or len(words)>CONFIG['maximum_operand_words']:
                    counts['unresolved_operand']+=1; continue
                if len(records)>=CONFIG['maximum_records_per_family']:
                    counts['cap_omitted']+=1; continue
                action_start=a+cue.end()+match.start('action')
                operand_start=a+cue.end()+match.start('rest')
                def span(x,y): return {'start':x,'end':y,'text':text[x:y]}
                key=match['action'].casefold()+'|'+' '.join(lexical).casefold()
                records.append({'relation_id':_hash(f'{VERSION}|{row["id"]}|{field}|{a+cue.start()}|{_hash(text)}'),
                    'family_id':row['id'],'source_field':field,'source_sha256':_hash(text),
                    'source_span':span(a,b),'cue_span':span(a+cue.start(),a+cue.end()),
                    'action_span':span(action_start,action_start+len(match['action'])),
                    'operand_span':span(operand_start,operand_start+len(operand)),
                    'trailing_context_span':span(operand_start+len(operand),b),
                    'alias_key':_hash(key),'alias_descriptor':key,
                    'condition_policy':'retain complete unit; no inferred compatibility',
                    'unresolved_roles':['subject_attachment','condition_attachment','cross_record_compatibility'],
                    'semantic_status':'UNSCREENED_NO_EDGES_ALLOWED'})
    return {'format':VERSION,'family_id':row['id'],'records':records,'counts':counts,'empty':not records}
