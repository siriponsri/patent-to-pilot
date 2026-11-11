"""Fixed R6 source/alias union and full-context screening; no corpus extraction."""
import hashlib
import json
from .mtm_runtime import InputBoundaryError, exact_fields
from .sg_sample_integrity import check_samples


def fixed_union(source_sample, aliases):
    checked=check_samples(source_sample,aliases)
    alias_ids={fid for pair in aliases['sample'] for fid in pair['families']}
    union=set(source_sample['records_by_family']) | alias_ids
    if (checked['source_families_without_extracted_records']!=86
            or len(alias_ids)!=183 or len(union)!=282):
        raise InputBoundaryError('R6 frozen sample cardinalities changed')
    return sorted(union)


def build_manifest(source_rows, source_sample, aliases):
    from .r6_critic_tasks import RECORD_CRITERIA, ALIAS_CRITERIA
    expected=fixed_union(source_sample,aliases)
    rows={row['id']:row for row in source_rows}
    if len(rows)!=len(source_rows) or sorted(rows)!=expected:
        raise InputBoundaryError('R6 complete fixed282 source join required')
    for row in rows.values():
        exact_fields(row,{'id','title','abstract','claims'})
        if any(type(v) is not str for v in row.values()):
            raise InputBoundaryError('unexpected source fields')

    def verify(record):
        row=rows[record['family_id']]; text=row[record['source_field']]
        span=record['source_span']
        if (hashlib.sha256(text.encode()).hexdigest()!=record['source_sha256']
                or text[span['start']:span['end']]!=span['text']):
            raise InputBoundaryError('retained record does not match complete source')

    def full(fid):
        row=rows[fid]
        return 'TITLE\n'+row['title']+'\nABSTRACT\n'+row['abstract']+'\nCLAIMS\n'+row['claims']

    coverage=[]; units=[]
    for fid,records in sorted(source_sample['records_by_family'].items()):
        for record in records:verify(record)
        coverage.append({'family_id':fid,'record_count':len(records),
            'status':'SCREENING_PENDING' if records else 'ABSTENTION',
            'semantic_pass':False})
        if records:
            units.append({'stable_id':fid,'unit_type':'source','source':full(fid),
                'artifacts':{'extracted_records':json.dumps(records,ensure_ascii=False,sort_keys=True,separators=(',',':'))},
                'criteria':dict(RECORD_CRITERIA),'scope':{'branch':'SG_RECORD','coverage':'retained claims only; full sample coverage reported separately'},
                'record_count':len(records)})
    for pair in aliases['sample']:
        records=[aliases['witness_records'][rid] for rid in pair['relation_ids']]
        for record in records:verify(record)
        candidate={'claim':'same positive technical function with individual contexts retained; no interchangeability',
            'pair':pair,'witness_records':records}
        units.append({'stable_id':pair['sampling_sha256'],'unit_type':'alias',
            'source':'FAMILY_A\n'+full(pair['families'][0])+'\nFAMILY_B\n'+full(pair['families'][1]),
            'artifacts':{'candidate_pair':json.dumps(candidate,ensure_ascii=False,sort_keys=True,separators=(',',':'))},
            'criteria':dict(ALIAS_CRITERIA),'scope':{'branch':'SG_ALIAS','full_family_source':'PROVIDED',
                'acceptance':'fixed witness pair only; no interchangeability or common operating ranges'},'record_count':2})
    for i,unit in enumerate(units):unit['query_id']=f'sg-r6-{i:03}'
    if len(units)!=114 or len(coverage)!=100:
        raise InputBoundaryError('R6 fixed task or coverage denominator changed')
    return {'version':'sg-r6-fixed114-full282','fixed_family_ids':expected,
        'coverage':coverage,'units':units,'semantic_pass':False,'accepted_edges':0}


def request(unit):
    from .reference_critic_v1 import prepare
    return prepare(**{k:unit[k] for k in ('query_id','source','artifacts','criteria','scope')})
