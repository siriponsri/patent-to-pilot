"""Integrity of fixed retained samples, not semantic fidelity or corpus recheck."""
import hashlib
import json
import re
from .mtm_runtime import InputBoundaryError
from .sg_materialization_v1 import SALT
from .sg_relations_v2 import VERSION, CONFIG


def check_samples(source, aliases):
    def require(condition, message):
        if not condition: raise InputBoundaryError(message)
    seen = {}
    def record(row):
        require(row['source_field'] in CONFIG['fields'], 'unexpected source field')
        require(type(row['source_sha256']) is str and re.fullmatch('[0-9a-f]{64}',row['source_sha256']) is not None,
                'invalid source hash')
        span = row['source_span']; start, end, text = span['start'], span['end'], span['text']
        require(type(start) is int and type(end) is int and 0 <= start < end and len(text)==end-start,
                'source unit offsets invalid')
        for key in ['cue_span', 'action_span', 'operand_span', 'trailing_context_span']:
            part = row[key]; a, b = part['start'], part['end']
            require(type(a) is int and type(b) is int and start <= a <= b <= end,
                    'role outside retained unit')
            require(text[a-start:b-start] == part['text'], 'retained role text mismatch')
        words = row['operand_span']['text'].split()
        words = words[1:] if words and words[0].casefold() in ('a','an','the') else words
        descriptor = row['action_span']['text'].casefold()+'|'+' '.join(words).casefold()
        require(descriptor == row['alias_descriptor'], 'alias normalization mismatch')
        require(hashlib.sha256(descriptor.encode()).hexdigest()==row['alias_key'], 'alias hash mismatch')
        require(row['semantic_status']=='UNSCREENED_NO_EDGES_ALLOWED', 'unexpected accepted status')
        identity=f"{VERSION}|{row['family_id']}|{row['source_field']}|{row['cue_span']['start']}|{row['source_sha256']}"
        require(hashlib.sha256(identity.encode()).hexdigest()==row['relation_id'], 'relation identity mismatch')
        body=hashlib.sha256(json.dumps(row,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
        require(row['relation_id'] not in seen or seen[row['relation_id']]==body, 'conflicting relation body')
        seen[row['relation_id']]=body
    families = source['records_by_family']
    require(source['no_substitution'] is True and len(families)==100, 'fixed source sample contract')
    for fid, rows in families.items():
        for row in rows:
            require(row['family_id']==fid, 'source sample family mismatch'); record(row)
    require(aliases['salt']==SALT and len(aliases['sample'])==100, 'fixed alias sample contract')
    require(aliases['uses_queries_qrels_retrieval_scores'] is False, 'unexpected evaluator input')
    digests = []
    for pair in aliases['sample']:
        members = pair['families']; require(len(members)==2 and members==sorted(set(members)), 'pair membership')
        require(len(pair['relation_ids'])==2, 'pair witness count')
        canonical=json.dumps([pair['alias_key'],*members],ensure_ascii=False,separators=(',',':'))
        digest=hashlib.sha256((SALT+canonical).encode()).hexdigest()
        require(digest==pair['sampling_sha256'], 'pair sampling identity mismatch'); digests.append(digest)
        for fid, rid in zip(members,pair['relation_ids']):
            row=aliases['witness_records'][rid]
            require(row['relation_id']==rid and row['family_id']==fid and row['alias_key']==pair['alias_key'],
                    'pair witness binding mismatch'); record(row)
    require(digests==sorted(set(digests)), 'duplicate or unsorted sample')
    return {'status':'PASS_RETAINED_SAMPLE_INTEGRITY_ONLY', 'source_families':len(families),
        'source_families_without_extracted_records':sum(not rows for rows in families.values()),
        'source_records':sum(len(rows) for rows in families.values()), 'alias_pair_units':len(digests),
        'unique_records_checked':len(seen), 'semantic_fidelity':'NOT_ASSESSED',
        'full_source_hash_reverification':'NOT_RUN_NO_CORPUS_READ',
        'sample_rank_against_full_population':'NOT_RECOMPUTED_FROZEN_MATERIALIZATION_RECEIPT',
        'accepted_edges':0,'cards_issued':0,'model_calls':0,'retrieval':'NOT_RUN'}
