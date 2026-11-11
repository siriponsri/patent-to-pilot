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


def preflight_graph(manifest,*,count_tokens,write_request,check_admission):
    if len(manifest['units'])!=114 or len(manifest['coverage'])!=100:
        raise InputBoundaryError('fixed Graph preflight denominator')
    results=[]
    for index,unit in enumerate(manifest['units']):
        check_admission(index)
        row={'query_id':unit['query_id'],'unit_type':unit['unit_type'],
            'stable_id_sha256':hashlib.sha256(unit['stable_id'].encode()).hexdigest()}
        try:prepared=request(unit)
        except InputBoundaryError as error:
            if str(error)!='catalogue too large; no truncation':raise
            row.update(status='CATALOGUE_LIMIT',input_tokens=None)
        else:
            before=json.dumps(prepared['messages'],ensure_ascii=False,sort_keys=True).encode()
            count=count_tokens(prepared['messages'])
            if (type(count) is not int or count<1 or
                    json.dumps(prepared['messages'],ensure_ascii=False,sort_keys=True).encode()!=before):
                raise InputBoundaryError('Graph tokenizer altered request or count')
            row.update(status='INPUT_LIMIT' if count>8192 else 'ADMITTED',input_tokens=count,
                messages_sha256=prepared['messages_sha256'],binding_sha256=prepared['binding_sha256'])
            write_request(index,prepared)
        results.append(row)
    risks=sum(r['status']!='ADMITTED' for r in results)
    return {'status':'STOP_GRAPH_INPUT_RISK_CAP' if risks>20 else 'PASS_GRAPH_INPUT_ADMISSION_WITH_RISKS',
        'units':results,'risk_units':risks,'screening_units':114,'source_coverage_units':100,
        'source_abstentions':sum(r['status']=='ABSTENTION' for r in manifest['coverage']),
        'model_calls':0,'semantic_fidelity':'NOT_ASSESSED','retrieval':'NOT_RUN','cards_issued':0}
